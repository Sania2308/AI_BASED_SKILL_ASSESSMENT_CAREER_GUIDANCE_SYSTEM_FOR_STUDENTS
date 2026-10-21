from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "skillguide-development-key-change-this"
DB = "skillguide.db"

SKILLS = [
    "Python", "SQL", "Excel", "Machine Learning", "Data Analysis",
    "Power BI", "Data Visualization", "Statistics", "Java", "JavaScript",
    "HTML", "CSS", "Communication", "Problem Solving", "Teamwork",
    "C", "C++", "C#", "R", "Tableau", "Deep Learning", "NLP",
    "Flask", "Django", "Git", "GitHub", "MongoDB", "MySQL", "Leadership"
]

CAREERS = [
    {"name": "Data Analyst", "match": 85},
    {"name": "Data Scientist", "match": 75},
    {"name": "Business Analyst", "match": 70},
    {"name": "ML Engineer", "match": 65}
]

TECHNICAL_SKILLS = [
    "Python", "SQL", "Java", "JavaScript", "HTML", "CSS", "C", "C++",
    "C#", "R", "Excel", "Power BI", "Tableau", "Machine Learning",
    "Data Analysis", "Data Visualization", "Statistics", "Deep Learning",
    "NLP", "Flask", "Django", "Git", "GitHub", "MongoDB", "MySQL"
]

