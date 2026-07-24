"""Learning Portal — Learner Profile / Mentor / Admin routes."""

from __future__ import annotations

import uuid
from datetime import datetime, date

from flask import Flask, request
from flaskr.dao import db
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.common.models import raise_param_error
from flaskr.service.learning_portal.models import (
    LearnerProfile,
    LearnerCoaching,
    CoachingPhase,
    CoachingChecklist,
    LearnerChecklistItem,
    LearnerTask,
    TaskNotification,
    CourseEnrollment,
)
from flaskr.util.uuid import generate_id


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

        coachings = []
        if profile:
            records = (
                LearnerCoaching.query.filter_by(learner_bid=profile.learner_bid)
                .order_by(LearnerCoaching.created_at.desc())
                .all()
            )
            for r in records:
                phase = CoachingPhase.query.get(r.phase_bid)
                coachings.append(
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
        coach_count = LearnerProfile.query.filter_by(coach_bid=user_bid).count()

        return make_common_response(
            {
                "coachings": coachings,
                "pending_tasks": tasks,
                "unread_notifications": notif_count,
                "coach_student_count": coach_count,
                "total_courses": LearnerCoaching.query.filter_by(
                    learner_bid=profile.learner_bid if profile else ""
                ).count(),
                "completed_courses": LearnerCoaching.query.filter_by(
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

        if not category_slug:
            items = (
                DraftShifu.query.filter(DraftShifu.deleted == 0)
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
                    DraftShifu.deleted == 0,
                )
                .order_by(DraftShifu.id.desc())
                .all()
            ) if bids else []

        return make_common_response([
            {
                "bid": s.shifu_bid,
                "name": s.title,
                "description": getattr(s, "description", ""),
                "tts_enabled": bool(s.tts_enabled) if hasattr(s, 'tts_enabled') else False,
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

    # ── GET /api/portal/coach/students ──
    @app.route(path_prefix + "/coach/students", methods=["GET"])
    def coach_students():
        user_bid = request.user.user_id
        students = (
            LearnerProfile.query.filter_by(coach_bid=user_bid)
            .order_by(LearnerProfile.created_at.desc())
            .all()
        )
        result = []
        for s in students:
            active_phase = (
                LearnerCoaching.query.filter_by(
                    learner_bid=s.learner_bid, status="in_progress"
                )
                .order_by(LearnerCoaching.created_at.desc())
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
                    "pending_task_count": LearnerTask.query.filter_by(learner_bid=s.learner_bid, status="pending").count(),
                    "pending_score_count": pending_count,
                }
            )
        return make_common_response(result)

    # ── GET /api/portal/coach/pending-scores ──
    @app.route(path_prefix + "/coach/pending-scores", methods=["GET"])
    def coach_pending_scores():
        user_bid = request.user.user_id
        students = LearnerProfile.query.filter_by(coach_bid=user_bid).all()
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

    # ── POST /api/portal/coaching/items/<record_bid>/score ──
    @app.route(
        path_prefix + "/coaching/items/<record_bid>/score", methods=["POST"]
    )
    def coach_score_item(record_bid):
        user_bid = request.user.user_id
        data = request.get_json() or {}
        score = data.get("score")
        comment = data.get("comment", "")

        item = LearnerChecklistItem.query.get(record_bid)
        if not item:
            raise_param_error("item not found")
        if item.status != "submitted":
            raise_param_error("item is not in submitted status")

        item.score = float(score) if score else None
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
        data = request.get_json() or {}
        learner_bid = data.get("learner_bid", "")
        title = data.get("title", "")
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
        page = int(request.args.get("page", "1"))
        size = int(request.args.get("size", "20"))
        query = LearnerProfile.query.order_by(LearnerProfile.created_at.desc())
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
        if not getattr(request.user, "is_operator", False):
            raise_param_error("admin permission required")
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
        if not getattr(request.user, "is_operator", False):
            raise_param_error("admin permission required")
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
        phases = CoachingPhase.query.order_by(CoachingPhase.sort_order).all()
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
                    "coach_weight": float(p.coach_weight) if p.coach_weight else None,
                    "is_active": bool(p.is_active),
                }
                for p in phases
            ]
        )

    # ── PUT /api/portal/admin/phases/<phase_bid> ──
    @app.route(path_prefix + "/admin/phases/<phase_bid>", methods=["PUT"])
    def admin_update_phase(phase_bid):
        data = request.get_json() or {}
        phase = CoachingPhase.query.get(phase_bid)
        if not phase:
            raise_param_error("phase not found")
        for field in (
            "name", "description", "duration_days", "passing_score",
            "theory_weight", "practice_weight", "review_weight", "coach_weight",
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
        items = CoachingChecklist.query.filter_by(phase_bid=phase_bid).order_by(
            CoachingChecklist.sort_order
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
        data = request.get_json() or {}
        item = CoachingChecklist(
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
        total_learners = LearnerProfile.query.count()
        active_learners = LearnerProfile.query.filter_by(status="active").count()
        in_progress = LearnerCoaching.query.filter_by(status="in_progress").count()
        passed = LearnerCoaching.query.filter_by(status="passed").count()
        return make_common_response(
            {
                "total_learners": total_learners,
                "active_learners": active_learners,
                "in_progress_coachings": in_progress,
                "passed_coachings": passed,
            }
        )

    # ── GET /api/portal/admin/roles ──
    @app.route(path_prefix + "/admin/roles", methods=["GET"])
    def admin_list_roles():
        """List all users with their role flags (requires is_operator)."""
        if not getattr(request.user, "is_operator", False):
            raise_param_error("admin permission required")

        page = int(request.args.get("page", "1"))
        size = int(request.args.get("size", "50"))
        from flaskr.service.user.models import UserEntity
        query = UserEntity.query.order_by(UserEntity.id.desc())
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        return make_common_response({
            "total": total,
            "page": page,
            "items": [
                {
                    "user_bid": u.user_bid,
                    "nickname": u.nickname,
                    "is_creator": bool(u.is_creator),
                    "is_operator": bool(u.is_operator),
                }
                for u in users
            ],
        })

    # ── PUT /api/portal/admin/roles/<user_bid> ──
    @app.route(path_prefix + "/admin/roles/<user_bid>", methods=["PUT"])
    def admin_update_roles(user_bid):
        """Grant or revoke creator/operator roles (requires is_operator)."""
        if not getattr(request.user, "is_operator", False):
            raise_param_error("admin permission required")

        data = request.get_json() or {}
        from flaskr.service.user.repository import mark_user_roles

        grant_creator = data.get("grant_creator")
        grant_operator = data.get("grant_operator")
        revoke_creator = data.get("revoke_creator")
        revoke_operator = data.get("revoke_operator")

        kwargs = {}
        if grant_creator is True:
            kwargs["is_creator"] = True
        if grant_operator is True:
            kwargs["is_operator"] = True
        if revoke_creator is True:
            kwargs["is_creator"] = False
        if revoke_operator is True:
            kwargs["is_operator"] = False

        if not kwargs:
            raise_param_error("no role changes specified")

        mark_user_roles(user_bid, **kwargs)
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
            **kwargs,
        })

    # ── POST /api/portal/coaching/start ──
    @app.route(path_prefix + "/coaching/start", methods=["POST"])
    def portal_start_coaching():
        data = request.get_json() or {}
        learner_bid = data.get("learner_bid", "")
        phase_bid = data.get("phase_bid", "")

        existing = LearnerCoaching.query.filter_by(
            learner_bid=learner_bid, phase_bid=phase_bid, status="in_progress"
        ).first()
        if existing:
            raise_param_error("phase already in progress")

        record = LearnerCoaching(
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
            phase = CoachingPhase.query.get(phase_bid)
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
        """Assign a course to a user for a training module."""
        user_bid = request.get_json().get("user_bid")
        shifu_bid = request.get_json().get("shifu_bid")
        module = request.get_json().get("module")
        if not all([user_bid, shifu_bid, module]):
            raise_param_error("user_bid, shifu_bid, module are required")
        if module not in ("onboarding", "coaching", "intensive", "leadership"):
            raise_param_error("invalid module")

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

    # ── GET /api/portal/coach/phase-detail/<learner_bid> ──
    @app.route(path_prefix + "/coach/phase-detail/<learner_bid>", methods=["GET"])
    def coach_phase_detail(learner_bid):
        """Get detailed phase progress for a learner."""
        records = LearnerCoaching.query.filter_by(learner_bid=learner_bid).order_by(LearnerCoaching.created_at).all()
        result = []
        for rec in records:
            phase = CoachingPhase.query.get(rec.phase_bid)
            items = LearnerChecklistItem.query.filter_by(learner_bid=learner_bid).all()
            scored = sum(1 for i in items if i.status == "scored")
            total = len(items) or 1
            result.append({
                "phase_bid": rec.phase_bid,
                "phase_name": phase.name if phase else "",
                "status": rec.status,
                "theory_score": float(rec.theory_score or 0),
                "practice_score": float(rec.practice_score or 0),
                "coach_score": float(rec.coach_score or 0),
                "total_score": float(rec.total_score or 0),
                "checklist_progress": f"{scored}/{len(items)}",
                "checklist_pct": round(scored / total * 100, 1),
                "started_at": str(rec.started_at or ""),
                "completed_at": str(rec.completed_at or ""),
                "coach_summary": rec.coach_summary or "",
                "learner_feedback": rec.learner_feedback or "",
                "improvement_plan": rec.improvement_plan or "",
            })
        return make_common_response(result)

    # ── POST /api/portal/coach/phase-summary/<record_bid> ──
    @app.route(path_prefix + "/coach/phase-summary/<record_bid>", methods=["POST"])
    def coach_phase_summary(record_bid):
        """Submit phase summary and evaluation."""
        data = request.get_json() or {}
        rec = LearnerCoaching.query.get(record_bid)
        if not rec:
            raise_param_error("phase record not found")
        if "coach_summary" in data:
            rec.coach_summary = data["coach_summary"]
        if "learner_feedback" in data:
            rec.learner_feedback = data["learner_feedback"]
        if "improvement_plan" in data:
            rec.improvement_plan = data["improvement_plan"]
        if data.get("complete"):
            rec.status = "completed"
            rec.completed_at = datetime.utcnow()
        rec.updated_at = datetime.utcnow()
        db.session.commit()
        return make_common_response({"ok": True})

    # ── POST /api/portal/coach/session ──
    @app.route(path_prefix + "/coach/session", methods=["POST"])
    def create_coach_session():
        """Record a coaching session."""
        import uuid
        data = request.get_json() or {}
        session = CoachSession(
            session_bid=uuid.uuid4().hex[:32],
            learner_bid=data["learner_bid"],
            coach_bid=request.user.user_id,
            phase_bid=data.get("phase_bid", ""),
            session_type=data.get("session_type", "regular"),
            session_date=datetime.utcnow(),
            duration_minutes=data.get("duration", 0),
            topic=data.get("topic", ""),
            coach_notes=data.get("coach_notes", ""),
            learner_notes=data.get("learner_notes", ""),
            action_items=data.get("action_items", ""),
        )
        db.session.add(session)
        db.session.commit()
        return make_common_response({"session_bid": session.session_bid})

    # ── GET /api/portal/coach/sessions/<learner_bid> ──
    @app.route(path_prefix + "/coach/sessions/<learner_bid>", methods=["GET"])
    def get_coach_sessions(learner_bid):
        """Get coaching session history."""
        sessions = CoachSession.query.filter_by(learner_bid=learner_bid).order_by(CoachSession.session_date.desc()).limit(50).all()
        return make_common_response([{
            "session_bid": s.session_bid,
            "session_type": s.session_type,
            "session_date": str(s.session_date),
            "duration": s.duration_minutes,
            "topic": s.topic,
            "coach_notes": s.coach_notes,
            "action_items": s.action_items,
            "status": s.status,
        } for s in sessions])

    # ── GET /api/portal/coach/report/<learner_bid> ──
    @app.route(path_prefix + "/coach/report/<learner_bid>", methods=["GET"])
    def coach_report(learner_bid):
        """Generate coaching analysis report."""
        profile = LearnerProfile.query.filter_by(user_bid=learner_bid).first()
        records = LearnerCoaching.query.filter_by(learner_bid=learner_bid).order_by(LearnerCoaching.created_at).all()
        sessions = CoachSession.query.filter_by(learner_bid=learner_bid).order_by(CoachSession.session_date).all()
        items = LearnerChecklistItem.query.filter_by(learner_bid=learner_bid).all()
        total_items = len(items)
        scored_items = sum(1 for i in items if i.status == "scored")
        passed_items = sum(1 for i in items if i.status == "scored" and (i.score or 0) >= 3)
        phases = []
        for rec in records:
            phase = CoachingPhase.query.get(rec.phase_bid)
            phases.append({
                "name": phase.name if phase else "",
                "status": rec.status,
                "total_score": float(rec.total_score or 0),
                "passing_score": float(phase.passing_score) if phase else 60,
                "theory_score": float(rec.theory_score or 0),
                "practice_score": float(rec.practice_score or 0),
                "coach_score": float(rec.coach_score or 0),
                "coach_summary": rec.coach_summary or "",
                "started_at": str(rec.started_at or ""),
                "completed_at": str(rec.completed_at or ""),
            })
        return make_common_response({
            "learner_name": profile.name if profile else "",
            "learner_bid": learner_bid,
            "total_phases": len(records),
            "completed_phases": sum(1 for r in records if r.status == "completed"),
            "in_progress_phases": sum(1 for r in records if r.status == "in_progress"),
            "checklist_total": total_items,
            "checklist_scored": scored_items,
            "checklist_passed": passed_items,
            "checklist_pass_rate": round(passed_items / total_items * 100, 1) if total_items else 0,
            "session_count": len(sessions),
            "phases": phases,
            "generated_at": str(datetime.utcnow()),
        })


def _recalc_phase_score(learner_bid: str) -> None:
    """Recalculate total score for all in-progress phases of a learner."""
    records = LearnerCoaching.query.filter_by(
        learner_bid=learner_bid, status="in_progress"
    ).all()
    for rec in records:
        phase = CoachingPhase.query.get(rec.phase_bid)
        if not phase:
            continue

        scored_items = LearnerChecklistItem.query.filter_by(
            learner_bid=learner_bid, status="scored"
        ).all()

        # Get category from checklist template
        theory_scores = []
        practice_scores = []
        review_scores = []
        coach_scores = []

