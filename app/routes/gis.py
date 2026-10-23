from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.db import get_db
from app.services.gis_service import get_peer_map_markers
from app.config import ALL_SKILLS

gis_bp = Blueprint("gis", __name__)

@gis_bp.route("/gis-map")
def gis_map_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # Preload initial markers
    markers = get_peer_map_markers(db, user_id)

    return render_template(
        "gis_map.html",
        page="gis-map",
        user=user,
        markers=markers,
        all_skills=ALL_SKILLS,
        levels=["Beginner", "Intermediate", "Advanced", "Expert"]
    )


@gis_bp.route("/api/gis-markers")
def api_gis_markers():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    skill_filter = request.args.get("skill", "all")
    level_filter = request.args.get("level", "all")

    db = get_db()
    markers = get_peer_map_markers(db, user_id, skill_filter, level_filter)
    return jsonify({
        "success": True,
        "count": len(markers),
        "markers": markers,
        "center": [12.9716, 77.5946],
        "privacy_notice": "Student locations are rendered using approximate institutional campus clusters to preserve privacy."
    })