TECHNICAL_QUESTIONS = {
    "Python": [
        ("Which keyword is used to define a function in Python?", ["func", "define", "def", "function"], 2),
        ("Which data type stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set"], 2),
        ("What does len([1,2,3]) return?", ["2", "3", "4", "Error"], 1),
        ("Which concept lets a class inherit from another class?", ["Encapsulation", "Inheritance", "Iteration", "Compilation"], 1),
        ("Which Python feature produces values lazily?", ["Generator", "Comment", "Decorator", "Module"], 0),
        ("What is the purpose of try/except?", ["Looping", "Exception handling", "Importing", "Sorting"], 1),
        ("Which symbol starts a list comprehension expression?", ["{", "(", "[", "<"], 2),
        ("What does a decorator commonly modify?", ["Function/class behavior", "Database schema", "CPU", "File system"], 0),
        ("Which structure follows LIFO?", ["Queue", "Stack", "Graph", "Tree"], 1),
        ("Which library is commonly used for tabular data analysis?", ["Pandas", "Flask", "Tkinter", "Requests"], 0)
    ],
    "SQL": [
        ("Which command retrieves data from a table?", ["GET", "SELECT", "FETCHALL", "READ"], 1),
        ("Which clause filters rows?", ["ORDER BY", "GROUP BY", "WHERE", "JOIN"], 2),
        ("Which command adds a new row?", ["ADD", "INSERT", "CREATE", "APPEND"], 1),
        ("Which key uniquely identifies a row?", ["Foreign key", "Primary key", "Index", "View"], 1),
        ("Which join returns matching rows from both tables?", ["INNER JOIN", "CROSS JOIN", "FULL JOIN", "SELF JOIN"], 0),
        ("Which function counts rows?", ["SUM", "COUNT", "ROWS", "TOTAL"], 1),
        ("Which clause groups rows for aggregate functions?", ["GROUP BY", "ORDER BY", "HAVING", "WHERE"], 0),
        ("Which command changes existing rows?", ["CHANGE", "UPDATE", "MODIFY", "ALTER"], 1),
        ("Which clause filters grouped results?", ["WHERE", "HAVING", "FILTER", "GROUP"], 1),
        ("Which normal form removes partial dependency?", ["1NF", "2NF", "3NF", "BCNF"], 1)
    ],
    "Java": [
        ("Which keyword creates an object?", ["class", "new", "this", "object"], 1),
        ("Which method is the entry point of a Java program?", ["start()", "run()", "main()", "init()"], 2),
        ("Which concept allows one interface with multiple implementations?", ["Polymorphism", "Parsing", "Iteration", "Casting"], 0),
        ("Which collection does not allow duplicate elements?", ["List", "Set", "ArrayList", "Vector"], 1),
        ("Which keyword prevents inheritance?", ["static", "final", "private", "const"], 1),
        ("What handles runtime exceptions?", ["try/catch", "switch", "package", "import"], 0),
        ("Which feature allows a class to implement multiple interfaces?", ["Multiple inheritance through classes", "Interfaces", "Packages", "Threads"], 1),
        ("Which structure stores key-value pairs?", ["HashMap", "ArrayList", "Stack", "Queue"], 0),
        ("Which keyword refers to the current object?", ["self", "this", "current", "super"], 1),
        ("Which JVM component executes bytecode?", ["Compiler", "JVM", "JDK", "Editor"], 1)
    ],
    "JavaScript": [
        ("Which keyword declares a block-scoped variable?", ["var", "let", "define", "dim"], 1),
        ("Which method converts JSON text into an object?", ["JSON.parse", "JSON.object", "JSON.read", "JSON.convert"], 0),
        ("Which symbol is commonly used for an arrow function?", ["=>", "->", "::", "==>"], 0),
        ("Which API selects an element by id?", ["getElementById", "queryId", "selectId", "findId"], 0),
        ("What is an array used for?", ["Storing ordered values", "Only strings", "Only functions", "CSS styling"], 0),
        ("What does === compare?", ["Only type", "Only value", "Value and type", "References only"], 2),
        ("Which feature handles asynchronous completion?", ["Promises", "Loops", "Classes", "Selectors"], 0),
        ("Which keyword creates a constant binding?", ["fixed", "constant", "const", "static"], 2),
        ("What does addEventListener do?", ["Adds an event handler", "Creates CSS", "Loads SQL", "Compiles code"], 0),
        ("Which method creates a new array by transforming elements?", ["map", "push", "join", "sort"], 0)
    ],
    "HTML": [
        ("What does HTML stand for?", ["HyperText Markup Language", "HighText Machine Language", "Hyperlink Text Management Language", "Home Tool Markup Language"], 0),
        ("Which tag creates a hyperlink?", ["<link>", "<a>", "<href>", "<url>"], 1),
        ("Which tag represents the largest heading?", ["<h6>", "<head>", "<h1>", "<title>"], 2),
        ("Which attribute provides alternative text for an image?", ["src", "alt", "title", "href"], 1),
        ("Which element creates a numbered list?", ["<ul>", "<ol>", "<li>", "<list>"], 1),
        ("Which element is used for a form?", ["<form>", "<input>", "<data>", "<submit>"], 0),
        ("Which semantic element represents navigation?", ["<nav>", "<navigate>", "<menuitem>", "<links>"], 0),
        ("Which attribute uniquely identifies an element?", ["class", "id", "name", "key"], 1),
        ("Which tag embeds an image?", ["<picture>", "<img>", "<image>", "<src>"], 1),
        ("Which declaration defines the HTML5 document type?", ["<html5>", "<!DOCTYPE html>", "<doctype>", "<document>"], 1)
    ]
}

QUESTIONS = [
    {"id": 1, "category": "Technical Skills", "text": "How comfortable are you with programming or technical tools?"},
    {"id": 2, "category": "Technical Skills", "text": "How well can you write and understand SQL or database queries?"},
    {"id": 3, "category": "Technical Skills", "text": "How comfortable are you with data analysis tools such as Excel, Python or Power BI?"},
    {"id": 4, "category": "Problem Solving", "text": "How confidently can you break a complex problem into smaller steps?"},
    {"id": 5, "category": "Problem Solving", "text": "How well can you identify errors and find solutions?"},
    {"id": 6, "category": "Communication", "text": "How confidently can you explain technical ideas to others?"},
    {"id": 7, "category": "Communication", "text": "How well do you communicate your project results?"},
    {"id": 8, "category": "Domain Knowledge", "text": "How strong is your understanding of your chosen technical domain?"},
    {"id": 9, "category": "Domain Knowledge", "text": "How well can you apply concepts to a real-world project?"},
    {"id": 10, "category": "Domain Knowledge", "text": "How comfortable are you learning a new technology when required?"}
]

