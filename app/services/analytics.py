from app.config import CAREER_CATALOG

def get_admin_dashboard_metrics(db_conn):
    """
    Computes cohort-level, privacy-conscious institutional analytics for the academic administrator dashboard:
    - Total enrolled students
    - Technical and overall assessments taken
    - Top 10 most common student skills
    - Average competency scores across 5 domains
    - Most targeted career paths
    - Skill gap prevalence across student body
    """
    cur = db_conn.cursor()

    # Total students (excluding admin)
    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    total_students = cur.fetchone()[0]

    # Total overall assessments taken
    cur.execute("SELECT COUNT(*) FROM assessments")
    total_overall_assessments = cur.fetchone()[0]

    # Total technical skill verification tests taken
    cur.execute("SELECT COUNT(*) FROM skill_assessments")
    total_technical_tests = cur.fetchone()[0]

    # Total skill swap requests
    cur.execute("SELECT COUNT(*) FROM skill_swap_requests")
    total_swaps = cur.fetchone()[0]

    # Average competency scores
    cur.execute("""
        SELECT 
            AVG(overall) as avg_overall,
            AVG(technical) as avg_technical,
            AVG(problem_solving) as avg_problem_solving,
            AVG(communication) as avg_communication,
            AVG(domain_knowledge) as avg_domain_knowledge,
            AVG(learning_ability) as avg_learning_ability
        FROM assessments
    """)
    avg_row = cur.fetchone()
    avg_scores = {
        "overall": round(avg_row["avg_overall"] or 0, 1),
        "technical": round(avg_row["avg_technical"] or 0, 1),
        "problem_solving": round(avg_row["avg_problem_solving"] or 0, 1),
        "communication": round(avg_row["avg_communication"] or 0, 1),
        "domain_knowledge": round(avg_row["avg_domain_knowledge"] or 0, 1),
        "learning_ability": round(avg_row["avg_learning_ability"] or 50, 1)
    }

    # Most common extracted skills (Top 10)
    cur.execute("""
        SELECT skill, COUNT(*) as student_count
        FROM extracted_skills
        GROUP BY skill
        ORDER BY student_count DESC, skill ASC
        LIMIT 10
    """)
    common_skills = [dict(r) for r in cur.fetchall()]

    # Most verified technical skills
    cur.execute("""
        SELECT skill, COUNT(*) as count, AVG(score) as avg_score
        FROM skill_assessments
        GROUP BY skill
        ORDER BY count DESC
        LIMIT 8
    """)
    verified_stats = [
        {"skill": r["skill"], "count": r["count"], "avg_score": round(r["avg_score"] or 0, 1)}
        for r in cur.fetchall()
    ]

    # Popular career preferences
    cur.execute("""
        SELECT preferred_career as career, COUNT(*) as count
        FROM career_preferences
        GROUP BY preferred_career
        ORDER BY count DESC
        LIMIT 6
    """)
    popular_careers = [dict(r) for r in cur.fetchall()]

    # Skill gaps across active roadmaps
    cur.execute("""
        SELECT title, COUNT(*) as in_progress_count
        FROM roadmap_progress
        WHERE status IN ('Not Started', 'In Progress')
        GROUP BY title
        ORDER BY in_progress_count DESC
        LIMIT 6
    """)
    gap_trends = [dict(r) for r in cur.fetchall()]

    # Recent student activity feed (privacy safe: only name, action, time)
    cur.execute("""
        SELECT u.name, 'Verified ' || s.skill || ' (' || s.level || ' - ' || s.score || '%)' as activity, s.taken_at as time
        FROM skill_assessments s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.taken_at DESC LIMIT 6
    """)
    recent_activity = [dict(r) for r in cur.fetchall()]

    return {
        "total_students": total_students,
        "total_assessments": total_overall_assessments + total_technical_tests,
        "total_overall_assessments": total_overall_assessments,
        "total_technical_tests": total_technical_tests,
        "total_swaps": total_swaps,
        "avg_scores": avg_scores,
        "common_skills": common_skills,
        "verified_stats": verified_stats,
        "popular_careers": popular_careers,
        "gap_trends": gap_trends,
        "recent_activity": recent_activity
    }
