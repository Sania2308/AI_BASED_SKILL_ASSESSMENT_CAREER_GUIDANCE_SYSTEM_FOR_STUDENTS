import hashlib
import json
from datetime import datetime

def generate_verification_hash(user_id, student_name, item_name, score, level, timestamp_str=None):
    """
    Cryptographic Blockchain Prototype Verification Engine:
    
    Generates a deterministic SHA-256 hash simulating a cryptographic block payload:
    Payload incorporates:
    - Unique Student Identity & Name
    - Skill / Certificate Name
    - Assessed Percentage Score & Tier
    - ISO Timestamp
    - Genesis Salt / SkillGuide Protocol Version
    
    Academic Transparency Note:
    This creates an immutable deterministic tamper-evident verification hash.
    It demonstrates the mathematical verification layer of distributed ledger systems.
    It does NOT connect to Ethereum or Bitcoin mainnets.
    """
    if not timestamp_str:
        timestamp_str = datetime.now().isoformat(timespec="seconds")

    payload = {
        "protocol": "SkillGuide-EdChain-v2",
        "student_id": user_id,
        "student_name": student_name,
        "item": item_name,
        "score": score,
        "level": level,
        "timestamp": timestamp_str
    }
    
    canonical_str = json.dumps(payload, sort_keys=True)
    hash_digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    verification_id = f"SG-{hash_digest[:12].upper()}"

    return {
        "verification_id": verification_id,
        "verification_hash": hash_digest,
        "payload": payload,
        "timestamp": timestamp_str
    }


def record_verification(db_conn, user_id, student_name, record_type, item_name, score, level):
    """
    Mints and saves a tamper-evident verification record in `verification_records`.
    Also updates the hash on `skill_assessments` if it's a technical skill.
    """
    cur = db_conn.cursor()
    now_str = datetime.now().isoformat(timespec="seconds")
    
    token = generate_verification_hash(user_id, student_name, item_name, score, level, now_str)
    ver_hash = token["verification_hash"]
    meta_json = json.dumps(token["payload"])

    # Insert into verification_records
    cur.execute("""
        INSERT INTO verification_records (user_id, record_type, item_name, score, level, verification_hash, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(verification_hash) DO UPDATE SET
            score=excluded.score, level=excluded.level, metadata_json=excluded.metadata_json
    """, (user_id, record_type, item_name, score, level, ver_hash, meta_json, now_str))

    # If it is a technical skill assessment, update skill_assessments verification_hash
    if record_type == "skill_badge":
        cur.execute("""
            UPDATE skill_assessments
            SET verification_hash = ?
            WHERE user_id = ? AND skill = ?
        """, (ver_hash, user_id, item_name))

    db_conn.commit()
    return token


def verify_hash_record(db_conn, query_hash_or_id):
    """
    Verifies a supplied verification ID or SHA-256 hash against database ledger records.
    Returns audit details if valid, or None if unrecognized.
    """
    if not query_hash_or_id:
        return None

    clean_query = query_hash_or_id.strip()
    cur = db_conn.cursor()

    # Search by full SHA-256 hash or verification ID prefix
    if clean_query.startswith("SG-"):
        prefix = clean_query.replace("SG-", "").lower()
        cur.execute("""
            SELECT v.*, u.name as student_name, u.email as student_email, u.course, u.year
            FROM verification_records v
            JOIN users u ON v.user_id = u.id
            WHERE LOWER(v.verification_hash) LIKE ?
            ORDER BY v.id DESC LIMIT 1
        """, (f"{prefix}%",))
    else:
        cur.execute("""
            SELECT v.*, u.name as student_name, u.email as student_email, u.course, u.year
            FROM verification_records v
            JOIN users u ON v.user_id = u.id
            WHERE LOWER(v.verification_hash) = LOWER(?)
            LIMIT 1
        """, (clean_query,))

    row = cur.fetchone()
    if not row:
        return None

    record = dict(row)
    # Parse metadata
    try:
        record["metadata"] = json.loads(record["metadata_json"])
    except Exception:
        record["metadata"] = {}

    record["verification_id"] = f"SG-{record['verification_hash'][:12].upper()}"
    record["is_valid"] = True
    return record
