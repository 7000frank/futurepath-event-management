import os
from datetime import date
from pathlib import Path

from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bootstrap = Bootstrap5()
login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__)
    package_dir = Path(__file__).resolve().parent
    database_path = package_dir / "database.sqlite"

    app.config.update(
        SECRET_KEY=os.environ.get("FUTUREPATH_SECRET_KEY", "futurepath-course-demo-secret"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(package_dir / "static" / "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "warning"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth import auth_bp
    from .errors import errors_bp
    from .views import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(errors_bp)

    from .forms import EmptyForm

    @app.context_processor
    def template_globals():
        return {"current_year": date.today().year, "logout_form": EmptyForm()}

    with app.app_context():
        db.create_all()
        if not app.config.get("TESTING") and not db.session.scalar(db.select(User.id).limit(1)):
            from .seed import seed_database

            seed_database()

    return app
