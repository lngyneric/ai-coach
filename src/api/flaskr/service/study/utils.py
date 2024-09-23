import datetime
import json
import re
from flask import Flask
from flaskr.util.uuid import generate_id
from langchain.prompts import PromptTemplate
from ...service.lesson.const import (
    LESSON_TYPE_BRANCH_HIDDEN,
    SCRIPT_TYPE_SYSTEM,
)
from ...service.lesson.models import AILesson, AILessonScript
from ...service.order.consts import (
    ATTEND_STATUS_BRANCH,
    ATTEND_STATUS_COMPLETED,
    ATTEND_STATUS_IN_PROGRESS,
    ATTEND_STATUS_LOCKED,
    ATTEND_STATUS_NOT_STARTED,
    ATTEND_STATUS_RESET,
    ATTEND_STATUS_VALUES,
)
from ...service.order.funs import (
    AICourseLessonAttendDTO,
)
from ...service.order.models import AICourseLessonAttend
from ...service.profile.funcs import get_user_profiles
from ...service.study.dtos import AILessonAttendDTO, ScriptDTO
from ...service.study.models import AICourseAttendAsssotion, AICourseLessonAttendScript
from ...dao import db


def get_current_lesson(
    app: Flask, lesssons: list[AICourseLessonAttendDTO]
) -> AICourseLessonAttendDTO:
    return lesssons[0]


def generation_attend(
    app: Flask, attend: AICourseLessonAttendDTO, script_info: AILessonScript
) -> AICourseLessonAttendScript:
    attendScript = AICourseLessonAttendScript()
    attendScript.attend_id = attend.attend_id
    attendScript.user_id = attend.user_id
    attendScript.lesson_id = script_info.lesson_id
    attendScript.course_id = attend.course_id
    attendScript.script_id = script_info.script_id
    attendScript.log_id = generate_id(app)
    return attendScript


def check_phone_number(app, user_id, input):
    if not re.match(r"^1[3-9]\d{9}$", input):
        return False
    return True


# 得到一个课程的System Prompt


def get_lesson_system(lesson_id: str) -> str:
    # 缓存逻辑
    lesson_ids = [lesson_id]
    lesson = AILesson.query.filter(AILesson.lesson_id == lesson_id).first()
    lesson_no = lesson.lesson_no
    parent_no = lesson_no
    if len(parent_no) > 2:
        parent_no = parent_no[:2]
    if parent_no != lesson_no:
        parent_lesson = AILesson.query.filter(AILesson.lesson_no == parent_no).first()
        if parent_lesson:
            lesson_ids.append(parent_lesson.lesson_id)
    scripts = AILessonScript.query.filter(
        AILessonScript.lesson_id.in_(lesson_ids) is True,
        AILessonScript.script_type == SCRIPT_TYPE_SYSTEM,
    ).all()
    if len(scripts) > 0:
        for script in scripts:
            if script.lesson_id == lesson_id:
                return script.script_prompt
        return scripts[0].script_prompt
    return None


