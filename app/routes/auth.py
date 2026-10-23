from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.db import get_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard_view"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Please enter both your email and password."
        else:
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_role"] = user["role"]
                return redirect(url_for("dashboard.dashboard_view"))
            error = "Invalid email or password. Please try again."

    return render_template("auth.html", mode="login", error=error)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard_view"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        course = request.form.get("course", "").strip() or "Computer Science"
        year = request.form.get("year", "").strip() or "3rd Year"
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm:
            error = "Please fill in all required fields."
        elif len(name) < 2:
            error = "Full name must be at least 2 characters long."
        elif "@" not in email or "." not in email:
            error = "Please provide a valid institutional or personal email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm:
            error = "Passwords do not match. Please re-enter."
        else:
            db = get_db()
            existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                error = "An account with this email address already exists. Please login instead."
            else:
                now_str = datetime.now().isoformat(timespec="seconds")
                cur = db.execute("""
                    INSERT INTO users (name, email, password_hash, role, bio, course, year, skill_points, created_at)
                    VALUES (?, ?, ?, 'student', '', ?, ?, 0, ?)
                """, (name, email, generate_password_hash(password), course, year, now_str))
                db.commit()
                new_user_id = cur.lastrowid

                session.clear()
                session["user_id"] = new_user_id
                session["user_name"] = name
                session["user_role"] = "student"
                return redirect(url_for("dashboard.dashboard_view"))

    return render_template("auth.html", mode="signup", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
