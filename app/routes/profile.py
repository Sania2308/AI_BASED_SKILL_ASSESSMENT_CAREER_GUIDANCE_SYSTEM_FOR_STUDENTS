from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db
from app.services.gamification import award_skill_points, check_and_unlock_achievements, get_user_achievements_summary
from app.config import CAREER_CATALOG

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET", "POST"])
def profile_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    message = None
    msg_type = "success"

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        course = request.form.get("course", "").strip()
        year = request.form.get("year", "").strip()
        bio = request.form.get("bio", "").strip()
        preferred_career = request.form.get("preferred_career", "").strip()

        if not name or not email:
            message = "Full Name and Email address are required fields."
            msg_type = "danger"
        else:
            try:
                db.execute("""
                    UPDATE users
                    SET name = ?, email = ?, course = ?, year = ?, bio = ?
                    WHERE id = ?
                """, (name, email, course, year, bio, user_id))

                if preferred_career and preferred_career in CAREER_CATALOG:
                    from datetime import datetime
                    now_str = datetime.now().isoformat(timespec="seconds")
                    db.execute("""
                        INSERT INTO career_preferences (user_id, preferred_career, updated_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET preferred_career=excluded.preferred_career, updated_at=excluded.updated_at
                    """, (user_id, preferred_career, now_str))

                if bio and len(bio.strip()) >= 5:
                    award_skill_points(db, user_id, "complete_profile", reference_id="profile")
                check_and_unlock_achievements(db, user_id)
                db.commit()

                session["user_name"] = name
                message = "Your profile details have been successfully updated!"
                msg_type = "success"
                user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            except Exception as e:
                message = f"Error saving profile: {str(e)}"
                msg_type = "danger"

    # Extracted skills
    cur = db.execute("SELECT skill, category FROM extracted_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    extracted_skills = [dict(r) for r in cur.fetchall()]

    # Verified technical skills
    cur = db.execute("SELECT skill, level, score, verification_hash FROM skill_assessments WHERE user_id = ? ORDER BY score DESC", (user_id,))
    verified_skills = [dict(r) for r in cur.fetchall()]

    # Learning skills
    cur = db.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    learning_skills = [r["skill"] for r in cur.fetchall()]

    # Target career
    cur = db.execute("SELECT preferred_career FROM career_preferences WHERE user_id = ?", (user_id,))
    pref_row = cur.fetchone()
    current_career_goal = pref_row["preferred_career"] if pref_row else "Not Set"

    # Total assessments completed
    cur = db.execute("SELECT COUNT(*) FROM assessment_history WHERE user_id = ?", (user_id,))
    assessments_completed = cur.fetchone()[0]

    # Achievements summary
    achievements_summary = get_user_achievements_summary(db, user_id)

    return render_template(
        "profile.html",
        page="profile",
        user=user,
        message=message,
        msg_type=msg_type,
        extracted_skills=extracted_skills,
        verified_skills=verified_skills,
        learning_skills=learning_skills,
        current_career_goal=current_career_goal,
        assessments_completed=assessments_completed,
        achievements_summary=achievements_summary,
        all_careers=list(CAREER_CATALOG.keys())
    )
