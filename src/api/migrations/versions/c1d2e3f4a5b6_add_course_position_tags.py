"""add course_position_tags table (AI recommendation, W2 task 4)

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-06 12:00:00.000000

New ``course_position_tags`` table links a published course (``shifu_bid``)
to one or more job positions (``position`` + ``tag``) with a ``weight`` for
sorting, powering the AI recommendation endpoint
``GET /api/portal/recommend``.

Design (mirrors the project's idempotent migration style — see
``a1b2c3d4e5f6_add_coach_phases_shifu_bid.py``):

- ``position`` is a stable machine code (``sales`` / ``medical`` /
  ``management`` / ``digital`` / ``general``), ``position_name`` a
  human-readable Chinese label, ``tag`` an optional finer-grained label.
- ``weight`` default 10, higher = stronger recommendation match.
- ``is_active`` lets an admin disable a mapping without deleting it.
- UNIQUE(shifu_bid, position) keeps the mapping idempotent (a second run of
  the seed never duplicates rows).
- The table charset/collation is pinned to ``utf8mb4`` / ``utf8mb4_0900_ai_ci``
  to match every other table in the schema (``shifu_published_shifus``,
  ``user_users``, …). Without this the JOIN with ``shifu_published_shifus``
  raises MySQL error 1267 (illegal mix of collations) because SQLAlchemy's
  default DDL emits ``utf8mb4_unicode_ci``.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names()


def upgrade():
    if _table_exists("course_position_tags"):
        return
    op.create_table(
        "course_position_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "shifu_bid",
            sa.String(length=32),
            nullable=False,
            comment="published course (shifu) business identifier",
        ),
        sa.Column(
            "position",
            sa.String(length=50),
            nullable=False,
            comment="position code: sales / medical / management / digital / general",
        ),
        sa.Column(
            "position_name",
            sa.String(length=100),
            nullable=True,
            comment="human-readable position label (Chinese)",
        ),
        sa.Column(
            "tag",
            sa.String(length=100),
            nullable=True,
            comment="optional finer-grained tag, e.g. 销售技巧",
        ),
        sa.Column(
            "weight",
            sa.Integer(),
            nullable=False,
            server_default="10",
            comment="match weight for sorting, higher first",
        ),
        sa.Column(
            "is_active",
            sa.SmallInteger(),
            nullable=False,
            server_default="1",
            comment="1=active, 0=disabled",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "shifu_bid",
            "position",
            name="uq_course_position_tags_shifu_position",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_course_position_tags_shifu_bid",
        "course_position_tags",
        ["shifu_bid"],
    )
    op.create_index(
        "ix_course_position_tags_position",
        "course_position_tags",
        ["position"],
    )


def downgrade():
    if not _table_exists("course_position_tags"):
        return
    op.drop_table("course_position_tags")
