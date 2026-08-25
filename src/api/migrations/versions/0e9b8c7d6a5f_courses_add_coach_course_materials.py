"""add coach_course_materials table

Revision ID: <head>_add_coach_course_materials
Revises: 0e9b8c7d6a5f
Create Date: 2026-08-25 09:00:00.000000

WECOM 9 节点 · 节点 1（课件上传）落库表：每行记录一条经企微收集表提交的
课件素材（name + link_url + 可选 course_bid + 提交人）。

对应端点 ``POST /api/shifu/coach/courses``（myenroll/routes.py
``coach_course_upload``）。表结构与
``learning_portal/models.py::CoachCourseMaterial`` 对齐。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0e9b8c7d6a5f_courses"
down_revision = "0e9b8c7d6a5f"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names()


def upgrade():
    if not _table_exists("coach_course_materials"):
        op.create_table(
            "coach_course_materials",
            sa.Column("material_bid", sa.String(length=32), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("link_url", sa.String(length=500), nullable=False),
            sa.Column("course_bid", sa.String(length=32), nullable=True),
            sa.Column("submitted_by", sa.String(length=32), nullable=True),
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index(
            "idx_cm_course", "coach_course_materials", ["course_bid"]
        )
        op.create_index(
            "idx_cm_submitted", "coach_course_materials", ["submitted_by"]
        )


def downgrade():
    if _table_exists("coach_course_materials"):
        op.drop_index("idx_cm_submitted", table_name="coach_course_materials")
        op.drop_index("idx_cm_course", table_name="coach_course_materials")
        op.drop_table("coach_course_materials")