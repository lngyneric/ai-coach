import time
import traceback
from typing import Generator
from flask import Flask

from flaskr.service.common.models import COURSE_NOT_FOUND
from flaskr.service.user.models import User
from ...api.langfuse import langfuse_client as langfuse
from ...service.lesson.const import (
    UI_TYPE_CHECKCODE,
    UI_TYPE_CONTINUED,
    UI_TYPE_PHONE,
    UI_TYPE_TO_PAY,
)
from ...service.lesson.models import AICourse, AILesson
from ...service.order.consts import (
    ATTEND_STATUS_IN_PROGRESS,
    ATTEND_STATUS_NOT_STARTED,
    BUY_STATUS_SUCCESS,
)
from ...service.order.funs import (
    AICourseLessonAttendDTO,
    init_trial_lesson,
    query_raw_buy_record,
)
from ...service.order.models import AICourseBuyRecord, AICourseLessonAttend
from ...service.study.const import (
    INPUT_TYPE_START,
)
from ...service.study.dtos import ScriptDTO
from ...dao import db, redis_client
from .utils import (
    make_script_dto,
    get_script,
    get_script_by_id,
    update_attend_lesson_info,
    get_current_lesson,
)
from .input_funcs import BreakException, handle_input
from .output_funcs import handle_output
from .ui_funcs import handle_ui


