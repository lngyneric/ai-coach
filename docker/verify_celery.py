"""Verify celery tasks."""
from app import create_app
app = create_app()
with app.app_context():
    from flaskr.service.learning_portal.tasks import daily_task_push, score_reminder, phase_deadline_reminder, probation_check
    for name, fn in [("daily_task_push",daily_task_push),("score_reminder",score_reminder),("phase_deadline_reminder",phase_deadline_reminder),("probation_check",probation_check)]:
        try:
            r = fn()
            print(f"OK {name}: {r}")
        except Exception as e:
            print(f"FAIL {name}: {e}")
