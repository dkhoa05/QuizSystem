import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = "dev-quiz-secret-key"  # đổi khi lên production
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "quiz.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery (demo, không bắt buộc phải chạy Redis)
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    # Folder lưu chứng chỉ
    CERT_FOLDER = "certificates"
