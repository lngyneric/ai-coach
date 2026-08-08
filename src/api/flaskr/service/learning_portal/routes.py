"""Learning Portal — Learner Profile / Mentor / Admin routes."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, date

from flask import Flask, request
from sqlalchemy import or_, text
from flaskr.dao import db
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.common.models import AppException, raise_param_error
from flaskr.service.coach.permissions import (
    get_user_permissions,
    has_permission,
    resolve_user_roles,
    visible_students_scope,
)
from flaskr.service.learning_portal.models import (
    LearnerProfile,
    LearnerMentorship,
    MentorshipPhase,
    MentorshipChecklist,
    LearnerChecklistItem,
    LearnerTask,
    TaskNotification,
    CourseEnrollment,
)
from flaskr.util.uuid import generate_id


# Permission denied business code (HTTP-agnostic, matches frontend `code !== 0`).
PERMISSION_DENIED_CODE = 403

# role tag → fuzzy keywords used to match learner_profiles.department /
# position_name (closed-loop-2 batch assignment). Codes align with P1P2 Q2;
# keywords mirror recommend.py's position fuzzy map. Unknown tags degrade to
# a literal substring match of the tag itself.
_ROLE_MATCH_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sales": ("销售", "sales", "客服", "客户"),
    "production": ("生产", "production", "产线", "制造", "车间"),
    "hr": ("人事", "hr", "人资", "招聘"),
    "qc": ("质检", "qc", "质量"),
    "management": ("管理", "management", "经理", "领导", "主管"),
    "medical": ("检验", "medical", "实验室", "流式"),
    "digital": ("数字化", "digital", "智能体"),
    "general": ("通用", "general", "入职", "新员工"),
}


def _require_permission(app, user, permission: str) -> None:
    """Raise a 403-style business error when the user lacks ``permission``."""
    if not has_permission(app, user, permission):
        raise AppException("没有权限执行此操作", PERMISSION_DENIED_CODE)


def _apply_students_scope(query, scope: str):
    """Filter a ``LearnerProfile`` query by a ``visible_students_scope`` string.

    Handles the exact strings returned by ``visible_students_scope``:

    - ``"all"``                    → no filter (admin / hr)
    - ``"department:<dept>"``      → ``LearnerProfile.department == dept``
    - ``"mentored:<user_bid>"``    → ``LearnerProfile.coach_bid == user_bid``
    - ``"self:<user_bid>"``        → ``LearnerProfile.user_bid == user_bid``

    Unknown / malformed scopes degrade to the empty filter (no rows) so a
    misconfigured scope can never widen visibility beyond ``all``.
    """
    if not scope or scope == "all":
        return query
    if scope.startswith("department:"):
        dept = scope.split(":", 1)[1]
        return query.filter(LearnerProfile.department == dept)
    if scope.startswith("mentored:"):
        coach_bid = scope.split(":", 1)[1]
        return query.filter(LearnerProfile.coach_bid == coach_bid)
    if scope.startswith("self:"):
        user_bid = scope.split(":", 1)[1]
        return query.filter(LearnerProfile.user_bid == user_bid)
    # Unknown scope → return nothing (safe degradation).
    return query.filter(db.text("1 = 0"))


def _require_mentored_learner(app, user, learner_bid: str) -> None:
    """Raise a 403 business error unless ``user`` may act on ``learner_bid``.

    Rule (docs/P0-ACCEPTANCE-TEST-REPORT.md §六 D4 / §八.4):
    - admin / hr (scope ``all``) keep the exception and may act on any learner;
    - everyone else must be the learner's own mentor
      (``LearnerProfile.coach_bid == user.user_id``), i.e. the ``mentored:``
      data scope.
    """
    scope = visible_students_scope(app, user)
    if scope == "all":
        return
    profile = LearnerProfile.query.filter_by(learner_bid=learner_bid).first()
    if profile is None or profile.coach_bid != user.user_id:
        raise AppException("没有权限操作非带教学员的数据", PERMISSION_DENIED_CODE)


def _match_learners_by_role(role_tag: str) -> set[str]:
    """Return the ``user_bid`` set of learners matching a role tag.

    Matching is a case-insensitive substring test against
    ``learner_profiles.department`` and ``learner_profiles.position_name``
    (closed-loop 2, PORTAL-COURSE-ALIGNMENT). Unknown / empty tags degrade to
    an empty set (never an error).
    """
    tag = str(role_tag or "").strip().lower()
    if not tag:
        return set()
    keywords = _ROLE_MATCH_KEYWORDS.get(tag, (tag,))
    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(LearnerProfile.department.like(pattern))
        conditions.append(LearnerProfile.position_name.like(pattern))
    rows = (
        LearnerProfile.query.with_entities(LearnerProfile.user_bid)
        .filter(or_(*conditions))
        .all()
    )
    return {row[0] for row in rows if row[0]}


def _batch_enroll_by_role(
    app, trainer_bid: str, shifu_bid: str, module: str, role_tags: list[str]
) -> dict:
    """Batch-assign a course to every learner matching any role tag.

    Already-enrolled users (unique ``(user_bid, shifu_bid)``) are skipped.
    Returns ``{"enrolled": N, "skipped": M, "errors": [...]}``; a DB failure
    rolls back the whole batch and surfaces the message in ``errors`` (the
    endpoint still returns a 0 business code, consistent with single-enroll).
    """
    matched: set[str] = set()
    for role_tag in role_tags:
        matched |= _match_learners_by_role(role_tag)

    enrolled = 0
    skipped = 0
    now = datetime.utcnow()
    for user_bid in sorted(matched):
        exists = CourseEnrollment.query.filter_by(
            user_bid=user_bid, shifu_bid=shifu_bid
        ).first()
        if exists is not None:
            skipped += 1
            continue
        db.session.add(
            CourseEnrollment(
                user_bid=user_bid,
                shifu_bid=shifu_bid,
                trainer_bid=trainer_bid,
                module=module,
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        enrolled += 1
    try:
        db.session.commit()
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        app.logger.error(
            "[portal] batch enroll failed for course %s role_tags=%s: %s",
            shifu_bid,
            role_tags,
            exc,
        )
        return {"enrolled": 0, "skipped": 0, "errors": [str(exc)]}
    return {"enrolled": enrolled, "skipped": skipped, "errors": []}


@inject
def register_learning_portal_routes(
    app: Flask, path_prefix: str = "/api/portal"
) -> None:
    app.logger.info("register learning portal routes %s", path_prefix)

    # ═══════════════════════════════════════════════
    #  学员端 API
    # ═══════════════════════════════════════════════

    # ── GET /api/portal/profile ──
    @app.route(path_prefix + "/profile", methods=["GET"])
    def portal_get_profile():
        user_bid = request.user.user_id
        profile = LearnerProfile.query.filter_by(
            user_bid=user_bid, status="active"
        ).first()
        if not profile:
            return make_common_response(None)
        return make_common_response(
            {
                "learner_bid": profile.learner_bid,
                "user_bid": profile.user_bid,
                "employee_no": profile.employee_no,
                "department": profile.department,
                "position_name": profile.position_name,
                "level": profile.level,
                "coach_bid": profile.coach_bid,
                "supervisor_bid": profile.supervisor_bid,
                "onboarding_date": str(profile.onboarding_date)
                if profile.onboarding_date
                else None,
                "probation_end_date": str(profile.probation_end_date)
                if profile.probation_end_date
                else None,
                "status": profile.status,
            }
        )

    # ── PUT /api/portal/profile ──
    @app.route(path_prefix + "/profile", methods=["PUT"])
    def portal_update_profile():
        user_bid = request.user.user_id
        data = request.get_json() or {}
        profile = LearnerProfile.query.filter_by(user_bid=user_bid).first()
        if not profile:
            profile = LearnerProfile(learner_bid=uuid.uuid4().hex, user_bid=user_bid)
            db.session.add(profile)

        for field in (
            "employee_no",
            "department",
            "position_name",
            "level",
            "coach_bid",
            "supervisor_bid",
        ):
            val = data.get(field)
            if val is not None:
                setattr(profile, field, str(val).strip())
        for field in ("onboarding_date", "probation_end_date"):
            val = data.get(field)
            if val:
                setattr(profile, field, date.fromisoformat(str(val)))
        db.session.commit()
        return make_common_response({"learner_bid": profile.learner_bid})

    # ── GET /api/portal/dashboard ──
    @app.route(path_prefix + "/dashboard", methods=["GET"])
    def portal_dashboard():
        user_bid = request.user.user_id
        profile = LearnerProfile.query.filter_by(user_bid=user_bid).first()

        mentorships = []
        if profile:
            records = (
                LearnerMentorship.query.filter_by(learner_bid=profile.learner_bid)
                .order_by(LearnerMentorship.created_at.desc())
                .all()
            )
            for r in records:
                phase = MentorshipPhase.query.get(r.phase_bid)
                mentorships.append(
                    {
                        "record_bid": r.record_bid,
                        "phase_bid": r.phase_bid,
                        "phase_name": phase.name if phase else "",
                        "status": r.status,
                        "total_score": float(r.total_score) if r.total_score else None,
                        "started_at": str(r.started_at) if r.started_at else None,
                    }
                )

        pending_tasks = (
            LearnerTask.query.filter_by(
                learner_bid=profile.learner_bid if profile else "",
                status="pending",
            )
            .order_by(LearnerTask.due_at.asc())
            .limit(10)
            .all()
        )
        tasks = [
            {
                "task_bid": t.task_bid,
                "title": t.title,
                "task_type": t.task_type,
                "due_at": str(t.due_at) if t.due_at else None,
            }
            for t in pending_tasks
        ]

        # Unread notifications count
        notif_count = 0
        if profile:
            notif_count = TaskNotification.query.filter_by(
                user_bid=user_bid, is_read=0
            ).count()

        # Check if user is a coach (has students assigned)
        mentor_count = LearnerProfile.query.filter_by(coach_bid=user_bid).count()

        return make_common_response(
            {
                "mentorships": mentorships,
                "pending_tasks": tasks,
                "unread_notifications": notif_count,
                "mentor_student_count": mentor_count,
                "total_courses": LearnerMentorship.query.filter_by(
                    learner_bid=profile.learner_bid if profile else ""
                ).count(),
                "completed_courses": LearnerMentorship.query.filter_by(
                    learner_bid=profile.learner_bid if profile else "",
                    status="passed",
                ).count(),
                "completion_rate": 0,
            }
        )

    # ═══════════════════════════════════════════════
    #  课程分类 API
    # ═══════════════════════════════════════════════

    # ── GET /api/portal/courses?category=onboarding ──
    @app.route(path_prefix + "/courses", methods=["GET"])
    def portal_courses_by_category():
        """List shifus, optionally filtered by category slug."""
        category_slug = (request.args.get("category") or "").strip().lower()
        from flaskr.service.shifu.models import DraftShifu
        from flaskr.service.shifu.utils import get_shifu_res_url_dict

        # 每个 shifu_bid 取最新 draft revision（draft_shifus 保存历史修订，
        # 直接全查会重复返回同一课程的旧版本，与 get_shifu_draft_list 一致去重）
        latest_subquery = (
            db.session.query(db.func.max(DraftShifu.id))
            .filter(DraftShifu.deleted == 0)
            .group_by(DraftShifu.shifu_bid)
        ).subquery()

        if not category_slug:
            items = (
                DraftShifu.query.filter(DraftShifu.id.in_(latest_subquery))
                .order_by(DraftShifu.id.desc())
                .all()
            )
        else:
            # Filter via shifu_category_map
            from flaskr.dao import db as _db
            rows = _db.session.execute(
                _db.text(
                    "SELECT m.shifu_bid FROM shifu_category_map m "
                    "JOIN course_categories c ON m.category_bid = c.category_bid "
                    "WHERE c.slug = :slug"
                ),
                {"slug": category_slug},
            ).fetchall()
            bids = [r[0] for r in rows]
            items = (
                DraftShifu.query.filter(
                    DraftShifu.shifu_bid.in_(bids),
                    DraftShifu.id.in_(latest_subquery),
                )
                .order_by(DraftShifu.id.desc())
                .all()
            ) if bids else []

        # avatar_res_bid → 资源 URL（与 get_shifu_draft_list 返回一致）
        res_url_map = get_shifu_res_url_dict(
            [s.avatar_res_bid for s in items if s.avatar_res_bid]
        )

        return make_common_response([
            {
                "bid": s.shifu_bid,
                "name": s.title,
                "description": getattr(s, "description", ""),
                "tts_enabled": bool(s.tts_enabled) if hasattr(s, 'tts_enabled') else False,
                "keywords": [
                    kw.strip()
                    for kw in (s.keywords or "").split(",")
                    if kw.strip()
                ],
                "avatar": res_url_map.get(s.avatar_res_bid, ""),
            }
            for s in items
        ])

    # ── GET /api/portal/notifications ──
    @app.route(path_prefix + "/notifications", methods=["GET"])
    def portal_notifications():
        user_bid = request.user.user_id
        notifs = (
            TaskNotification.query.filter_by(user_bid=user_bid)
            .order_by(TaskNotification.created_at.desc())
            .limit(20)
            .all()
        )
        return make_common_response(
            [
                {
                    "notif_bid": n.notif_bid,
                    "title": n.title,
                    "content": n.content,
                    "notif_type": n.notif_type,
                    "is_read": bool(n.is_read),
                    "created_at": str(n.created_at) if n.created_at else None,
                }
                for n in notifs
            ]
        )

    # ── POST /api/portal/notifications/read ──
    @app.route(path_prefix + "/notifications/read", methods=["POST"])
    def portal_notifications_read():
        user_bid = request.user.user_id
        TaskNotification.query.filter_by(user_bid=user_bid, is_read=0).update(
            {"is_read": 1}
        )
        db.session.commit()
        return make_common_response({"ok": True})

    # ═══════════════════════════════════════════════
    #  导师端 API
    # ═══════════════════════════════════════════════

    # ── GET /api/portal/mentor/students ──
    @app.route(path_prefix + "/mentor/students", methods=["GET"])
    def mentor_students():
        _require_permission(app, request.user, "view_all_students")
        # B1 (P0-PERMISSION-GAP-AUDIT D-G2): consume visible_students_scope
        # exactly like ``admin/learners`` so admin/hr see everyone, dept_head
        # see their own department and coach see their mentees.
        scope = visible_students_scope(app, request.user)
        query = LearnerProfile.query.order_by(LearnerProfile.created_at.desc())
        query = _apply_students_scope(query, scope)
        students = query.all()
        result = []
        for s in students:
            active_phase = (
                LearnerMentorship.query.filter_by(
                    learner_bid=s.learner_bid, status="in_progress"
                )
                .order_by(LearnerMentorship.created_at.desc())
                .first()
            )
            pending_count = LearnerChecklistItem.query.filter_by(
                learner_bid=s.learner_bid, status="submitted"
            ).count()
            result.append(
                {
                    "learner_bid": s.learner_bid,
                    "user_bid": s.user_bid,
                    "employee_no": s.employee_no,
                    "department": s.department,
                    "position_name": s.position_name,
                    "onboarding_date": str(s.onboarding_date)
                    if s.onboarding_date
                    else None,
                    "status": s.status,
                    "current_phase_status": active_phase.status if active_phase else None,
                    "pending_score_count": pending_count,
                }
            )
        return make_common_response(result)

    # ── GET /api/portal/mentor/pending-scores ──
    @app.route(path_prefix + "/mentor/pending-scores", methods=["GET"])
    def mentor_pending_scores():
        _require_permission(app, request.user, "view_all_students")
        # B1 (D-G2): same data-scope fix as ``mentor/students``.
        scope = visible_students_scope(app, request.user)
        query = _apply_students_scope(LearnerProfile.query, scope)
        students = query.all()
        learner_bids = [s.learner_bid for s in students]
        if not learner_bids:
            return make_common_response([])

        items = (
            LearnerChecklistItem.query.filter(
                LearnerChecklistItem.learner_bid.in_(learner_bids),
                LearnerChecklistItem.status == "submitted",
            )
            .order_by(LearnerChecklistItem.submitted_at.asc())
            .all()
        )
        return make_common_response(
            [
                {
                    "record_bid": i.record_bid,
                    "learner_bid": i.learner_bid,
                    "item_bid": i.item_bid,
                    "comment": i.comment,
                    "submitted_at": str(i.submitted_at) if i.submitted_at else None,
                }
                for i in items
            ]
        )

    # ── POST /api/portal/mentorship/items/<record_bid>/score ──
    @app.route(
        path_prefix + "/mentorship/items/<record_bid>/score", methods=["POST"]
    )
    def mentor_score_item(record_bid):
        _require_permission(app, request.user, "score")
        user_bid = request.user.user_id
        data = request.get_json() or {}
        score = data.get("score")
        comment = data.get("comment", "")

        item = LearnerChecklistItem.query.get(record_bid)
        if not item:
            raise_param_error("item not found")
        if item.status != "submitted":
            raise_param_error("item is not in submitted status")

        # D4 fix: score ownership — a coach may only score learners they
        # mentor. admin / hr (scope "all") keep the exception.
        _require_mentored_learner(app, request.user, item.learner_bid)

        # W3-3 scoring hardening:
        # - ``score=0`` is a valid grade — the old `float(score) if score else None`
        #   collapsed 0 into None (falsy), silently dropping a real score.
        # - bounds come from the checklist template's ``max_score`` (default 5.0);
        #   NaN / ±Inf and non-numeric payloads are rejected up front.
        if score is None or str(score).strip() == "":
            raise_param_error("score is required")
        try:
            score_value = float(score)
        except (TypeError, ValueError):
            raise_param_error("score must be a number")
        if not math.isfinite(score_value):
            raise_param_error("score must be a finite number")
        checklist = MentorshipChecklist.query.get(item.item_bid)
        max_score = (
            float(checklist.max_score)
            if checklist is not None and checklist.max_score is not None
            else 5.0
        )
        if score_value < 0 or score_value > max_score:
            raise_param_error(f"score must be between 0 and {max_score}")

        item.score = score_value
        item.scored_by = user_bid
        item.comment = comment
        item.status = "scored"
        item.scored_at = datetime.utcnow()
        db.session.commit()

        # Recalculate phase total score
        _recalc_phase_score(item.learner_bid)

        return make_common_response({"ok": True})

    # ── POST /api/portal/tasks ──
    @app.route(path_prefix + "/tasks", methods=["POST"])
    def portal_create_task():
        # W3-4 guard: task assignment is a coaching operation — requires
        # create_session (admin/coach) AND the target learner must be in the
        # caller's mentored scope (admin/hr scope-all exception preserved).
        _require_permission(app, request.user, "create_session")
        data = request.get_json() or {}
        learner_bid = data.get("learner_bid", "")
        title = data.get("title", "")
        _require_mentored_learner(app, request.user, learner_bid)
        task_type = data.get("task_type", "course")
        due_at = data.get("due_at")

        if not learner_bid or not title:
            raise_param_error("learner_bid and title are required")

        task = LearnerTask(
            task_bid=uuid.uuid4().hex,
            learner_bid=learner_bid,
            title=title,
            description=data.get("description", ""),
            task_type=task_type,
            due_at=datetime.fromisoformat(due_at) if due_at else None,
            created_by=request.user.user_id,
        )
        db.session.add(task)

        # Notify learner
        profile = LearnerProfile.query.get(learner_bid)
        if profile:
            notif = TaskNotification(
                notif_bid=uuid.uuid4().hex,
                user_bid=profile.user_bid,
                title="新的学习任务",
                content=f"你有一个新的{task_type}任务: {title}",
                notif_type="task_assign",
                related_bid=task.task_bid,
            )
            db.session.add(notif)

        db.session.commit()
        return make_common_response({"task_bid": task.task_bid})

    # ═══════════════════════════════════════════════
    #  管理员 API
    # ═══════════════════════════════════════════════

    # ── GET /api/portal/admin/learners ──
    @app.route(path_prefix + "/admin/learners", methods=["GET"])
    def admin_learners():
        # D2: permission guard — learner without `view_all_students` is 403.
        _require_permission(app, request.user, "view_all_students")
        page = int(request.args.get("page", "1"))
        size = int(request.args.get("size", "20"))
        # D3: data-scope filter — admin/hr=all, dept_head=department,
        # coach=mentored, learner=self (though learner is blocked by D2).
        scope = visible_students_scope(app, request.user)
        query = LearnerProfile.query.order_by(LearnerProfile.created_at.desc())
        query = _apply_students_scope(query, scope)
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return make_common_response(
            {
                "total": total,
                "page": page,
                "items": [
                    {
                        "learner_bid": s.learner_bid,
                        "user_bid": s.user_bid,
                        "employee_no": s.employee_no,
                        "department": s.department,
                        "position_name": s.position_name,
                        "level": s.level,
                        "coach_bid": s.coach_bid,
                        "status": s.status,
                        "onboarding_date": str(s.onboarding_date)
                        if s.onboarding_date
                        else None,
                    }
                    for s in items
                ],
            }
        )

    # ── PUT /api/portal/admin/learners/<learner_bid> ──
    @app.route(path_prefix + "/admin/learners/<learner_bid>", methods=["PUT"])
    def admin_update_learner(learner_bid):
        # P2-2: legacy is_operator guard -> has_permission (manage_users).
        _require_permission(app, request.user, "manage_users")
        data = request.get_json() or {}
        profile = LearnerProfile.query.get(learner_bid)
        if not profile:
            raise_param_error("learner not found")
        for field in (
            "employee_no",
            "department",
            "position_name",
            "level",
            "coach_bid",
            "supervisor_bid",
            "status",
        ):
            val = data.get(field)
            if val is not None:
                setattr(profile, field, str(val).strip())
        for field in ("onboarding_date", "probation_end_date"):
            val = data.get(field)
            if val:
                setattr(profile, field, date.fromisoformat(str(val)))
        db.session.commit()
        return make_common_response({"ok": True})

    # ── POST /api/portal/admin/learners ── (create)
    @app.route(path_prefix + "/admin/learners", methods=["POST"])
    def admin_create_learner():
        # P2-2: legacy is_operator guard -> has_permission (manage_users).
        _require_permission(app, request.user, "manage_users")
        data = request.get_json() or {}
        user_bid = data.get("user_bid", "")
        if not user_bid:
            raise_param_error("user_bid is required")

        existing = LearnerProfile.query.filter_by(user_bid=user_bid).first()
        if existing:
            raise_param_error("learner already exists")

        profile = LearnerProfile(
            learner_bid=uuid.uuid4().hex,
            user_bid=user_bid,
            employee_no=data.get("employee_no"),
            department=data.get("department"),
            position_name=data.get("position_name"),
            level=data.get("level"),
            coach_bid=data.get("coach_bid"),
            status="active",
        )
        db.session.add(profile)
        db.session.commit()
        return make_common_response({"learner_bid": profile.learner_bid})

    # ── GET /api/portal/admin/phases ──
    @app.route(path_prefix + "/admin/phases", methods=["GET"])
    def admin_phases():
        # W3-4 guard: phase configuration visible to roster viewers
        # (admin/hr/dept_head/coach). learner → 403.
        _require_permission(app, request.user, "view_all_students")
        phases = MentorshipPhase.query.order_by(MentorshipPhase.sort_order).all()
        return make_common_response(
            [
                {
                    "phase_bid": p.phase_bid,
                    "name": p.name,
                    "code": p.code,
                    "description": p.description,
                    "sort_order": p.sort_order,
                    "duration_days": p.duration_days,
                    "passing_score": float(p.passing_score) if p.passing_score else None,
                    "theory_weight": float(p.theory_weight) if p.theory_weight else None,
                    "practice_weight": float(p.practice_weight) if p.practice_weight else None,
                    "review_weight": float(p.review_weight) if p.review_weight else None,
                    "mentor_weight": float(p.mentor_weight) if p.mentor_weight else None,
                    "is_active": bool(p.is_active),
                }
                for p in phases
            ]
        )

    # ── PUT /api/portal/admin/phases/<phase_bid> ──
    @app.route(path_prefix + "/admin/phases/<phase_bid>", methods=["PUT"])
    def admin_update_phase(phase_bid):
        # W3-4 guard: phase editing is a management operation (admin/hr).
        _require_permission(app, request.user, "manage_users")
        data = request.get_json() or {}
        phase = MentorshipPhase.query.get(phase_bid)
        if not phase:
            raise_param_error("phase not found")
        for field in (
            "name", "description", "duration_days", "passing_score",
            "theory_weight", "practice_weight", "review_weight", "mentor_weight",
        ):
            val = data.get(field)
            if val is not None:
                setattr(phase, field, val)
        if "is_active" in data:
            phase.is_active = 1 if data["is_active"] else 0
        db.session.commit()
        return make_common_response({"ok": True})

    # ── GET /api/portal/admin/checklist/<phase_bid> ──
    @app.route(path_prefix + "/admin/checklist/<phase_bid>", methods=["GET"])
    def admin_checklist(phase_bid):
        # W3-4 guard: checklist templates readable by anyone who can view any
        # report (admin/hr/dept_head/coach). learner → 403.
        _require_permission(app, request.user, "view_any_report")
        items = MentorshipChecklist.query.filter_by(phase_bid=phase_bid).order_by(
            MentorshipChecklist.sort_order
        ).all()
        return make_common_response(
            [
                {
                    "item_bid": i.item_bid,
                    "name": i.name,
                    "description": i.description,
                    "category": i.category,
                    "max_score": float(i.max_score) if i.max_score else None,
                    "sort_order": i.sort_order,
                    "is_required": bool(i.is_required),
                }
                for i in items
            ]
        )

    # ── POST /api/portal/admin/checklist ──
    @app.route(path_prefix + "/admin/checklist", methods=["POST"])
    def admin_create_checklist():
        # W3-4 guard: checklist template management = content certification
        # (admin/hr/dept_head). learner/coach → 403.
        _require_permission(app, request.user, "certify_content")
        data = request.get_json() or {}
        item = MentorshipChecklist(
            item_bid=uuid.uuid4().hex,
            phase_bid=data.get("phase_bid", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", "exam"),
            max_score=float(data.get("max_score", 5)),
        )
        db.session.add(item)
        db.session.commit()
        return make_common_response({"item_bid": item.item_bid})

    # ── GET /api/portal/admin/stats ──
    @app.route(path_prefix + "/admin/stats", methods=["GET"])
    def admin_stats():
        # W3-4 guard: KPI stats visible to view_kpi holders (admin/hr/dept/coach).
        _require_permission(app, request.user, "view_kpi")
        # B1 (P0-PERMISSION-GAP-AUDIT D-G8-2): scope the KPI counts the same
        # way as ``admin/learners`` so a dept_head sees only their department
        # and a coach only their mentees (previously global counts leaked
        # every learner's KPI to dept/coach).
        scope = visible_students_scope(app, request.user)
        learners_query = _apply_students_scope(LearnerProfile.query, scope)
        total_learners = learners_query.count()
        active_learners = learners_query.filter_by(status="active").count()
        learner_bids = [
            row[0]
            for row in learners_query.with_entities(
                LearnerProfile.learner_bid
            ).all()
        ]
        if learner_bids:
            in_progress = LearnerMentorship.query.filter(
                LearnerMentorship.learner_bid.in_(learner_bids),
                LearnerMentorship.status == "in_progress",
            ).count()
            passed = LearnerMentorship.query.filter(
                LearnerMentorship.learner_bid.in_(learner_bids),
                LearnerMentorship.status == "passed",
            ).count()
        else:
            in_progress = 0
            passed = 0
        return make_common_response(
            {
                "total_learners": total_learners,
                "active_learners": active_learners,
                "in_progress_mentorships": in_progress,
                "passed_mentorships": passed,
            }
        )

    # ── GET /api/portal/admin/roles ──
    @app.route(path_prefix + "/admin/roles", methods=["GET"])
    def admin_list_roles():
        """List users with legacy flags (is_creator/is_operator) + 5-level roles."""
        _require_permission(app, request.user, "manage_users")

        page = int(request.args.get("page", "1"))
        size = int(request.args.get("size", "50"))
        from flaskr.service.user.models import UserInfo as UserEntity
        query = UserEntity.query.order_by(UserEntity.id.desc())
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        items = []
        for u in users:
            roles = resolve_user_roles(app, u.user_bid)
            items.append({
                "user_bid": u.user_bid,
                "nickname": u.nickname,
                "is_creator": bool(u.is_creator),
                "is_operator": bool(u.is_operator),
                "roles": [
                    {"role_bid": r["role_bid"], "name": r["name"]}
                    for r in roles
                ],
            })
        return make_common_response({
            "total": total,
            "page": page,
            "items": items,
        })

    # ── PUT /api/portal/admin/roles/<user_bid> ──
    @app.route(path_prefix + "/admin/roles/<user_bid>", methods=["PUT"])
    def admin_update_roles(user_bid):
        """Grant/revoke 5-level roles (requires manage_users).

        B6 (P0-PERMISSION-GAP-AUDIT D-G4): ``user_role_assignments`` is the
        single source of truth. The legacy ``is_creator`` / ``is_operator``
        flags are no longer written here (older clients sending
        grant_operator/revoke_operator etc. are ignored); see the retirement
        schedule in docs/P0-PERMISSION-MODEL-UPGRADE.md §十.
        """
        _require_permission(app, request.user, "manage_users")

        data = request.get_json() or {}
        grant_roles = data.get("grant_roles") or []
        revoke_roles = data.get("revoke_roles") or []

        if not grant_roles and not revoke_roles:
            raise_param_error("no role changes specified")

        # Grant 5-level roles (idempotent insert into user_role_assignments).
        for role_bid in grant_roles:
            existing = db.session.execute(
                text(
                    "SELECT 1 FROM user_role_assignments "
                    "WHERE user_bid = :ub AND role_bid = :rb"
                ),
                {"ub": user_bid, "rb": role_bid},
            ).first()
            if not existing:
                db.session.execute(
                    text(
                        "INSERT INTO user_role_assignments (user_bid, role_bid) "
                        "VALUES (:ub, :rb)"
                    ),
                    {"ub": user_bid, "rb": role_bid},
                )

        # Revoke 5-level roles.
        for role_bid in revoke_roles:
            db.session.execute(
                text(
                    "DELETE FROM user_role_assignments "
                    "WHERE user_bid = :ub AND role_bid = :rb"
                ),
                {"ub": user_bid, "rb": role_bid},
            )
        db.session.commit()

        # Notify user
        notif = TaskNotification(
            notif_bid=uuid.uuid4().hex,
            user_bid=user_bid,
            title="角色权限变更",
            content="你的系统角色已更新",
            notif_type="system",
        )
        db.session.add(notif)
        db.session.commit()

        return make_common_response({
            "ok": True,
            "roles": [
                {"role_bid": r["role_bid"], "name": r["name"]}
                for r in resolve_user_roles(app, user_bid)
            ],
        })

    # ── GET /api/portal/permissions ──
    @app.route(path_prefix + "/permissions", methods=["GET"])
    def portal_my_permissions():
        """Return the current user's roles + permission keys + data scope."""
        user = request.user
        user_bid = getattr(user, "user_id", None) or getattr(user, "user_bid", "")
        roles = resolve_user_roles(app, user_bid)
        return make_common_response(
            {
                "roles": [
                    {"role_bid": r["role_bid"], "name": r["name"]}
                    for r in roles
                ],
                "permissions": get_user_permissions(app, user),
                "data_scope": visible_students_scope(app, user),
            }
        )

    # ── POST /api/portal/mentorship/start ──
    @app.route(path_prefix + "/mentorship/start", methods=["POST"])
    def portal_start_mentorship():
        _require_permission(app, request.user, "create_session")
        data = request.get_json() or {}
        learner_bid = data.get("learner_bid", "")
        phase_bid = data.get("phase_bid", "")

        # D4 fix (same class of horizontal privilege escalation): a coach may
        # only start a phase for a learner they mentor; admin / hr (scope
        # "all") keep the exception.
        _require_mentored_learner(app, request.user, learner_bid)

        existing = LearnerMentorship.query.filter_by(
            learner_bid=learner_bid, phase_bid=phase_bid, status="in_progress"
        ).first()
        if existing:
            raise_param_error("phase already in progress")

        record = LearnerMentorship(
            record_bid=uuid.uuid4().hex,
            learner_bid=learner_bid,
            phase_bid=phase_bid,
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        db.session.add(record)

        # Notify
        profile = LearnerProfile.query.get(learner_bid)
        if profile:
            phase = MentorshipPhase.query.get(phase_bid)
            notif = TaskNotification(
                notif_bid=uuid.uuid4().hex,
                user_bid=profile.user_bid,
                title="新阶段开始",
                content=f"你的{phase.name if phase else ''}阶段已开始，请查看学习计划",
                notif_type="phase_start",
            )
            db.session.add(notif)

        db.session.commit()
        return make_common_response({"record_bid": record.record_bid})

    # ── Enrollment (Training Module Assignment) Routes ──

    @app.route(path_prefix + "/admin/enroll", methods=["POST"])
    def admin_enroll():
        """Assign a course to a user for a training module.

        Two modes (closed-loop 2, PORTAL-COURSE-ALIGNMENT):
        - single: ``{"user_bid", "shifu_bid", "module"}`` (unchanged behavior);
        - batch:  ``{"role_tags": [...], "shifu_bid", "module"}`` — assign the
          course to every learner whose department / position_name matches any
          role tag; returns ``{"enrolled", "skipped", "errors"}``.
        """
        # W3-4 guard: course assignment is a manage_users operation (admin/hr).
        _require_permission(app, request.user, "manage_users")
        data = request.get_json(force=True) or {}
        shifu_bid = data.get("shifu_bid")
        module = data.get("module")
        if module not in ("onboarding", "mentorship", "intensive", "leadership"):
            raise_param_error("invalid module")

        # Batch mode: role_tags present → ignore user_bid, assign by position.
        role_tags = data.get("role_tags")
        if role_tags is not None:
            if not isinstance(role_tags, list) or not role_tags:
                raise_param_error("role_tags must be a non-empty array")
            if not shifu_bid:
                raise_param_error("shifu_bid is required")
            result = _batch_enroll_by_role(
                app, request.user.user_id, shifu_bid, module, role_tags
            )
            return make_common_response(result)

        # Single mode (legacy, unchanged).
        user_bid = data.get("user_bid")
        if not all([user_bid, shifu_bid, module]):
            raise_param_error("user_bid, shifu_bid, module are required")

        enrollment = CourseEnrollment(
            user_bid=user_bid,
            shifu_bid=shifu_bid,
            trainer_bid=request.user.user_id,
            module=module,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(enrollment)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise_param_error("duplicate enrollment or database error")
        return make_common_response({"enroll_id": enrollment.id, "status": "active"})

    @app.route(path_prefix + "/admin/enroll", methods=["DELETE"])
    def admin_unenroll():
        """Remove a course assignment."""
        # W3-4 guard: unenroll is a manage_users operation (admin/hr).
        _require_permission(app, request.user, "manage_users")
        user_bid = request.get_json().get("user_bid")
        shifu_bid = request.get_json().get("shifu_bid")
        if not user_bid or not shifu_bid:
            raise_param_error("user_bid and shifu_bid required")
        deleted = CourseEnrollment.query.filter_by(
            user_bid=user_bid, shifu_bid=shifu_bid
        ).delete()
        db.session.commit()
        return make_common_response({"deleted": deleted > 0})

    @app.route(path_prefix + "/enrollments", methods=["GET"])
    def my_enrollments():
        """Get current user's enrolled courses, optionally filtered by module."""
        module = request.args.get("module", "")
        query = CourseEnrollment.query.filter_by(user_bid=request.user.user_id)
        if module:
            query = query.filter_by(module=module)
        enrollments = query.order_by(CourseEnrollment.created_at.desc()).all()
        result = []
        for e in enrollments:
            result.append(
                {
                    "id": e.id,
                    "shifu_bid": e.shifu_bid,
                    "module": e.module,
                    "status": e.status,
                    "deadline": e.deadline.isoformat() if e.deadline else None,
                    "progress_pct": e.progress_pct,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
            )
        return make_common_response(result)

    @app.route(path_prefix + "/admin/enrollments", methods=["GET"])
    def admin_list_enrollments():
        """Admin: list enrollments for a user or all."""
        # W3-4 guard: enrollment management is a manage_users operation
        # (admin/hr). learner → 403 (was an open horizontal-privilege hole).
        _require_permission(app, request.user, "manage_users")
        user_bid = request.args.get("user_bid", "")
        module = request.args.get("module", "")
        query = CourseEnrollment.query
        if user_bid:
            query = query.filter_by(user_bid=user_bid)
        if module:
            query = query.filter_by(module=module)
        enrollments = query.order_by(CourseEnrollment.created_at.desc()).all()
        result = []
        for e in enrollments:
            result.append(
                {
                    "id": e.id,
                    "user_bid": e.user_bid,
                    "shifu_bid": e.shifu_bid,
                    "trainer_bid": e.trainer_bid,
                    "module": e.module,
                    "status": e.status,
                    "deadline": e.deadline.isoformat() if e.deadline else None,
                    "progress_pct": e.progress_pct,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
            )
        return make_common_response(result)

    @app.route(path_prefix + "/courses/<shifu_bid>/progress", methods=["PUT"])
    def update_progress(shifu_bid):
        """Update learning progress for an enrolled course."""
        user_bid = request.user.user_id
        data = request.get_json() or {}
        progress = data.get("progress_pct", 0)
        status = data.get("status", "")
        enrollment = CourseEnrollment.query.filter_by(
            user_bid=user_bid, shifu_bid=shifu_bid
        ).first()
        if not enrollment:
            raise_param_error("enrollment not found")
        enrollment.progress_pct = min(max(int(progress), 0), 100)
        if status:
            enrollment.status = status
        if enrollment.progress_pct >= 100:
            enrollment.status = "completed"
        enrollment.updated_at = datetime.utcnow()
        db.session.commit()
        return make_common_response({"progress_pct": enrollment.progress_pct})


def _recalc_phase_score(learner_bid: str) -> None:
    """Recalculate sub-scores + total score for every active phase.

    P2-1: completes the previously half-finished implementation. For each
    ``LearnerMentorship`` (learner_coaching) row in ``pending``/``in_progress``
    (W3-3: also cover ``pending`` so scoring always refreshes an active
    phase):

    1. collect the learner's ``scored`` checklist items that map to this
       phase's ``coach_checklist`` templates (join on ``item_bid``);
    2. bucket item scores by ``coach_checklist.category``:
         theory   <- category in (theory, exam)
         practice <- category in (practice)
         review   <- category in (review, peer_review, peer)
         coach    <- category in (mentor, coach, mentor_review)
       each bucket's mean becomes the matching sub-score; when a bucket has
       no items, fall back to the value already stored on the coaching row
       (an explicit sub-score written by another pipeline);
    3. persist the four sub-scores back to ``learner_coaching``;
    4. ``total_score = theory*w_theory + practice*w_practice
                        + peer_review*w_review + coach*w_mentor``
       (weights from ``coach_phases``); ``None`` when every sub-score is absent.
    """
    records = (
        LearnerMentorship.query.filter(
            LearnerMentorship.learner_bid == learner_bid,
            LearnerMentorship.status.in_(("pending", "in_progress")),
        ).all()
    )
    for rec in records:
        phase = MentorshipPhase.query.get(rec.phase_bid)
        if not phase:
            continue

        # Scored items belonging to THIS phase's checklist templates.
        rows = (
            db.session.query(LearnerChecklistItem, MentorshipChecklist.category)
            .join(
                MentorshipChecklist,
                LearnerChecklistItem.item_bid == MentorshipChecklist.item_bid,
            )
            .filter(
                LearnerChecklistItem.learner_bid == learner_bid,
                LearnerChecklistItem.status == "scored",
                MentorshipChecklist.phase_bid == rec.phase_bid,
            )
            .all()
        )

        theory_scores, practice_scores, review_scores, mentor_scores = [], [], [], []
        for item, category in rows:
            if item.score is None:
                continue
            cat = (category or "").strip().lower()
            score = float(item.score)
            if cat in ("theory", "exam"):
                theory_scores.append(score)
            elif cat == "practice":
                practice_scores.append(score)
            elif cat in ("review", "peer_review", "peer"):
                review_scores.append(score)
            elif cat in ("mentor", "coach", "mentor_review"):
                mentor_scores.append(score)

        def _mean(scores):
            return round(sum(scores) / len(scores), 2) if scores else None

        theory = _mean(theory_scores)
        practice = _mean(practice_scores)
        peer_review = _mean(review_scores)
        coach = _mean(mentor_scores)

        # Fall back to explicitly stored sub-scores when no items were scored.
        if theory is None:
            theory = float(rec.theory_score) if rec.theory_score is not None else None
        if practice is None:
            practice = (
                float(rec.practice_score) if rec.practice_score is not None else None
            )
        if peer_review is None:
            peer_review = (
                float(rec.peer_review_score)
                if rec.peer_review_score is not None
                else None
            )
        if coach is None:
            coach = float(rec.coach_score) if rec.coach_score is not None else None

        rec.theory_score = theory
        rec.practice_score = practice
        rec.peer_review_score = peer_review
        rec.coach_score = coach

        def _w(v):
            return float(v) if v is not None else 0.0

        total = None
        if any(s is not None for s in (theory, practice, peer_review, coach)):
            total = round(
                (theory or 0.0) * _w(phase.theory_weight)
                + (practice or 0.0) * _w(phase.practice_weight)
                + (peer_review or 0.0) * _w(phase.review_weight)
                + (coach or 0.0) * _w(phase.mentor_weight),
                2,
            )
        rec.total_score = total

    db.session.commit()

