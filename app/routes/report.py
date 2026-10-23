from flask import Blueprint, render_template, redirect, url_for, session
from app.db import get_db
from app.services.recommendation import calculate_career_matches, perform_skill_gap_analysis
from app.services.roadmap_generator import get_user_roadmap
from app.services.gamification import get_user_achievements_summary
from datetime import datetime

report_bp = Blueprint("report", __name__)

@report_bp.route("/report")
def report_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Latest overall assessment
    cur = db.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    assessment_row = cur.fetchone()
    assessment = dict(assessment_row) if assessment_row else {
        "overall": 0, "technical": 0, "problem_solving": 0,
        "communication": 0, "domain_knowledge": 0, "learning_ability": 0,
        "correct": 0, "total": 10, "taken_at": "Not Attempted"
    }

    # Extracted skills
    cur = db.execute("SELECT skill, category FROM extracted_skills WHERE user_id = ? ORDER BY category, skill", (user_id,))
    extracted_rows = cur.fetchall()
    extracted_skills = [r["skill"] for r in extracted_rows]

    # Verified technical skills
    cur = db.execute("""
        SELECT skill, level, score, verification_hash, taken_at
        FROM skill_assessments
        WHERE user_id = ?
        ORDER BY score DESC
    """, (user_id,))
    verified_rows = cur.fetchall()
    verified_skills = [dict(r) for r in verified_rows]
    verified_map = {r["skill"]: dict(r) for r in verified_rows}

    # Target career
    cur = db.execute("SELECT preferred_career FROM career_preferences WHERE user_id = ?", (user_id,))
    pref_row = cur.fetchone()
    preferred_career = pref_row["preferred_career"] if pref_row else None

    # Evidence check
    has_assessment = bool(assessment_row and assessment.get("overall", 0) > 0)
    has_evidence = bool(extracted_skills or has_assessment or verified_skills)

    # Recommendations (empty if no evidence)
    career_matches = calculate_career_matches(extracted_skills, verified_map, assessment, preferred_career) if has_evidence else []
    top_career = career_matches[0] if career_matches else None
    target_career = preferred_career or (top_career["name"] if top_career else None)

    # Gap analysis for target role
    gap_data = perform_skill_gap_analysis(target_career, extracted_skills, verified_map) if target_career else None

    # Active roadmap
    roadmap = get_user_roadmap(db, user_id, target_career) if target_career else {"steps": [], "completed_count": 0, "total_steps": 0, "completion_pct": 0}

    # Achievements summary
    achievements = get_user_achievements_summary(db, user_id)

    generated_date = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    return render_template(
        "report.html",
        page="reports",
        user=user,
        assessment=assessment,
        extracted_skills=extracted_skills,
        verified_skills=verified_skills,
        career_matches=career_matches[:5],
        top_career=top_career,
        target_career=target_career,
        gap_data=gap_data,
        roadmap=roadmap,
        achievements=achievements,
        generated_date=generated_date
    )
