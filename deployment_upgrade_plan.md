# SkillGuide Deployment Upgrade Plan
## Upgrading from Localhost College Prototype to Secure Public Web Application

---

### 1. Current Architecture

- **Web Framework**: Python 3.11 + Flask 3.1.3
- **Architectural Style**: Modular Flask Application using Application Factory (`create_app`) and 13 Blueprints:
  - `auth_bp`, `dashboard_bp`, `assessment_bp`, `career_bp`, `roadmap_bp`, `swap_bp`, `gis_bp`, `achievements_bp`, `verification_bp`, `profile_bp`, `report_bp`, `admin_bp`, `api_bp`
- **Frontend / UI**:
  - Semantic HTML5, Bootstrap 5.3+, Bootstrap Icons
  - Chart.js for skill breakdown radar, progress analytics, and admin metrics
  - Leaflet.js + OpenStreetMap tile layer for peer GIS location clustering
- **Database**:
  - Local SQLite 3 database (`skillguide.db`, ~156 KB)
  - Accessed via Python's built-in `sqlite3` driver with row factory `sqlite3.Row` and WAL mode enabled
  - Foreign keys enabled via `PRAGMA foreign_keys = ON;`
- **NLP / Document Parsing**:
  - Resume parser supporting PDF (`pypdf`), DOCX (`python-docx`), and plain text
  - Rule-based keyword matching and regex extraction against `SKILL_TAXONOMY` in `app/config.py`
- **Security & Integrity**:
  - Werkzeug `generate_password_hash` / `check_password_hash` (pbkdf2:sha256)
  - Cryptographic verification ledger prototype using SHA-256 hashes linking user achievements, skills, and assessment scores
  - Transaction-based gamification ledger (`skill_point_transactions`) to prevent duplicate point grants
- **Execution & Hosting**:
  - Local server run directly via `python app.py` binding to `127.0.0.1:5000`
  - Uploaded files written locally to `<BASE_DIR>/uploads`

---

### 2. Complete Database Schema (Inspected from `skillguide.db`)

The real SQLite database contains **13 application tables**:

1. **`users`**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `name`: TEXT NOT NULL
   - `email`: TEXT UNIQUE NOT NULL
   - `password_hash`: TEXT NOT NULL
   - `role`: TEXT DEFAULT 'student'
   - `bio`: TEXT DEFAULT ''
   - `course`: TEXT DEFAULT 'Computer Science'
   - `year`: TEXT DEFAULT '3rd Year'
   - `skill_points`: INTEGER DEFAULT 0
   - `created_at`: TEXT NOT NULL

2. **`assessments`** (Overall 5-domain student assessment)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FK -> `users(id)`)
   - `overall`: INTEGER NOT NULL
   - `technical`: INTEGER NOT NULL
   - `problem_solving`: INTEGER NOT NULL
   - `communication`: INTEGER NOT NULL
   - `domain_knowledge`: INTEGER NOT NULL
   - `learning_ability`: INTEGER DEFAULT 50
   - `correct`: INTEGER NOT NULL
   - `total`: INTEGER NOT NULL
   - `taken_at`: TEXT NOT NULL

3. **`assessment_history`** (Retake and audit history)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
   - `assessment_type`: TEXT NOT NULL
   - `score`: INTEGER NOT NULL
   - `level`: TEXT DEFAULT ''
   - `correct`: INTEGER NOT NULL
   - `total`: INTEGER NOT NULL
   - `details_json`: TEXT DEFAULT '{}'
   - `taken_at`: TEXT NOT NULL

4. **`extracted_skills`** (Skills extracted from uploaded resumes or raw text)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FK -> `users(id)`)
   - `skill`: TEXT NOT NULL
   - `category`: TEXT DEFAULT 'General'
   - `source`: TEXT DEFAULT 'text'
   - `created_at`: TEXT DEFAULT CURRENT_TIMESTAMP
   - `UNIQUE(user_id, skill)`

5. **`skill_assessments`** (Verified technical skills from MCQ verification tests)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FK -> `users(id)`)
   - `skill`: TEXT NOT NULL
   - `score`: INTEGER NOT NULL
   - `level`: TEXT NOT NULL
   - `correct`: INTEGER NOT NULL
   - `total`: INTEGER NOT NULL
   - `verification_hash`: TEXT DEFAULT ''
   - `taken_at`: TEXT NOT NULL
   - `UNIQUE(user_id, skill)`

