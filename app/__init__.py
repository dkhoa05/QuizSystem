from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"

celery_app = None  # sẽ được set trong create_app


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Tạo thư mục certificate
    cert_folder = app.config.get("CERT_FOLDER", "certificates")
    cert_path = os.path.join(app.instance_path, cert_folder)
    os.makedirs(cert_path, exist_ok=True)

    # Register blueprints
    from app.auth import auth_bp
    from app.quiz import quiz_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(quiz_bp, url_prefix="/quiz")

    # Celery (optional – fallback nếu chưa cài)
    try:
        from app.celery_app import make_celery
        global celery_app
        celery_app = make_celery(app)
    except Exception:
        print("⚠ Celery chưa cài, background task sẽ chạy sync.")

    # Route /
    @app.route("/")
    def index():
        return redirect(url_for("quiz.home"))

    return app


# Import models sau khi db đã tạo
from app import models  # noqa
