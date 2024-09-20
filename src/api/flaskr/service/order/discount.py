# 优惠券&折扣码的逻辑


# 支持一码多用
# 支持一码一用，批量生成


from datetime import datetime
import random
import string
import pytz
from ...service.order.funs import (
    query_buy_record,
    success_buy_record,
)

from .models import AICourseBuyRecord, Discount, DiscountRecord
from ...dao import db
from .consts import (
    DISCOUNT_APPLY_TYPE_ALL,
    DISCOUNT_STATUS_ACTIVE,
    DISCOUNT_TYPE_FIXED,
    DISCOUNT_TYPE_PERCENT,
    DISCOUNT_STATUS_USED,
)
from flask import Flask
from ...util import generate_id
from ..common import (
    ORDER_NOT_FOUND,
    DISCOUNT_NOT_FOUND,
    DISCOUNT_ALREADY_USED,
    ORDER_DISCOUNT_ALREADY_USED,
    DISCOUNT_LIMIT_EXCEEDED,
    DISCOUNT_ALREADY_EXPIRED,
)


# 生成折扣码
def generate_discount_strcode(app: Flask):
    with app.app_context():
        characters = string.ascii_uppercase + string.digits
        discount_code = "".join(random.choices(characters, k=12))
        return discount_code


def generate_discount_code(
    app: Flask,
    discount_value,
    course_id,
    discout_start,
    discount_end,
    discount_channel,
    discount_type,
    discount_apply_type,
    discount_count=100,
    discount_code=None,
):
    with app.app_context():
        if discount_code is None:
            discount_code = generate_discount_strcode(app)
        discount = Discount()
        discount.discount_id = generate_id(app)
        discount.course_id = course_id
        discount.discount_code = discount_code
        discount.discount_type = discount_type
        discount.discount_apply_type = discount_apply_type
        discount.discount_value = discount_value
        discount.discount_count = discount_count
        discount.discount_start = discout_start
        discount.discount_end = discount_end
        discount.discount_channel = discount_channel
        discount.discount_filter = "{" + '"course_id":{}'.format(course_id) + "}"
        db.session.add(discount)
        db.session.commit()
        return discount.discount_id


# 用折扣码规则生成折扣码


def generate_discount_code_by_rule(app: Flask, discount_id):
    with app.app_context():
        discount_info = Discount.query.filter(
            Discount.discount_id == discount_id
        ).first()
        if not discount_info:
            return None
        if discount_info.discount_apply_type == DISCOUNT_APPLY_TYPE_ALL:
            return None
        discount_code = generate_discount_strcode(app)
        discountRecord = DiscountRecord()
        discountRecord.record_id = generate_id(app)
        discountRecord.discount_id = discount_id
        discountRecord.discount_code = discount_code
        discountRecord.discount_type = discount_info.discount_type
        discountRecord.discount_value = discount_info.discount_value
        discountRecord.status = DISCOUNT_STATUS_ACTIVE
        discount_info.discount_count = discount_info.discount_count + 1
        db.session.add(discountRecord)
        db.session.commit()


# 使用折扣码
def use_discount_code(app: Flask, user_id, discount_code, order_id):
    with app.app_context():
        # 创建时区信息
        bj_time = pytz.timezone("Asia/Shanghai")
        # 转换 record.created（一个浮点数时间戳）到北京时间
        now = datetime.fromtimestamp(datetime.now().timestamp(), bj_time)
        app.logger.info("now: %s", now)
        buy_record = AICourseBuyRecord.query.filter(
            AICourseBuyRecord.record_id == order_id
        ).first()
        if not buy_record:
            return ORDER_NOT_FOUND
        order_discount = DiscountRecord.query.filter(
            DiscountRecord.order_id == order_id,
            DiscountRecord.status == DISCOUNT_STATUS_USED,
        ).first()
        if order_discount:
            raise ORDER_DISCOUNT_ALREADY_USED
        if order_discount:
            return order_discount
        discountRecord = DiscountRecord.query.filter(
            DiscountRecord.discount_code == discount_code,
            DiscountRecord.status == DISCOUNT_STATUS_ACTIVE,
        ).first()
        discount = None
        if not discountRecord:
            # query fixcode
            app.logger.info("query fixcode")

            discount = Discount.query.filter(
                Discount.discount_code == discount_code
            ).first()
            if not discount:
                raise DISCOUNT_NOT_FOUND
            discount_end = bj_time.localize(discount.discount_end)
            app.logger.info("discount_end: %s", discount_end)
            if discount_end < now:
                raise DISCOUNT_ALREADY_EXPIRED
            if discount.discount_used + 1 > discount.discount_count:
                raise DISCOUNT_LIMIT_EXCEEDED

            discountRecord = DiscountRecord()
            discountRecord.record_id = generate_id(app)
            discountRecord.discount_id = discount.discount_id
            discountRecord.discount_code = discount_code
            discountRecord.discount_type = discount.discount_type
            discountRecord.discount_value = discount.discount_value
            discountRecord.status = DISCOUNT_STATUS_ACTIVE
            discountRecord.created = now
            discountRecord.updated = now
            db.session.add(discountRecord)
        if discount is None:
            discount = Discount.query.filter(
                Discount.discount_id == discountRecord.discount_id
            ).first()

        if not discount:
            return DISCOUNT_NOT_FOUND
        if discountRecord.status != DISCOUNT_STATUS_ACTIVE:
            raise DISCOUNT_ALREADY_USED

        discountRecord.status = DISCOUNT_STATUS_USED
        discountRecord.updated = now
        discountRecord.user_id = user_id
        discountRecord.order_id = order_id
        if discount.discount_type == DISCOUNT_TYPE_FIXED:
            buy_record.discount_value = (
                buy_record.discount_value + discountRecord.discount_value  # noqa W503
            )
        elif discount.discount_type == DISCOUNT_TYPE_PERCENT:
            buy_record.discount_value = (
                buy_record.discount_value
                + buy_record.price * discountRecord.discount_value  # noqa W503
            )
        if buy_record.discount_value >= buy_record.price:
            buy_record.discount_value = buy_record.price
        buy_record.pay_value = buy_record.price - buy_record.discount_value
        if buy_record.pay_value < 0:
            buy_record.pay_value = 0
        buy_record.updated = now
        discountRecord.updated = now
        discount.discount_used = discount.discount_used + 1
        db.session.commit()
        if buy_record.discount_value >= buy_record.price:
            return success_buy_record(app, buy_record.record_id)
        return query_buy_record(app, buy_record.record_id)
