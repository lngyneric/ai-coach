from flaskr.service.view.models import (
    INPUT_TYPE_TEXT,
    InputItem,
    TableColumnItem,
    ViewDef,
)

from .models import FeedBack

FeedbackView = ViewDef(
    "feedback",
    [
        TableColumnItem("id", "ID"),
        TableColumnItem("user_id", "用户ID"),
        TableColumnItem("feedback", "反馈内容"),
        TableColumnItem("created", "创建时间"),
        TableColumnItem("updated", "更新时间"),
    ],
    [
        InputItem("user_id", "用户ID", "like", INPUT_TYPE_TEXT),
        InputItem("feedback", "反馈内容", "like", INPUT_TYPE_TEXT),
        InputItem("created", "创建时间", "like", INPUT_TYPE_TEXT),
        InputItem("updated", "更新时间", "like", INPUT_TYPE_TEXT),
    ],
    FeedBack,
)
