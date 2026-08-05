"""Verify the P0 ORM column mapping end-to-end against SQLite (same as CI)."""
from datetime import datetime

from flaskr.service.user.models import UserInfo as UserEntity
from flaskr.service.user.repository import (
    create_user_entity,
    load_user_aggregate,
    build_user_info_from_aggregate,
)
from flaskr.service.user.consts import USER_STATE_REGISTERED


def _make_entity_with_extended_fields(user_bid: str) -> UserEntity:
    entity = create_user_entity(
        user_bid=user_bid,
        identify=user_bid,
        nickname="ORM Test",
        language="zh-CN",
        avatar="",
        state=USER_STATE_REGISTERED,
    )
    entity.is_certifier = 1
    entity.department = "销售部"
    entity.supervisor_bid = "usr_boss"
    entity.mentor_bid = ""
    entity.employee_no = "sch-orm-001"
    return entity


def test_orm_extended_columns_roundtrip(app):
    user_bid = "usr_orm_ext_test"
    with app.app_context():
        entity = _make_entity_with_extended_fields(user_bid)
        from flaskr.dao import db

        db.session.flush()
        db.session.commit()

        try:
            # Reload from DB to prove columns are mapped & persisted
            reloaded = UserEntity.query.filter_by(user_bid=user_bid).first()
            assert reloaded is not None
            assert reloaded.is_certifier == 1
            assert reloaded.department == "销售部"
            assert reloaded.supervisor_bid == "usr_boss"
            assert reloaded.employee_no == "sch-orm-001"

            # Aggregate -> DTO -> JSON flow
            aggregate = load_user_aggregate(user_bid)
            assert aggregate is not None
            assert aggregate.is_certifier is True
            assert aggregate.department == "销售部"
            assert aggregate.supervisor_bid == "usr_boss"
            assert aggregate.employee_no == "sch-orm-001"

            dto = build_user_info_from_aggregate(aggregate)
            payload = dto.__json__()
            assert payload["is_certifier"] is True
            assert payload["department"] == "销售部"
            assert payload["supervisor_bid"] == "usr_boss"
            assert payload["employee_no"] == "sch-orm-001"
            # Empty-string fields must round-trip as ""
            assert payload["mentor_bid"] == ""
        finally:
            UserEntity.query.filter_by(user_bid=user_bid).delete()
            db.session.commit()


def test_orm_extended_columns_defaults(app):
    user_bid = "usr_orm_default_test"
    with app.app_context():
        from flaskr.dao import db

        entity = create_user_entity(
            user_bid=user_bid,
            identify=user_bid,
            nickname="Defaults",
            language="en-US",
            avatar="",
            state=USER_STATE_REGISTERED,
        )
        db.session.flush()
        db.session.commit()
        try:
            reloaded = UserEntity.query.filter_by(user_bid=user_bid).first()
            assert reloaded is not None
            # Column defaults must apply without explicit assignment
            assert reloaded.is_certifier == 0
            assert reloaded.department == ""
            assert reloaded.supervisor_bid == ""
            assert reloaded.mentor_bid == ""
            assert reloaded.employee_no == ""
        finally:
            UserEntity.query.filter_by(user_bid=user_bid).delete()
            db.session.commit()