OPTIONS = [
    ("1", "Beginner"),
    ("2", "Basic"),
    ("3", "Intermediate"),
    ("4", "Advanced"),
    ("5", "Expert")
]


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            bio TEXT DEFAULT '',
            course TEXT DEFAULT 'Computer Science',
            year TEXT DEFAULT '3rd Year',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            overall INTEGER NOT NULL,
            technical INTEGER NOT NULL,
            problem_solving INTEGER NOT NULL,
            communication INTEGER NOT NULL,
            domain_knowledge INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            taken_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS extracted_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            UNIQUE(user_id, skill),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS learning_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            UNIQUE(user_id, skill),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS skill_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            score INTEGER NOT NULL,
            level TEXT NOT NULL,
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            taken_at TEXT NOT NULL,
            UNIQUE(user_id, skill),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def logged_in():
    return current_user() is not None


def extract_skills(text):
    """Simple transparent NLP prototype: normalize text and match a controlled skill vocabulary."""
    text = re.sub(r"[^a-zA-Z0-9+#.\- ]", " ", text.lower())
    found = []
    for skill in SKILLS:
        pattern = re.escape(skill.lower())
        if re.search(r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])", text):
            found.append(skill)
    return found


def save_skills(user_id, skills):
    conn = db()
    for skill in skills:
        conn.execute("INSERT OR IGNORE INTO extracted_skills(user_id, skill) VALUES (?, ?)", (user_id, skill))
    conn.commit()
    conn.close()


def get_skills(user_id):
    conn = db()
    rows = conn.execute("SELECT skill FROM extracted_skills WHERE user_id = ? ORDER BY skill", (user_id,)).fetchall()
    conn.close()
    return [r["skill"] for r in rows]


def get_learning_skills(user_id):
    conn = db()
    rows = conn.execute("SELECT skill FROM learning_skills WHERE user_id = ? ORDER BY skill", (user_id,)).fetchall()
    conn.close()
    return [r["skill"] for r in rows]


def save_learning_skills(user_id, skills):
    conn = db()
    for skill in skills:
        conn.execute("INSERT OR IGNORE INTO learning_skills(user_id, skill) VALUES (?, ?)", (user_id, skill))
    conn.commit()
    conn.close()


