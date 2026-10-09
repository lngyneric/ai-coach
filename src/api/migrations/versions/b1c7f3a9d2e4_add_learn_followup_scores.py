"""add learn_followup_scores

Revision ID: b1c7f3a9d2e4
Revises: a2f4c6e8d1b3
Create Date: 2026-09-24 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "b1c7f3a9d2e4"
down_revision = "a2f4c6e8d1b3"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if _table_exists("learn_followup_scores"):
        return
    op.create_table(
        "learn_followup_scores",
        sa.Column("id", mysql.BIGINT(), primary_key=True, autoincrement=True),
        sa.Column("score_bid", sa.String(36), nullable=False, unique=True),
        sa.Column("user_bid", sa.String(36), nullable=False, server_default=""),
        sa.Column("shifu_bid", sa.String(36), nullable=False, server_default=""),
        sa.Column("outline_item_bid", sa.String(36), nullable=False, server_default=""),
        sa.Column("progress_record_bid", sa.String(36), nullable=False, server_default=""),
        sa.Column("answer_block_bid", sa.String(36), nullable=False, server_default=""),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_excerpt", sa.Text(), nullable=True),
        sa.Column("mastery_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ask_type", sa.String(20), nullable=True),
        sa.Column("answer_on_topic", sa.Numeric(4, 3), nullable=True),
        sa.Column("answer_quality", sa.Numeric(5, 2), nullable=True),
        sa.Column("difficulty_hint", sa.String(10), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("provider_model", sa.String(64), nullable=False, server_default=""),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("deleted", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        comment="JEV follow-up question/answer scoring records",
    )
    op.create_index(
        "ix_learn_followup_scores_user_bid",
        "learn_followup_scores",
        ["user_bid"],
    )
    op.create_index(
        "ix_learn_followup_scores_shifu_bid",
        "learn_followup_scores",
        ["shifu_bid"],
    )
    op.create_index(
        "ix_learn_followup_scores_outline_item_bid",
        "learn_followup_scores",
        ["outline_item_bid"],
    )
    op.create_index(
        "ix_learn_followup_scores_progress_record_bid",
        "learn_followup_scores",
        ["progress_record_bid"],
    )
    op.create_index(
        "ix_learn_followup_scores_answer_block_bid",
        "learn_followup_scores",
        ["answer_block_bid"],
    )
    op.create_index(
        "ix_learn_followup_scores_deleted",
        "learn_followup_scores",
        ["deleted"],
    )


def downgrade():
    if _table_exists("learn_followup_scores"):
        op.drop_table("learn_followup_scores")
