from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.db import get_db
from app.services.swap_service import (
    get_swap_peer_matches, create_swap_request, update_swap_request_status, get_user_swap_requests
)
from app.services.gamification import award_skill_points, check_and_unlock_achievements
from app.config import ALL_SKILLS
import re

swap_bp = Blueprint("swap", __name__)

@swap_bp.route("/skill-swap")
def skill_swap_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Verified skills I can teach
    cur = db.execute("""
        SELECT skill, level, score, verification_hash
        FROM skill_assessments
        WHERE user_id = ?
        ORDER BY score DESC
    """, (user_id,))
    verified_teach = [dict(r) for r in cur.fetchall()]

    # Skills I want to learn
    cur = db.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    learning_skills = [r["skill"] for r in cur.fetchall()]

    # Peer matches
    peer_matches = get_swap_peer_matches(db, user_id)

    # Active swap requests
    swap_requests = get_user_swap_requests(db, user_id)

    return render_template(
        "skill_swap.html",
        page="skill-swap",
        user=user,
        verified_teach=verified_teach,
        learning_skills=learning_skills,
        peer_matches=peer_matches,
        swap_requests=swap_requests,
        all_supported_skills=ALL_SKILLS
    )


@swap_bp.route("/api/learning-skills", methods=["POST"])
def add_learning_skills():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    raw_input = data.get("skills", "")

    if isinstance(raw_input, list):
        items = raw_input
    else:
        items = re.split(r"[,\n]+", str(raw_input))

    canonical = {s.lower(): s for s in ALL_SKILLS}
    to_add = []
    for it in items:
        clean = it.strip().lower()
        if clean in canonical and canonical[clean] not in to_add:
            to_add.append(canonical[clean])

    if not to_add:
        return jsonify({"error": "Please specify at least one recognized skill from the taxonomy."}), 400

    db = get_db()
    for s in to_add:
        db.execute("""
            INSERT INTO learning_skills (user_id, skill)
            VALUES (?, ?)
            ON CONFLICT(user_id, skill) DO NOTHING
        """, (user_id, s))
    db.commit()

    cur = db.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    current_learning = [r["skill"] for r in cur.fetchall()]
    updated_matches = get_swap_peer_matches(db, user_id)

    return jsonify({
        "success": True,
        "skills": current_learning,
        "matches": updated_matches,
        "message": f"Added {len(to_add)} learning goals."
    })


@swap_bp.route("/api/remove-learning-skill", methods=["POST"])
def remove_learning_skill():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    skill = data.get("skill", "").strip()

    db = get_db()
    db.execute("DELETE FROM learning_skills WHERE user_id = ? AND skill = ?", (user_id, skill))
    db.commit()

    cur = db.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (user_id,))
    current_learning = [r["skill"] for r in cur.fetchall()]
    return jsonify({"success": True, "skills": current_learning})


@swap_bp.route("/api/request-swap", methods=["POST"])
def request_swap():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    teach_skill = data.get("teach_skill", "").strip()
    learn_skill = data.get("learn_skill", "").strip()
    notes = data.get("notes", "").strip()

    if not receiver_id:
        return jsonify({"error": "Target peer is required."}), 400

    db = get_db()
    # Enforce rule: student can only teach VERIFIED technical skills!
    if teach_skill:
        cur = db.execute("SELECT id FROM skill_assessments WHERE user_id = ? AND skill = ?", (user_id, teach_skill))
        if not cur.fetchone():
            return jsonify({"error": f"You can only offer to teach verified technical skills. Please complete the {teach_skill} assessment first."}), 400

    try:
        req_id = create_swap_request(db, user_id, int(receiver_id), teach_skill or "Peer Guidance", learn_skill or "Mutual Learning", notes)
        return jsonify({"success": True, "request_id": req_id, "message": "Skill swap proposal sent successfully!"})
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400


@swap_bp.route("/api/update-swap-status", methods=["POST"])
def update_swap_status():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    request_id = data.get("request_id")
    new_status = data.get("status")

    db = get_db()
    try:
        update_swap_request_status(db, int(request_id), user_id, new_status)
        if new_status == "Completed":
            award_skill_points(db, user_id, "complete_skill_swap", reference_id=str(request_id))
            check_and_unlock_achievements(db, user_id)

        return jsonify({"success": True, "status": new_status, "message": f"Exchange request marked as {new_status}."})
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400
