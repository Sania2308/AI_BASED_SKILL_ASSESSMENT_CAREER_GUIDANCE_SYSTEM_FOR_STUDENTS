-- ==============================================================================
-- SkillGuide — Supabase PostgreSQL Production Schema
-- AI-Based Skill Assessment and Career Guidance System for Students
-- ==============================================================================

-- 1. Base Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Overall 5-Domain Assessment Results
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    overall INTEGER NOT NULL,
    technical INTEGER NOT NULL,
    problem_solving INTEGER NOT NULL,
    communication INTEGER NOT NULL,
    domain_knowledge INTEGER NOT NULL,
    learning_ability INTEGER DEFAULT 50,
    correct INTEGER NOT NULL,
    total INTEGER NOT NULL,
    taken_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON assessments(user_id);

-- 3. Assessment History (Full retake and audit trail)
CREATE TABLE IF NOT EXISTS assessment_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_type TEXT NOT NULL,
    score INTEGER NOT NULL,
    level TEXT DEFAULT '',
    correct INTEGER NOT NULL,
    total INTEGER NOT NULL,
    details_json TEXT DEFAULT '{}',
    taken_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_assessment_history_user_id ON assessment_history(user_id);

-- 4. Extracted Skills (Extracted from parsed resume PDF/DOCX/TXT)
CREATE TABLE IF NOT EXISTS extracted_skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    category TEXT DEFAULT 'General',
    source TEXT DEFAULT 'text',
    created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD"T"HH24:MI:SS'),
    CONSTRAINT uq_extracted_skills_user_skill UNIQUE(user_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_extracted_skills_user_id ON extracted_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_extracted_skills_skill ON extracted_skills(skill);

-- 5. Verified Technical Skills (Scores from technical MCQ verification tests)
CREATE TABLE IF NOT EXISTS skill_assessments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    score INTEGER NOT NULL,
    level TEXT NOT NULL,
    correct INTEGER NOT NULL,
    total INTEGER NOT NULL,
    verification_hash TEXT DEFAULT '',
    taken_at TEXT NOT NULL,
    CONSTRAINT uq_skill_assessments_user_skill UNIQUE(user_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_skill_assessments_user_id ON skill_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_skill ON skill_assessments(skill);

-- 6. Learning Skills (Skills student wants to learn for Skill Swap & career prep)
CREATE TABLE IF NOT EXISTS learning_skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    created_at TEXT DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD"T"HH24:MI:SS'),
    CONSTRAINT uq_learning_skills_user_skill UNIQUE(user_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_learning_skills_user_id ON learning_skills(user_id);

-- 7. Career Preferences (Target career role set by student)
CREATE TABLE IF NOT EXISTS career_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    preferred_career TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_career_preferences_user_id ON career_preferences(user_id);

-- 8. Interactive Roadmap Milestone Progress
CREATE TABLE IF NOT EXISTS roadmap_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    career_name TEXT NOT NULL,
    step_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'Course',
    status TEXT DEFAULT 'Not Started',
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_roadmap_progress_user_career_step UNIQUE(user_id, career_name, step_id)
);

CREATE INDEX IF NOT EXISTS idx_roadmap_progress_user_career ON roadmap_progress(user_id, career_name);

-- 9. Peer-to-Peer Skill Swap Requests
CREATE TABLE IF NOT EXISTS skill_swap_requests (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    teach_skill TEXT NOT NULL,
    learn_skill TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_swap_sender ON skill_swap_requests(sender_id);
CREATE INDEX IF NOT EXISTS idx_swap_receiver ON skill_swap_requests(receiver_id);
CREATE INDEX IF NOT EXISTS idx_swap_status ON skill_swap_requests(status);

-- 10. Achievements Badges Catalog
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    points INTEGER DEFAULT 20
);

-- 11. User Unlocked Achievements
CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_code TEXT NOT NULL REFERENCES achievements(code) ON DELETE CASCADE,
    unlocked_at TEXT NOT NULL,
    CONSTRAINT uq_user_achievements_user_code UNIQUE(user_id, achievement_code)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);

-- 12. SHA-256 Cryptographic Verification Ledger Prototype Records
CREATE TABLE IF NOT EXISTS verification_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    record_type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    level TEXT DEFAULT '',
    verification_hash TEXT UNIQUE NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_verification_records_user ON verification_records(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_hash ON verification_records(verification_hash);

-- 13. Gamification Transaction Ledger (Strict Deduplication for Anti-Exploit)
CREATE TABLE IF NOT EXISTS skill_point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_key TEXT NOT NULL,
    reference_id TEXT DEFAULT '',
    points INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_skill_point_transactions UNIQUE(user_id, action_key, reference_id)
);

CREATE INDEX IF NOT EXISTS idx_point_tx_user ON skill_point_transactions(user_id);

-- ==============================================================================
-- Default Achievement Catalog Seeding
-- ==============================================================================
INSERT INTO achievements(code, title, description, icon, points) VALUES
('profile_complete', 'Profile Pioneer', 'Complete your student profile details and bio', 'bi-person-check', 10),
('resume_uploaded', 'Resume Decoder', 'Upload or analyze your resume text via AI/NLP', 'bi-file-earmark-code', 10),
('assessment_master', 'Assessment Master', 'Complete the comprehensive 5-domain skill assessment', 'bi-award', 20),
('python_verified', 'Python Verified', 'Pass the Python technical skill verification test', 'bi-patch-check-fill', 30),
('first_verified_skill', 'Certified Scholar', 'Verify your first technical skill with high proficiency', 'bi-shield-check', 30),
('multi_skilled', 'Polymath', 'Successfully verify 3 or more technical skills', 'bi-gem', 50),
('career_explorer', 'Career Explorer', 'Explore personalized career recommendations and set a career goal', 'bi-compass', 15),
('roadmap_pioneer', 'Roadmap Pioneer', 'Complete a learning roadmap milestone for your target role', 'bi-signpost-split', 10),
('skill_mentor', 'Skill Mentor', 'Create or accept a peer-to-peer skill swap exchange', 'bi-people', 40),
('blockchain_badged', 'Cryptographic Trust', 'Mint a deterministic blockchain-prototype skill certificate', 'bi-link-45deg', 25)
ON CONFLICT (code) DO NOTHING;
