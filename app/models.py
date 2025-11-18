from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db, login


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="student")  # student / admin

    submissions = db.relationship("Submission", backref="user", lazy="dynamic")
    certificates = db.relationship("Certificate", backref="user", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username}>"


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time_limit = db.Column(db.Integer)  # phút, None = không giới hạn
    mode = db.Column(db.String(20), default="exam")  # exam / practice
    is_active = db.Column(db.Boolean, default=True)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # extra
    num_questions = db.Column(db.Integer)        # số câu random từ bank
    pass_score = db.Column(db.Float, default=5)  # thang 10
    enable_certificate = db.Column(db.Boolean, default=False)
    show_explanation = db.Column(db.Boolean, default=True)

    questions = db.relationship("Question", backref="quiz", lazy="dynamic")
    submissions = db.relationship("Submission", backref="quiz", lazy="dynamic")

    def __repr__(self):
        return f"<Quiz {self.title}>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)

    type = db.Column(db.String(20), default="mcq")  # mcq / true_false / fill_in / essay
    content = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)  # giải thích đáp án

    difficulty = db.Column(db.String(20))  # easy / medium / hard
    time_limit = db.Column(db.Integer)  # giây, optional

    choices = db.relationship("Choice", backref="question", lazy="dynamic")
    answers = db.relationship("Answer", backref="question", lazy="dynamic")

    def __repr__(self):
        return f"<Question {self.id}>"


class Choice(db.Model):
    __tablename__ = "choices"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Choice {self.id}>"


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)

    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)  # thang 10
    time_spent = db.Column(db.Integer, default=0)  # giây

    answers = db.relationship("Answer", backref="submission", lazy="dynamic")

    def __repr__(self):
        return f"<Submission user={self.user_id} quiz={self.quiz_id}>"


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)

    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)
    checked = db.Column(db.Boolean, default=False)  # essay chấm tay / celery

    def __repr__(self):
        return f"<Answer sub={self.submission_id} q={self.question_id}>"


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)

    file_path = db.Column(db.String(255), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz = db.relationship("Quiz", backref=db.backref("certificates", lazy="dynamic"))

    def __repr__(self):
        return f"<Certificate user={self.user_id} quiz={self.quiz_id}>"