def fmt(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    else:
        return o.__json__()


def get_profile_array(profile: str) -> list:
    return re.findall(r"\[(.*?)\]", profile)


def get_lesson_and_attend_info(app: Flask, parent_no, course_id, user_id):
    lessons = AILesson.query.filter(
        AILesson.lesson_no.like(parent_no + "%"),
        AILesson.course_id == course_id,
        AILesson.lesson_type != LESSON_TYPE_BRANCH_HIDDEN,
        AILesson.status == 1,
    ).all()
    if len(lessons) == 0:
        return []
    app.logger.info(
        "lessons:{}".format(
            ",".join("'" + lesson.lesson_no + "'" for lesson in lessons)
        )
    )
    attend_infos = AICourseLessonAttend.query.filter(
        AICourseLessonAttend.lesson_id.in_([lesson.lesson_id for lesson in lessons]),
        AICourseLessonAttend.user_id == user_id,
        AICourseLessonAttend.status != ATTEND_STATUS_RESET,
    ).all()
    attend_lesson_infos = [
        {
            "attend": attend,
            "lesson": [
                lesson for lesson in lessons if lesson.lesson_id == attend.lesson_id
            ][0],
        }
        for attend in attend_infos
    ]
    attend_lesson_infos = sorted(
        attend_lesson_infos,
        key=lambda x: (len(x["lesson"].lesson_no), x["lesson"].lesson_no),
    )
    app.logger.info(
        "attends:{}".format(
            ",".join("'" + a["lesson"].lesson_no + "'" for a in attend_lesson_infos)
        )
    )
    return attend_lesson_infos


# 从文本中提取json对象
def extract_json(app: Flask, text: str):
    stack = []
    start = None
    for i, char in enumerate(text):
        if char == "{":
            if not stack:
                start = i
            stack.append(char)
        elif char == "}":
            if stack:
                stack.pop()
                if not stack:
                    json_str = text[start : i + 1]  # noqa
                    try:
                        json_obj = json.loads(json_str)
                        return json_obj
                    except json.JSONDecodeError:
                        pass
    return {}


def extract_variables(template: str) -> list:
    # 使用正则表达式匹配单层 {} 中的内容，忽略双层大括号
    pattern = r"\{([^{}]+)\}(?!})"
    matches = re.findall(pattern, template)

    # 去重并过滤包含双引号的元素
    variables = list(set(matches))
    filtered_variables = [var for var in variables if '"' not in var]
    return filtered_variables


def get_fmt_prompt(
    app: Flask,
    user_id: str,
    profile_tmplate: str,
    input: str = None,
    profile_array_str: str = None,
) -> str:
    app.logger.info("raw prompt:" + profile_tmplate)
    propmpt_keys = []
    profiles = {}
    if profile_array_str:
        propmpt_keys = get_profile_array(profile_array_str)
        profiles = get_user_profiles(app, user_id, propmpt_keys)
    else:
        profiles = get_user_profiles(app, user_id)
        propmpt_keys = list(profiles.keys())
    if input:
        profiles["input"] = input
        propmpt_keys.append("input")
    app.logger.info(propmpt_keys)
    app.logger.info(profiles)
    prompt_template_lc = PromptTemplate.from_template(profile_tmplate)
    keys = extract_variables(profile_tmplate)
    fmt_keys = {}
    for key in keys:
        if key in profiles:
            fmt_keys[key] = profiles[key]
        else:
            fmt_keys[key] = "目前未知"
            app.logger.info("key not found:" + key + " ,user_id:" + user_id)
    app.logger.info(fmt_keys)
    if len(fmt_keys) == 0:
        if len(profile_tmplate) == 0:
            prompt = input
        else:
            prompt = profile_tmplate
    else:
        prompt = prompt_template_lc.format(**fmt_keys)
    app.logger.info("fomat input:{}".format(prompt))
    return prompt


def get_script(app: Flask, attend_id: str, next: int = 0):

    is_first = False
    attend_info = AICourseLessonAttend.query.filter(
        AICourseLessonAttend.attend_id == attend_id
    ).first()
    attend_infos = []
    app.logger.info(
        "get next script,current:{},next:{}".format(attend_info.script_index, next)
    )
    if attend_info.status == ATTEND_STATUS_NOT_STARTED or attend_info.script_index <= 0:
        attend_info.status = ATTEND_STATUS_IN_PROGRESS
        attend_info.script_index = 1

        # 检查是否是第一节课
        lesson = AILesson.query.filter(
            AILesson.lesson_id == attend_info.lesson_id
        ).first()
        attend_infos.append(
            AILessonAttendDTO(
                lesson.lesson_no,
                lesson.lesson_name,
                lesson.lesson_id,
                ATTEND_STATUS_VALUES[ATTEND_STATUS_IN_PROGRESS],
            )
        )
        app.logger.info(lesson.lesson_no)
        app.logger.info(lesson.lesson_no[-2:])
        if len(lesson.lesson_no) >= 2 and lesson.lesson_no[-2:] == "01":
            # 第一节课
            app.logger.info("first lesson")
            parent_lesson = AILesson.query.filter(
                AILesson.lesson_no == lesson.lesson_no[:-2]
            ).first()
            parent_attend = AICourseLessonAttend.query.filter(
                AICourseLessonAttend.lesson_id == parent_lesson.lesson_id,
                AICourseLessonAttend.user_id == attend_info.user_id,
                AICourseLessonAttend.status != ATTEND_STATUS_RESET,
            ).first()
            is_first = True
            if (
                parent_attend is not None
                and parent_attend.status == ATTEND_STATUS_NOT_STARTED
            ):
                parent_attend.status = ATTEND_STATUS_IN_PROGRESS
                attend_infos.append(
                    AILessonAttendDTO(
                        parent_lesson.lesson_no,
                        parent_lesson.lesson_name,
                        parent_lesson.lesson_id,
                        ATTEND_STATUS_VALUES[ATTEND_STATUS_IN_PROGRESS],
                    )
                )

    elif attend_info.status == ATTEND_STATUS_BRANCH:
        # 分支课程
        app.logger.info("branch")
        current = attend_info
        assoation = AICourseAttendAsssotion.query.filter(
            AICourseAttendAsssotion.from_attend_id == current.attend_id
        ).first()
        if assoation:
            app.logger.info("found assoation")
            current = AICourseLessonAttend.query.filter(
                AICourseLessonAttend.attend_id == assoation.to_attend_id
            ).first()
        while current.status == ATTEND_STATUS_BRANCH:
            # 分支课程
            assoation = AICourseAttendAsssotion.query.filter(
                AICourseAttendAsssotion.from_attend_id == current.attend_id
            ).first()
            if assoation:
                current = AICourseLessonAttend.query.filter(
                    AICourseLessonAttend.attend_id == assoation.to_attend_id
                ).first()
        app.logger.info("to get branch script")
        db.session.flush()
        script_info, attend_infos, is_first = get_script(app, current.attend_id, next)
        if script_info:
            return script_info, [], is_first
        else:
            current.status = ATTEND_STATUS_COMPLETED
            attend_info.status = ATTEND_STATUS_IN_PROGRESS
            db.session.flush()
            return get_script(app, attend_id, next)
    elif next > 0:
        attend_info.script_index = attend_info.script_index + next
    script_info = AILessonScript.query.filter(
        AILessonScript.lesson_id == attend_info.lesson_id,
        AILessonScript.status == 1,
        AILessonScript.script_index == attend_info.script_index,
        AILessonScript.script_type != SCRIPT_TYPE_SYSTEM,
    ).first()
    if not script_info:
        app.logger.info("no script found")
        app.logger.info(attend_info.lesson_id)
        if attend_info.status == ATTEND_STATUS_IN_PROGRESS:
            attend_info.status = ATTEND_STATUS_COMPLETED
            lesson = AILesson.query.filter(
                AILesson.lesson_id == attend_info.lesson_id
            ).first()
            attend_infos.append(
                AILessonAttendDTO(
                    lesson.lesson_no,
                    lesson.lesson_name,
                    lesson.lesson_id,
                    ATTEND_STATUS_VALUES[ATTEND_STATUS_COMPLETED],
                )
            )
    db.session.flush()
    return script_info, attend_infos, is_first


def get_script_by_id(app: Flask, script_id: str) -> AILessonScript:
    return AILessonScript.query.filter_by(script_id=script_id).first()


def make_script_dto(script_type, script_content, script_id) -> str:
    return (
        "data: "
        + json.dumps(ScriptDTO(script_type, script_content, script_id), default=fmt)
        + "\n\n".encode("utf-8").decode("utf-8")
    )


def update_attend_lesson_info(app: Flask, attend_id: str) -> list[AILessonAttendDTO]:
    res = []
    attend_info = AICourseLessonAttend.query.filter(
        AICourseLessonAttend.attend_id == attend_id
    ).first()
    lesson = AILesson.query.filter(AILesson.lesson_id == attend_info.lesson_id).first()
    lesson_no = lesson.lesson_no
    parent_no = lesson_no
    attend_info.status = ATTEND_STATUS_COMPLETED
    res.append(
        AILessonAttendDTO(
            lesson_no,
            lesson.lesson_name,
            lesson.lesson_id,
            ATTEND_STATUS_VALUES[ATTEND_STATUS_COMPLETED],
        )
    )
    if len(parent_no) > 2:
        parent_no = parent_no[:2]
    app.logger.info("parent_no:" + parent_no)
    attend_lesson_infos = get_lesson_and_attend_info(
        app, parent_no, lesson.course_id, attend_info.user_id
    )
    if attend_lesson_infos[-1]["attend"].attend_id == attend_id:
        # 最后一个已经完课
        # 整体章节完课
        if attend_lesson_infos[0]["attend"].status == ATTEND_STATUS_IN_PROGRESS:
            attend_lesson_infos[0]["attend"].status = ATTEND_STATUS_COMPLETED
            res.append(
                AILessonAttendDTO(
                    attend_lesson_infos[0]["lesson"].lesson_no,
                    attend_lesson_infos[0]["lesson"].lesson_name,
                    attend_lesson_infos[0]["lesson"].lesson_id,
                    ATTEND_STATUS_VALUES[ATTEND_STATUS_COMPLETED],
                )
            )
        # 找到下一章节进行解锁
        next_no = str(int(parent_no) + 1).zfill(2)
        next_lessons = get_lesson_and_attend_info(
            app, next_no, lesson.course_id, attend_info.user_id
        )

        app.logger.info("next_no:" + next_no)
        if len(next_lessons) > 0:
            # 解锁
            app.logger.info(
                "next lesson: {} ".format(
                    ",".join(
                        [
                            (nl["lesson"].lesson_no + ":" + str(nl["attend"].status))
                            for nl in next_lessons
                        ]
                    )
                )
            )
            for next_lesson_attend in next_lessons:
                if next_lesson_attend["lesson"].lesson_no == next_no and (
                    next_lesson_attend["attend"].status == ATTEND_STATUS_LOCKED
                    or next_lesson_attend["attend"].status == ATTEND_STATUS_NOT_STARTED
                    or next_lesson_attend["attend"].status == ATTEND_STATUS_IN_PROGRESS
                ):
                    app.logger.info("unlock next lesson")
                    next_lesson_attend["attend"].status = ATTEND_STATUS_NOT_STARTED
                    res.append(
                        AILessonAttendDTO(
                            next_lesson_attend["lesson"].lesson_no,
                            next_lesson_attend["lesson"].lesson_name,
                            next_lesson_attend["lesson"].lesson_id,
                            ATTEND_STATUS_VALUES[ATTEND_STATUS_NOT_STARTED],
                        )
                    )
                if next_lesson_attend["lesson"].lesson_no == next_no + "01" and (
                    next_lesson_attend["attend"].status == ATTEND_STATUS_LOCKED
                    or next_lesson_attend["attend"].status == ATTEND_STATUS_NOT_STARTED
                    or next_lesson_attend["attend"].status == ATTEND_STATUS_IN_PROGRESS
                ):
                    app.logger.info("unlock next lesson")
                    next_lesson_attend["attend"].status = ATTEND_STATUS_NOT_STARTED
                    res.append(
                        AILessonAttendDTO(
                            next_lesson_attend["lesson"].lesson_no,
                            next_lesson_attend["lesson"].lesson_name,
                            next_lesson_attend["lesson"].lesson_id,
                            ATTEND_STATUS_VALUES[ATTEND_STATUS_NOT_STARTED],
                        )
                    )
        else:
            app.logger.info("no next lesson")
    for i in range(len(attend_lesson_infos)):
        if (
            i > 0
            and attend_lesson_infos[i - 1]["attend"].attend_id == attend_id
            and attend_lesson_infos[i]["attend"].status == ATTEND_STATUS_LOCKED
        ):
            # 更新下一节
            attend_lesson_infos[i]["attend"].status = ATTEND_STATUS_NOT_STARTED
            res.append(
                AILessonAttendDTO(
                    attend_lesson_infos[i]["lesson"].lesson_no,
                    attend_lesson_infos[i]["lesson"].lesson_name,
                    attend_lesson_infos[i]["lesson"].lesson_id,
                    ATTEND_STATUS_VALUES[ATTEND_STATUS_NOT_STARTED],
                )
            )
    app.logger.info("res:{}".format(",".join([r.lesson_no for r in res])))
    return res


def get_follow_up_ask_prompt(app: Flask, attend, script) -> str:
    return """# 现在学员在学习上述教学内容时，产生了一些疑问，你需要恰当的回答学员的追问。

**你就是老师本人，不要打招呼，直接用第一人称回答！**

如果学员的追问内容与当前章节教学内容有关，请优先结合当前章节中已经输出的内容进行回答。

如果学员的追问内容与当前章节教学内容关系不大，但与该课程的其他章节有关，你可以简要回答并友好的告知学员稍安勿躁，后续xx章节有涉及学员追问问题的详细教学内容。

如果学员的追问内容与课程教学内容无关，但与教学平台有关（平台使用问题；售卖、订单、退费等；账号、密码、登录等），请耐心的告知学员通过「哎师傅-AI学习社区」服务号找到我们进行相应的解决。

如果学员的追问内容与课程教学内容无关，也与教学平台无关，请友好的回绝学员的追问，并请学员专注在该课程内容的学习上。


学员的追问是：
`{input}`
"""


def get_follow_up_model(app: Flask, attend, script) -> str:
    return "ERNIE-4.0-8K"
