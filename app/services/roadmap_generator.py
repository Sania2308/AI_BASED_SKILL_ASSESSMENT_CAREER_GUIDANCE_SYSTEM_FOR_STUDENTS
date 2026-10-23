from datetime import datetime
from app.config import CAREER_CATALOG, LEARNING_RESOURCES, DEFAULT_RESOURCES

# Dynamic templates for 8-step career roadmaps based on chosen career and missing skills
def generate_default_roadmap_steps(career_name, missing_skills):
    """
    Constructs an 8-stage personalized curriculum tailored to the target role,
    prioritizing the student's identified missing skills.
    """
    config = CAREER_CATALOG.get(career_name, CAREER_CATALOG["Data Analyst"])
    core = config["core_skills"]

    # Select top missing skills or default to top role skills
    primary_missing = missing_skills if missing_skills else core

    s1 = primary_missing[0] if len(primary_missing) > 0 else core[0]
    s2 = primary_missing[1] if len(primary_missing) > 1 else (core[1] if len(core) > 1 else "Database Systems")
    s3 = primary_missing[2] if len(primary_missing) > 2 else (core[2] if len(core) > 2 else "Core Programming")
    s4 = primary_missing[3] if len(primary_missing) > 3 else (core[3] if len(core) > 3 else "Modern Frameworks")

    steps = [
        {
            "step_id": 1,
            "title": f"Foundation Mastery: {s1}",
            "description": f"Master core syntax, foundational principles, and fundamental tooling for {s1}.",
            "category": "Foundations"
        },
        {
            "step_id": 2,
            "title": f"Data Architecture & Querying: {s2}",
            "description": f"Learn relational concepts, data transformation patterns, and query performance with {s2}.",
            "category": "Data & Backend"
        },
        {
            "step_id": 3,
            "title": f"Production Engineering: {s3}",
            "description": f"Apply object-oriented patterns, modular code practices, and clean architecture using {s3}.",
            "category": "Core Development"
        },
        {
            "step_id": 4,
            "title": f"Specialized Tooling & Ecosystem: {s4}",
            "description": f"Deep-dive into industry-standard tooling, libraries, and best practices in {s4}.",
            "category": "Specialization"
        },
        {
            "step_id": 5,
            "title": "System Design & Quality Assurance",
            "description": "Understand testing methodologies, scalability tradeoffs, security baselines, and CI/CD pipelines.",
            "category": "Architecture"
        },
        {
            "step_id": 6,
            "title": "Production Capstone Portfolio Project",
            "description": f"Architect and deploy an end-to-end open-source project showcasing verified {career_name} competencies on GitHub.",
            "category": "Portfolio"
        },
        {
            "step_id": 7,
            "title": "Resume Enhancement & Project Documentation",
            "description": "Craft an ATS-optimized technical resume, articulate project metrics, and document system architecture diagrams.",
            "category": "Career Prep"
        },
        {
            "step_id": 8,
            "title": "Technical Viva & Mock Interview Practice",
            "description": "Complete simulated technical assessments, algorithm problem sets, and behavioral viva preparation.",
            "category": "Interview"
        }
    ]
    return steps


def sync_user_roadmap(db_conn, user_id, career_name, missing_skills):
    """
    Ensures the user has active database records in `roadmap_progress` for the specified career.
    Preserves any existing progress statuses (Completed, In Progress).
    """
    cur = db_conn.cursor()
    # Check existing steps for this user and career
    cur.execute(
        "SELECT step_id, status FROM roadmap_progress WHERE user_id = ? AND career_name = ?",
        (user_id, career_name)
    )
    existing_map = {r["step_id"]: r["status"] for r in cur.fetchall()}

    default_steps = generate_default_roadmap_steps(career_name, missing_skills)
    now = datetime.now().isoformat(timespec="seconds")

    for step in default_steps:
        sid = step["step_id"]
        if sid not in existing_map:
            cur.execute("""
                INSERT INTO roadmap_progress (user_id, career_name, step_id, title, description, category, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'Not Started', ?)
            """, (user_id, career_name, sid, step["title"], step["description"], step["category"], now))

    db_conn.commit()


def get_user_roadmap(db_conn, user_id, career_name):
    """
    Retrieves the 8-step roadmap for a user and calculates completion metrics.
    """
    cur = db_conn.cursor()
    cur.execute("""
        SELECT step_id, title, description, category, status, updated_at
        FROM roadmap_progress
        WHERE user_id = ? AND career_name = ?
        ORDER BY step_id ASC
    """, (user_id, career_name))
    rows = [dict(r) for r in cur.fetchall()]

    completed_count = sum(1 for r in rows if r["status"] == "Completed")
    in_progress_count = sum(1 for r in rows if r["status"] == "In Progress")
    total_steps = len(rows) if rows else 8
    
    completion_pct = round((completed_count / total_steps) * 100) if total_steps > 0 else 0

    return {
        "career_name": career_name,
        "steps": rows,
        "total_steps": total_steps,
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "completion_pct": completion_pct
    }


def get_resources_for_skills(skills_list):
    """
    Gathers curated learning resource cards for missing skills.
    Groups into Courses, Documentation, Practice, Projects.
    """
    resources = []
    seen = set()

    for s in skills_list:
        norm_s = s.strip()
        skill_res = LEARNING_RESOURCES.get(norm_s)
        if not skill_res:
            # Check case-insensitive
            for k, val in LEARNING_RESOURCES.items():
                if k.lower() == norm_s.lower():
                    skill_res = val
                    break

        if skill_res:
            for item in skill_res:
                key = (item["name"], item["provider"])
                if key not in seen:
                    seen.add(key)
                    res_copy = dict(item)
                    res_copy["skill"] = norm_s
                    resources.append(res_copy)

    # If no specific resources found, supply default resources
    if not resources:
        for item in DEFAULT_RESOURCES:
            res_copy = dict(item)
            res_copy["skill"] = "General Engineering"
            resources.append(res_copy)

    return resources
