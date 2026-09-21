"""add is_certifier to user_users

Revision ID: a2f4c6e8d1b3
Revises: d3e5f7a9b1c2
Create Date: 2026-08-25 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a2f4c6e8d1b3"
down_revision = "d3e5f7a9b1c2"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in [c["name"] for c in inspector.get_columns(table_name)]


def upgrade():
    if _column_exists("user_users", "is_certifier"):
        return
    with op.batch_alter_table("user_users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_certifier",
                sa.SmallInteger(),
                nullable=False,
                server_default="0",
                comment="Certifier flag: 0=regular user, 1=certifier",
            )
        )
        batch_op.create_index(
            batch_op.f("ix_user_users_is_certifier"),
            ["is_certifier"],
            unique=False,
        )


def downgrade():
    if not _column_exists("user_users", "is_certifier"):
        return
    with op.batch_alter_table("user_users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_users_is_certifier"))
        batch_op.drop_column("is_certifier")
