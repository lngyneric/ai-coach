"""Regression tests for shifu_permission_verification auth_type format handling.

Covers the legacy plain-text auth_type formats (the bug that returned False
for every permission when auth_type was not valid JSON, causing "没有权限"
errors for shared view-only courses) and confirms the canonical JSON array
format still works. See docs/AUTH-TYPE-FIX.md for the full background.
"""

from __future__ import annotations

import json
import uuid
from decimal import Decimal

import pytest

from flaskr.dao import db
from flaskr.service.shifu.funcs import shifu_permission_verification
from flaskr.service.shifu.models import AiCourseAuth, DraftShifu
from flaskr.service.shifu.utils import get_shifu_creator_bid


def _seed_owned_course(shifu_bid: str, owner_bid: str) -> None:
    draft = DraftShifu(
        shifu_bid=shifu_bid,
        title=f"Course {shifu_bid[:6]}",
        description="desc",
        avatar_res_bid="",
        keywords="",
        llm="gpt-test",
        llm_temperature=Decimal("0"),
        llm_system_prompt="",
        price=Decimal("0"),
        created_user_bid=owner_bid,
        updated_user_bid=owner_bid,
    )
    db.session.add(draft)
    db.session.commit()


def _seed_viewer_auth(course_bid: str, user_bid: str, auth_type: str) -> None:
    db.session.add(
        AiCourseAuth(
            course_auth_id=uuid.uuid4().hex[:32],
            user_id=user_bid,
            course_id=course_bid,
            auth_type=auth_type,
            status=1,
        )
    )
    db.session.commit()


@pytest.mark.parametrize(
    ("raw_auth_type", "expect_view", "expect_edit", "expect_publish"),
    [
        (json.dumps(["view"]), True, False, False),  # canonical JSON array
        (json.dumps(["view", "edit"]), True, True, False),  # JSON array multi
        ('"view"', True, False, False),  # JSON string
        ("view", True, False, False),  # plain single token
        ("view,edit", True, True, False),  # plain comma separated
        ("1", True, False, False),  # numeric view code
        ("2", True, True, False),  # numeric edit code (implies view)
        ("4", False, False, True),  # numeric publish code
        (json.dumps([]), False, False, False),  # empty array -> nothing
    ],
)
def test_auth_type_format_variants(
    app,
    raw_auth_type: str,
    expect_view: bool,
    expect_edit: bool,
    expect_publish: bool,
):
    shifu_bid = uuid.uuid4().hex[:32]
    owner_bid = uuid.uuid4().hex[:32]
    viewer_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, owner_bid)
        _seed_viewer_auth(shifu_bid, viewer_bid, raw_auth_type)
        # Creator is someone else, so the viewer path must be exercised.
        assert get_shifu_creator_bid(app, shifu_bid) == owner_bid
        assert (
            shifu_permission_verification(app, viewer_bid, shifu_bid, "view")
            is expect_view
        )
        assert (
            shifu_permission_verification(app, viewer_bid, shifu_bid, "edit")
            is expect_edit
        )
        assert (
            shifu_permission_verification(app, viewer_bid, shifu_bid, "publish")
            is expect_publish
        )


def test_creator_always_has_all_permissions(app):
    shifu_bid = uuid.uuid4().hex[:32]
    creator_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, creator_bid)
        for perm in ("view", "edit", "publish"):
            assert shifu_permission_verification(
                app, creator_bid, shifu_bid, perm
            ) is True


def test_no_auth_record_denies(app):
    shifu_bid = uuid.uuid4().hex[:32]
    owner_bid = uuid.uuid4().hex[:32]
    stranger_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, owner_bid)
        assert (
            shifu_permission_verification(app, stranger_bid, shifu_bid, "view")
            is False
        )
