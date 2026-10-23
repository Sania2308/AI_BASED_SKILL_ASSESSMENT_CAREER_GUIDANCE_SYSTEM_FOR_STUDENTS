import os
import tempfile

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    BASE_DIR = BASE_DIR

    # Environment mode
    APP_ENV = os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "development"
    IS_PRODUCTION = APP_ENV.lower() in ("production", "prod") or bool(os.environ.get("VERCEL"))

    # Secret key for session security
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("SKILLGUIDE_SECRET_KEY") or "skillguide-dev-secret-key-2026-v2"

    # Database: Supabase PostgreSQL in production or local SQLite fallback
    DATABASE_URL = os.environ.get("DATABASE_URL")
    DATABASE = os.environ.get("SKILLGUIDE_DB", os.path.join(BASE_DIR, "skillguide.db"))

    # Production-safe session cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_SAMESITE = "Lax"

    # Upload configuration (use /tmp on serverless/read-only filesystems)
    if os.environ.get("VERCEL") or not os.access(BASE_DIR, os.W_OK):
        UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "skillguide_uploads")
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# Comprehensive categorized skill dictionary
SKILL_TAXONOMY = {
    "Programming": [
        "Python", "Java", "C", "C++", "C#", "R", "Go", "Rust", "PHP", "Ruby"
    ],
    "Web Development": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Angular", "Vue",
        "Node.js", "Flask", "Django", "FastAPI", "Bootstrap", "Tailwind"
    ],
    "Databases": [
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "Redis"
    ],
    "Analytics & AI": [
        "Excel", "Power BI", "Tableau", "Data Analysis", "Machine Learning",
        "Deep Learning", "NLP", "Statistics", "Data Visualization", "Pandas",
        "NumPy", "Scikit-Learn", "TensorFlow", "Keras"
    ],
    "Cloud & DevOps": [
        "Git", "GitHub", "Docker", "Kubernetes", "Linux", "AWS", "Azure",
        "GCP", "CI/CD", "DevOps"
    ],
    "Cybersecurity": [
        "Network Security", "Cryptography", "Ethical Hacking", "Linux Security", "Penetration Testing"
    ],
    "Soft Skills": [
        "Communication", "Problem Solving", "Teamwork", "Leadership",
        "Critical Thinking", "Time Management", "Adaptability"
    ]
}

# Flattened set of all recognized skills for fast lookup
ALL_SKILLS = []
SKILL_TO_CATEGORY = {}
for cat, skills in SKILL_TAXONOMY.items():
    for s in skills:
        ALL_SKILLS.append(s)
        SKILL_TO_CATEGORY[s.lower()] = cat

