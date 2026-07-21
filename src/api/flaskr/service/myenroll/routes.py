import json
from flask import request
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response

@inject
def register_my_enroll_routes(app, path_prefix="/api/shifu"):
    app.logger.info(f"register my enroll routes {path_prefix}")
    @app.route(path_prefix + "/enrollments", methods=["GET"])
    def my_enrollments():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            uid = request.user.user_id
            rows = db.session.execute(text("SELECT e.shifu_bid, e.module, e.status, e.progress_pct, e.created_at, s.title, s.description FROM course_enrollments e LEFT JOIN shifu_published_shifus s ON e.shifu_bid = s.shifu_bid WHERE e.user_bid = :uid ORDER BY e.created_at DESC").bindparams(uid=uid)).fetchall()
            items = [{"shifu_bid": r[0], "module": r[1], "status": r[2], "progress_pct": r[3], "created_at": str(r[4]) if r[4] else None, "course_name": r[5] or "", "course_desc": r[6] or ""} for r in rows]
            return make_common_response({"items": items, "total": len(items)})
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)
    @app.route(path_prefix + "/dashboard", methods=["GET"])
    def my_dashboard():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            uid = request.user.user_id
            rows = db.session.execute(text("SELECT module, status, progress_pct FROM course_enrollments WHERE user_bid = :uid").bindparams(uid=uid)).fetchall()
            total = len(rows)
            completed = sum(1 for r in rows if r[1] == "completed")
            in_progress = sum(1 for r in rows if r[1] == "active" and (r[2] or 0) > 0)
            assigned = sum(1 for r in rows if r[1] == "active" and (r[2] or 0) == 0)
            modules = {}
            for r in rows:
                m = r[0] or "other"
                modules[m] = modules.get(m, 0) + 1
            return make_common_response({"total_courses": total, "completed": completed, "in_progress": in_progress, "assigned": assigned, "modules": modules})
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)

    # ── Coach phase detail ──
    @app.route(path_prefix + "/coach/phase-detail/<learner_bid>", methods=["GET"])
    def coach_phase_detail(learner_bid):
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            rows = db.session.execute(text("""
                SELECT lm.record_bid, lm.phase_bid, mp.name, lm.status,
                       lm.theory_score, lm.practice_score, lm.coach_score, lm.total_score,
                       lm.started_at, lm.completed_at, lm.remark
                FROM learner_coaching lm
                LEFT JOIN coach_phases mp ON lm.phase_bid = mp.phase_bid
                WHERE lm.learner_bid = :uid ORDER BY lm.created_at
            """).bindparams(uid=learner_bid)).fetchall()
            result = [dict(r._mapping) for r in rows]
            for r in result:
                for k in ['theory_score','practice_score','coach_score','total_score']:
                    if r.get(k) is not None: r[k] = float(r[k])
                for k in ['started_at','completed_at']:
                    if r.get(k) is not None: r[k] = str(r[k])
            return make_common_response(result)
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)

    # ── Phase summary ──
    @app.route(path_prefix + "/coach/phase-summary", methods=["POST"])
    def coach_phase_summary():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            data = request.get_json() or {}
            record_bid = data.get("record_bid")
            if not record_bid:
                return make_common_response({"error": "missing record_bid"})
            updates = []
            if "coach_summary" in data:
                updates.append("coach_summary = :summary")
            if "learner_feedback" in data:
                updates.append("learner_feedback = :feedback")
            if "improvement_plan" in data:
                updates.append("improvement_plan = :plan")
            if data.get("complete"):
                updates.append("status = 'completed'")
                updates.append("completed_at = :now")
            if updates:
                sql = "UPDATE learner_coaching SET " + ", ".join(updates) + ", updated_at = :now WHERE record_bid = :bid"
                db.session.execute(text(sql).bindparams(
                    bid=record_bid, summary=data.get("coach_summary",""),
                    feedback=data.get("learner_feedback",""),
                    plan=data.get("improvement_plan",""), now=dt.utcnow()
                ))
                db.session.commit()
            return make_common_response({"ok": True})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── Coach report ──
    @app.route(path_prefix + "/coach/report/<learner_bid>", methods=["GET"])
    def coach_report(learner_bid):
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            rows = db.session.execute(text("""
                SELECT lm.*, mp.name as phase_name, mp.passing_score
                FROM learner_coaching lm
                LEFT JOIN coach_phases mp ON lm.phase_bid = mp.phase_bid
                WHERE lm.learner_bid = :uid ORDER BY lm.created_at
            """).bindparams(uid=learner_bid)).fetchall()
            phases = []
            for r in rows:
                d = dict(r._mapping)
                for k in ['theory_score','practice_score','coach_score','total_score']:
                    if d.get(k) is not None: d[k] = float(d[k])
                phases.append(d)
            total = len(phases)
            completed = sum(1 for p in phases if p.get('status') == 'completed')
            in_progress = sum(1 for p in phases if p.get('status') == 'in_progress')
            return make_common_response({
                "learner_bid": learner_bid,
                "total_phases": total,
                "completed_phases": completed,
                "in_progress_phases": in_progress,
                "phases": phases,
                "generated_at": str(dt.utcnow()),
            })
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)

    # ── POST /api/shifu/coach/session (enhanced) ──
    @app.route(path_prefix + "/coach/session", methods=["POST"])
    def create_coach_session_v2():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            import uuid
            data = request.get_json() or {}
            bid = uuid.uuid4().hex[:32]
            db.session.execute(text("""
                INSERT INTO coach_sessions (session_bid, learner_bid, mentor_bid, phase_bid,
                  session_type, session_date, duration_minutes, topic, mentor_notes,
                  learner_notes, action_items, pre_course_bids, coach_rating, ai_summary, next_action)
                VALUES (:b, :l, :m, :p, :t, :d, :dur, :top, :mn, :ln, :ai, :pc, :cr, :as, :na)
            """).bindparams(
                b=bid, l=data.get("learner_bid",""), m=request.user.user_id,
                p=data.get("phase_bid",""), t=data.get("session_type","regular"),
                d=dt.utcnow(), dur=data.get("duration",0), top=data.get("topic",""),
                mn=data.get("mentor_notes",""), ln=data.get("learner_notes",""),
                ai=data.get("action_items",""), pc=data.get("pre_course_bids",""),
                cr=data.get("coach_rating"), as_=data.get("ai_summary",""),
                na=data.get("next_action","")
            ))
            db.session.commit()
            return make_common_response({"session_bid": bid})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── POST /api/shifu/coach/feedback ──
    @app.route(path_prefix + "/coach/feedback", methods=["POST"])
    def create_coach_feedback():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            import uuid
            data = request.get_json() or {}
            bid = uuid.uuid4().hex[:32]
            db.session.execute(text("""
                INSERT INTO coach_feedback (feedback_bid, session_bid, learner_bid, question, category, ai_answer, resolved)
                VALUES (:b, :s, :l, :q, :c, :a, :r)
            """).bindparams(
                b=bid, s=data.get("session_bid",""), l=data.get("learner_bid",""),
                q=data.get("question",""), c=data.get("category",""),
                a=data.get("ai_answer",""), r=data.get("resolved",0)
            ))
            db.session.commit()
            return make_common_response({"feedback_bid": bid})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── POST /api/shifu/coach/ai-summary/<session_bid> ──
    @app.route(path_prefix + "/coach/ai-summary/<session_bid>", methods=["POST"])
    def ai_summary_session(session_bid):
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            session = db.session.execute(text("SELECT * FROM coach_sessions WHERE session_bid = :b").bindparams(b=session_bid)).fetchone()
            if not session:
                return make_common_response({"error": "session not found"})
            s = dict(session._mapping)
            # Generate AI summary (simulated)
            summary = f"面谈主题：{s.get('topic','')}。教练记录：{s.get('mentor_notes','')[:100]}。学员反馈：{s.get('learner_notes','')[:100]}。"
            db.session.execute(text("UPDATE coach_sessions SET ai_summary = :summary, updated_at = :now WHERE session_bid = :b").bindparams(summary=summary, now=dt.utcnow(), b=session_bid))
            db.session.commit()
            return make_common_response({"ai_summary": summary})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── GET /api/shifu/coach/recommendations/<learner_bid> ──
    @app.route(path_prefix + "/coach/recommendations/<learner_bid>", methods=["GET"])
    def coach_recommendations(learner_bid):
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            feedbacks = db.session.execute(text("SELECT category, COUNT(*) as cnt FROM coach_feedback WHERE learner_bid=:l GROUP BY category ORDER BY cnt DESC LIMIT 5").bindparams(l=learner_bid)).fetchall()
            weak_areas = [dict(r._mapping) for r in feedbacks]
            # Recommend courses based on weak areas (simulated)
            courses = db.session.execute(text("SELECT shifu_bid, title FROM shifu_published_shifus WHERE deleted=0 ORDER BY RAND() LIMIT 3")).fetchall()
            return make_common_response({
                "weak_areas": weak_areas,
                "recommended_courses": [dict(r._mapping) for r in courses],
                "reason": "根据带教期间的追问分析和岗位需求推荐"
            })
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)
    # ── POST /api/shifu/coach/learner-rating ──
    @app.route(path_prefix + "/coach/learner-rating", methods=["POST"])
    def coach_learner_rating():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            data = request.get_json() or {}
            db.session.execute(text("UPDATE learner_coaching SET peer_review_score = :score, updated_at = :now WHERE learner_bid = :learner AND phase_bid = :phase")
                .bindparams(score=data.get("score"), now=dt.utcnow(), learner=data.get("learner_bid",""), phase=data.get("phase_bid","")))
            db.session.commit()
            return make_common_response({"ok": True})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── POST /api/shifu/coach/final-rating ──
    @app.route(path_prefix + "/coach/final-rating", methods=["POST"])
    def coach_final_rating():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            data = request.get_json() or {}
            learner = data.get("learner_bid")
            weighted = (data.get("theory_score",0) * 0.4 + data.get("practice_score",0) * 0.3 + 
                       data.get("peer_score",0) * 0.2 + data.get("coach_score",0) * 0.1)
            db.session.execute(text("UPDATE learner_coaching SET theory_score=:ts, practice_score=:ps, peer_review_score=:pr, coach_score=:cs, total_score=:total, status='completed', completed_at=:now WHERE learner_bid=:l AND phase_bid=:ph AND status='in_progress'")
                .bindparams(ts=data.get("theory_score",0), ps=data.get("practice_score",0), pr=data.get("peer_score",0), cs=data.get("coach_score",0), 
                total=round(weighted,1), now=dt.utcnow(), l=learner, ph=data.get("phase_bid","")))
            db.session.commit()
            return make_common_response({"total_score": round(weighted,1)})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── POST /api/shifu/coach/learning-records ──
    @app.route(path_prefix + "/coach/learning-records", methods=["POST"])
    def coach_learning_records():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            import uuid
            data = request.get_json() or {}
            bid = uuid.uuid4().hex[:32]
            db.session.execute(text("INSERT INTO course_enrollments (user_bid, shifu_bid, module, status, progress_pct, trainer_bid, created_at, updated_at) VALUES (:u, :s, 'elearning', 'completed', 100, :t, :c, :c)")
                .bindparams(u=data.get("learner_bid",""), s=data.get("course_bid",""), t=request.user.user_id, c=dt.utcnow()))
            db.session.commit()
            return make_common_response({"ok": True})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    # ── GET /api/shifu/coach/students ──
    @app.route(path_prefix + "/coach/students", methods=["GET"])
    def coach_students_list():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            uid = request.user.user_id
            rows = db.session.execute(text("""
                SELECT lp.learner_bid, lp.user_bid, u.nickname as name, COALESCE(u.nickname, "") as name2, lp.employee_no, lp.department,
                       lp.position_name, lp.onboarding_date, lp.status,
                       lc.status as phase_status, lc.phase_bid
                FROM learner_profiles lp LEFT JOIN user_users u ON lp.user_bid = u.user_bid
                LEFT JOIN learner_coaching lc ON lp.learner_bid = lc.learner_bid AND lc.status = 'in_progress'
                WHERE lp.mentor_bid = :uid
                ORDER BY lp.created_at DESC
            """).bindparams(uid=uid)).fetchall()
            result = []
            for r in rows:
                d = dict(r._mapping)
                task_count = db.session.execute(text("SELECT COUNT(*) FROM learner_tasks WHERE learner_bid=:l AND status='pending'").bindparams(l=d.get('learner_bid',''))).scalar()
                pending_score = db.session.execute(text("SELECT COUNT(*) FROM learner_checklist_items WHERE learner_bid=:l AND status='submitted'").bindparams(l=d.get('learner_bid',''))).scalar()
                result.append({
                    "learner_bid": d.get("learner_bid"),
                    "name": d.get("name") or d.get("nickname", ""),
                    "employee_no": d.get("employee_no"),
                    "department": d.get("department"),
                    "position_name": d.get("position_name"),
                    "onboarding_date": str(d.get("onboarding_date")) if d.get("onboarding_date") else None,
                    "current_phase_status": d.get("phase_status"),
                    "pending_task_count": task_count or 0,
                    "pending_score_count": pending_score or 0,
                })
            return make_common_response(result)
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)


    # ── GET /api/shifu/coach/pending-scores ──
    @app.route(path_prefix + "/coach/pending-scores", methods=["GET"])
    def coach_pending_scores():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            uid = request.user.user_id
            rows = db.session.execute(text("""
                SELECT lci.record_bid, lci.learner_bid, lci.item_bid, lci.comment, lci.submitted_at
                FROM learner_checklist_items lci
                JOIN learner_profiles lp ON lci.learner_bid = lp.learner_bid
                WHERE lp.mentor_bid = :uid AND lci.status = 'submitted'
                ORDER BY lci.submitted_at ASC
            """).bindparams(uid=uid)).fetchall()
            return make_common_response([dict(r._mapping) for r in rows])
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)

    # ── POST /api/shifu/coach/score ──
    @app.route(path_prefix + "/coach/score", methods=["POST"])
    def coach_score_item():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            from datetime import datetime as dt
            data = request.get_json() or {}
            record_bid = data.get("record_bid")
            if not record_bid:
                return make_common_response({"error": "missing record_bid"})
            db.session.execute(text("UPDATE learner_checklist_items SET score=:s, comment=:c, scored_by=:u, status='scored', scored_at=:now WHERE record_bid=:b")
                .bindparams(s=data.get("score",0), c=data.get("comment",""), u=request.user.user_id, now=dt.utcnow(), b=record_bid))
            db.session.commit()
            return make_common_response({"ok": True})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/coaches", methods=["GET"])
    def admin_coaches():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            rows = db.session.execute(text("""
                SELECT cp.coach_bid, cp.user_bid, cp.employee_no, cp.name, cp.department,
                       cp.specialties, cp.max_students, cp.status,
                       (SELECT COUNT(*) FROM learner_profiles lp WHERE lp.mentor_bid = cp.coach_bid AND lp.status='active') as student_count
                FROM coach_profiles cp
                ORDER BY cp.created_at DESC
            """)).fetchall()
            return make_common_response([dict(r._mapping) for r in rows])
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/learners", methods=["GET"])
    def admin_learners():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            pi = int(request.args.get("page_index", 1))
            ps = int(request.args.get("page_size", 20))
            rows = db.session.execute(text("""
                SELECT lp.learner_bid, lp.user_bid, lp.employee_no, lp.department, lp.position_name,
                       lp.mentor_bid as coach_bid, lp.onboarding_date, lp.status,
                       cp.name as coach_name, cp.employee_no as coach_employee_no,
                       lc.status as phase_status
                FROM learner_profiles lp
                LEFT JOIN coach_profiles cp ON lp.mentor_bid = cp.coach_bid
                LEFT JOIN learner_coaching lc ON lp.learner_bid = lc.learner_bid AND lc.status = 'in_progress'
                ORDER BY lp.created_at DESC
                LIMIT :limit OFFSET :offset
            """).bindparams(limit=ps, offset=(pi-1)*ps)).fetchall()
            total = db.session.execute(text("SELECT COUNT(*) FROM learner_profiles")).scalar()
            return make_common_response({
                "items": [dict(r._mapping) for r in rows],
                "total": total
            })
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/reassign-coach", methods=["POST"])
    def admin_reassign_coach():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            payload = request.get_json(silent=True) or {}
            learner_bid = payload.get("learner_bid")
            new_coach_bid = payload.get("new_coach_bid")
            if not learner_bid or not new_coach_bid:
                return make_common_response({"error": "missing learner_bid or new_coach_bid"}, code=1001)
            db.session.execute(text("UPDATE learner_profiles SET mentor_bid=:c WHERE learner_bid=:l").bindparams(c=new_coach_bid, l=learner_bid))
            db.session.commit()
            return make_common_response({"ok": True})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/sync-now", methods=["POST"])
    def admin_sync_now():
        try:
            from flaskr.dao import db
            from sqlalchemy import text
            from datetime import datetime
            
            log_id = db.session.execute(text("INSERT INTO wecom_sync_log (sync_type, status, started_at) VALUES ('manual', 'running', NOW()) RETURNING id")).scalar()
            
            # ---- SIMULATE SYNC (placeholder for WeChat Work smart table integration) ----
            sync_summary = {"coaches_added": 0, "coaches_updated": 0, "learners_added": 0, "learners_updated": 0, "errors": []}
            
            db.session.execute(text("""
                UPDATE wecom_sync_log SET status='completed', finished_at=NOW(), summary=:s WHERE id=:lid
            """).bindparams(s=json.dumps(sync_summary), lid=log_id))
            db.session.commit()
            
            return make_common_response({"ok": True, "sync_id": log_id, "summary": sync_summary})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/sync-history", methods=["GET"])
    def admin_sync_history():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            rows = db.session.execute(text("SELECT * FROM wecom_sync_log ORDER BY started_at DESC LIMIT 20")).fetchall()
            return make_common_response([dict(r._mapping) for r in rows])
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/coach-profiles", methods=["POST"])
    def admin_create_coach_profile():
        try:
            from flaskr.dao import db
            from sqlalchemy import text
            from datetime import datetime
            import uuid
            payload = request.get_json(silent=True) or {}
            coach_bid = str(uuid.uuid4()).replace("-", "")
            db.session.execute(text("""
                INSERT INTO coach_profiles (coach_bid, user_bid, employee_no, name, department, specialties, max_students, status, created_at)
                VALUES (:b, :u, :e, :n, :d, :s, :m, 'active', NOW())
            """).bindparams(
                b=coach_bid, u=payload.get("user_bid", coach_bid),
                e=payload.get("employee_no", ""), n=payload.get("name", ""),
                d=payload.get("department", ""),
                s=json.dumps(payload.get("specialties", [])),
                m=payload.get("max_students", 5)
            ))
            db.session.commit()
            return make_common_response({"coach_bid": coach_bid})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/roles", methods=["GET"])
    def admin_roles():
        try:
            from sqlalchemy import text
            from flaskr.dao import db
            rows = db.session.execute(text("SELECT role_bid, name, label FROM coach_roles WHERE is_active=1")).fetchall()
            return make_common_response([dict(r._mapping) for r in rows])
        except Exception as e:
            return make_common_response({"error": str(e)}, code=1001)

    @app.route(path_prefix + "/admin/role-assign", methods=["POST"])
    def admin_role_assign():
        try:
            from flaskr.dao import db
            from sqlalchemy import text
            payload = request.get_json(silent=True) or {}
            user_bid = payload.get("user_bid")
            role_bid = payload.get("role_bid")
            if not user_bid or not role_bid:
                return make_common_response({"error": "missing user_bid or role_bid"}, code=1001)
            db.session.execute(text("INSERT IGNORE INTO user_role_assignments (user_bid, role_bid) VALUES (:u, :r)").bindparams(u=user_bid, r=role_bid))
            db.session.commit()
            return make_common_response({"ok": True})
        except Exception as e:
            db.session.rollback()
            return make_common_response({"error": str(e)}, code=1001)

    return app
