from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.db import get_db
from app.services.recommendation import calculate_career_matches, perform_skill_gap_analysis
from app.services.gamification import award_skill_points, check_and_unlock_achievements
from app.config import CAREER_CATALOG
from datetime import datetime

career_bp = Blueprint("career", __name__)

@career_bp.route("/career")
def career_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Get latest assessment
    cur = db.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    assessment_row = cur.fetchone()
    assessment = dict(assessment_row) if assessment_row else {
        "overall": 0, "technical": 0, "problem_solving": 0,
        "communication": 0, "domain_knowledge": 0, "learning_ability": 0
    }

    # Get extracted skills
    cur = db.execute("SELECT skill FROM extracted_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    extracted_skills = [r["skill"] for r in cur.fetchall()]

    # Get verified skills
    cur = db.execute("SELECT skill, level, score FROM skill_assessments WHERE user_id = ?", (user_id,))
    verified_map = {r["skill"]: dict(r) for r in cur.fetchall()}

    # Get preferred career
    cur = db.execute("SELECT preferred_career FROM career_preferences WHERE user_id = ?", (user_id,))
    pref_row = cur.fetchone()
    preferred_career = pref_row["preferred_career"] if pref_row else None

    # Evidence check
    has_assessment = bool(assessment_row and assessment.get("overall", 0) > 0)
    has_evidence = bool(extracted_skills or has_assessment or verified_map)

    # Calculate 13 career tracks (gated if insufficient student evidence)
    career_recommendations = calculate_career_matches(extracted_skills, verified_map, assessment, preferred_career) if has_evidence else []
    top_career = career_recommendations[0] if career_recommendations else None

    # Active selected career for gap analysis
    selected_career = request.args.get("selected") or preferred_career or (top_career["name"] if top_career else "Data Analyst")
    gap_analysis = perform_skill_gap_analysis(selected_career, extracted_skills, verified_map)

    return render_template(
        "career.html",
        page="career",
        user=user,
        careers=career_recommendations,
        top_career=top_career,
        selected_career=selected_career,
        gap_analysis=gap_analysis,
        preferred_career=preferred_career,
        all_catalog_careers=list(CAREER_CATALOG.keys()),
        has_evidence=has_evidence
    )


@career_bp.route("/api/set-career-goal", methods=["POST"])
def set_career_goal():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    career_name = data.get("career_name", "").strip()

    if career_name not in CAREER_CATALOG:
        return jsonify({"error": "Invalid career choice."}), 400

    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")
    db.execute("""
        INSERT INTO career_preferences (user_id, preferred_career, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET preferred_career=excluded.preferred_career, updated_at=excluded.updated_at
    """, (user_id, career_name, now_str))

    # Setting a career goal unlocks career_explorer achievement without generating unearned roadmap points
    check_and_unlock_achievements(db, user_id)
    db.commit()

    return jsonify({
        "success": True,
        "career_name": career_name,
        "message": f"Target career successfully set to {career_name}!"
    })
