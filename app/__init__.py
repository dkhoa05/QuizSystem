from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask import redirect


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # BLUEPRINTS
    from app.auth import auth_bp
    from app.quiz import quiz_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)

    # ROOT: redirect về quiz
    @app.route("/")
    def index_redirect():
        return redirect("/quiz/")

    return app
