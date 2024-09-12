from ...service.order.models import AICourseLessonAttend
from ...service.view.models import (
    INPUT_TYPE_TEXT,
    InputItem,
    TableColumnItem,
    ViewDef,
    OperationItem,
    OperationType,
)
from ..lesson.const import SCRIPT_TYPES, UI_TYPES
from .models import AICourseLessonAttendScript
from ...service.user.models import User
from ...service.lesson.models import AILesson

LogScriptView = ViewDef(
    "logscriptview",
    [
        TableColumnItem(AICourseLessonAttendScript.attend_id, "ID"),
        TableColumnItem(AICourseLessonAttendScript.script_index, "序号"),
        TableColumnItem(AICourseLessonAttendScript.script_role, "角色"),
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
        InputItem("id", "ID", "like", INPUT_TYPE_TEXT),
        InputItem("script_name", "名称", "like", INPUT_TYPE_TEXT),
        InputItem(
            "script_type", "类型", "like", INPUT_TYPE_TEXT, input_options=SCRIPT_TYPES
        ),
        InputItem("status", "状态", "like", INPUT_TYPE_TEXT),
        InputItem(
            "script_ui_type", "UI类型", "like", INPUT_TYPE_TEXT, input_options=UI_TYPES
        ),
        InputItem("created", "创建时间", "like", INPUT_TYPE_TEXT),
        InputItem("updated", "更新时间", "like", INPUT_TYPE_TEXT),
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
        TableColumnItem(AICourseLessonAttend.status, "状态"),
        TableColumnItem(AICourseLessonAttend.created, "创建时间"),
        TableColumnItem(AICourseLessonAttend.updated, "更新时间"),
    ],
    [
        InputItem("id", "ID", "like", INPUT_TYPE_TEXT),
        InputItem("lesson_id", "课程", "like", INPUT_TYPE_TEXT),
        InputItem("user_id", "用户", "like", INPUT_TYPE_TEXT),
        InputItem("status", "状态", "like", INPUT_TYPE_TEXT),
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
