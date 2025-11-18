from functools import wraps
import random
from datetime import datetime

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    abort,
    send_from_directory,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.quiz import quiz_bp
from app.models import Quiz, Question, Choice, Submission, Answer, User, Certificate
from app.certificates import generate_certificate
from app.tasks import grade_essay_submission


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


# =============================
#           STUDENT
# =============================
@quiz_bp.route("/")
@login_required
def home():
    quizzes = Quiz.query.filter_by(is_active=True).all()
    return render_template("quiz/home.html", quizzes=quizzes)


@quiz_bp.route("/list")
@login_required
def quiz_list():
    quizzes = Quiz.query.filter_by(is_active=True).all()
    return render_template("quiz/list.html", quizzes=quizzes)


@quiz_bp.route("/start/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    # exam mode: không cho làm lại
    if quiz.mode == "exam":
        existing = Submission.query.filter_by(
            user_id=current_user.id, quiz_id=quiz.id
        ).first()
        if existing and request.method == "GET":
            return redirect(url_for("quiz.view_result", submission_id=existing.id))

    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    random.shuffle(questions)

    if quiz.num_questions and len(questions) > quiz.num_questions:
        questions = questions[: quiz.num_questions]

    if request.method == "POST":
        submission = Submission(user_id=current_user.id, quiz_id=quiz.id)
        db.session.add(submission)
        db.session.flush()

        total = len(questions)
        correct = 0

        try:
            submission.time_spent = int(request.form.get("time_spent", "0"))
        except ValueError:
            submission.time_spent = 0

        for q in questions:
            field_name = f"q_{q.id}"
            user_answer = request.form.get(field_name)

            ans = Answer(
                submission_id=submission.id,
                question_id=q.id,
                user_answer=user_answer or "",
            )

            is_correct = False
            if q.type in ("mcq", "true_false"):
                if user_answer:
                    choice = Choice.query.get(int(user_answer))
                    if choice and choice.is_correct:
                        is_correct = True

            ans.is_correct = is_correct
            ans.score = 1.0 if is_correct else 0.0
            ans.checked = q.type != "essay"

            if is_correct:
                correct += 1

            db.session.add(ans)

        submission.total_questions = total
        submission.correct_answers = correct
        submission.score = (correct / total) * 10 if total > 0 else 0
        submission.finished_at = datetime.utcnow()

        has_essay = any(q.type == "essay" for q in questions)
        db.session.commit()

        if has_essay:
            grade_essay_submission(submission.id)

        return redirect(url_for("quiz.view_result", submission_id=submission.id))

    countdown_seconds = quiz.time_limit * 60 if quiz.time_limit else None

    return render_template(
        "quiz/do_quiz.html",
        quiz=quiz,
        questions=questions,
        countdown_seconds=countdown_seconds,
    )


@quiz_bp.route("/result/<int:submission_id>")
@login_required
def view_result(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    quiz = submission.quiz

    # cá nhân: lịch sử điểm để vẽ chart
    user_scores = (
        Submission.query
        .filter_by(user_id=submission.user_id, quiz_id=submission.quiz_id)
        .order_by(Submission.created_at.asc())
        .all()
    )
    labels = [s.created_at.strftime("%d/%m %H:%M") for s in user_scores]
    scores = [s.score for s in user_scores]

    cert = None
    if quiz.enable_certificate and submission.score >= quiz.pass_score:
        cert = Certificate.query.filter_by(
            user_id=submission.user_id,
            quiz_id=submission.quiz_id
        ).first()
        if not cert:
            cert = generate_certificate(submission)

    return render_template(
        "quiz/result.html",
        submission=submission,
        quiz=quiz,
        certificate=cert,
        score_labels=labels,
        score_values=scores,
    )


@quiz_bp.route("/review/<int:submission_id>")
@login_required
def review_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    quiz = submission.quiz
    if not quiz.show_explanation:
        abort(403)

    answers_by_q = {a.question_id: a for a in submission.answers}
    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    return render_template(
        "quiz/review.html",
        submission=submission,
        quiz=quiz,
        questions=questions,
        answers_by_q=answers_by_q,
    )


@quiz_bp.route("/history")
@login_required
def history():
    submissions = (
        Submission.query.filter_by(user_id=current_user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )
    return render_template("quiz/history.html", submissions=submissions)


@quiz_bp.route("/leaderboard/<int:quiz_id>")
@login_required
def leaderboard(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    rows = (
        db.session.query(
            User.username,
            func.max(Submission.score).label("best_score"),
        )
        .join(User, User.id == Submission.user_id)
        .filter(Submission.quiz_id == quiz.id)
        .group_by(User.id)
        .order_by(func.max(Submission.score).desc())
        .limit(10)
        .all()
    )

    return render_template(
        "quiz/leaderboard.html",
        quiz=quiz,
        leaderboard=rows,
    )


@quiz_bp.route("/certificate/<int:quiz_id>")
@login_required
def download_certificate(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    cert = Certificate.query.filter_by(
        user_id=current_user.id, quiz_id=quiz.id
    ).first_or_404()

    folder = current_app.config.get("CERT_FOLDER", "certificates")
    import os
    return send_from_directory(
        os.path.join(current_app.instance_path, folder),
        cert.file_path,
        as_attachment=True,
    )


# =============================
#           ADMIN
# =============================
@quiz_bp.route("/admin/quizzes")
@admin_required
def manage_quizzes():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template("quiz/manage_quizzes.html", quizzes=quizzes)


@quiz_bp.route("/admin/quizzes/new", methods=["GET", "POST"])
@admin_required
def create_quiz():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        time_limit = request.form.get("time_limit") or None
        mode = request.form.get("mode") or "exam"
        num_questions = request.form.get("num_questions") or None
        pass_score = request.form.get("pass_score") or 5
        enable_certificate = bool(request.form.get("enable_certificate"))
        show_explanation = bool(request.form.get("show_explanation"))

        quiz = Quiz(
            title=title,
            description=description,
            time_limit=int(time_limit) if time_limit else None,
            mode=mode,
            created_by=current_user.id,
            is_active=True,
            num_questions=int(num_questions) if num_questions else None,
            pass_score=float(pass_score),
            enable_certificate=enable_certificate,
            show_explanation=show_explanation,
        )
        db.session.add(quiz)
        db.session.commit()
        return redirect(url_for("quiz.manage_quizzes"))

    return render_template("quiz/create_quiz.html")


@quiz_bp.route("/admin/quizzes/<int:quiz_id>/questions", methods=["GET", "POST"])
@admin_required
def manage_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == "POST":
        content = request.form.get("content")
        qtype = request.form.get("type") or "mcq"
        explanation = request.form.get("explanation")
        difficulty = request.form.get("difficulty") or None
        q_time_limit = request.form.get("time_limit") or None

        q = Question(
            quiz_id=quiz.id,
            type=qtype,
            content=content,
            explanation=explanation,
            difficulty=difficulty,
            time_limit=int(q_time_limit) if q_time_limit else None,
        )
        db.session.add(q)
        db.session.flush()

        correct_choice = request.form.get("correct_choice")  # '1'..'4'
        for i in range(1, 5):
            text = request.form.get(f"choice_{i}")
            if not text:
                continue
            choice = Choice(
                question_id=q.id,
                content=text,
                is_correct=(str(i) == correct_choice),
            )
            db.session.add(choice)

        db.session.commit()
        return redirect(url_for("quiz.manage_questions", quiz_id=quiz.id))

    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    return render_template("quiz/manage_questions.html", quiz=quiz, questions=questions)

# =============================
#       DELETE QUESTION
# =============================
@quiz_bp.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def delete_question(question_id):
    q = Question.query.get_or_404(question_id)
    quiz_id = q.quiz_id

    # delete choices + answers
    Choice.query.filter_by(question_id=q.id).delete()
    Answer.query.filter_by(question_id=q.id).delete()

    db.session.delete(q)
    db.session.commit()

    return redirect(url_for("quiz.manage_questions", quiz_id=quiz_id))


# =============================
#       EDIT QUESTION
# =============================
@quiz_bp.route("/admin/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    q = Question.query.get_or_404(question_id)
    quiz = q.quiz
    choices = Choice.query.filter_by(question_id=q.id).all()

    if request.method == "POST":
        q.content = request.form.get("content")
        q.type = request.form.get("type")
        q.explanation = request.form.get("explanation")
        q.difficulty = request.form.get("difficulty")
        q.time_limit = request.form.get("time_limit") or None

        # UPDATE choices (cho MCQ và True/False)
        correct_choice = request.form.get("correct_choice")

        for i, choice in enumerate(choices, start=1):
            new_text = request.form.get(f"choice_{i}")
            if new_text:
                choice.content = new_text
            choice.is_correct = (str(i) == correct_choice)

        db.session.commit()

        return redirect(url_for("quiz.manage_questions", quiz_id=quiz.id))

    return render_template(
        "quiz/edit_question.html",
        quiz=quiz,
        question=q,
        choices=choices,
    )
@quiz_bp.route("/admin/history")
@admin_required
def admin_history():
    submissions = (
        db.session.query(Submission, User, Quiz)
        .join(User, Submission.user_id == User.id)
        .join(Quiz, Submission.quiz_id == Quiz.id)
        .order_by(Submission.created_at.desc())
        .all()
    )
    return render_template("quiz/admin_history.html", submissions=submissions)

