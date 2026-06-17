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
    LearnerMentorship,
    MentorshipPhase,
    MentorshipChecklist,
    LearnerChecklistItem,
    LearnerTask,
    TaskNotification,
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
                "mentor_bid": profile.mentor_bid,
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
            "mentor_bid",
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

        # Check if user is a mentor (has students assigned)
        mentor_count = LearnerProfile.query.filter_by(mentor_bid=user_bid).count()

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

    # ── GET /api/portal/mentor/students ──
    @app.route(path_prefix + "/mentor/students", methods=["GET"])
    def mentor_students():
        user_bid = request.user.user_id
        students = (
            LearnerProfile.query.filter_by(mentor_bid=user_bid)
            .order_by(LearnerProfile.created_at.desc())
            .all()
        )
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
        user_bid = request.user.user_id
        students = LearnerProfile.query.filter_by(mentor_bid=user_bid).all()
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
                        "mentor_bid": s.mentor_bid,
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
            "mentor_bid",
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
            mentor_bid=data.get("mentor_bid"),
            status="active",
        )
        db.session.add(profile)
        db.session.commit()
        return make_common_response({"learner_bid": profile.learner_bid})

    # ── GET /api/portal/admin/phases ──
    @app.route(path_prefix + "/admin/phases", methods=["GET"])
    def admin_phases():
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
        total_learners = LearnerProfile.query.count()
        active_learners = LearnerProfile.query.filter_by(status="active").count()
        in_progress = LearnerMentorship.query.filter_by(status="in_progress").count()
        passed = LearnerMentorship.query.filter_by(status="passed").count()
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

    # ── POST /api/portal/mentorship/start ──
    @app.route(path_prefix + "/mentorship/start", methods=["POST"])
    def portal_start_mentorship():
        data = request.get_json() or {}
        learner_bid = data.get("learner_bid", "")
        phase_bid = data.get("phase_bid", "")

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


def _recalc_phase_score(learner_bid: str) -> None:
    """Recalculate total score for all in-progress phases of a learner."""
    records = LearnerMentorship.query.filter_by(
        learner_bid=learner_bid, status="in_progress"
    ).all()
    for rec in records:
        phase = MentorshipPhase.query.get(rec.phase_bid)
        if not phase:
            continue

        scored_items = LearnerChecklistItem.query.filter_by(
            learner_bid=learner_bid, status="scored"
        ).all()

        # Get category from checklist template
        theory_scores = []
        practice_scores = []
        review_scores = []
        mentor_scores = []

        for si in scored_items:
            tmpl = MentorshipChecklist.query.get(si.item_bid)
            cat = tmpl.category if tmpl else "exam"
            s = float(si.score or 0)
            if cat == "exam":
                theory_scores.append(s)
            elif cat == "practice":
                practice_scores.append(s)
            elif cat == "review":
                review_scores.append(s)
            elif cat == "mentor":
                mentor_scores.append(s)

        rec.theory_score = sum(theory_scores) / max(len(theory_scores), 1)
        rec.practice_score = sum(practice_scores) / max(len(practice_scores), 1)
        rec.peer_review_score = sum(review_scores) / max(len(review_scores), 1)
        rec.mentor_score = sum(mentor_scores) / max(len(mentor_scores), 1)

        rec.total_score = (
            float(rec.theory_score or 0) * float(phase.theory_weight or 0.4)
            + float(rec.practice_score or 0) * float(phase.practice_weight or 0.3)
            + float(rec.peer_review_score or 0) * float(phase.review_weight or 0.2)
            + float(rec.mentor_score or 0) * float(phase.mentor_weight or 0.1)
        )

        if rec.total_score >= float(phase.passing_score or 60):
            rec.status = "passed"
            rec.completed_at = datetime.utcnow()

    db.session.commit()
