from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime
import json
from app.db import get_db
from app.services.nlp_parser import parse_and_extract_skills, extract_text_from_file
from app.services.assessment_engine import (
    TECHNICAL_QUESTION_BANK, BROAD_ASSESSMENT_QUESTIONS, RATING_OPTIONS,
    grade_technical_assessment, grade_overall_assessment
)
from app.services.crypto_verification import record_verification
from app.services.gamification import award_skill_points, check_and_unlock_achievements

assessment_bp = Blueprint("assessment", __name__)

@assessment_bp.route("/assessment")
def assessment_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Latest overall assessment
    cur = db.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    latest = cur.fetchone()

    # Extracted skills grouped by category
    cur = db.execute("SELECT skill, category, source FROM extracted_skills WHERE user_id = ? ORDER BY category, skill", (user_id,))
    extracted_rows = cur.fetchall()
    extracted_skills = [r["skill"] for r in extracted_rows]

    categorized_extracted = {}
    for r in extracted_rows:
        cat = r["category"] or "General"
        if cat not in categorized_extracted:
            categorized_extracted[cat] = []
        categorized_extracted[cat].append(r["skill"])

    # Verified technical skills
    cur = db.execute("""
        SELECT skill, score, level, correct, total, verification_hash, taken_at
        FROM skill_assessments
        WHERE user_id = ?
        ORDER BY score DESC
    """, (user_id,))
    verified_skills = [dict(r) for r in cur.fetchall()]
    verified_map = {v["skill"]: v for v in verified_skills}

    # Assessment retake history (audit trail)
    cur = db.execute("""
        SELECT assessment_type, score, level, correct, total, taken_at
        FROM assessment_history
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 10
    """, (user_id,))
    history = [dict(r) for r in cur.fetchall()]

    available_technical_skills = list(TECHNICAL_QUESTION_BANK.keys())

    return render_template(
        "assessment.html",
        page="assessment",
        user=user,
        latest=latest,
        extracted_skills=extracted_skills,
        categorized_extracted=categorized_extracted,
        verified_skills=verified_skills,
        verified_map=verified_map,
        history=history,
        technical_skills=available_technical_skills,
        broad_questions=BROAD_ASSESSMENT_QUESTIONS,
        rating_options=RATING_OPTIONS
    )


