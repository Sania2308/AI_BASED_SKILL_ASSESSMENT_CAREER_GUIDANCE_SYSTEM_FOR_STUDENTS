from datetime import datetime

def get_swap_peer_matches(db_conn, current_user_id):
    """
    Computes reciprocal peer matches for the logged-in student:
    - ONLY verified technical skills (from `skill_assessments`) qualify for 'I can teach'.
    - 'I want to learn' comes from `learning_skills`.
    - Match score is boosted if mutual (I teach what they want, they teach what I want).
    - Privacy-conscious: Returns only student name, course, verified skills, and learning goals.
    """
    cur = db_conn.cursor()

    # My learning skills
    cur.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (current_user_id,))
    my_learning = {r["skill"] for r in cur.fetchall()}

    # My verified skills that I can teach
    cur.execute("SELECT skill, level, score FROM skill_assessments WHERE user_id = ? ORDER BY skill", (current_user_id,))
    my_teach_rows = cur.fetchall()
    my_teach = {r["skill"]: {"level": r["level"], "score": r["score"]} for r in my_teach_rows}

    # Fetch other registered students
    cur.execute("""
        SELECT id, name, course, year
        FROM users
        WHERE id != ? AND role = 'student'
        ORDER BY name
    """, (current_user_id,))
    peers = cur.fetchall()

    matches = []

    for p in peers:
        peer_id = p["id"]
        # Peer verified skills (what peer can teach)
        cur.execute("SELECT skill, level, score FROM skill_assessments WHERE user_id = ? ORDER BY skill", (peer_id,))
        peer_verified = {r["skill"]: {"level": r["level"], "score": r["score"]} for r in cur.fetchall()}

        # Peer learning goals
        cur.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (peer_id,))
        peer_learning = {r["skill"] for r in cur.fetchall()}

        # What peer can teach me that I want to learn
        skills_peer_can_teach_me = sorted(my_learning & set(peer_verified.keys()))
        # What I can teach peer that they want to learn
        skills_i_can_teach_peer = sorted(set(my_teach.keys()) & peer_learning)

        # Matching Rule:
        # Current student's requested learning skill -> Other student's technically verified skill
        # Match exists -> Eligible peer. A peer does NOT appear simply because they have an account.
        if my_learning:
            if not skills_peer_can_teach_me:
                continue
            overlap_count = len(skills_peer_can_teach_me)
            base_ratio = overlap_count / max(len(my_learning), 1)
            match_pct = round(base_ratio * 70)
            if skills_i_can_teach_peer:
                match_pct = min(98, match_pct + 28)
            match_pct = max(30, match_pct)
        elif my_teach and skills_i_can_teach_peer and peer_verified:
            match_pct = 50
        else:
            # If no learning goals and no mutual teachable skill match exists, peer is not eligible
            continue

        teach_details = [
            {"skill": s, "level": peer_verified[s]["level"], "score": peer_verified[s]["score"]}
            for s in sorted(peer_verified.keys())
        ]

        matches.append({
            "peer_id": peer_id,
            "name": p["name"],
            "course": p["course"],
            "year": p["year"],
            "match": match_pct,
            "teach_skills": teach_details,
            "learn_skills": sorted(peer_learning),
            "relevant_teach": skills_peer_can_teach_me,
            "relevant_learn": skills_i_can_teach_peer
        })

    # Sort descending by match score
    matches.sort(key=lambda x: x["match"], reverse=True)
    return matches


def create_swap_request(db_conn, sender_id, receiver_id, teach_skill, learn_skill, notes=""):
    """
    Creates a new skill swap proposal in `skill_swap_requests`.
    """
    cur = db_conn.cursor()
    # Check if a pending request already exists
    cur.execute("""
        SELECT id FROM skill_swap_requests
        WHERE sender_id = ? AND receiver_id = ? AND status = 'Pending'
    """, (sender_id, receiver_id))
    if cur.fetchone():
        raise ValueError("You already have a pending exchange request with this peer.")

    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("""
        INSERT INTO skill_swap_requests (sender_id, receiver_id, teach_skill, learn_skill, status, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?)
    """, (sender_id, receiver_id, teach_skill, learn_skill, notes, now, now))
    db_conn.commit()
    return cur.lastrowid


def update_swap_request_status(db_conn, request_id, user_id, new_status):
    """
    Updates status of a skill swap request (Accepted, Completed, Cancelled).
    Validates authorization: only receiver or sender can transition status.
    """
    if new_status not in ["Pending", "Accepted", "Completed", "Cancelled"]:
        raise ValueError("Invalid swap status.")

    cur = db_conn.cursor()
    cur.execute("SELECT * FROM skill_swap_requests WHERE id = ?", (request_id,))
    req = cur.fetchone()
    if not req:
        raise ValueError("Request not found.")

    if user_id not in [req["sender_id"], req["receiver_id"]]:
        raise PermissionError("You are not authorized to update this exchange request.")

    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("""
        UPDATE skill_swap_requests
        SET status = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, now, request_id))
    db_conn.commit()
    return True


def get_user_swap_requests(db_conn, user_id):
    """
    Fetches all incoming and outgoing swap requests with student display names.
    """
    cur = db_conn.cursor()
    cur.execute("""
        SELECT r.*, 
               sender.name as sender_name,
               receiver.name as receiver_name
        FROM skill_swap_requests r
        JOIN users sender ON r.sender_id = sender.id
        JOIN users receiver ON r.receiver_id = receiver.id
        WHERE r.sender_id = ? OR r.receiver_id = ?
        ORDER BY r.updated_at DESC
    """, (user_id, user_id))
    return [dict(row) for row in cur.fetchall()]
