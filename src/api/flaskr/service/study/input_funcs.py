# 输入处理的函数
# 全部的输入处理函数都在这里
# 正常返回为yield，异常返回为raise


import json
import time
from trace import Trace
from flask import Flask
from sqlalchemy import func

from flaskr.service.order.consts import ATTEND_STATUS_BRANCH, ATTEND_STATUS_IN_PROGRESS
from flaskr.service.study.models import AICourseAttendAsssotion
from flaskr.service.lesson.const import UI_TYPE_BRANCH
from flaskr.service.view.models import INPUT_TYPE_SELECT, INPUT_TYPE_TEXT
from flaskr.api.llm import invoke_llm
from flaskr.api.edun import check_text
from flaskr.service.common.models import AppException
from flaskr.service.profile.funcs import (
    get_user_profiles,
    save_user_profiles,
    get_user_profile_labels,
    update_user_profile_with_lable,
)
from flaskr.service.study.utils import extract_json, generation_attend, get_fmt_prompt
from flaskr.service.user import verify_sms_code_without_phone
from flaskr.service.check_risk import add_risk_control_result

from ...service.lesson.models import AILesson, AILessonScript
from ...service.order.models import AICourseLessonAttend
from ...service.study.const import (
    INPUT_TYPE_CHECKCODE,
    INPUT_TYPE_CONTINUE,
    INPUT_TYPE_LOGIN,
    INPUT_TYPE_PHONE,
    INPUT_TYPE_START,
    ROLE_STUDENT,
    ROLE_TEACHER,
)
from ...dao import db
from .utils import (
    make_script_dto,
    get_profile_array,
    check_phone_number,
)
from flaskr.util.uuid import generate_id


class BreakException(Exception):
    pass


UI_HANDLE_MAP = {}


def register_input_handler(input_type: str):
    def decorator(func):
        print(f"register_input_handler {input_type} ==> {func.__name__}")
        UI_HANDLE_MAP[input_type] = func
        return func

    return decorator