6. **`learning_skills`** (Skills student wants to learn for Skill Swap & career prep)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FK -> `users(id)`)
   - `skill`: TEXT NOT NULL
   - `created_at`: TEXT DEFAULT CURRENT_TIMESTAMP
   - `UNIQUE(user_id, skill)`

7. **`career_preferences`** (Student target career selection)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL UNIQUE (FK -> `users(id)` ON DELETE CASCADE)
   - `preferred_career`: TEXT NOT NULL
   - `updated_at`: TEXT NOT NULL

8. **`roadmap_progress`** (Interactive milestone completion tracking)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
   - `career_name`: TEXT NOT NULL
   - `step_id`: INTEGER NOT NULL
   - `title`: TEXT NOT NULL
   - `description`: TEXT DEFAULT ''
   - `category`: TEXT DEFAULT 'Course'
   - `status`: TEXT DEFAULT 'Not Started'
   - `updated_at`: TEXT NOT NULL
   - `UNIQUE(user_id, career_name, step_id)`

9. **`skill_swap_requests`** (Peer-to-peer exchange requests)
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `sender_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
   - `receiver_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
   - `teach_skill`: TEXT NOT NULL
   - `learn_skill`: TEXT NOT NULL
   - `status`: TEXT DEFAULT 'Pending'
   - `notes`: TEXT DEFAULT ''
   - `created_at`: TEXT NOT NULL
   - `updated_at`: TEXT NOT NULL

10. **`achievements`** (Predefined achievement badges catalog)
    - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
    - `code`: TEXT UNIQUE NOT NULL
    - `title`: TEXT NOT NULL
    - `description`: TEXT NOT NULL
    - `icon`: TEXT NOT NULL
    - `points`: INTEGER DEFAULT 20

11. **`user_achievements`** (Unlocked student achievements)
    - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
    - `user_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
    - `achievement_code`: TEXT NOT NULL (FK -> `achievements(code)` ON DELETE CASCADE)
    - `unlocked_at`: TEXT NOT NULL
    - `UNIQUE(user_id, achievement_code)`

12. **`verification_records`** (Cryptographic SHA-256 ledger certificates)
    - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
    - `user_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
    - `record_type`: TEXT NOT NULL
    - `item_name`: TEXT NOT NULL
    - `score`: INTEGER DEFAULT 0
    - `level`: TEXT DEFAULT ''
    - `verification_hash`: TEXT UNIQUE NOT NULL
    - `metadata_json`: TEXT DEFAULT '{}'
    - `created_at`: TEXT NOT NULL

13. **`skill_point_transactions`** (Deduplication ledger for gamification points)
    - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
    - `user_id`: INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
    - `action_key`: TEXT NOT NULL
    - `reference_id`: TEXT DEFAULT ''
    - `points`: INTEGER NOT NULL
    - `created_at`: TEXT NOT NULL
    - `UNIQUE(user_id, action_key, reference_id)`

---

### 3. Deployment Blockers Identified

1. **Local SQLite File Persistence on Vercel**:
   - Vercel is a serverless execution environment with an ephemeral, read-only root filesystem.
   - Any modifications to a local `.db` file in the project folder will fail or be erased between serverless invocations.
   - **Resolution**: Provide PostgreSQL database adapter layer configured through `DATABASE_URL` (connecting to Supabase PostgreSQL over SSL with connection pooling), while keeping SQLite functional for local development and offline unit tests.
2. **Read-Only Filesystem & Uploads Directory**:
   - `os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)` in `app/__init__.py` attempts to create an `uploads/` folder in the project root directory. On Vercel, this will raise `OSError: [Errno 30] Read-only file system`.
   - **Resolution**: Use `tempfile.gettempdir()` (e.g. `/tmp` on Linux/serverless) for transient resume file processing and immediately delete files upon extracting text.
3. **Missing WSGI Entry Point for Vercel Serverless Function**:
   - Vercel expects a Python entrypoint (such as `api/index.py` or exposing WSGI `app` at root) and correct `requirements.txt` / `vercel.json` if necessary.
   - **Resolution**: Standard Vercel Python entry point pointing to the Flask WSGI instance `app`.
4. **Missing Database Driver**:
   - `requirements.txt` only specifies `Flask`, `pypdf`, `python-docx`, `werkzeug`. It lacks PostgreSQL client libraries (`psycopg2-binary` or `psycopg`).
   - **Resolution**: Add `psycopg2-binary` to dependencies.
