from functools import wraps

from flask import render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user

from app import db
from app.quiz import quiz_bp
from app.models import Quiz, Question, Choice, Submission, Answer


# ---- helper: chỉ admin mới vào được ----
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
    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    if request.method == "POST":
        submission = Submission(user_id=current_user.id, quiz_id=quiz.id)
        db.session.add(submission)
        db.session.flush()

        total = len(questions)
        correct = 0

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

        db.session.commit()
        return redirect(url_for("quiz.view_result", submission_id=submission.id))

    return render_template("quiz/do_quiz.html", quiz=quiz, questions=questions)


@quiz_bp.route("/result/<int:submission_id>")
@login_required
def view_result(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id and current_user.role != "admin":
        abort(403)
    return render_template("quiz/result.html", submission=submission)


@quiz_bp.route("/history")
@login_required
def history():
    submissions = (
        Submission.query.filter_by(user_id=current_user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )
    return render_template("quiz/history.html", submissions=submissions)


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

        quiz = Quiz(
            title=title,
            description=description,
            time_limit=int(time_limit) if time_limit else None,
            mode=mode,
            created_by=current_user.id,
            is_active=True,
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

        q = Question(
            quiz_id=quiz.id,
            type=qtype,
            content=content,
            explanation=explanation,
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