@register_input_handler(input_type=INPUT_TYPE_TEXT)
def handle_input_text(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    prompt = get_fmt_prompt(
        app, user_id, script_info.script_check_prompt, input, script_info.script_profile
    )
    # todo 换成通用的
    log_script = generation_attend(app, attend, script_info)
    log_script.script_content = input
    log_script.script_role = ROLE_STUDENT
    db.session.add(log_script)
    span = trace.span(name="user_input", input=input)
    res = check_text(log_script.log_id, input)
    span.event(name="check_text", input=input, output=res)
    add_risk_control_result(
        app, log_script.log_id, user_id, input, "edun", str(res), "", 1, "check_text"
    )
    resp = invoke_llm(
        app,
        span,
        model=script_info.script_model,
        json=True,
        stream=True,
        temperature=script_info.script_temprature,
        message=prompt,
    )
    response_text = ""
    check_success = False
    for i in resp:
        current_content = i.result
        if isinstance(current_content, str):
            response_text += current_content
    jsonObj = extract_json(app, response_text)
    check_success = jsonObj.get("result", "") == "ok"
    if check_success:
        app.logger.info("check success")
        profile_tosave = jsonObj.get("parse_vars")
        save_user_profiles(app, user_id, profile_tosave)
        for key in profile_tosave:
            yield make_script_dto(
                "profile_update",
                {"key": key, "value": profile_tosave[key]},
                script_info.script_id,
            )
            time.sleep(0.01)
        span.end()
        db.session.flush()

    else:
        reason = jsonObj.get("reason", response_text)
        for text in reason:
            yield make_script_dto("text", text, script_info.script_id)
            time.sleep(0.01)
        yield make_script_dto("text_end", "", script_info.script_id)
        log_script = generation_attend(app, attend, script_info)
        log_script.script_content = reason
        log_script.script_role = ROLE_TEACHER
        db.session.add(log_script)
        span.end(output=response_text)
        trace_args["output"] = trace_args["output"] + "\r\n" + response_text
        trace.update(**trace_args)
        db.session.flush()
        yield make_script_dto(
            "input", script_info.script_ui_content, script_info.script_id
        )
        raise BreakException


@register_input_handler(input_type=INPUT_TYPE_CONTINUE)
def handle_input_continue(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    log_script = generation_attend(app, attend, script_info)
    log_script.script_content = input
    log_script.script_role = ROLE_STUDENT
    db.session.add(log_script)
    span = trace.span(name="user_continue", input=input)
    span.end()
    # 分支课程
    if script_info.script_ui_type == UI_TYPE_BRANCH:
        app.logger.info(
            "script_id:{},branch:{}".format(
                script_info.script_id, script_info.script_other_conf
            )
        )
        branch_info = json.loads(script_info.script_other_conf)
        branch_key = branch_info.get("var_name", "")
        profile = get_user_profiles(app, user_id, [branch_key])
        branch_value = profile.get(branch_key, "")
        jump_rule = branch_info.get("jump_rule", [])

        app.logger.info("branch key:{}".format(branch_key))

        if attend.status != ATTEND_STATUS_BRANCH:
            for rule in jump_rule:
                app.logger.info(
                    "rule value:{},branch_value:{}".format(
                        rule.get("value", ""), branch_value
                    )
                )
                if branch_value == rule.get("value", ""):
                    app.logger.info("found branch rule")
                    attend_info = AICourseLessonAttend.query.filter(
                        AICourseLessonAttend.attend_id == attend.attend_id
                    ).first()
                    next_lesson = AILesson.query.filter(
                        AILesson.lesson_feishu_id == rule.get("lark_table_id", ""),
                        AILesson.status == 1,
                        func.length(AILesson.lesson_no) > 2,
                    ).first()
                    if next_lesson:
                        next_attend = AICourseLessonAttend.query.filter(
                            AICourseLessonAttend.user_id == user_id,
                            AICourseLessonAttend.course_id == next_lesson.course_id,
                            AICourseLessonAttend.lesson_id == next_lesson.lesson_id,
                        ).first()
                        if next_attend is None:
                            next_attend = AICourseLessonAttend()
                            next_attend.user_id = user_id
                            next_attend.course_id = next_lesson.course_id
                            next_attend.lesson_id = next_lesson.lesson_id
                            next_attend.attend_id = generate_id(app)
                            db.session.add(next_attend)
                        if next_attend:
                            assoation = AICourseAttendAsssotion.query.filter(
                                AICourseAttendAsssotion.from_attend_id
                                == attend_info.attend_id,  # noqa: W503
                                AICourseAttendAsssotion.to_attend_id
                                == next_attend.attend_id,  # noqa: W503
                            ).first()
                            if not assoation:
                                assoation = AICourseAttendAsssotion()
                                assoation.from_attend_id = attend_info.attend_id
                                assoation.to_attend_id = next_attend.attend_id
                                assoation.user_id = user_id
                                db.session.add(assoation)
                            next_attend.status = ATTEND_STATUS_IN_PROGRESS
                            next_attend.script_index = -1
                            attend_info.status = ATTEND_STATUS_BRANCH
                            attend_info = next_attend
                            app.logger.info("branch jump")
                    else:
                        app.logger.info(
                            "branch lesson not found: {}".format(
                                rule.get("lark_table_id", "")
                            )
                        )

    db.session.flush()


@register_input_handler(input_type=INPUT_TYPE_SELECT)
def handle_input_select(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    profile_keys = get_profile_array(script_info.script_ui_profile)
    profile_tosave = {}
    if len(profile_keys) == 0:
        btns = json.loads(script_info.script_other_conf)
        conf_key = btns.get("var_name", "input")
        profile_tosave[conf_key] = input
    for k in profile_keys:
        profile_tosave[k] = input
    save_user_profiles(app, user_id, profile_tosave)
    log_script = generation_attend(app, attend, script_info)
    log_script.script_content = input
    log_script.script_role = ROLE_STUDENT
    db.session.add(log_script)
    span = trace.span(name="user_select", input=input)
    span.end()
    db.session.flush()


@register_input_handler(input_type=INPUT_TYPE_PHONE)
def handle_input_phone(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    log_script = generation_attend(app, attend, script_info)
    log_script.script_content = input
    log_script.script_role = ROLE_STUDENT  # type: ignore
    db.session.add(log_script)
    span = trace.span(name="user_input_phone", input=input)
    response_text = "请输入正确的手机号"
    if not check_phone_number(app, user_id, input):
        for i in response_text:
            yield make_script_dto("text", i, script_info.script_id)
            time.sleep(0.01)
        yield make_script_dto("text_end", "", script_info.script_id)
        yield make_script_dto(
            INPUT_TYPE_PHONE, script_info.script_ui_content, script_info.script_id
        )
        log_script = generation_attend(app, attend, script_info)
        log_script.script_content = response_text
        log_script.script_role = ROLE_TEACHER
        db.session.add(log_script)
        span.end(output=response_text)
        db.session.flush()
        raise BreakException
    span.end()


@register_input_handler(input_type=INPUT_TYPE_CHECKCODE)
def handle_input_checkcode(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    try:
        origin_user_id = user_id
        ret = verify_sms_code_without_phone(app, user_id, input)
        verify_user_id = ret.userInfo.user_id
        if origin_user_id != verify_user_id:
            app.logger.info(
                f"origin_user_id:{origin_user_id},verify_user_id:{verify_user_id} copy profile"
            )
            new_profiles = get_user_profile_labels(app, origin_user_id)
            update_user_profile_with_lable(app, verify_user_id, new_profiles)
        yield make_script_dto(
            "profile_update",
            {"key": "phone", "value": ret.userInfo.mobile},
            script_info.script_id,
        )
        yield make_script_dto(
            "user_login",
            {
                "phone": ret.userInfo.mobile,
                "user_id": ret.userInfo.user_id,
                "token": ret.token,
            },
            script_info.script_id,
        )
        input = None
        span = trace.span(name="user_input_phone", input=input)
        span.end()
    except AppException as e:
        for i in e.message:
            yield make_script_dto("text", i, script_info.script_id)
            time.sleep(0.01)
        yield make_script_dto("text_end", "", script_info.script_id)
        yield make_script_dto(
            INPUT_TYPE_CHECKCODE, script_info.script_ui_content, script_info.script_id
        )
        log_script = generation_attend(app, attend, script_info)
        log_script.script_content = e.message
        log_script.script_role = ROLE_TEACHER
        db.session.add(log_script)
        raise BreakException


@register_input_handler(input_type=INPUT_TYPE_LOGIN)
def handle_input_login(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    # todo
    yield make_script_dto(
        INPUT_TYPE_LOGIN,
        # {"phone": ret.userInfo.mobile, "user_id": ret.userInfo.user_id},
        script_info.script_id,
    )


@register_input_handler(input_type=INPUT_TYPE_START)
def handle_input_start(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    return None


def handle_input(
    app: Flask,
    user_id: str,
    input_type: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    app.logger.info(f"handle_input {input_type},user_id:{user_id},input:{input} ")
    if input_type in UI_HANDLE_MAP:
        respone = UI_HANDLE_MAP[input_type](
            app, user_id, attend, script_info, input, trace, trace_args
        )
        if respone:
            yield from respone
    else:
        return None
