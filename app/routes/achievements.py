from flask import Blueprint, render_template, redirect, url_for, session
from app.db import get_db
from app.services.gamification import get_user_achievements_summary, check_and_unlock_achievements

achievements_bp = Blueprint("achievements", __name__)

@achievements_bp.route("/achievements")
def achievements_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    # Check for any newly eligible achievements
    check_and_unlock_achievements(db, user_id)

    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    summary = get_user_achievements_summary(db, user_id)

    # Calculate student tier based on skill points
    points = user["skill_points"] or 0
    if points >= 300:
        tier_title = "Vanguard Master"
        tier_level = 5
        tier_next = 500
    elif points >= 180:
        tier_title = "Senior Scholar"
        tier_level = 4
        tier_next = 300
    elif points >= 90:
        tier_title = "Competent Explorer"
        tier_level = 3
        tier_next = 180
    elif points >= 30:
        tier_title = "Active Apprentice"
        tier_level = 2
        tier_next = 90
    else:
        tier_title = "Initiate"
        tier_level = 1
        tier_next = 30

    progress_to_next = round((points / max(tier_next, 1)) * 100)

    # Campus / Peer Leaderboard (privacy-conscious: shows name, course, verified count, and points)
    cur = db.execute("""
        SELECT u.id, u.name, u.course, u.year, u.skill_points,
               COUNT(DISTINCT s.id) as verified_count,
               COUNT(DISTINCT ua.id) as badge_count
        FROM users u
        LEFT JOIN skill_assessments s ON u.id = s.user_id
        LEFT JOIN user_achievements ua ON u.id = ua.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY u.skill_points DESC, verified_count DESC
        LIMIT 10
    """)
    leaderboard = [dict(r) for r in cur.fetchall()]

    return render_template(
        "achievements.html",
        page="achievements",
        user=user,
        summary=summary,
        tier_title=tier_title,
        tier_level=tier_level,
        tier_next=tier_next,
        progress_to_next=min(100, progress_to_next),
        leaderboard=leaderboard
    )
