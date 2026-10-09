"""add learn_quiz tables (and merge migration heads)

Revision ID: c3d9f1a7b5e2
Revises: b1c7f3a9d2e4, 0e9b8c7d6a5f_courses
Create Date: 2026-09-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "c3d9f1a7b5e2"
down_revision = ("b1c7f3a9d2e4", "0e9b8c7d6a5f_courses")
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _ts_columns(comment_created: str, comment_updated: str):
    return (
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment=comment_created,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment=comment_updated,
        ),
    )


def upgrade():
    if not _table_exists("learn_quiz_questions"):
        op.create_table(
            "learn_quiz_questions",
            sa.Column("id", mysql.BIGINT(), primary_key=True, autoincrement=True),
            sa.Column("question_bid", sa.String(36), nullable=False, unique=True),
            sa.Column("user_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("shifu_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("outline_item_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("progress_record_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("block_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("question_type", sa.String(20), nullable=False, server_default=""),
            sa.Column("source_excerpt", sa.Text(), nullable=True),
            sa.Column("mdflow", sa.Text(), nullable=True),
            sa.Column("options_json", sa.JSON(), nullable=True),
            sa.Column("correct_answer", sa.Text(), nullable=True),
            sa.Column("validity_score", sa.Numeric(5, 2), nullable=True),
            sa.Column("unique_answer", sa.Numeric(4, 3), nullable=True),
            sa.Column("difficulty_score", sa.Numeric(5, 2), nullable=True),
            sa.Column("reliability_score", sa.Numeric(5, 2), nullable=True),
            sa.Column("provider_model", sa.String(64), nullable=False, server_default=""),
            sa.Column("raw_json", sa.JSON(), nullable=True),
            sa.Column("deleted", sa.SmallInteger(), nullable=False, server_default="0"),
            *_ts_columns("Creation timestamp", "Last update timestamp"),
            comment="Generated in-lesson quiz questions",
        )
        for col in (
            "user_bid",
            "shifu_bid",
            "outline_item_bid",
            "progress_record_bid",
            "block_bid",
            "deleted",
        ):
            op.create_index(
                f"ix_learn_quiz_questions_{col}", "learn_quiz_questions", [col]
            )

    if not _table_exists("learn_quiz_attempts"):
        op.create_table(
            "learn_quiz_attempts",
            sa.Column("id", mysql.BIGINT(), primary_key=True, autoincrement=True),
            sa.Column("attempt_bid", sa.String(36), nullable=False, unique=True),
            sa.Column("question_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("answer_block_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("user_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("shifu_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("outline_item_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("progress_record_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("answer", sa.Text(), nullable=True),
            sa.Column("is_correct", sa.SmallInteger(), nullable=True),
            sa.Column("score", sa.Numeric(5, 2), nullable=True),
            sa.Column("grading_json", sa.JSON(), nullable=True),
            sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
            sa.Column("deleted", sa.SmallInteger(), nullable=False, server_default="0"),
            *_ts_columns("Creation timestamp", "Last update timestamp"),
            comment="Learner quiz answer attempts",
        )
        for col in (
            "question_bid",
            "answer_block_bid",
            "user_bid",
            "shifu_bid",
            "outline_item_bid",
            "progress_record_bid",
            "deleted",
        ):
            op.create_index(
                f"ix_learn_quiz_attempts_{col}", "learn_quiz_attempts", [col]
            )

    if not _table_exists("learn_quiz_chapter_aggregates"):
        op.create_table(
            "learn_quiz_chapter_aggregates",
            sa.Column("id", mysql.BIGINT(), primary_key=True, autoincrement=True),
            sa.Column("aggregate_bid", sa.String(36), nullable=False, unique=True),
            sa.Column("user_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("shifu_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("outline_item_bid", sa.String(36), nullable=False, server_default=""),
            sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("accuracy", sa.Numeric(5, 2), nullable=True),
            sa.Column("mastery_score", sa.Numeric(5, 2), nullable=True),
            sa.Column("weak_points_json", sa.JSON(), nullable=True),
            sa.Column("deleted", sa.SmallInteger(), nullable=False, server_default="0"),
            *_ts_columns("Creation timestamp", "Last update timestamp"),
            comment="Learner quiz chapter-level aggregates",
        )
        for col in ("user_bid", "shifu_bid", "outline_item_bid", "deleted"):
            op.create_index(
                f"ix_learn_quiz_chapter_aggregates_{col}",
                "learn_quiz_chapter_aggregates",
                [col],
            )
        op.create_index(
            "idx_learn_quiz_chapter_agg_unique_active",
            "learn_quiz_chapter_aggregates",
            ["user_bid", "shifu_bid", "outline_item_bid", "deleted"],
            unique=True,
        )


def downgrade():
    for table in (
        "learn_quiz_chapter_aggregates",
        "learn_quiz_attempts",
        "learn_quiz_questions",
    ):
        if _table_exists(table):
            op.drop_table(table)
