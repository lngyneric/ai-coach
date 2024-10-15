from flaskr.service.order.consts import ATTEND_STATUS_VALUES
from flaskr.service.study.const import ROLE_VALUES
from flaskr.service.order.models import AICourseLessonAttend
from .view.models import (
    INPUT_TYPE_TEXT,
    InputItem,
    TableColumnItem,
    ViewDef,
    OperationItem,
    OperationType,
)
from flaskr.service.study.models import AICourseLessonAttendScript
from flaskr.service.user.models import User
from flaskr.service.lesson.models import AILesson

LogScriptView = ViewDef(
    "logscriptview",
    [
        TableColumnItem(AICourseLessonAttendScript.attend_id, "ID"),
        TableColumnItem(AICourseLessonAttendScript.script_index, "序号"),
        TableColumnItem(
            AICourseLessonAttendScript.script_role, "角色", items=ROLE_VALUES
        ),
        TableColumnItem(AICourseLessonAttendScript.script_content, "内容"),
        TableColumnItem(
            AICourseLessonAttendScript.user_id,
            "用户",
            model=User,
            display="mobile",
            index_id="user_id",
        ),
        TableColumnItem(AICourseLessonAttendScript.status, "状态"),
        TableColumnItem(AICourseLessonAttendScript.created, "创建时间"),
        TableColumnItem(AICourseLessonAttendScript.updated, "更新时间"),
    ],
    [
        InputItem(
            "script_role", "角色", "like", INPUT_TYPE_TEXT, input_options=ROLE_VALUES
        ),
    ],
    AICourseLessonAttendScript,
)


AttendLessonView = ViewDef(
    "attendlessonview",
    [
        TableColumnItem(AICourseLessonAttend.attend_id, "ID"),
        TableColumnItem(
            AICourseLessonAttend.lesson_id,
            "章节",
            model=AILesson,
            display="lesson_name",
            index_id="lesson_id",
        ),
        TableColumnItem(
            AICourseLessonAttend.user_id,
            "用户",
            model=User,
            display="mobile",
            index_id="user_id",
        ),
        TableColumnItem(AICourseLessonAttend.status, "状态", items=ATTEND_STATUS_VALUES),
        TableColumnItem(AICourseLessonAttend.created, "创建时间"),
        TableColumnItem(AICourseLessonAttend.updated, "更新时间"),
    ],
    [
        InputItem("id", "ID", "like", INPUT_TYPE_TEXT),
        InputItem("lesson_id", "课程", "like", INPUT_TYPE_TEXT),
        InputItem("user_id", "用户", "like", INPUT_TYPE_TEXT),
        InputItem(
            "status", "状态", "like", INPUT_TYPE_TEXT, input_options=ATTEND_STATUS_VALUES
        ),
        InputItem("created", "创建时间", "like", INPUT_TYPE_TEXT),
        InputItem("updated", "更新时间", "like", INPUT_TYPE_TEXT),
    ],
    AICourseLessonAttend,
    [
        OperationItem(
            "查看脚本",
            OperationType.GO_TO_LIST,
            "logscriptview",
            "logscriptview",
            {"attend_id": "attend_id"},
        ),
    ],
)
