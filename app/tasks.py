from app import celery_app, db
from app.models import Submission


def _grade_essay_internal(submission_id: int):
    submission = Submission.query.get(submission_id)
    if not submission:
        return "Submission not found"

    # demo: đánh dấu essay thành đã chấm, score = 0
    for ans in submission.answers:
        if ans.question.type == "essay" and not ans.checked:
            ans.score = 0.0
            ans.checked = True

    db.session.commit()
    return f"Graded essay submission {submission_id}"


# Nếu Celery chạy → dùng Celery task
if celery_app and hasattr(celery_app, "task"):
    @celery_app.task
    def grade_essay_submission(submission_id):
        return _grade_essay_internal(submission_id)

# Nếu Celery không chạy → fallback chạy sync
else:
    def grade_essay_submission(submission_id):
        print("[Celery OFF] Grade essay sync:", submission_id)
        return _grade_essay_internal(submission_id)
