import os
import sqlite3
import re
from datetime import datetime
from flask import g, current_app
from app.config import Config
from werkzeug.security import generate_password_hash

# Try importing psycopg2 for production PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def translate_query_for_postgres(sql: str) -> str:
    """
    Translates SQLite parameter placeholders ('?') to PostgreSQL placeholders ('%s'),
    preserving literal '?' inside single or double-quoted string literals.
    """
    tokens = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        if c == "'" and not in_double_quote:
            if i + 1 < n and sql[i + 1] == "'":
                tokens.append("''")
                i += 2
                continue
            in_single_quote = not in_single_quote
            tokens.append(c)
        elif c == '"' and not in_single_quote:
            if i + 1 < n and sql[i + 1] == '"':
                tokens.append('""')
                i += 2
                continue
            in_double_quote = not in_double_quote
            tokens.append(c)
        elif c == '?' and not in_single_quote and not in_double_quote:
            tokens.append('%s')
        else:
            tokens.append(c)
        i += 1
    return "".join(tokens)


class PostgresRow(dict):
    """
    Row object wrapper that provides both dictionary access (`row['email']`, `dict(row)`)
    and tuple index access (`row[0]`), mirroring `sqlite3.Row` exactly.
    """
    def __init__(self, cols, vals):
        super().__init__(zip(cols, vals))
        self._vals = list(vals)
        self._cols = list(cols)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._vals[item]
        return super().__getitem__(item)

    def keys(self):
        return self._cols

    def values(self):
        return self._vals

    def items(self):
        return list(zip(self._cols, self._vals))


