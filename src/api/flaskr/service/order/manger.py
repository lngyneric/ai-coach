from flaskr.service.user.models import User
from flaskr.service.order.consts import (
    BUY_STATUS_TYPES,
    BUY_STATUS_VALUES,
    DISCOUNT_STATUS_TYPES,
    DISCOUNT_STATUS_VALUES,
    DISCOUNT_TYPE_VALUES,
)
from flaskr.service.order.models import AICourseBuyRecord, DiscountRecord
from flaskr.service.view.models import (
    INPUT_TYPE_TEXT,
    InputItem,
    TableColumnItem,
    ViewDef,
)


OrderView = ViewDef(
    "order",
    [
        TableColumnItem("id", "ID"),
        TableColumnItem("record_id", "订单ID"),
        TableColumnItem(
            "user_id", "用户ID", model=User, display="mobile", index_id="user_id"
        ),
        TableColumnItem("course_id", "课程ID"),
        TableColumnItem("price", "订单原价"),
        TableColumnItem("pay_value", "应付金额"),
        TableColumnItem("discount_value", "折扣金额"),
        TableColumnItem("status", "状态", items=BUY_STATUS_VALUES),
        TableColumnItem("created", "创建时间"),
        TableColumnItem("updated", "更新时间"),
    ],
    [
        InputItem("user_id", "用户ID", "like", INPUT_TYPE_TEXT),
        InputItem("course_id", "课程ID", "like", INPUT_TYPE_TEXT),
        InputItem("price", "价格", "like", INPUT_TYPE_TEXT),
        InputItem(
            "status", "状态", "like", INPUT_TYPE_TEXT, input_options=BUY_STATUS_TYPES
        ),
        InputItem("created", "创建时间", "like", INPUT_TYPE_TEXT),
        InputItem("updated", "更新时间", "like", INPUT_TYPE_TEXT),
    ],
    AICourseBuyRecord,
)


DisCountdRecordView = ViewDef(
    "discount",
    [
        TableColumnItem("id", "ID"),
        TableColumnItem("discount_value", "折扣金额"),
        TableColumnItem(
            "user_id", "用户ID", model=User, display="mobile", index_id="user_id"
        ),
        TableColumnItem("discount_code", "折扣码"),
        TableColumnItem("discount_type", "折扣类型", items=DISCOUNT_TYPE_VALUES),
        TableColumnItem("status", "状态", items=DISCOUNT_STATUS_VALUES),
        TableColumnItem("created", "创建时间"),
        TableColumnItem("updated", "更新时间"),
    ],
    [
        InputItem("discount_value", "折扣金额", "like", INPUT_TYPE_TEXT),
        InputItem(
            "status", "状态", "like", INPUT_TYPE_TEXT, input_options=DISCOUNT_STATUS_TYPES
        ),
    ],
    DiscountRecord,
)
