"""add shifu_bid to coach_phases

Revision ID: a1b2c3d4e5f6
Revises: d4e5f6a7b8c9
Create Date: 2026-08-06 00:00:00.000000

Nullable varchar(32): links a phase to its course (shifu) so phase-deadline
notifications can build a valid WeCom textcard URL /c/{shifu_bid} instead of
the coaching record bid (which is not a course and would 404 in cook-web).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column in [c["name"] for c in inspector.get_columns(table)]


def upgrade():
    if _column_exists("coach_phases", "shifu_bid"):
        return
    op.add_column(
        "coach_phases",
        sa.Column(
            "shifu_bid",
            sa.String(length=32),
            nullable=True,
            comment="course (shifu) bid linked to this phase; used for WeCom textcard /c/{bid} links",
        ),
    )


def downgrade():
    if not _column_exists("coach_phases", "shifu_bid"):
        return
    op.drop_column("coach_phases", "shifu_bid")