def get_verified_skills(user_id):
    conn = db()
    rows = conn.execute("SELECT skill, score, level, correct, total FROM skill_assessments WHERE user_id = ? ORDER BY skill", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_verified_skill_map(user_id):
    return {r["skill"]: r for r in get_verified_skills(user_id)}

def proficiency_level(score):
    if score >= 90:
        return "Expert"
    if score >= 70:
        return "Advanced"
    if score >= 40:
        return "Intermediate"
    return "Beginner"

def get_peer_matches(user_id):
    my_learning = set(get_learning_skills(user_id))
    if not my_learning:
        return []
    conn = db()
    users = conn.execute("SELECT id, name FROM users WHERE id != ? ORDER BY name", (user_id,)).fetchall()
    matches = []
    my_teach = set(get_verified_skill_map(user_id))
    for u in users:
        verified = get_verified_skill_map(u["id"])
        teach = set(verified)
        other_learning = set(get_learning_skills(u["id"]))
        overlap = sorted(my_learning & teach)
        if not overlap:
            continue
        mutual = sorted(my_teach & other_learning)
        match = round((len(overlap) / len(my_learning)) * 100)
        if mutual:
            match = min(100, match + 20)
        matched_details = [{"skill": s, "score": verified[s]["score"], "level": verified[s]["level"]} for s in overlap]
        matches.append({"name": u["name"], "match": match, "teach": matched_details, "learn": sorted(other_learning)})
    conn.close()
    return sorted(matches, key=lambda x: x["match"], reverse=True)[:6]


def get_latest_assessment(user_id):
    conn = db()
    row = conn.execute(
        "SELECT * FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"overall": 0, "technical": 0, "problem_solving": 0, "communication": 0, "domain_knowledge": 0, "correct": 0, "total": 10}


def get_careers(assessment, skills):
    score = assessment["overall"]
    skillset = {s.lower() for s in skills}
    data = []
    data.append({"name": "Data Analyst", "match": min(99, max(45, score + (10 if {"python", "sql", "data analysis"} & skillset else 0)))})
    data.append({"name": "Data Scientist", "match": min(97, max(40, score - 2 + (12 if {"python", "machine learning", "statistics"} & skillset else 0)))})
    data.append({"name": "Business Analyst", "match": min(95, max(40, score - 5 + (10 if {"excel", "communication"} & skillset else 0)))})
    data.append({"name": "ML Engineer", "match": min(96, max(35, score - 8 + (15 if {"python", "machine learning", "deep learning"} & skillset else 0)))})
    return data


@app.route("/")
def index():
    if not logged_in():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        error = "Invalid email or password."
    return render_template("auth.html", mode="login", error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not email or not password:
            error = "Please fill in all fields."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            conn = db()
            try:
                cur = conn.execute(
                    "INSERT INTO users(name,email,password_hash,created_at) VALUES (?,?,?,?)",
                    (name, email, generate_password_hash(password), datetime.now().isoformat(timespec="seconds"))
                )
                conn.commit()
                user_id = cur.lastrowid
                session.clear()
                session["user_id"] = user_id
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                error = "An account with this email already exists."
            finally:
                conn.close()
    return render_template("auth.html", mode="signup", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    assessment = get_latest_assessment(user["id"])
    skills = get_skills(user["id"])
    careers = get_careers(assessment, skills)
    return render_template("dashboard.html", page="dashboard", user=user, assessment=assessment, skills=skills, careers=careers)


@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    latest = get_latest_assessment(user["id"])
    return render_template("assessment.html", page="assessment", user=user, questions=QUESTIONS, options=OPTIONS, latest=latest, saved_skills=get_skills(user["id"]), technical_skills=TECHNICAL_SKILLS, verified_skills=get_verified_skills(user["id"]), technical_assessment_skills=list(TECHNICAL_QUESTIONS.keys()))


@app.route("/career")
def career():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    assessment_data = get_latest_assessment(user["id"])
    skills = get_skills(user["id"])
    return render_template("career.html", page="career", user=user, careers=get_careers(assessment_data, skills), assessment=assessment_data, skills=skills)


@app.route("/skill-swap")
def skill_swap():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("skill_swap.html", page="skill-swap", user=user, skills=get_skills(user["id"]), verified_skills=get_verified_skills(user["id"]), learning_skills=get_learning_skills(user["id"]), peer_matches=get_peer_matches(user["id"]))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    message = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        course = request.form.get("course", "").strip()
        year = request.form.get("year", "").strip()
        bio = request.form.get("bio", "").strip()
        if not name or not email:
            message = "Name and email are required."
        else:
            conn = db()
            try:
                conn.execute(
                    "UPDATE users SET name=?, email=?, course=?, year=?, bio=? WHERE id=?",
                    (name, email, course, year, bio, user["id"])
                )
                conn.commit()
                message = "Profile updated successfully."
            except sqlite3.IntegrityError:
                message = "That email is already used by another account."
            finally:
                conn.close()
            user = current_user()
    return render_template("profile.html", page="profile", user=user, message=message, skills=get_skills(user["id"]))


@app.post("/api/extract-skills")
def api_extract_skills():
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    text = request.form.get("text", "")
    skills = extract_skills(text)
    save_skills(user["id"], skills)
    return jsonify({"skills": skills, "all_skills": get_skills(user["id"])})


@app.post("/api/assessment")
def api_assessment():
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})
    values = []
    category_values = {"Technical Skills": [], "Problem Solving": [], "Communication": [], "Domain Knowledge": []}
    for q in QUESTIONS:
        raw = answers.get(str(q["id"]))
        try:
            value = int(raw)
            if value < 1 or value > 5:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": f"Please answer question {q['id']}."}), 400
        values.append(value)
        category_values[q["category"]].append(value)
    overall = round((sum(values) / (len(values) * 5)) * 100)
    scores = {k: round((sum(v) / (len(v) * 5)) * 100) for k, v in category_values.items()}
    correct = round(overall / 10)
    conn = db()
    conn.execute(
        "INSERT INTO assessments(user_id,overall,technical,problem_solving,communication,domain_knowledge,correct,total,taken_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (user["id"], overall, scores["Technical Skills"], scores["Problem Solving"], scores["Communication"], scores["Domain Knowledge"], correct, 10, datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()
    return jsonify({"score": overall, "categories": scores, "correct": correct, "total": 10, "message": "Assessment saved successfully."})


@app.get("/api/technical-assessment/<skill>")
def api_technical_questions(skill):
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    canonical = {s.lower(): s for s in TECHNICAL_QUESTIONS}
    key = canonical.get(skill.strip().lower())
    if not key:
        return jsonify({"error": "No assessment is available for this technical skill yet."}), 404
    questions = []
    for i, (text, options, _) in enumerate(TECHNICAL_QUESTIONS[key], 1):
        questions.append({"id": i, "text": text, "options": options})
    return jsonify({"skill": key, "questions": questions})


@app.post("/api/technical-assessment/<skill>")
def api_submit_technical_assessment(skill):
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    canonical = {s.lower(): s for s in TECHNICAL_QUESTIONS}
    key = canonical.get(skill.strip().lower())
    if not key:
        return jsonify({"error": "No assessment is available for this technical skill yet."}), 404
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})
    questions = TECHNICAL_QUESTIONS[key]
    correct = 0
    for i, (_, options, answer_index) in enumerate(questions, 1):
        raw = answers.get(str(i))
        try:
            selected = int(raw)
        except (TypeError, ValueError):
            return jsonify({"error": f"Please answer question {i}."}), 400
        if selected < 0 or selected >= len(options):
            return jsonify({"error": f"Invalid answer for question {i}."}), 400
        if selected == answer_index:
            correct += 1
    total = len(questions)
    score = round(correct / total * 100)
    level = proficiency_level(score)
    conn = db()
    conn.execute(
        "INSERT INTO skill_assessments(user_id,skill,score,level,correct,total,taken_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(user_id,skill) DO UPDATE SET score=excluded.score, level=excluded.level, correct=excluded.correct, total=excluded.total, taken_at=excluded.taken_at",
        (user["id"], key, score, level, correct, total, datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()
    return jsonify({"skill": key, "score": score, "level": level, "correct": correct, "total": total, "message": f"{key} assessment completed."})


@app.get("/api/verified-skills")
def api_verified_skills():
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    return jsonify({"skills": get_verified_skills(user["id"])})


@app.post("/api/learning-skills")
def api_learning_skills():
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    data = request.get_json(silent=True) or {}
    raw = data.get("skills", "")
    if isinstance(raw, list):
        requested = raw
    else:
        requested = re.split(r"[,\n]+", str(raw))
    canonical = {s.lower(): s for s in SKILLS}
    selected = []
    for item in requested:
        key = str(item).strip().lower()
        if key in canonical and canonical[key] not in selected:
            selected.append(canonical[key])
    if not selected:
        return jsonify({"error": "Enter at least one supported skill.", "supported": SKILLS}), 400
    save_learning_skills(user["id"], selected)
    return jsonify({"skills": get_learning_skills(user["id"]), "matches": get_peer_matches(user["id"])})


@app.post("/api/reset-learning-skills")
def reset_learning_skills():
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    conn = db()
    conn.execute("DELETE FROM learning_skills WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return jsonify({"skills": []})


@app.post("/api/reset-skills")
def reset_skills():
    user = current_user()
    if not user:
        return jsonify({"error": "Login required"}), 401
    conn = db()
    conn.execute("DELETE FROM extracted_skills WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return jsonify({"skills": []})


init_db()

if __name__ == "__main__":
    app.run(debug=True)
