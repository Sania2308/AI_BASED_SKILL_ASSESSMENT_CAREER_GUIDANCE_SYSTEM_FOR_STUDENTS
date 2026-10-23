from flask import Blueprint, render_template, redirect, url_for, session, jsonify
from app.db import get_db
from app.services.recommendation import calculate_career_matches
from app.services.gamification import check_and_unlock_achievements

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    # Check for any new unlocked achievements
    check_and_unlock_achievements(db, user_id)
    # Re-fetch user in case points updated
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Latest overall assessment
    cur = db.execute("""
        SELECT * FROM assessments
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    assessment_row = cur.fetchone()
    if assessment_row:
        assessment = dict(assessment_row)
    else:
        assessment = {
            "overall": 0, "technical": 0, "problem_solving": 0,
            "communication": 0, "domain_knowledge": 0, "learning_ability": 0,
            "correct": 0, "total": 10
        }

    # Extracted skills
    cur = db.execute("SELECT skill, category FROM extracted_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    extracted_rows = cur.fetchall()
    extracted_skills = [r["skill"] for r in extracted_rows]

    # Verified technical skills
    cur = db.execute("SELECT skill, level, score, verification_hash FROM skill_assessments WHERE user_id = ? ORDER BY skill", (user_id,))
    verified_rows = cur.fetchall()
    verified_skills = [dict(r) for r in verified_rows]
    verified_map = {r["skill"]: dict(r) for r in verified_rows}

    # Preferred career
    cur = db.execute("SELECT preferred_career FROM career_preferences WHERE user_id = ?", (user_id,))
    pref_row = cur.fetchone()
    preferred_career = pref_row["preferred_career"] if pref_row else None

    # Evidence check
    has_assessment = bool(assessment_row and assessment.get("overall", 0) > 0)
    has_evidence = bool(extracted_skills or has_assessment or verified_skills)

    # Calculate career recommendations (empty if no evidence)
    career_matches = calculate_career_matches(extracted_skills, verified_map, assessment, preferred_career) if has_evidence else []
    top_career = career_matches[0] if career_matches else None

    # Count of assessments completed
    cur = db.execute("SELECT COUNT(*) FROM assessment_history WHERE user_id = ?", (user_id,))
    total_assessments_taken = cur.fetchone()[0]
    if total_assessments_taken == 0:
        total_assessments_taken = (1 if has_assessment else 0) + len(verified_skills)

    # Learning roadmap progress (only evaluate if target role is identified)
    target_role = preferred_career or (top_career["name"] if top_career else None)
    if target_role:
        cur = db.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as done
            FROM roadmap_progress
            WHERE user_id = ? AND career_name = ?
        """, (user_id, target_role))
        prog_row = cur.fetchone()
        total_steps = prog_row["total"] or 0
        done_steps = prog_row["done"] or 0
        learning_progress_pct = round((done_steps / total_steps) * 100) if total_steps > 0 else 0
    else:
        learning_progress_pct = 0

    # Skills to improve (only populated once career recommendations exist)
    skills_to_improve = []
    if top_career:
        skills_to_improve = [s.split(' ')[0] for s in top_career.get("needs_improvement", [])] + top_career.get("missing_skills", [])[:3]

    # AI Career Insight Generation with Progressive State Intelligence
    if not has_evidence:
        ai_insight = "Your career insight will appear after you complete your skill assessment and resume analysis."
    elif verified_skills:
        verified_top = [v["skill"] for v in sorted(verified_skills, key=lambda x: x["score"], reverse=True)[:3]]
        ai_insight = (
            f"Verified Career Readiness: Your strongest verified areas are {', '.join(verified_top)}. "
            f"Based on your proctored technical evaluations and competency scores, {top_career['name']} stands as your "
            f"strongest career match with {top_career['match']}% verified readiness."
        )
    elif has_assessment and extracted_skills:
        ai_insight = (
            f"Career Match: Based on your 5-domain competency assessment and {len(extracted_skills)} resume skills, "
            f"{top_career['name']} currently stands as your strongest match ({top_career['match']}% compatibility). "
            f"Complete technical skill verifications to earn verified role readiness."
        )
    elif has_assessment:
        ai_insight = (
            f"Career Match: Based on your 5-domain competency profile, {top_career['name']} stands as your strongest match "
            f"({top_career['match']}% compatibility). Upload your resume to refine recommendations."
        )
    else:
        # Resume analyzed only (State 2)
        ai_insight = (
            f"Preliminary Career Match: Based solely on {len(extracted_skills)} detected skills from your resume, "
            f"{top_career['name']} is your leading preliminary track ({top_career['match']}% match). "
            f"Complete the comprehensive assessment to verify your readiness."
        )

    return render_template(
        "dashboard.html",
        page="dashboard",
        user=user,
        assessment=assessment,
        extracted_skills=extracted_skills,
        verified_skills=verified_skills,
        top_career=top_career,
        career_matches=career_matches[:4],
        skills_to_improve=skills_to_improve[:4],
        assessments_completed=total_assessments_taken,
        learning_progress_pct=learning_progress_pct,
        ai_insight=ai_insight,
        has_assessment=has_assessment,
        has_evidence=has_evidence
    )


@dashboard_bp.route("/api/dashboard-charts")
def dashboard_charts():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    # Latest assessment
    cur = db.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cur.fetchone()
    has_assessment = bool(row and (row["overall"] > 0 or row["technical"] > 0))

    if has_assessment:
        tech = row["technical"]
        ps = row["problem_solving"]
        comm = row["communication"]
        dom = row["domain_knowledge"]
        learn = row["learning_ability"] if "learning_ability" in row.keys() else 50
        overall = row["overall"]
    else:
        tech = 0
        ps = 0
        comm = 0
        dom = 0
        learn = 0
        overall = 0

    # Assessment history over time
    cur = db.execute("""
        SELECT score, taken_at, assessment_type
        FROM assessment_history
        WHERE user_id = ?
        ORDER BY id ASC LIMIT 10
    """, (user_id,))
    history_rows = cur.fetchall()
    
    if history_rows:
        line_labels = [r["taken_at"].split("T")[0] for r in history_rows]
        line_data = [r["score"] for r in history_rows]
    elif has_assessment:
        line_labels = ["Attempt 1"]
        line_data = [overall]
    else:
        line_labels = ["No Data"]
        line_data = [0]

    return jsonify({
        "has_data": has_assessment,
        "radar": {
            "labels": ["Technical Skills", "Problem Solving", "Communication", "Domain Knowledge", "Learning Ability"],
            "data": [tech, ps, comm, dom, learn]
        },
        "bar": {
            "labels": ["Technical", "Problem Solving", "Communication", "Domain", "Learning"],
            "student": [tech, ps, comm, dom, learn],
            "benchmark": [70, 75, 70, 65, 70] if has_assessment else [0, 0, 0, 0, 0]
        },
        "doughnut": {
            "readiness": overall if has_assessment else 0,
            "gap": (100 - overall) if has_assessment else 100
        },
        "line": {
            "labels": line_labels,
            "data": line_data
        }
    })
