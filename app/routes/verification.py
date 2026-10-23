from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.db import get_db
from app.services.crypto_verification import verify_hash_record, record_verification
from app.services.gamification import award_skill_points, check_and_unlock_achievements

verification_bp = Blueprint("verification", __name__)

@verification_bp.route("/verification")
def verification_view():
    user_id = session.get("user_id")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None

    # Optional query parameter for instant lookup
    query = request.args.get("query", "").strip()
    record = None
    if query:
        record = verify_hash_record(db, query)

    # User's own issued verified badges/records if logged in
    user_records = []
    if user_id:
        cur = db.execute("""
            SELECT * FROM verification_records
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))
        user_records = [dict(r) for r in cur.fetchall()]

    return render_template(
        "verification.html",
        page="verification",
        user=user,
        query=query,
        record=record,
        user_records=user_records
    )


@verification_bp.route("/verify/<path:token>")
def direct_verify(token):
    db = get_db()
    record = verify_hash_record(db, token)
    user_id = session.get("user_id")
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None

    return render_template(
        "verification.html",
        page="verification",
        user=user,
        query=token,
        record=record,
        user_records=[]
    )


@verification_bp.route("/api/verify-token")
def api_verify_token():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Verification query is required."}), 400

    db = get_db()
    record = verify_hash_record(db, query)
    if not record:
        return jsonify({"valid": False, "message": "No matching ledger record was found for this verification query."}), 404

    return jsonify({
        "valid": True,
        "record": {
            "verification_id": record["verification_id"],
            "verification_hash": record["verification_hash"],
            "student_name": record["student_name"],
            "item_name": record["item_name"],
            "score": record["score"],
            "level": record["level"],
            "created_at": record["created_at"],
            "metadata": record.get("metadata", {})
        }
    })


@verification_bp.route("/api/mint-swap-certificate", methods=["POST"])
def mint_swap_certificate():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    swap_id = data.get("swap_id")

    db = get_db()
    user = db.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    student_name = user["name"] if user else "Student"

    token = record_verification(
        db, user_id, student_name, "peer_exchange", f"Peer Skill Exchange #{swap_id}", 100, "Completed"
    )

    award_skill_points(db, user_id, "complete_skill_swap", reference_id=str(swap_id))
    check_and_unlock_achievements(db, user_id)
    db.commit()

    return jsonify({
        "success": True,
        "verification_id": token["verification_id"],
        "verification_hash": token["verification_hash"],
        "message": "Peer exchange certificate minted into prototype ledger!"
    })