@assessment_bp.route("/api/upload-resume", methods=["POST"])
def upload_resume():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if "resume_file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["resume_file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ["pdf", "docx", "txt"]:
        return jsonify({"error": "Unsupported file format. Please upload PDF, DOCX, or TXT."}), 400

    try:
        text = extract_text_from_file(file)
        if not text.strip():
            return jsonify({"error": "Could not extract readable text from document. Ensure it is not an image-only scan."}), 400

        result = parse_and_extract_skills(text)
        db = get_db()
        now_str = datetime.now().isoformat(timespec="seconds")

        for skill in result["skills"]:
            cat = result["categorized"].get(skill, "General")
            db.execute("""
                INSERT INTO extracted_skills (user_id, skill, category, source, created_at)
                VALUES (?, ?, ?, 'file_upload', ?)
                ON CONFLICT(user_id, skill) DO UPDATE SET category=excluded.category, source='file_upload'
            """, (user_id, skill, cat, now_str))

        db.commit()
        if result["count"] > 0:
            award_skill_points(db, user_id, "upload_resume", reference_id="resume_analysis")
        check_and_unlock_achievements(db, user_id)

        return jsonify({
            "success": True,
            "skills": result["skills"],
            "categorized": result["categorized"],
            "count": result["count"],
            "message": f"Successfully extracted {result['count']} skills from {file.filename}!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@assessment_bp.route("/api/extract-text-skills", methods=["POST"])
def extract_text_skills():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    text = request.form.get("text", "") or (request.get_json(silent=True) or {}).get("text", "")
    if not text.strip():
        return jsonify({"error": "Please paste or enter your resume or skills text."}), 400

    result = parse_and_extract_skills(text)
    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")

    for skill in result["skills"]:
        cat = result["categorized"].get(skill, "General")
        db.execute("""
            INSERT INTO extracted_skills (user_id, skill, category, source, created_at)
            VALUES (?, ?, ?, 'text', ?)
            ON CONFLICT(user_id, skill) DO UPDATE SET category=excluded.category, source='text'
        """, (user_id, skill, cat, now_str))

    db.commit()
    if result["count"] > 0:
        award_skill_points(db, user_id, "upload_resume", reference_id="resume_analysis")
    check_and_unlock_achievements(db, user_id)

    return jsonify({
        "success": True,
        "skills": result["skills"],
        "categorized": result["categorized"],
        "count": result["count"],
        "message": f"Identified {result['count']} skills using transparent rule-based NLP."
    })


@assessment_bp.route("/api/technical-questions/<skill>")
def get_technical_questions(skill):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    canonical = {k.lower(): k for k in TECHNICAL_QUESTION_BANK}
    norm = canonical.get(skill.strip().lower())
    if not norm:
        return jsonify({"error": f"No assessment questions available for {skill}."}), 404

    questions = []
    for idx, (q_text, options, _) in enumerate(TECHNICAL_QUESTION_BANK[norm], 1):
        questions.append({
            "id": idx,
            "text": q_text,
            "options": options
        })

    return jsonify({
        "skill": norm,
        "questions": questions,
        "total": len(questions)
    })


@assessment_bp.route("/api/submit-technical/<skill>", methods=["POST"])
def submit_technical_test(skill):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})

    try:
        graded = grade_technical_assessment(skill, answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    db = get_db()
    user = db.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    student_name = user["name"] if user else "Student"
    now_str = datetime.now().isoformat(timespec="seconds")

    # Record tamper-evident blockchain-prototype verification record
    token = record_verification(
        db, user_id, student_name, "skill_badge", graded["skill"], graded["score"], graded["level"]
    )
    ver_hash = token["verification_hash"]

    # Save to skill_assessments
    db.execute("""
        INSERT INTO skill_assessments (user_id, skill, score, level, correct, total, verification_hash, taken_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, skill) DO UPDATE SET
            score=excluded.score, level=excluded.level, correct=excluded.correct,
            total=excluded.total, verification_hash=excluded.verification_hash, taken_at=excluded.taken_at
    """, (user_id, graded["skill"], graded["score"], graded["level"], graded["correct"], graded["total"], ver_hash, now_str))

    # Save to assessment_history (retake audit trail)
    db.execute("""
        INSERT INTO assessment_history (user_id, assessment_type, score, level, correct, total, details_json, taken_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, graded["skill"], graded["score"], graded["level"], graded["correct"], graded["total"], json.dumps({"feedback": graded["feedback"]}), now_str))

    # Award points & check achievements idempotently
    if graded["score"] >= 40:
        award_skill_points(db, user_id, "verify_technical_skill", reference_id=graded["skill"])
    check_and_unlock_achievements(db, user_id)
    db.commit()

    return jsonify({
        "success": True,
        "skill": graded["skill"],
        "score": graded["score"],
        "level": graded["level"],
        "correct": graded["correct"],
        "total": graded["total"],
        "verification_id": token["verification_id"],
        "verification_hash": ver_hash,
        "feedback": graded["feedback"],
        "message": f"Verified {graded['skill']} at {graded['level']} level ({graded['score']}%). Verification badge minted!"
    })


@assessment_bp.route("/api/submit-overall", methods=["POST"])
def submit_overall_test():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})

    try:
        result = grade_overall_assessment(answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")
    cats = result["categories"]

    # Insert into assessments
    db.execute("""
        INSERT INTO assessments (
            user_id, overall, technical, problem_solving, communication,
            domain_knowledge, learning_ability, correct, total, taken_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, result["overall"], cats["Technical Skills"], cats["Problem Solving"],
        cats["Communication"], cats["Domain Knowledge"], cats["Learning Ability"],
        result["correct"], result["total"], now_str
    ))

    # Log in assessment_history
    db.execute("""
        INSERT INTO assessment_history (user_id, assessment_type, score, level, correct, total, details_json, taken_at)
        VALUES (?, 'overall_competency', ?, '', ?, ?, ?, ?)
    """, (user_id, result["overall"], result["correct"], result["total"], json.dumps(result), now_str))

    award_skill_points(db, user_id, "complete_assessment", reference_id="overall_assessment")
    check_and_unlock_achievements(db, user_id)
    db.commit()

    return jsonify({
        "success": True,
        "overall": result["overall"],
        "categories": result["categories"],
        "strengths": result["strengths"],
        "weaknesses": result["weaknesses"],
        "recommendations": result["recommendations"],
        "message": "Comprehensive 5-domain skill assessment saved successfully!"
    })


@assessment_bp.route("/api/reset-skills", methods=["POST"])
def reset_skills():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    db.execute("DELETE FROM extracted_skills WHERE user_id = ?", (user_id,))
    db.commit()
    return jsonify({"success": True, "message": "Saved resume skills cleared."})
