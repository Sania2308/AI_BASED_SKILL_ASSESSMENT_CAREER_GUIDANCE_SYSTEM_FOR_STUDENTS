import os
from flask import Flask, session, g, redirect, url_for, render_template
from app.config import Config
from app.db import close_db, init_db, get_db

def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(Config.BASE_DIR, "templates"),
        static_folder=os.path.join(Config.BASE_DIR, "static")
    )
    app.config.from_object(Config)

    if test_config is not None:
        app.config.update(test_config)

    # Ensure uploads folder exists safely (no-op on read-only serverless filesystems)
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Initialize and migrate database safely
    with app.app_context():
        try:
            init_db(app.config.get("DATABASE"), app.config.get("DATABASE_URL"))
        except Exception as e:
            app.logger.warning("Database initialization deferred or already up to date: %s", str(e))

    # Teardown database connection
    app.teardown_appcontext(close_db)

    # Global context processor for templates
    @app.context_processor
    def inject_user_context():
        user = None
        user_id = session.get("user_id")
        if user_id:
            try:
                db = get_db()
                user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            except Exception:
                user = None
        return {"current_user": user}

    # Root route
    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard.dashboard_view"))
        return redirect(url_for("auth.login"))

    # Lightweight production health check endpoint
    @app.route("/health")
    def health():
        db_status = "connected"
        try:
            db = get_db()
            db.execute("SELECT 1")
        except Exception:
            db_status = "unavailable"
        status_code = 200 if db_status == "connected" else 503
        return {
            "status": "ok" if db_status == "connected" else "degraded",
            "database": db_status
        }, status_code

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.assessment import assessment_bp
    from app.routes.career import career_bp
    from app.routes.roadmap import roadmap_bp
    from app.routes.swap import swap_bp
    from app.routes.gis import gis_bp
    from app.routes.achievements import achievements_bp
    from app.routes.verification import verification_bp
    from app.routes.profile import profile_bp
    from app.routes.report import report_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(swap_bp)
    app.register_blueprint(gis_bp)
    app.register_blueprint(achievements_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("Internal Server Error: %s", str(e), exc_info=True)
        if app.config.get("IS_PRODUCTION"):
            user_error = "An internal error occurred. Please try again later."
        else:
            user_error = str(e)
        return render_template("500.html", error=user_error), 500

    return app
