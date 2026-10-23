from flask import Blueprint, request, jsonify, session
from app.db import get_db
from app.services.nlp_parser import parse_and_extract_skills
from app.services.assessment_engine import grade_technical_assessment, grade_overall_assessment, TECHNICAL_QUESTION_BANK
from app.services.crypto_verification import record_verification
from app.services.gamification import award_skill_points, check_and_unlock_achievements
from app.services.swap_service import get_swap_peer_matches
from datetime import datetime
import json
import re

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/extract-skills", methods=["POST"])
def legacy_extract_skills():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    text = request.form.get("text", "") or (request.get_json(silent=True) or {}).get("text", "")
    result = parse_and_extract_skills(text)
    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")

    for s in result["skills"]:
        cat = result["categorized"].get(s, "General")
        db.execute("""
            INSERT INTO extracted_skills (user_id, skill, category, source, created_at)
            VALUES (?, ?, ?, 'text', ?)
            ON CONFLICT(user_id, skill) DO NOTHING
        """, (user_id, s, cat, now_str))

    db.commit()
    if len(result["skills"]) > 0:
        award_skill_points(db, user_id, "upload_resume", reference_id="resume_analysis")
    check_and_unlock_achievements(db, user_id)

    cur = db.execute("SELECT skill FROM extracted_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    all_skills = [r["skill"] for r in cur.fetchall()]

    return jsonify({"skills": result["skills"], "all_skills": all_skills})


@api_bp.route("/api/assessment", methods=["POST"])
def legacy_assessment():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})

    try:
        res = grade_overall_assessment(answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")
    cats = res["categories"]

    db.execute("""
        INSERT INTO assessments (
            user_id, overall, technical, problem_solving, communication,
            domain_knowledge, learning_ability, correct, total, taken_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, res["overall"], cats["Technical Skills"], cats["Problem Solving"],
        cats["Communication"], cats["Domain Knowledge"], cats["Learning Ability"],
        res["correct"], 10, now_str
    ))

    db.execute("""
        INSERT INTO assessment_history (user_id, assessment_type, score, level, correct, total, details_json, taken_at)
        VALUES (?, 'overall_competency', ?, '', ?, ?, ?, ?)
    """, (user_id, res["overall"], res["correct"], 10, json.dumps(res), now_str))

    award_skill_points(db, user_id, "complete_assessment", reference_id="overall_assessment")
    check_and_unlock_achievements(db, user_id)
    db.commit()

    return jsonify({
        "score": res["overall"],
        "categories": res["categories"],
        "correct": res["correct"],
        "total": 10,
        "message": "Assessment saved successfully."
    })


@api_bp.route("/api/technical-assessment/<skill>", methods=["GET", "POST"])
def legacy_technical_assessment(skill):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    canonical = {k.lower(): k for k in TECHNICAL_QUESTION_BANK}
    norm_skill = canonical.get(skill.strip().lower())
    if not norm_skill:
        return jsonify({"error": "No assessment is available for this technical skill yet."}), 404

    if request.method == "GET":
        questions = []
        for idx, (q_text, opts, _) in enumerate(TECHNICAL_QUESTION_BANK[norm_skill], 1):
            questions.append({"id": idx, "text": q_text, "options": opts})
        return jsonify({"skill": norm_skill, "questions": questions})

    # POST submit
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})

    try:
        graded = grade_technical_assessment(norm_skill, answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    db = get_db()
    user = db.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    student_name = user["name"] if user else "Student"
    now_str = datetime.now().isoformat(timespec="seconds")

    token = record_verification(
        db, user_id, student_name, "skill_badge", graded["skill"], graded["score"], graded["level"]
    )
    ver_hash = token["verification_hash"]

    db.execute("""
        INSERT INTO skill_assessments (user_id, skill, score, level, correct, total, verification_hash, taken_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, skill) DO UPDATE SET
            score=excluded.score, level=excluded.level, correct=excluded.correct,
            total=excluded.total, verification_hash=excluded.verification_hash, taken_at=excluded.taken_at
    """, (user_id, graded["skill"], graded["score"], graded["level"], graded["correct"], graded["total"], ver_hash, now_str))

    db.execute("""
        INSERT INTO assessment_history (user_id, assessment_type, score, level, correct, total, details_json, taken_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, graded["skill"], graded["score"], graded["level"], graded["correct"], graded["total"], json.dumps({"feedback": graded["feedback"]}), now_str))

    if graded["score"] >= 40:
        award_skill_points(db, user_id, "verify_technical_skill", reference_id=graded["skill"])
    check_and_unlock_achievements(db, user_id)
    db.commit()

    return jsonify({
        "skill": graded["skill"],
        "score": graded["score"],
        "level": graded["level"],
        "correct": graded["correct"],
        "total": graded["total"],
        "message": f"{graded['skill']} assessment completed."
    })


@api_bp.route("/api/verified-skills")
def legacy_verified_skills():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    db = get_db()
    cur = db.execute("SELECT skill, score, level, correct, total, verification_hash FROM skill_assessments WHERE user_id = ? ORDER BY skill", (user_id,))
    return jsonify({"skills": [dict(r) for r in cur.fetchall()]})


@api_bp.route("/api/reset-learning-skills", methods=["POST"])
def legacy_reset_learning_skills():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Login required"}), 401

    db = get_db()
    db.execute("DELETE FROM learning_skills WHERE user_id = ?", (user_id,))
    db.commit()
    return jsonify({"skills": []})
