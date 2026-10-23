import hashlib

# Base demo reference coordinate (Bangalore University & Educational Tech Hub Zone)
BASE_LAT = 12.9716
BASE_LNG = 77.5946

# Safe simulated academic hubs across the metropolitan campus region
CAMPUS_ZONES = [
    {"name": "Central Campus", "lat": 12.9720, "lng": 77.5950},
    {"name": "Engineering Tech Block", "lat": 12.9352, "lng": 77.6245},
    {"name": "North Innovation Quad", "lat": 13.0088, "lng": 77.5682},
    {"name": "South Academic Park", "lat": 12.9141, "lng": 77.6109},
    {"name": "East Research Labs", "lat": 12.9850, "lng": 77.6630},
    {"name": "West Computing Center", "lat": 12.9600, "lng": 77.5300}
]

def generate_safe_approximate_coords(user_id):
    """
    Generates deterministic, non-invasive approximate demo coordinates for each student.
    Ensures student privacy: NEVER tracks or requests GPS device location.
    Clearly flagged as demo coordinates for viva transparency.
    """
    zone_idx = user_id % len(CAMPUS_ZONES)
    zone = CAMPUS_ZONES[zone_idx]
    
    # Deterministic pseudo-offset using hash to disperse markers visually on the map
    h = hashlib.sha256(f"peer_geo_privacy_{user_id}".encode()).hexdigest()
    lat_offset = ((int(h[:4], 16) % 100) - 50) * 0.0003
    lng_offset = ((int(h[4:8], 16) % 100) - 50) * 0.0003

    return round(zone["lat"] + lat_offset, 6), round(zone["lng"] + lng_offset, 6), zone["name"]


def get_peer_map_markers(db_conn, current_user_id, filter_skill=None, filter_level=None):
    """
    Retrieves all student peers with verified skills and learning goals formatted for Leaflet.js.
    Supports dynamic filtering by skill and proficiency level.
    """
    cur = db_conn.cursor()

    # Get my learning skills to calculate match
    cur.execute("SELECT skill FROM learning_skills WHERE user_id = ?", (current_user_id,))
    my_learning = {r["skill"].lower() for r in cur.fetchall()}

    # Fetch peers
    cur.execute("""
        SELECT id, name, course, year
        FROM users
        WHERE id != ? AND role = 'student'
        ORDER BY id
    """, (current_user_id,))
    peers = cur.fetchall()

    markers = []

    for p in peers:
        peer_id = p["id"]
        
        # Get verified skills
        cur.execute("SELECT skill, level, score FROM skill_assessments WHERE user_id = ? ORDER BY skill", (peer_id,))
        verified_skills = [dict(r) for r in cur.fetchall()]

        # Get learning skills
        cur.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (peer_id,))
        learning_skills = [r["skill"] for r in cur.fetchall()]

        # Filter check: skill filter
        if filter_skill and filter_skill != "all":
            has_skill = any(v["skill"].lower() == filter_skill.lower() for v in verified_skills)
            if not has_skill:
                continue

        # Filter check: level filter
        if filter_level and filter_level != "all":
            has_level = any(v["level"].lower() == filter_level.lower() for v in verified_skills)
            if not has_level:
                continue

        # Calculate match percentage
        peer_teach_set = {v["skill"].lower() for v in verified_skills}
        if my_learning:
            overlap = len(my_learning & peer_teach_set)
            match_pct = min(98, max(25, round((overlap / len(my_learning)) * 100) + 20 if overlap else 25))
        else:
            match_pct = 50 if verified_skills else 20

        lat, lng, campus_zone = generate_safe_approximate_coords(peer_id)

        markers.append({
            "id": peer_id,
            "name": p["name"],
            "course": p["course"],
            "year": p["year"],
            "zone": campus_zone,
            "lat": lat,
            "lng": lng,
            "match": match_pct,
            "verified_skills": verified_skills,
            "learning_skills": learning_skills,
            "is_demo_coords": True,
            "location_disclaimer": "Safe approximate campus coordinate for demo purposes."
        })

    return markers
