from .models import User
from ..view.models import (
    INPUT_TYPE_TEXT,
    ViewDef,
    TableColumnItem,
    InputItem,
    OperationItem,
    OperationType,
)

UserView = ViewDef(
    "userview",
    [
        TableColumnItem(User.id, "ID"),
        TableColumnItem(User.user_id, "用户ID"),
        TableColumnItem(User.username, "用户名"),
        TableColumnItem(User.name, "姓名"),
        TableColumnItem(User.email, "邮箱"),
        TableColumnItem(User.mobile, "手机"),
        TableColumnItem(User.created, "创建时间"),
        TableColumnItem(User.updated, "更新时间"),
    ],
    [
        InputItem("username", "用户名", "like", INPUT_TYPE_TEXT),
        InputItem("name", "姓名", "like", INPUT_TYPE_TEXT),
        InputItem("email", "邮箱", "like", INPUT_TYPE_TEXT),
        InputItem("mobile", "手机", "like", INPUT_TYPE_TEXT),
        InputItem("created", "创建时间", "like", INPUT_TYPE_TEXT),
        InputItem("updated", "更新时间", "like", INPUT_TYPE_TEXT),
    ],
    User,
    [
        OperationItem("编辑", OperationType.GO_TO_DETAIL, "edit", "edit", {}),
        OperationItem("删除", OperationType.OPERATION, "delete", "delete", {"id": "id"}),
    ],
)