5. **SQL Placeholder & Row Handling Differences**:
   - SQLite uses `?` parameter markers; PostgreSQL uses `%s`.
   - SQLite cursor returns `sqlite3.Row` supporting both name and positional indexing; PostgreSQL drivers need appropriate cursor factories (e.g., `psycopg2.extras.DictCursor`) and automatic `?` -> `%s` translation or adapter wrapper.
   - SQLite `cur.lastrowid` is used in user signup (`app/routes/auth.py`) and swap proposal creation (`app/services/swap_service.py`). PostgreSQL requires handling via `RETURNING id` or tracking.

---

### 4. Security Problems Identified & Remediation

1. **Hardcoded Fallback Secret Key**:
   - `app/config.py` had default `"skillguide-dev-secret-key-2026-v2"`.
   - **Remediation**: Read `SECRET_KEY` from environment variables; fail securely or generate a secure warning/session secret in production; require `SECRET_KEY` in production.
2. **Default Admin Account Credentials in Code**:
   - `app/db.py` contained hardcoded `admin@skillguide.edu` / `admin123`.
   - **Remediation**: Allow overriding through environment variables `ADMIN_EMAIL` and `ADMIN_INITIAL_PASSWORD`, or prevent automatic seeding of weak credentials if an admin already exists.
3. **Session Cookie Security**:
   - Flask sessions did not explicitly enforce `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True`, and `SESSION_COOKIE_SAMESITE = 'Lax'`.
   - **Remediation**: Configure secure cookie flags in `app/config.py` based on `APP_ENV` / `FLASK_ENV`.
4. **Git Exposure Risks**:
   - `.gitignore` was missing `.env`, `*.db`, `skillguide.db`, and secrets.
   - **Remediation**: Update `.gitignore` to explicitly ignore `.env`, `.env.*`, `*.db`, `*.sqlite`, `*.sqlite3`, credentials, and temporary uploads.
5. **Error Handler Information Leakage**:
   - `app/__init__.py` passed `error=str(e)` directly into `render_template("500.html", error=str(e))`, which could reveal internal database tracebacks, file paths, or query errors to end users.
   - **Remediation**: Mask internal errors in production, showing user-friendly guidance while logging details server-side.

---

### 5. Required Migrations

1. **`supabase_schema.sql`**:
   - Full PostgreSQL DDL reproducing all 13 tables, primary keys, foreign keys with `ON DELETE CASCADE`, unique constraints, default values, and indexes.
   - Appropriate PostgreSQL data types:
     - `INTEGER PRIMARY KEY AUTOINCREMENT` -> `SERIAL PRIMARY KEY` or `INTEGER GENERATED ALWAYS AS IDENTITY`
     - `TEXT` -> `TEXT` or `VARCHAR`
     - `BOOLEAN` / `INTEGER`
     - `TIMESTAMPTZ` / `TEXT`
   - Pre-seeding standard `achievements` catalogue records.
2. **Universal Database Adapter in `app/db.py`**:
   - If `DATABASE_URL` is set: connects to Supabase PostgreSQL using `psycopg2-binary`.
   - Translates `?` queries to `%s`.
   - Handles `cursor.lastrowid` via transparent `RETURNING id` support.
   - Returns dictionary-like rows supporting `row['col']` and `row[0]`.
   - If `DATABASE_URL` is not set: falls back cleanly to SQLite for local development and offline test suites.

---

### 6. Files That Need Modification / Creation

| File | Status | Purpose |
|------|--------|---------|
| `deployment_upgrade_plan.md` | Created | Audit documentation and migration roadmap |
| `supabase_schema.sql` | To Create | Production PostgreSQL schema for Supabase |
| `.env.example` | To Create | Template for environment variable names only |
| `.gitignore` | To Modify | Add `.env`, `*.db`, `skillguide.db`, cache, etc. |
| `requirements.txt` | To Modify | Add `psycopg2-binary` |
| `app/config.py` | To Modify | Support `DATABASE_URL`, `SECRET_KEY`, secure session cookies, serverless upload dir |
| `app/db.py` | To Modify | Universal database adapter (SQLite + Supabase PostgreSQL) |
| `app/__init__.py` | To Modify | Safe upload folder handling, add `/health` route, sanitize 500 error handler |
| `vercel.json` | To Create | Vercel configuration for Python WSGI entry point if needed |
| `api/index.py` | To Create | Standard Vercel Serverless Function entrypoint exporting `app` |
| `README.md` | To Modify | Complete updated instructions for Supabase & Vercel |
