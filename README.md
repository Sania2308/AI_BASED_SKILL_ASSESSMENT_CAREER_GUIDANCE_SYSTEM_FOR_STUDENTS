# SkillGuide: AI-Based Skill Assessment and Career Guidance System for Students

> **Academic Product:** SkillGuide  
> **Target Degree:** B.Tech Computer Science & Engineering (Capstone Project)  
> **Global Alignment:** United Nations Sustainable Development Goal 4 (Quality Education)  
> **Deployment Target:** Public HTTPS URL on Vercel backed by Supabase PostgreSQL  
> **Version:** 2.0 (Production-Ready Architecture)

---

## 1. Project Overview & Problem Statement

### Title
**AI-Based Skill Assessment and Career Guidance System for Students**

### Problem Statement
University students commonly struggle with four major transitions during their undergraduate career:
1. **Ambiguous Skill Awareness:** Difficulty quantifying actual technical competence versus self-claimed resume buzzwords.
2. **Uncertain Career Direction:** Choosing career pathways based on market trends rather than explainable compatibility matching against their individual strengths.
3. **Unstructured Skill Gaps:** Lacking clear, actionable learning roadmaps with curated resources to bridge gaps for target industry roles.
4. **Isolated Peer Learning:** Missing localized, verified peer-to-peer networks to exchange verified skills safely on campus.

**SkillGuide** addresses these challenges by combining rule-based Natural Language Processing (NLP), multi-domain psychometric competency assessment, 10 technical verification engines, explainable AI career matching across 13 engineering domains, Leaflet GIS spatial peer exchange, and a deterministic cryptographic verification ledger prototype.

---

## 2. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.11+, Flask 3.1+ (Application Factory & 13 Blueprints) |
| **Production Serverless** | Vercel WSGI Python Runtime (`api/index.py`, `vercel.json`) |
| **Cloud Database** | Supabase Managed PostgreSQL (Production via `DATABASE_URL`) |
| **Local Database** | SQLite 3 (`skillguide.db`, zero-configuration local dev fallback) |
| **Database Drivers** | `psycopg2-binary` (PostgreSQL), `sqlite3` (built-in standard library) |
| **Security & Authentication** | Werkzeug (`generate_password_hash` / `check_password_hash`), secure session cookies (HTTPOnly, Secure, SameSite=Lax) |
| **Cryptographic Ledger** | Deterministic SHA-256 hash chains linking student, assessment score, and timestamp |
| **Document Ingestion & NLP**| `pypdf` (in-memory PDF stream parsing), `python-docx` (DOCX extraction), Regex token matcher |
| **Frontend Styling** | HTML5, Modern CSS3 (Variables, Light/Dark theme tokens, Responsive Grid), Bootstrap 5.3.3 |
| **Interactive Analytics** | Chart.js 4.4 (Radar, Bar, Doughnut, and Line charts) |
| **GIS Mapping** | Leaflet.js 1.9.4, OpenStreetMap (OSM) tile servers (approximate campus coordinates) |
| **Automated Test Suite** | Python standard `unittest`, Flask Test Client, production readiness test suite |

---

## 3. Production Architecture

```
Browser (Student / Admin / Public)
   ↓ HTTPS
Vercel Edge / Serverless Function (api/index.py)
   ↓ WSGI Request
Flask Application (13 Modular Blueprints)
   ↓ Server-side SQL via psycopg2-binary (SSL required)
Supabase PostgreSQL Database (13 Persistent Tables)
```

### Key Architectural Highlights:
- **Universal Dual-Database Engine (`app/db.py`)**: Seamlessly connects to Supabase PostgreSQL when `DATABASE_URL` is set, while preserving SQLite for offline development and local unit tests.
- **Serverless-Safe File Handling**: Uploaded resume files (`.pdf`, `.docx`, `.txt`) are parsed directly from transient memory streams and cleaned up immediately; no local filesystem dependency.
- **Strict Data Isolation**: Multi-tenant privacy guarantees ensure each student only accesses their own assessments, resumes, career matches, roadmap, and point ledgers.
- **Verified Skill Swap Matching**: Peers only appear in Skill Swap recommendations if they possess a technically verified skill matching the current student's learning goals.

---

## 4. Database Schema (13 Tables)

The production schema (`supabase_schema.sql`) defines 13 normalized tables:

1. `users` — Student accounts, hashed passwords, roles (`student`, `admin`), points balance, and profile info.
2. `assessments` — 5-domain competency evaluations (Technical, Problem Solving, Communication, Domain Knowledge, Learning Ability).
3. `assessment_history` — Comprehensive audit trail of test attempts and retakes.
4. `extracted_skills` — Technical skills identified from parsed resumes with category tagging.
5. `skill_assessments` — Verified technical skill results (score, level, verification hash).
6. `learning_skills` — Target competencies students wish to acquire.
7. `career_preferences` — Stored target career role for personalized guidance.
8. `roadmap_progress` — Milestone tracking across dynamic 8-step learning roadmaps.
9. `skill_swap_requests` — Peer-to-peer exchange requests lifecycle (`Pending`, `Accepted`, `Completed`, `Cancelled`).
10. `achievements` — Catalog of pre-seeded achievement badges and point values.
11. `user_achievements` — Unlocked badges linked to students.
12. `verification_records` — Deterministic SHA-256 tamper-evident verification ledger entries.
13. `skill_point_transactions` — Gamification transaction ledger enforcing strict deduplication to prevent exploit loops.