# Careers catalog (13 comprehensive career tracks)
CAREER_CATALOG = {
    "Data Analyst": {
        "title": "Data Analyst",
        "category": "Data & Analytics",
        "icon": "bi-bar-chart-line",
        "description": "Transforms structured data into actionable business insights through queries, statistics, and dashboards.",
        "core_skills": ["SQL", "Excel", "Data Analysis", "Python", "Power BI", "Tableau", "Statistics", "Data Visualization"],
        "recommended_min_technical": 50,
        "ideal_strengths": ["Domain Knowledge", "Problem Solving"]
    },
    "Data Scientist": {
        "title": "Data Scientist",
        "category": "Data & Analytics",
        "icon": "bi-diagram-3",
        "description": "Applies statistical modeling, machine learning, and data pipelines to solve complex predictive problems.",
        "core_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Analysis", "Pandas", "Data Visualization", "Deep Learning"],
        "recommended_min_technical": 65,
        "ideal_strengths": ["Problem Solving", "Technical Skills"]
    },
    "Machine Learning Engineer": {
        "title": "Machine Learning Engineer",
        "category": "Artificial Intelligence",
        "icon": "bi-cpu",
        "description": "Designs, trains, deploys, and optimizes production-ready machine learning and deep learning models.",
        "core_skills": ["Python", "Machine Learning", "Deep Learning", "NumPy", "Pandas", "Scikit-Learn", "Git", "Docker"],
        "recommended_min_technical": 70,
        "ideal_strengths": ["Technical Skills", "Problem Solving"]
    },
    "AI Engineer": {
        "title": "AI Engineer",
        "category": "Artificial Intelligence",
        "icon": "bi-robot",
        "description": "Builds intelligent agents, natural language processing pipelines, and generative AI systems.",
        "core_skills": ["Python", "Machine Learning", "NLP", "Deep Learning", "Data Analysis", "Git", "Flask", "Docker"],
        "recommended_min_technical": 70,
        "ideal_strengths": ["Technical Skills", "Learning Ability"]
    },
    "Software Developer": {
        "title": "Software Developer",
        "category": "Software Engineering",
        "icon": "bi-code-slash",
        "description": "Engineers reliable, maintainable software systems and applications using object-oriented principles.",
        "core_skills": ["Java", "Python", "C++", "C", "SQL", "Git", "Problem Solving", "GitHub"],
        "recommended_min_technical": 60,
        "ideal_strengths": ["Problem Solving", "Technical Skills"]
    },
    "Frontend Developer": {
        "title": "Frontend Developer",
        "category": "Web Development",
        "icon": "bi-window-sidebar",
        "description": "Crafts responsive, engaging, and accessible user interfaces and web applications.",
        "core_skills": ["HTML", "CSS", "JavaScript", "React", "Bootstrap", "Git", "TypeScript"],
        "recommended_min_technical": 55,
        "ideal_strengths": ["Communication", "Technical Skills"]
    },
    "Backend Developer": {
        "title": "Backend Developer",
        "category": "Web Development",
        "icon": "bi-hdd-network",
        "description": "Builds robust server-side APIs, database schemas, and microservices powering web applications.",
        "core_skills": ["Python", "Java", "SQL", "Flask", "Django", "Node.js", "Git", "PostgreSQL"],
        "recommended_min_technical": 65,
        "ideal_strengths": ["Technical Skills", "Problem Solving"]
    },
    "Full Stack Developer": {
        "title": "Full Stack Developer",
        "category": "Web Development",
        "icon": "bi-layers-half",
        "description": "Bridges frontend interfaces and backend infrastructure to deliver complete end-to-end applications.",
        "core_skills": ["HTML", "CSS", "JavaScript", "Python", "SQL", "React", "Node.js", "Git", "Flask"],
        "recommended_min_technical": 70,
        "ideal_strengths": ["Technical Skills", "Problem Solving", "Learning Ability"]
    },
    "Business Analyst": {
        "title": "Business Analyst",
        "category": "Business & Strategy",
        "icon": "bi-graph-up-arrow",
        "description": "Translates business requirements into technical specifications, workflows, and analytical dashboards.",
        "core_skills": ["Excel", "Communication", "Problem Solving", "Power BI", "SQL", "Data Analysis", "Leadership"],
        "recommended_min_technical": 45,
        "ideal_strengths": ["Communication", "Domain Knowledge"]
    },
    "Cloud Engineer": {
        "title": "Cloud Engineer",
        "category": "Cloud & Infrastructure",
        "icon": "bi-cloud-check",
        "description": "Architects, provisions, and manages secure, scalable infrastructure across major cloud providers.",
        "core_skills": ["Linux", "AWS", "Azure", "Docker", "Git", "Python", "Kubernetes", "DevOps"],
        "recommended_min_technical": 65,
        "ideal_strengths": ["Technical Skills", "Problem Solving"]
    },
    "DevOps Engineer": {
        "title": "DevOps Engineer",
        "category": "Cloud & Infrastructure",
        "icon": "bi-gear-wide-connected",
        "description": "Automates continuous integration, deployment pipelines, containerization, and system observability.",
        "core_skills": ["Docker", "Kubernetes", "Git", "Linux", "CI/CD", "Python", "AWS"],
        "recommended_min_technical": 70,
        "ideal_strengths": ["Technical Skills", "Problem Solving"]
    },
    "Database Administrator": {
        "title": "Database Administrator",
        "category": "Data & Infrastructure",
        "icon": "bi-database-fill-gear",
        "description": "Maintains database integrity, performance optimization, indexing, backups, and security access.",
        "core_skills": ["SQL", "MySQL", "PostgreSQL", "MongoDB", "Linux", "Problem Solving", "Database Administrator"],
        "recommended_min_technical": 65,
        "ideal_strengths": ["Technical Skills", "Domain Knowledge"]
    },
    "Cybersecurity Analyst": {
        "title": "Cybersecurity Analyst",
        "category": "Security",
        "icon": "bi-shield-lock",
        "description": "Protects organizational infrastructure, audits system vulnerabilities, and mitigates security threats.",
        "core_skills": ["Linux", "Network Security", "Cryptography", "Python", "Problem Solving", "Ethical Hacking"],
        "recommended_min_technical": 65,
        "ideal_strengths": ["Problem Solving", "Technical Skills"]
    }
}