def run_script_inner(
    app: Flask,
    user_id: str,
    course_id: str,
    lesson_id: str = None,
    input: str = None,
    input_type: str = None,
    script_id: str = None,
) -> Generator[str, None, None]:
    with app.app_context():
        try:
            course_info = AICourse.query.filter(AICourse.course_id == course_id).first()
            user_info = User.query.filter(User.user_id == user_id).first()
            if not course_info:
                course_info = AICourse.query.first()
                course_id = course_info.course_id
            if not lesson_id:
                app.logger.info("lesson_id is None")
                buy_record = AICourseBuyRecord.query.filter_by(
                    user_id=user_id, course_id=course_id
                ).first()
                if not buy_record:

                    app.logger.info(
                        "user_id:{},course_id:{},lesson_id:{}".format(
                            user_id, course_id, lesson_id
                        )
                    )
                lessons = init_trial_lesson(app, user_id, course_id)
                attend = get_current_lesson(app, lessons)
                app.logger.info("{}".format(attend))
                lesson_id = attend.lesson_id

            else:
                # get attend info
                app.logger.info(
                    "user_id:{},course_id:{},lesson_id:{}".format(
                        user_id, course_id, lesson_id
                    )
                )
                # 查找lesson_id
                lesson_info = AILesson.query.filter(
                    AILesson.lesson_id == lesson_id,
                    AILesson.status == 1,
                ).first()
                if not lesson_info:
                    raise COURSE_NOT_FOUND

                parent_no = lesson_info.lesson_no
                if len(parent_no) >= 2:
                    parent_no = parent_no[:-2]

                lessons = AILesson.query.filter(
                    AILesson.lesson_no.like(parent_no + "__"),
                    AILesson.status == 1,
                ).all()
                app.logger.info(
                    "study lesson no :{}".format(
                        ",".join([lesson.lesson_no for lesson in lessons])
                    )
                )
                lesson_ids = [lesson.lesson_id for lesson in lessons]
                attend_info = AICourseLessonAttend.query.filter(
                    AICourseLessonAttend.user_id == user_id,
                    AICourseLessonAttend.course_id == course_id,
                    AICourseLessonAttend.lesson_id.in_(lesson_ids),
                    AICourseLessonAttend.status.in_(
                        [ATTEND_STATUS_NOT_STARTED, ATTEND_STATUS_IN_PROGRESS]
                    ),
                ).first()
                app.logger.info(
                    "attend_info -- attend_id:{},lesson_id:{}".format(
                        attend_info.attend_id, attend_info.lesson_id
                    )
                )
                lesson_id = attend_info.lesson_id
                if not attend_info:
                    # 没有课程记录
                    for i in "请购买课程":
                        yield make_script_dto("text", i, None)
                        time.sleep(0.01)
                    yield make_script_dto("text_end", "", None)
                    return
                attend = AICourseLessonAttendDTO(
                    attend_info.attend_id,
                    attend_info.lesson_id,
                    attend_info.course_id,
                    attend_info.user_id,
                    attend_info.status,
                    attend_info.script_index,
                )
                db.session.flush()
            # Langfuse 集成
            trace_args = {}
            trace_args["user_id"] = user_id
            trace_args["session_id"] = attend.attend_id
            trace_args["input"] = input
            trace_args["name"] = "ai-python"
            trace = langfuse.trace(**trace_args)
            trace_args["output"] = ""
            next = False
            # 如果有用户输入,就得到当前这一条,否则得到下一条
            if script_id:
                # 如果有指定脚本
                # 为了测试使用
                script_info = get_script_by_id(app, script_id)
            else:
                # 获取当前脚本
                script_info, attend_updates = get_script(
                    app, attend_id=attend.attend_id, next=next
                )
                if len(attend_updates) > 0:
                    for attend_update in attend_updates:
                        if len(attend_update.lesson_no) > 2:
                            yield make_script_dto(
                                "lesson_update", attend_update.__json__(), ""
                            )
                        else:
                            yield make_script_dto(
                                "chapter_update", attend_update.__json__(), ""
                            )
            if script_info:
                try:
                    check_paid = True
                    # 如果是购课的脚本
                    if script_info.script_ui_type == UI_TYPE_TO_PAY:
                        order = query_raw_buy_record(app, user_id, course_id)
                        if order and order.status == BUY_STATUS_SUCCESS:
                            # 如果已经购买
                            check_paid = True
                        else:
                            check_paid = False

                    else:
                        # 处理用户输入
                        response = handle_input(
                            app,
                            user_id,
                            input_type,
                            attend,
                            script_info,
                            input,
                            trace,
                            trace_args,
                        )
                        if response:
                            yield from response
                    # 如果是Start或是Continue，就不需要再次获取脚本
                    if input_type == INPUT_TYPE_START:
                        next = False
                    else:
                        next = check_paid
                    while True:
                        if next:
                            script_info, attend_updates = get_script(
                                app, attend_id=attend.attend_id, next=next
                            )
                        next = True
                        if len(attend_updates) > 0:
                            for attend_update in attend_updates:
                                if len(attend_update.lesson_no) > 2:
                                    yield make_script_dto(
                                        "lesson_update", attend_update.__json__(), ""
                                    )
                                else:
                                    yield make_script_dto(
                                        "chapter_update", attend_update.__json__(), ""
                                    )
                        if script_info:
                            response = handle_output(
                                app,
                                user_id,
                                attend,
                                script_info,
                                input,
                                trace,
                                trace_args,
                            )
                            if response:
                                yield from response
                            if script_info.script_ui_type == UI_TYPE_CONTINUED:
                                continue
                            if (
                                script_info.script_ui_type == UI_TYPE_PHONE
                                and user_info.user_state != 0
                            ):
                                continue
                            if (
                                script_info.script_ui_type == UI_TYPE_CHECKCODE
                                and user_info.user_state != 0
                            ):
                                continue

                            break
                        else:
                            break
                    if script_info:
                        # 返回下一轮交互
                        # 返回  下一轮的交互方式
                        if script_info.script_ui_type == UI_TYPE_CONTINUED:
                            next = True
                            input_type = None
                        else:
                            yield from handle_ui(
                                app,
                                user_id,
                                attend,
                                script_info,
                                input,
                                trace,
                                trace_args,
                            )

                    else:
                        attends = update_attend_lesson_info(app, attend.attend_id)
                        for attend_update in attends:
                            if len(attend_update.lesson_no) > 2:
                                yield make_script_dto(
                                    "lesson_update", attend_update.__json__(), ""
                                )
                            else:
                                yield make_script_dto(
                                    "chapter_update", attend_update.__json__(), ""
                                )
                        app.logger.info("script_info is None")
                except BreakException:
                    # app.logger.error("BreakException")
                    # app.logger.error(e)
                    db.session.commit()
                    return
            else:
                app.logger.info("script_info is None,to update attend")
                attends = update_attend_lesson_info(app, attend.attend_id)
                for attend_update in attends:
                    if len(attend_update.lesson_no) > 2:
                        yield make_script_dto(
                            "lesson_update", attend_update.__json__(), ""
                        )
                    else:
                        yield make_script_dto(
                            "chapter_update", attend_update.__json__(), ""
                        )
            db.session.commit()
        except GeneratorExit:
            db.session.rollback()
            app.logger.info("GeneratorExit")


def run_script(
    app: Flask,
    user_id: str,
    course_id: str,
    lesson_id: str = None,
    input: str = None,
    input_type: str = None,
    script_id: str = None,
) -> Generator[ScriptDTO, None, None]:
    timeout = 5 * 60
    blocking_timeout = 1
    lock_key = app.config.get("REDIS_KEY_PRRFIX") + ":run_script:" + user_id
    lock = redis_client.lock(
        lock_key, timeout=timeout, blocking_timeout=blocking_timeout
    )
    if lock.acquire(blocking=True):
        try:
            app.logger.info("run_script with lock")
            yield from run_script_inner(
                app, user_id, course_id, lesson_id, input, input_type, script_id
            )
            app.logger.info("run_script end")
        except Exception as e:
            app.logger.error("run_script error")
            # 输出详细的错误信息
            app.logger.error(e)
            # 输出异常信息
            error_info = {
                "name": type(e).__name__,
                "description": str(e),
                "traceback": traceback.format_exc(),
            }
            app.logger.error(error_info)
            yield make_script_dto("text", "系统错误", None)
            yield make_script_dto("text_end", "", None)
        finally:

            lock.release()
            app.logger.info("run_script release lock")
        return
    else:

        app.logger.info("lockfail")
        yield make_script_dto("text_end", "", None)
    return
