"""Coach service package — 5-role permission model (AI-Coach P0).

Contains the backend permission service consumed by portal/admin routes:
``permissions.py`` exposes role resolution, permission checks, data-scope
resolution and the permission-key set for the frontend.
"""

from flaskr.service.coach.permissions import (
    get_user_permissions,
    has_permission,
    resolve_user_roles,
    visible_students_scope,
)

__all__ = [
    "resolve_user_roles",
    "has_permission",
    "visible_students_scope",
    "get_user_permissions",
]