---

## 5. Environment Variables Configuration

Copy `.env.example` to `.env` for local testing:

```bash
cp .env.example .env
```

| Variable | Description | Example / Required in Production |
| :--- | :--- | :--- |
| `SECRET_KEY` | Secret key used to cryptographically sign Flask session cookies | Secure random 64-character string (Required) |
| `DATABASE_URL` | Supabase PostgreSQL connection URI | `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres` |
| `APP_ENV` | Application environment mode | `production` (on Vercel) or `development` |
| `FLASK_ENV` | Flask environment | `production` |
| `ADMIN_EMAIL` | Optional initial administrator email | `admin@skillguide.edu` |
| `ADMIN_INITIAL_PASSWORD` | Optional initial administrator password | Set a strong password |

> **IMPORTANT**: Never commit your `.env` file or passwords to GitHub. The `.gitignore` file is configured to exclude all `.env` files and local databases.

---

## 6. Local Development Setup

### Prerequisites
- Python 3.11+
- Git

### Steps:
```bash
# 1. Clone repository
git clone https://github.com/<your-username>/SkillGuide.git
cd SkillGuide

# 2. Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start local development server (uses SQLite fallback automatically)
python app.py
```

Open your browser at **`http://127.0.0.1:5000`**.

---

## 7. Cloud Migration: Supabase Setup (PostgreSQL)

1. **Create Supabase Project**:
   - Go to [Supabase](https://supabase.com/) and create a free project.
   - Note down the database password.
2. **Execute Schema**:
   - Open the Supabase dashboard for your project.
   - Click **SQL Editor** in the left sidebar.
   - Copy the contents of `supabase_schema.sql` from this repository.
   - Paste into the SQL Editor and click **Run**.
   - Confirm all 13 tables are created successfully.
3. **Copy Connection String**:
   - Go to **Project Settings** → **Database** → **Connection string**.
   - Select **URI** (or Transaction Pooler mode on port 6543).
   - Copy the URI and replace `[YOUR-PASSWORD]` with your real database password.

---

## 8. Cloud Deployment: Vercel Setup

1. **Push to GitHub**:
   - Push your code to your private/public GitHub repository.
2. **Import into Vercel**:
   - Go to [Vercel](https://vercel.com/) and click **Add New** → **Project**.
   - Select your GitHub repository.
   - Framework Preset: **Other** (Root directory: `./`).
3. **Configure Environment Variables**:
   Under **Environment Variables**, add:
   - `SECRET_KEY`: `<your-secure-random-secret>`
   - `DATABASE_URL`: `<your-supabase-connection-string>`
   - `APP_ENV`: `production`
   - `FLASK_ENV`: `production`
4. **Deploy**:
   - Click **Deploy**. Vercel will build and assign a public `https://<your-project>.vercel.app` URL.
5. **Verify Health**:
   - Visit `https://<your-project>.vercel.app/health` in your browser.
   - You should receive `{"database": "connected", "status": "ok"}`.

---

## 9. Automated Testing Suite

The repository includes comprehensive unit, integration, and production readiness tests:

```bash
# Run all test suites
python -m unittest discover tests

# Run specific production readiness verification
python -m unittest tests.test_production_readiness

# Run database adapter translation tests
python -m unittest tests.test_db_adapter
```

All test suites verify:
- Complete auth lifecycle (Signup, Login, Logout)
- Safe resume stream parsing (PDF, DOCX, TXT)
- 4 Progressive Career Recommendation States
- Multi-user data isolation (Students A, B, C)
- Skill Swap verified matching rules & self-match prevention
- Deduplicated point transactions & anti-exploit protection
- Admin role authorization & 403 enforcement
- Cryptographic SHA-256 verification ledger checks
- Production health check endpoint (`/health`)

---

## 10. Security & Privacy Notes

- **Password Hashing**: Passwords are never stored in plaintext; hashed with Werkzeug pbkdf2/scrypt.
- **Session Protection**: Cookies use `HttpOnly`, `SameSite=Lax`, and `Secure` flags in production.
- **Database Access**: Direct database credentials are kept strictly server-side; frontend JavaScript never receives database connection tokens.
- **Privacy-Conscious GIS**: Leaflet map displays approximate campus coordinate zones (±500m cluster); precise home GPS coordinates are never stored or exposed.
- **Input Sanitization**: File uploads validate file extensions, stream MIME signatures, and enforce a 5 MB maximum limit.
- **Cryptographic Immutability**: Verification IDs and certificate hashes are generated via SHA-256 for tamper-evident credentials.
