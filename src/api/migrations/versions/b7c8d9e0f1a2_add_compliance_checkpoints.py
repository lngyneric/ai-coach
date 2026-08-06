"""add compliance checkpoints to learner_coaching + coach_checklist_improvements

Revision ID: b7c8d9e0f1a2
Revises: c1d2e3f4a5b6
Create Date: 2026-08-06 16:00:00.000000

W3 task 2 — compliance checkpoint chain (sign → sync → improvement):

- ``learner_coaching`` gains five columns carrying the three-state gate:
  ``sign_at``/``signed_by`` (learner sign-off), ``sync_at``/``synced_by``
  (coach face-to-face sync) and ``sync_note`` (沟通记录).
- New ``coach_checklist_improvements`` table stores improvement items agreed
  during the sync (action + owner + due date + status). A coaching record is
  only ``completed`` when sign + sync are recorded AND every improvement item
  is ``done`` (or there are no items).

Both operations are idempotent so re-running the migration is a no-op.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column in [c["name"] for c in inspector.get_columns(table)]


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names()


def upgrade():
    # learner_coaching three-state columns (idempotent).
    for column, coltype in (
        ("sign_at", sa.DateTime()),
        ("signed_by", sa.String(length=32)),
        ("sync_at", sa.DateTime()),
        ("synced_by", sa.String(length=32)),
        ("sync_note", sa.Text()),
    ):
        if _column_exists("learner_coaching", column):
            continue
        op.add_column("learner_coaching", sa.Column(column, coltype, nullable=True))

    # coach_checklist_improvements table.
    if not _table_exists("coach_checklist_improvements"):
        op.create_table(
            "coach_checklist_improvements",
            sa.Column("improvement_bid", sa.String(length=32), primary_key=True),
            sa.Column("record_bid", sa.String(length=32), nullable=False),
            sa.Column("action", sa.String(length=500), nullable=False),
            sa.Column("owner_bid", sa.String(length=32), nullable=True),
            sa.Column("owner_name", sa.String(length=100), nullable=True),
            sa.Column("due_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("created_by", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index(
            "idx_ci_record", "coach_checklist_improvements", ["record_bid"]
        )


def downgrade():
    if _table_exists("coach_checklist_improvements"):
        op.drop_index("idx_ci_record", table_name="coach_checklist_improvements")
        op.drop_table("coach_checklist_improvements")

    for column in ("sign_at", "signed_by", "sync_at", "synced_by", "sync_note"):
        if _column_exists("learner_coaching", column):
            op.drop_column("learner_coaching", column)