class PostgresCursorWrapper:
    """
    Cursor wrapper providing SQLite-compatible API over a psycopg2 cursor:
    - Automatically translates '?' query parameters to '%s'.
    - Ignores SQLite PRAGMA commands safely.
    - Sets `lastrowid` on INSERT operations using RETURNING id.
    - Converts fetched tuples into PostgresRow objects.
    """
    def __init__(self, raw_cursor):
        self._cursor = raw_cursor
        self.lastrowid = None

    def execute(self, sql, params=None):
        clean_sql = sql.strip()
        # No-op SQLite PRAGMAs on PostgreSQL
        if clean_sql.upper().startswith("PRAGMA"):
            return self

        translated = translate_query_for_postgres(sql)
        upper_translated = translated.strip().upper()
        is_insert = upper_translated.startswith("INSERT INTO")
        has_returning = "RETURNING" in upper_translated

        if is_insert and not has_returning:
            # Append RETURNING id to capture generated primary key
            translated_with_ret = f"{translated} RETURNING id"
            try:
                self._cursor.execute(translated_with_ret, params or ())
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row[0]
            except Exception:
                # Fallback to standard execute if RETURNING fails (e.g. non-id table)
                self._cursor.execute(translated, params or ())
                self.lastrowid = None
        else:
            self._cursor.execute(translated, params or ())
            self.lastrowid = None
        return self

    def executemany(self, sql, seq_of_params):
        clean_sql = sql.strip()
        if clean_sql.upper().startswith("PRAGMA"):
            return self
        translated = translate_query_for_postgres(sql)
        self._cursor.executemany(translated, seq_of_params)
        return self

    def fetchone(self):
        val = self._cursor.fetchone()
        if val is None:
            return None
        cols = [desc[0] for desc in self._cursor.description]
        return PostgresRow(cols, val)

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        cols = [desc[0] for desc in self._cursor.description]
        return [PostgresRow(cols, r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size) if size else self._cursor.fetchmany()
        if not rows:
            return []
        cols = [desc[0] for desc in self._cursor.description]
        return [PostgresRow(cols, r) for r in rows]

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        return self._cursor.close()


class PostgresConnectionWrapper:
    """
    Connection wrapper providing SQLite-compatible API over a psycopg2 connection:
    - Provides `connection.execute(sql, params)` convenience method.
    - Manages wrapped cursors, commits, rollbacks, and connection closing.
    """
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor())

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def normalize_postgres_url(url: str) -> str:
    """Ensures postgresql:// prefix and sslmode compatibility for cloud providers like Supabase."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_db():
    """
    Returns the active database connection for the current Flask request context.
    Uses Supabase PostgreSQL if DATABASE_URL is configured; otherwise uses SQLite.
    """
    if "db" not in g:
        db_url = current_app.config.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
        if db_url and PSYCOPG2_AVAILABLE:
            normalized_url = normalize_postgres_url(db_url)
            raw_conn = psycopg2.connect(normalized_url)
            raw_conn.autocommit = False
            g.db = PostgresConnectionWrapper(raw_conn)
        else:
            db_path = current_app.config.get("DATABASE", Config.DATABASE)
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(e=None):
    """Closes the current request's database connection if open."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_direct_db(db_path=None, db_url=None):
    """
    Returns a direct database connection outside of the Flask request lifecycle.
    Useful for schema initialization, background jobs, and migrations.
    """
    url = db_url or os.environ.get("DATABASE_URL")
    if url and PSYCOPG2_AVAILABLE:
        normalized_url = normalize_postgres_url(url)
        raw_conn = psycopg2.connect(normalized_url)
        raw_conn.autocommit = False
        return PostgresConnectionWrapper(raw_conn)

    if not db_path:
        db_path = Config.DATABASE
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None, db_url=None):
    """
    Initializes and verifies the database schema and seeds initial data.
    Automatically handles PostgreSQL (Supabase) or SQLite based on configuration.
    """
    url = db_url or os.environ.get("DATABASE_URL")

    if url and PSYCOPG2_AVAILABLE:
        # PostgreSQL (Supabase) initialization
        conn = get_direct_db(db_url=url)
        cur = conn.cursor()

        # Read and execute supabase_schema.sql if present
        schema_path = os.path.join(Config.BASE_DIR, "supabase_schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            cur.execute(schema_sql)
            conn.commit()

        # Seed admin user if none exists
        cur.execute("SELECT id FROM users WHERE role = 'admin'")
        if not cur.fetchone():
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@skillguide.edu")
            admin_pass = os.environ.get("ADMIN_INITIAL_PASSWORD", "admin123")
            now_str = datetime.now().isoformat(timespec="seconds")
            cur.execute("""
                INSERT INTO users (name, email, password_hash, role, bio, course, year, skill_points, created_at)
                VALUES (?, ?, ?, 'admin', 'SkillGuide Academic Administrator', 'Administration', 'Faculty', 500, ?)
            """, ("Administrator", admin_email, generate_password_hash(admin_pass), now_str))
            conn.commit()

        conn.close()
        return

    # SQLite local development initialization
    conn = get_direct_db(db_path)
    cur = conn.cursor()

    # 1. Base users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            bio TEXT DEFAULT '',
            course TEXT DEFAULT 'Computer Science',
            year TEXT DEFAULT '3rd Year',
            skill_points INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)

    # Check and add missing columns to users if migrating
    user_cols = [r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
    if "skill_points" not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN skill_points INTEGER DEFAULT 0")

    # 2. Overall assessment table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            overall INTEGER NOT NULL,
            technical INTEGER NOT NULL,
            problem_solving INTEGER NOT NULL,
            communication INTEGER NOT NULL,
            domain_knowledge INTEGER NOT NULL,
            learning_ability INTEGER DEFAULT 50,
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            taken_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    assess_cols = [r[1] for r in cur.execute("PRAGMA table_info(assessments)").fetchall()]
    if "learning_ability" not in assess_cols:
        cur.execute("ALTER TABLE assessments ADD COLUMN learning_ability INTEGER DEFAULT 50")

    # 3. Assessment history (retake audit trail)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assessment_type TEXT NOT NULL,
            score INTEGER NOT NULL,
            level TEXT DEFAULT '',
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            details_json TEXT DEFAULT '{}',
            taken_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 4. Extracted skills from resume/text
    cur.execute("""
        CREATE TABLE IF NOT EXISTS extracted_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            source TEXT DEFAULT 'text',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, skill),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    ext_cols = [r[1] for r in cur.execute("PRAGMA table_info(extracted_skills)").fetchall()]
    if "category" not in ext_cols:
        cur.execute("ALTER TABLE extracted_skills ADD COLUMN category TEXT DEFAULT 'General'")
    if "source" not in ext_cols:
        cur.execute("ALTER TABLE extracted_skills ADD COLUMN source TEXT DEFAULT 'text'")
    if "created_at" not in ext_cols:
        cur.execute("ALTER TABLE extracted_skills ADD COLUMN created_at TEXT DEFAULT ''")

    # 5. Verified technical skills
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            score INTEGER NOT NULL,
            level TEXT NOT NULL,
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            verification_hash TEXT DEFAULT '',
            taken_at TEXT NOT NULL,
            UNIQUE(user_id, skill),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    skill_cols = [r[1] for r in cur.execute("PRAGMA table_info(skill_assessments)").fetchall()]
    if "verification_hash" not in skill_cols:
        cur.execute("ALTER TABLE skill_assessments ADD COLUMN verification_hash TEXT DEFAULT ''")

    # 6. Learning skills
    cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, skill),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 7. Career preferences & target career
    cur.execute("""
        CREATE TABLE IF NOT EXISTS career_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            preferred_career TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 8. Interactive roadmap progress
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roadmap_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            career_name TEXT NOT NULL,
            step_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'Course',
            status TEXT DEFAULT 'Not Started',
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, career_name, step_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 9. Peer-to-peer Skill Swap requests
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            teach_skill TEXT NOT NULL,
            learn_skill TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 10. Achievements catalog
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            points INTEGER DEFAULT 20
        );
    """)

    # 11. User unlocked achievements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_code TEXT NOT NULL,
            unlocked_at TEXT NOT NULL,
            UNIQUE(user_id, achievement_code),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(achievement_code) REFERENCES achievements(code) ON DELETE CASCADE
        );
    """)

    # 12. Verification records ledger prototype
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verification_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            record_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            level TEXT DEFAULT '',
            verification_hash TEXT UNIQUE NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 13. Gamification transaction ledger (deduplication)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_point_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_key TEXT NOT NULL,
            reference_id TEXT DEFAULT '',
            points INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, action_key, reference_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # Seed predefined achievements if empty
    cur.execute("SELECT COUNT(*) FROM achievements")
    if cur.fetchone()[0] == 0:
        default_achievements = [
            ("profile_complete", "Profile Pioneer", "Complete your student profile details and bio", "bi-person-check", 10),
            ("resume_uploaded", "Resume Decoder", "Upload or analyze your resume text via AI/NLP", "bi-file-earmark-code", 10),
            ("assessment_master", "Assessment Master", "Complete the comprehensive 5-domain skill assessment", "bi-award", 20),
            ("python_verified", "Python Verified", "Pass the Python technical skill verification test", "bi-patch-check-fill", 30),
            ("first_verified_skill", "Certified Scholar", "Verify your first technical skill with high proficiency", "bi-shield-check", 30),
            ("multi_skilled", "Polymath", "Successfully verify 3 or more technical skills", "bi-gem", 50),
            ("career_explorer", "Career Explorer", "Explore personalized career recommendations and set a career goal", "bi-compass", 15),
            ("roadmap_pioneer", "Roadmap Pioneer", "Complete a learning roadmap milestone for your target role", "bi-signpost-split", 10),
            ("skill_mentor", "Skill Mentor", "Create or accept a peer-to-peer skill swap exchange", "bi-people", 40),
            ("blockchain_badged", "Cryptographic Trust", "Mint a deterministic blockchain-prototype skill certificate", "bi-link-45deg", 25)
        ]
        cur.executemany("INSERT INTO achievements(code, title, description, icon, points) VALUES (?,?,?,?,?)", default_achievements)

    # Seed an admin user if not present
    cur.execute("SELECT id FROM users WHERE role = 'admin'")
    if not cur.fetchone():
        try:
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@skillguide.edu")
            admin_pass = os.environ.get("ADMIN_INITIAL_PASSWORD", "admin123")
            cur.execute("""
                INSERT INTO users(name, email, password_hash, role, bio, course, year, skill_points, created_at)
                VALUES (?, ?, ?, 'admin', 'SkillGuide Academic Administrator', 'Administration', 'Faculty', 500, ?)
            """, ("Administrator", admin_email, generate_password_hash(admin_pass), datetime.now().isoformat(timespec="seconds")))
        except Exception:
            pass

    conn.commit()
    conn.close()
