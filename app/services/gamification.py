import sqlite3
from datetime import datetime

POINT_RULES = {
    "complete_profile": 10,
    "upload_resume": 10,
    "complete_assessment": 20,
    "verify_technical_skill": 30,
    "complete_roadmap_step": 10,
    "complete_skill_swap": 40
}

def award_skill_points(db_conn, user_id, action_key, reference_id="", reason=""):
    """
    Awards skill points to a student and updates the persistent score in `users`.
    Uses skill_point_transactions to prevent duplicate points from refreshing
    pages or repeating the same one-time action.
    Returns: (total_points, points_awarded)
    """
    pts = POINT_RULES.get(action_key, 0)
    if pts <= 0:
        return 0, 0

    cur = db_conn.cursor()
    now_str = datetime.now().isoformat(timespec="seconds")
    ref = str(reference_id or action_key)
    awarded = 0

    try:
        cur.execute("""
            INSERT INTO skill_point_transactions (user_id, action_key, reference_id, points, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, action_key, ref, pts, now_str))

        cur.execute("""
            UPDATE users
            SET skill_points = COALESCE(skill_points, 0) + ?
            WHERE id = ?
        """, (pts, user_id))
        db_conn.commit()
        awarded = pts
    except Exception:
        # Duplicate action or integrity violation; do not award points repeatedly
        pass

    cur.execute("SELECT skill_points FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    total = row["skill_points"] if row else 0
    return total, awarded


def check_and_unlock_achievements(db_conn, user_id):
    """
    Evaluates student milestones across the database and awards any newly unlocked badges.
    Returns: list of newly unlocked achievement records.
    """
    cur = db_conn.cursor()
    now_str = datetime.now().isoformat(timespec="seconds")

    # Fetch currently unlocked achievements
    cur.execute("SELECT achievement_code FROM user_achievements WHERE user_id = ?", (user_id,))
    already_unlocked = {r["achievement_code"] for r in cur.fetchall()}

    # Check student metrics
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM extracted_skills WHERE user_id = ?", (user_id,))
    extracted_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM assessments WHERE user_id = ?", (user_id,))
    overall_count = cur.fetchone()[0]

    cur.execute("SELECT skill, level, score FROM skill_assessments WHERE user_id = ?", (user_id,))
    verified_skills = cur.fetchall()
    verified_count = len(verified_skills)
    has_python_verified = any(r["skill"].lower() == "python" and r["score"] >= 40 for r in verified_skills)

    cur.execute("SELECT COUNT(*) FROM career_preferences WHERE user_id = ?", (user_id,))
    has_career_goal = cur.fetchone()[0] > 0

    cur.execute("SELECT COUNT(*) FROM roadmap_progress WHERE user_id = ? AND status = 'Completed'", (user_id,))
    completed_steps = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM skill_swap_requests WHERE (sender_id = ? OR receiver_id = ?) AND status = 'Completed'", (user_id, user_id))
    completed_swaps = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM verification_records WHERE user_id = ?", (user_id,))
    minted_certs = cur.fetchone()[0]

    to_unlock = []

    # 1. Profile Pioneer
    if "profile_complete" not in already_unlocked and user and user["bio"] and len(user["bio"].strip()) > 5:
        to_unlock.append("profile_complete")

    # 2. Resume Decoder
    if "resume_uploaded" not in already_unlocked and extracted_count > 0:
        to_unlock.append("resume_uploaded")

    # 3. Assessment Master
    if "assessment_master" not in already_unlocked and overall_count > 0:
        to_unlock.append("assessment_master")

    # 4. Python Verified
    if "python_verified" not in already_unlocked and has_python_verified:
        to_unlock.append("python_verified")

    # 5. First Verified Skill
    if "first_verified_skill" not in already_unlocked and verified_count >= 1:
        to_unlock.append("first_verified_skill")

    # 6. Polymath
    if "multi_skilled" not in already_unlocked and verified_count >= 3:
        to_unlock.append("multi_skilled")

    # 7. Career Explorer
    if "career_explorer" not in already_unlocked and has_career_goal:
        to_unlock.append("career_explorer")

    # 8. Roadmap Pioneer
    if "roadmap_pioneer" not in already_unlocked and completed_steps > 0:
        to_unlock.append("roadmap_pioneer")

    # 9. Skill Mentor
    if "skill_mentor" not in already_unlocked and completed_swaps > 0:
        to_unlock.append("skill_mentor")

    # 10. Cryptographic Trust
    if "blockchain_badged" not in already_unlocked and minted_certs > 0:
        to_unlock.append("blockchain_badged")

    unlocked_details = []
    for code in to_unlock:
        try:
            cur.execute("""
                INSERT INTO user_achievements (user_id, achievement_code, unlocked_at)
                VALUES (?, ?, ?)
            """, (user_id, code, now_str))

            # Fetch achievement details
            cur.execute("SELECT points, title FROM achievements WHERE code = ?", (code,))
            row = cur.fetchone()
            pts = row["points"] if row else 20

            unlocked_details.append({
                "code": code,
                "title": row["title"] if row else code,
                "points": pts
            })
        except Exception:
            pass

    db_conn.commit()
    return unlocked_details


def get_user_achievements_summary(db_conn, user_id):
    """
    Returns full list of all achievements (both unlocked and locked) with progress.
    """
    cur = db_conn.cursor()
    cur.execute("""
        SELECT a.code, a.title, a.description, a.icon, a.points,
               ua.unlocked_at,
               CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END as is_unlocked
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.code = ua.achievement_code AND ua.user_id = ?
        ORDER BY is_unlocked DESC, a.points ASC
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]

    unlocked_count = sum(1 for r in rows if r["is_unlocked"] == 1)
    total_count = len(rows)

    return {
        "achievements": rows,
        "unlocked_count": unlocked_count,
        "total_count": total_count,
        "completion_pct": round((unlocked_count / max(total_count, 1)) * 100)
    }