# Learning Resources catalog for missing skills
LEARNING_RESOURCES = {
    "Python": [
        {"name": "Python for Everybody", "provider": "Coursera / Univ of Michigan", "level": "Beginner", "type": "Courses", "link": "https://www.coursera.org/specializations/python"},
        {"name": "Official Python 3 Docs & Tutorial", "provider": "Python Software Foundation", "level": "All Levels", "type": "Documentation", "link": "https://docs.python.org/3/tutorial/"},
        {"name": "LeetCode Python Problem Set", "provider": "LeetCode", "level": "Intermediate", "type": "Practice", "link": "https://leetcode.com/problemset/all/"},
        {"name": "Build 10 Python Automation Projects", "provider": "freeCodeCamp", "level": "Hands-on", "type": "Projects", "link": "https://www.freecodecamp.org/news/python-projects-for-beginners/"}
    ],
    "SQL": [
        {"name": "SQL for Data Science", "provider": "Coursera / UC Davis", "level": "Beginner", "type": "Courses", "link": "https://www.coursera.org/learn/sql-for-data-science"},
        {"name": "PostgreSQL Official Documentation", "provider": "PostgreSQL Global Dev Group", "level": "All Levels", "type": "Documentation", "link": "https://www.postgresql.org/docs/"},
        {"name": "SQLZoo Interactive Exercises", "provider": "SQLZoo", "level": "Beginner to Intermediate", "type": "Practice", "link": "https://sqlzoo.net/"},
        {"name": "E-Commerce Database Schema Design", "provider": "GitHub Projects", "level": "Advanced", "type": "Projects", "link": "https://github.com/topics/sql-project"}
    ],
    "Java": [
        {"name": "Java Programming Masterclass", "provider": "Udemy", "level": "Beginner to Advanced", "type": "Courses", "link": "https://dev.java/learn/"},
        {"name": "Oracle Java Documentation", "provider": "Oracle", "level": "Reference", "type": "Documentation", "link": "https://docs.oracle.com/en/java/"},
        {"name": "HackerRank Java Track", "provider": "HackerRank", "level": "Practice", "type": "Practice", "link": "https://www.hackerrank.com/domains/java"},
        {"name": "Student Management System in Java", "provider": "Open Source", "level": "Hands-on", "type": "Projects", "link": "https://github.com/topics/java-project"}
    ],
    "JavaScript": [
        {"name": "The Modern JavaScript Tutorial", "provider": "javascript.info", "level": "Beginner to Advanced", "type": "Documentation", "link": "https://javascript.info/"},
        {"name": "MDN Web Docs: JavaScript", "provider": "Mozilla Developer Network", "level": "Reference", "type": "Documentation", "link": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
        {"name": "30 Days of JavaScript", "provider": "LeetCode", "level": "Intermediate", "type": "Practice", "link": "https://leetcode.com/studyplan/30-days-of-javascript/"},
        {"name": "Interactive Web App Portfolio", "provider": "freeCodeCamp", "level": "Hands-on", "type": "Projects", "link": "https://www.freecodecamp.org/"}
    ],
    "HTML": [
        {"name": "HTML5 & Web Fundamentals", "provider": "W3Schools / MDN", "level": "Beginner", "type": "Courses", "link": "https://developer.mozilla.org/en-US/docs/Learn/HTML"},
        {"name": "HTML Living Standard Reference", "provider": "WHATWG", "level": "Reference", "type": "Documentation", "link": "https://html.spec.whatwg.org/"},
        {"name": "Frontend Mentor Challenges", "provider": "Frontend Mentor", "level": "Practice", "type": "Practice", "link": "https://www.frontendmentor.io/"},
        {"name": "Semantic Responsive Landing Page", "provider": "GitHub", "level": "Hands-on", "type": "Projects", "link": "https://github.com/topics/html5-template"}
    ],
    "CSS": [
        {"name": "CSS Grid & Flexbox Mastery", "provider": "CSS-Tricks / MDN", "level": "Intermediate", "type": "Documentation", "link": "https://css-tricks.com/snippets/css/a-guide-to-flexbox/"},
        {"name": "Responsive Web Design Certification", "provider": "freeCodeCamp", "level": "Beginner to Intermediate", "type": "Courses", "link": "https://www.freecodecamp.org/learn/2022/responsive-web-design/"},
        {"name": "CSSBattle Code Golf", "provider": "CSSBattle.dev", "level": "Practice", "type": "Practice", "link": "https://cssbattle.dev/"},
        {"name": "Modern SaaS Landing Page CSS", "provider": "Codepen", "level": "Hands-on", "type": "Projects", "link": "https://codepen.io/"}
    ],
    "C": [
        {"name": "C Programming Language by K&R", "provider": "CS50 Harvard", "level": "Beginner", "type": "Courses", "link": "https://cs50.harvard.edu/x/"},
        {"name": "GNU C Library Manual", "provider": "GNU.org", "level": "Reference", "type": "Documentation", "link": "https://www.gnu.org/software/libc/manual/"},
        {"name": "HackerRank C Challenges", "provider": "HackerRank", "level": "Practice", "type": "Practice", "link": "https://www.hackerrank.com/domains/c"},
        {"name": "Simple Unix Shell in C", "provider": "Stephen Brennan Guide", "level": "Hands-on", "type": "Projects", "link": "https://brennan.io/2015/01/16/write-a-shell-in-c/"}
    ],
    "C++": [
        {"name": "C++ for Programmers", "provider": "learncpp.com", "level": "Beginner to Advanced", "type": "Documentation", "link": "https://www.learncpp.com/"},
        {"name": "C++ Reference Documentation", "provider": "cppreference.com", "level": "Reference", "type": "Documentation", "link": "https://en.cppreference.com/"},
        {"name": "Codeforces Problemset (C++)", "provider": "Codeforces", "level": "Advanced", "type": "Practice", "link": "https://codeforces.com/problemset"},
        {"name": "STL Custom Data Structures", "provider": "GitHub", "level": "Hands-on", "type": "Projects", "link": "https://github.com/topics/cpp-projects"}
    ],
    "Machine Learning": [
        {"name": "Machine Learning Specialization", "provider": "DeepLearning.AI / Stanford (Andrew Ng)", "level": "Intermediate", "type": "Courses", "link": "https://www.coursera.org/specializations/machine-learning-introduction"},
        {"name": "Scikit-Learn Official User Guide", "provider": "Scikit-Learn Consortium", "level": "Reference", "type": "Documentation", "link": "https://scikit-learn.org/stable/user_guide.html"},
        {"name": "Kaggle Competitions & Datasets", "provider": "Kaggle", "level": "Practice", "type": "Practice", "link": "https://www.kaggle.com/competitions"},
        {"name": "End-to-End Housing Price Predictor", "provider": "GitHub ML Repos", "level": "Hands-on", "type": "Projects", "link": "https://github.com/ageron/handson-ml3"}
    ],
    "Data Analysis": [
        {"name": "Google Data Analytics Professional Certificate", "provider": "Google / Coursera", "level": "Beginner", "type": "Courses", "link": "https://www.coursera.org/professional-certificates/google-data-analytics"},
        {"name": "Pandas User Guide & Tutorials", "provider": "Pandas Dev Team", "level": "Reference", "type": "Documentation", "link": "https://pandas.pydata.org/docs/user_guide/index.html"},
        {"name": "Kaggle Micro-courses: Data Analysis", "provider": "Kaggle", "level": "Practice", "type": "Practice", "link": "https://www.kaggle.com/learn"},
        {"name": "COVID-19 Global Trends Dashboard", "provider": "Our World In Data / GitHub", "level": "Hands-on", "type": "Projects", "link": "https://github.com/topics/data-analysis"}
    ],
    "Power BI": [
        {"name": "Microsoft Power BI Data Analyst (PL-300)", "provider": "Microsoft Learn", "level": "Beginner to Advanced", "type": "Courses", "link": "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/"},
        {"name": "Power BI Official Documentation", "provider": "Microsoft", "level": "Reference", "type": "Documentation", "link": "https://learn.microsoft.com/en-us/power-bi/"},
        {"name": "Enterprise Sales Dashboard Build", "provider": "Guy in a Cube", "level": "Hands-on", "type": "Projects", "link": "https://guyinacube.com/"}
    ],
    "Excel": [
        {"name": "Excel Skills for Business", "provider": "Macquarie University / Coursera", "level": "Beginner to Intermediate", "type": "Courses", "link": "https://www.coursera.org/specializations/excel"},
        {"name": "Excel Jet Functions Library", "provider": "ExcelJet", "level": "Reference", "type": "Documentation", "link": "https://exceljet.net/"},
        {"name": "Financial Modeling Template Project", "provider": "Corporate Finance Institute", "level": "Hands-on", "type": "Projects", "link": "https://corporatefinanceinstitute.com/"}
    ],
    "Docker": [
        {"name": "Docker for Developers", "provider": "Docker Official Guides", "level": "Beginner", "type": "Documentation", "link": "https://docs.docker.com/get-started/"},
        {"name": "Full-Stack Containerization Lab", "provider": "Katacoda / Killercoda", "level": "Practice", "type": "Practice", "link": "https://killercoda.com/"}
    ],
    "Git": [
        {"name": "Pro Git Book (Free)", "provider": "Scott Chacon & Ben Straub", "level": "All Levels", "type": "Documentation", "link": "https://git-scm.com/book/en/v2"},
        {"name": "Learn Git Branching (Visual)", "provider": "learnGitBranching", "level": "Practice", "type": "Practice", "link": "https://learngitbranching.js.org/"}
    ]
}

# Default resource fallback if skill is not explicitly mapped
DEFAULT_RESOURCES = [
    {"name": "freeCodeCamp Developer Guides", "provider": "freeCodeCamp", "level": "All Levels", "type": "Courses", "link": "https://www.freecodecamp.org/"},
    {"name": "GeeksforGeeks Computer Science Portal", "provider": "GeeksforGeeks", "level": "Reference", "type": "Documentation", "link": "https://www.geeksforgeeks.org/"},
    {"name": "HackerRank Practice Tracks", "provider": "HackerRank", "level": "Practice", "type": "Practice", "link": "https://www.hackerrank.com/"},
    {"name": "GitHub Student Developer Pack", "provider": "GitHub Education", "level": "Hands-on", "type": "Projects", "link": "https://education.github.com/pack"}
]
