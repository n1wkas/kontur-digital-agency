from pathlib import Path

from flask import Flask, render_template

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.models import AdminUser

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(AdminUser, int(user_id))
        except (TypeError, ValueError):
            return None

    from app.routes.public import bp as public_bp

    app.register_blueprint(public_bp)

    from app.routes.admin import bp as admin_bp

    app.register_blueprint(admin_bp)

    from app.cli import register_cli

    register_cli(app)

    @app.template_filter("dt")
    def format_datetime(value):
        if not value:
            return "—"
        return value.strftime("%d.%m.%Y %H:%M")

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    return app
