from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from app.db import get_db
from app.config import CAREER_CATALOG
from app.services.recommendation import perform_skill_gap_analysis, calculate_career_matches
from app.services.roadmap_generator import sync_user_roadmap, get_user_roadmap, get_resources_for_skills
from app.services.gamification import award_skill_points, check_and_unlock_achievements

roadmap_bp = Blueprint("roadmap", __name__)

@roadmap_bp.route("/roadmap")
def roadmap_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Determine target career
    cur = db.execute("SELECT preferred_career FROM career_preferences WHERE user_id = ?", (user_id,))
    pref_row = cur.fetchone()
    preferred_career = pref_row["preferred_career"] if pref_row else None

    # Extracted and verified skills
    cur = db.execute("SELECT skill FROM extracted_skills WHERE user_id = ?", (user_id,))
    extracted = [r["skill"] for r in cur.fetchall()]

    cur = db.execute("SELECT skill, level, score FROM skill_assessments WHERE user_id = ?", (user_id,))
    verified_map = {r["skill"]: dict(r) for r in cur.fetchall()}

    cur = db.execute("SELECT * FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    assessment_row = cur.fetchone()
    assessment = dict(assessment_row) if assessment_row else {}

    # Determine if target career can reasonably be identified
    param_career = request.args.get("career")
    if param_career and param_career in CAREER_CATALOG:
        target_career = param_career
    elif preferred_career:
        target_career = preferred_career
    else:
        # Check if recommendations can discover a target career
        recs = calculate_career_matches(extracted, verified_map, assessment)
        target_career = recs[0]["name"] if recs else None

    # Gated: If no career can reasonably be identified yet, show the required empty state
    if not target_career:
        return render_template(
            "roadmap.html",
            page="roadmap",
            user=user,
            target_career=None,
            all_careers=list(CAREER_CATALOG.keys()),
            roadmap={"steps": [], "completed_count": 0, "total_steps": 0, "completion_pct": 0},
            gap_data=None,
            resources=[]
        )

    # Perform gap analysis to obtain missing skills
    gap_data = perform_skill_gap_analysis(target_career, extracted, verified_map)
    missing_skill_names = [m["skill"] for m in gap_data["missing"]] + [n["skill"] for n in gap_data["needs_improvement"]]

    # Synchronize roadmap steps in database
    sync_user_roadmap(db, user_id, target_career, missing_skill_names)

    # Fetch user roadmap with progress
    roadmap_data = get_user_roadmap(db, user_id, target_career)

    # Curate learning resources for missing skills
    resources = get_resources_for_skills(missing_skill_names[:6] if missing_skill_names else CAREER_CATALOG[target_career]["core_skills"][:4])

    return render_template(
        "roadmap.html",
        page="roadmap",
        user=user,
        target_career=target_career,
        all_careers=list(CAREER_CATALOG.keys()),
        roadmap=roadmap_data,
        gap_data=gap_data,
        resources=resources
    )


@roadmap_bp.route("/api/update-roadmap-step", methods=["POST"])
def update_roadmap_step():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    career_name = data.get("career_name")
    step_id = data.get("step_id")
    new_status = data.get("status")

    if new_status not in ["Not Started", "In Progress", "Completed"]:
        return jsonify({"error": "Invalid status."}), 400

    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")

    cur = db.execute("""
        UPDATE roadmap_progress
        SET status = ?, updated_at = ?
        WHERE user_id = ? AND career_name = ? AND step_id = ?
    """, (new_status, now_str, user_id, career_name, step_id))

    if cur.rowcount == 0:
        # Auto-sync roadmap steps if not yet generated for this user
        sync_user_roadmap(db, user_id, career_name, [])
        cur = db.execute("""
            UPDATE roadmap_progress
            SET status = ?, updated_at = ?
            WHERE user_id = ? AND career_name = ? AND step_id = ?
        """, (new_status, now_str, user_id, career_name, step_id))

    # Award points idempotently if milestone completed
    if new_status == "Completed":
        award_skill_points(db, user_id, "complete_roadmap_step", reference_id=f"{career_name}_{step_id}")
        check_and_unlock_achievements(db, user_id)

    db.commit()

    # Get updated overall progress
    roadmap_data = get_user_roadmap(db, user_id, career_name)

    return jsonify({
        "success": True,
        "step_id": step_id,
        "status": new_status,
        "completion_pct": roadmap_data["completion_pct"],
        "completed_count": roadmap_data["completed_count"],
        "message": f"Milestone updated to '{new_status}'!"
    })
