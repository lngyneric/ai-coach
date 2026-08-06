"""rename learner_profiles.mentor_bid -> coach_bid

Revision ID: d3e5f7a9b1c2
Revises: b7c8d9e0f1a2
Create Date: 2026-08-06 18:00:00.000000

W3 task 3 — rename ``learner_profiles.mentor_bid`` to ``coach_bid``:

- The learner's assigned coach column on ``learner_profiles`` is renamed so the
  domain language matches everywhere else (``coach_profiles.coach_bid``,
  ``coach_sessions``, ``learner_coaching.coach_score``). Values are **not**
  transformed — the same bid is kept, only the column name changes.
- The ORM model ``LearnerProfile.mentor_bid`` becomes ``coach_bid`` in the same
  change set; user/coach-session ``mentor_bid`` columns (``user_users``,
  ``coach_sessions``) are intentionally left untouched (out of scope).

Idempotency / robustness:
- If ``coach_bid`` already exists and ``mentor_bid`` does not → no-op (already
  migrated).
- If both exist (partial / re-run after a manual column add) → copy any values
  missing in ``coach_bid`` from ``mentor_bid``, then drop ``mentor_bid``.
- The happy path (``mentor_bid`` present, ``coach_bid`` absent) uses a
  `RENAME COLUMN` which preserves the data and the index in place.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d3e5f7a9b1c2"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def _table_columns(table: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return None
    return {c["name"] for c in inspector.get_columns(table)}


def upgrade():
    cols = _table_columns("learner_profiles")
    if cols is None:
        return
    has_mentor = "mentor_bid" in cols
    has_coach = "coach_bid" in cols

    if not has_mentor and has_coach:
        return  # already migrated

    if has_mentor and not has_coach:
        # MySQL 8.0 / SQLite 3.25+ RENAME COLUMN — data + index preserved.
        op.alter_column(
            "learner_profiles",
            "mentor_bid",
            new_column_name="coach_bid",
            existing_type=sa.String(length=32),
            existing_nullable=True,
        )
        return

    if has_mentor and has_coach:
        # Partial state (e.g. a manual column add during a hot cutover):
        # backfill any rows whose coach_bid is still empty, then drop the old.
        op.execute(
            "UPDATE learner_profiles SET coach_bid = mentor_bid "
            "WHERE coach_bid IS NULL OR coach_bid = ''"
        )
        op.drop_column("learner_profiles", "mentor_bid")


def downgrade():
    cols = _table_columns("learner_profiles")
    if cols is None:
        return
    has_mentor = "mentor_bid" in cols
    has_coach = "coach_bid" in cols

    if not has_coach:
        return

    if has_coach and not has_mentor:
        op.alter_column(
            "learner_profiles",
            "coach_bid",
            new_column_name="mentor_bid",
            existing_type=sa.String(length=32),
            existing_nullable=True,
        )
    elif has_coach and has_mentor:
        op.execute(
            "UPDATE learner_profiles SET mentor_bid = coach_bid "
            "WHERE mentor_bid IS NULL OR mentor_bid = ''"
        )
        op.drop_column("learner_profiles", "coach_bid")
