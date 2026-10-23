from flask import Blueprint, render_template, redirect, url_for, session, abort
from app.db import get_db
from app.services.analytics import get_admin_dashboard_metrics

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user["role"] != "admin":
        return render_template("403.html", user=user), 403

    metrics = get_admin_dashboard_metrics(db)

    return render_template(
        "admin.html",
        page="admin",
        user=user,
        metrics=metrics
    )
