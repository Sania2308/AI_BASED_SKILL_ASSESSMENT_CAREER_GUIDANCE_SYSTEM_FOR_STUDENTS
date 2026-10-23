from datetime import datetime

# 10 Technical Assessments with 10 questions each
TECHNICAL_QUESTION_BANK = {
    "Python": [
        ("Which keyword is used to define a function in Python?", ["func", "define", "def", "function"], 2),
        ("Which data type stores key-value pairs in Python?", ["List", "Tuple", "Dictionary", "Set"], 2),
        ("What does len([1, 2, 3]) return?", ["2", "3", "4", "Error"], 1),
        ("Which concept allows a class to inherit features from another class?", ["Encapsulation", "Inheritance", "Iteration", "Compilation"], 1),
        ("Which Python feature produces values lazily one at a time?", ["Generator", "Comment", "Decorator", "Module"], 0),
        ("What is the primary purpose of try/except blocks in Python?", ["Looping", "Exception handling", "Package import", "Sorting"], 1),
        ("Which symbol is used for Python list comprehension expressions?", ["{ }", "( )", "[ ]", "< >"], 2),
        ("What does a Python decorator commonly wrap or modify?", ["Function/Class behavior", "Database schema", "Hardware CPU", "Operating system"], 0),
        ("Which built-in module is used for regular expressions?", ["regex_tool", "re", "pyregex", "match"], 1),
        ("Which library is the industry standard for tabular data manipulation?", ["Pandas", "Flask", "Tkinter", "Requests"], 0)
    ],
    "Java": [
        ("Which keyword is used to instantiate an object in Java?", ["class", "new", "this", "object"], 1),
        ("Which method signature serves as the primary entry point of a Java program?", ["start()", "run()", "public static void main(String[] args)", "init()"], 2),
        ("Which OOP concept allows the same interface for different underlying forms?", ["Polymorphism", "Parsing", "Iteration", "Casting"], 0),
        ("Which Java collection does NOT allow duplicate elements?", ["List", "Set", "ArrayList", "Vector"], 1),
        ("Which keyword prevents a Java class or method from being overridden/subclassed?", ["static", "final", "private", "const"], 1),
        ("Which block handles runtime exceptions that may be thrown?", ["try/catch", "switch/case", "package", "import"], 0),
        ("Which interface in Java is commonly used to support multithreading?", ["Runnable", "Serializable", "Comparable", "Cloneable"], 0),
        ("Which collection class stores key-value pairs using hash tables?", ["HashMap", "ArrayList", "Stack", "Queue"], 0),
        ("Which keyword explicitly refers to the current object instance?", ["self", "this", "current", "super"], 1),
        ("Which JVM component translates bytecode into native machine instructions at runtime?", ["JIT Compiler", "JDK Editor", "Garbage Dispatcher", "JAR Archiver"], 0)
    ],
    "SQL": [
        ("Which SQL clause is used to retrieve distinct records?", ["SELECT UNIQUE", "SELECT DISTINCT", "DISTINCT FROM", "FILTER UNIQUE"], 1),
        ("Which clause is used to filter records in an aggregate query after GROUP BY?", ["WHERE", "HAVING", "LIMIT", "FILTER"], 1),
        ("Which SQL statement is used to add new rows into a database table?", ["ADD ROW", "INSERT INTO", "CREATE ROW", "APPEND"], 1),
        ("What type of key enforces entity integrity and uniquely identifies every row?", ["Foreign Key", "Primary Key", "Index Key", "Candidate View"], 1),
        ("Which join returns all matching records from both tables?", ["INNER JOIN", "CROSS JOIN", "FULL OUTER JOIN", "SELF JOIN"], 0),
        ("Which aggregate function returns the total number of non-null rows?", ["SUM()", "COUNT()", "TOTAL()", "ROWS()"], 1),
        ("Which SQL command removes a table structure and all its data permanently?", ["DELETE TABLE", "DROP TABLE", "REMOVE TABLE", "TRUNCATE"], 1),
        ("Which command modifies data in existing rows of a table?", ["CHANGE", "UPDATE", "MODIFY", "ALTER"], 1),
        ("Which property ensures all parts of a transaction succeed or fail together?", ["Atomicity", "Consistency", "Isolation", "Durability"], 0),
        ("Which Normal Form specifically eliminates transitive dependencies?", ["1NF", "2NF", "3NF", "BCNF"], 2)
    ],
    "JavaScript": [
        ("Which keyword declares a reassignable block-scoped variable in modern JS?", ["var", "let", "define", "dim"], 1),
        ("Which method parses a valid JSON string into a JavaScript object?", ["JSON.parse()", "JSON.object()", "JSON.read()", "JSON.decode()"], 0),
        ("Which operator tests equality of both value and data type without coercion?", ["==", "===", "=", "equals()"], 1),
        ("Which DOM method retrieves an element using its unique ID attribute?", ["getElementById()", "queryId()", "selectId()", "findId()"], 0),
        ("Which language feature provides a cleaner syntax for handling asynchronous operations?", ["async/await", "thread.sleep", "while(busy)", "eval()"], 0),
        ("Which array method creates a new array by applying a function to each item?", ["filter()", "map()", "forEach()", "reduce()"], 1),
        ("What is the concept where an inner function retains access to outer variables?", ["Closure", "Hoisting", "Prototype", "Polyfill"], 0),
        ("Which statement creates a read-only, block-scoped reference to a value?", ["fixed", "constant", "const", "static"], 2),
        ("Which method registers an event listener callback on an HTML element?", ["addEventListener()", "bindEvent()", "attachHandler()", "listen()"], 0),
        ("What does `typeof null` evaluate to in standard JavaScript?", ["null", "undefined", "object", "boolean"], 2)
    ],
    "HTML": [
        ("What does HTML stand for?", ["HyperText Markup Language", "HighText Machine Language", "Hyperlink Text Management Language", "Home Tool Markup Language"], 0),
        ("Which HTML element defines a hyperlink anchor?", ["<link>", "<a>", "<href>", "<url>"], 1),
        ("Which tag represents the highest priority, top-level heading?", ["<h6>", "<head>", "<h1>", "<title>"], 2),
        ("Which attribute provides accessible alternative text for assistive screen readers?", ["src", "alt", "title", "caption"], 1),
        ("Which tag wraps an ordered (numbered) list?", ["<ul>", "<ol>", "<li>", "<list>"], 1),
        ("Which semantic element represents introductory or navigational content?", ["<header>", "<div>", "<section>", "<aside>"], 0),
        ("Which element is used to collect user inputs in a structured format?", ["<form>", "<fieldset>", "<input>", "<submit>"], 0),
        ("Which attribute uniquely identifies an element on an entire HTML page?", ["class", "id", "name", "tag"], 1),
        ("Which DOCTYPE declaration correctly specifies the HTML5 standard?", ["<!DOCTYPE html>", "<html5>", "<doctype html5>", "<doctype>"], 0),
        ("Which tag is used to embed client-side JavaScript within an HTML document?", ["<script>", "<javascript>", "<code>", "<js>"], 0)
    ],
    "CSS": [
        ("What does CSS stand for?", ["Cascading Style Sheets", "Creative Style System", "Computer Style Sheets", "Colorful Style System"], 0),
        ("Which CSS property controls the spacing between inside content and its border?", ["margin", "padding", "border-spacing", "gap"], 1),
        ("Which CSS display mode allows 2-dimensional grid layouts?", ["flex", "grid", "inline-block", "table"], 1),
        ("Which CSS selector targets elements with the class 'highlight'?", ["#highlight", ".highlight", "*highlight", "highlight"], 1),
        ("Which CSS property sets the background color of an element?", ["color", "background-color", "bg-color", "surface-color"], 1),
        ("Which value of 'position' positions an element relative to the viewport?", ["relative", "absolute", "fixed", "sticky"], 2),
        ("Which pseudo-class styles an element when the user's cursor hovers over it?", [":focus", ":active", ":hover", ":visited"], 2),
        ("What does CSS 'z-index' control on positioned elements?", ["Horizontal order", "Vertical scale", "Stacking order along the Z-axis", "Zoom level"], 2),
        ("Which modern CSS feature allows queries based on the user's screen width?", ["@media", "@screen", "@device", "@layout"], 0),
        ("Which flexbox property aligns flex items along the main axis?", ["align-items", "justify-content", "align-content", "flex-direction"], 1)
    ],
    "C": [
        ("Which header file is required to use printf() and scanf() in C?", ["<stdlib.h>", "<conio.h>", "<stdio.h>", "<string.h>"], 2),
        ("What operator is used to obtain the memory address of a variable in C?", ["*", "&", "#", "->"], 1),
        ("Which function dynamically allocates uninitialized memory in C?", ["malloc()", "calloc()", "realloc()", "alloc()"], 0),
        ("What is the format specifier for printing an integer in printf?", ["%f", "%c", "%d", "%s"], 2),
        ("What is the index of the first element in a standard C array?", ["-1", "0", "1", "Depends on size"], 1),
        ("Which keyword terminates a loop or switch case prematurely?", ["continue", "break", "return", "exit"], 1),
        ("What character always marks the termination of a string in C?", ["\\n", "\\0", "EOF", ";"], 1),
        ("What operator dereferences a pointer variable to access its value?", ["&", "*", "->", "."], 1),
        ("Which keyword defines a custom user-defined data structure?", ["class", "struct", "record", "typedef_obj"], 1),
        ("What function must be called to release dynamically allocated memory?", ["delete()", "free()", "clear()", "dispose()"], 1)
    ],
    "C++": [
        ("Which stream object in C++ is standard for console output?", ["cin", "cout", "cerr", "print"], 1),
        ("Which feature allows multiple functions with the same name but different parameters?", ["Function Overloading", "Function Overriding", "Dynamic Binding", "Virtualization"], 0),
        ("Which operator allocates dynamic memory on the heap in C++?", ["malloc", "alloc", "new", "create"], 2),
        ("What is a constructor called when an existing object initializes a new one?", ["Default Constructor", "Copy Constructor", "Parameterized Constructor", "Destructor"], 1),
        ("Which access specifier keeps members accessible only to the class and derived classes?", ["public", "private", "protected", "internal"], 2),
        ("What is the Standard Template Library component used for a dynamic array?", ["std::array", "std::vector", "std::list", "std::map"], 1),
        ("Which keyword enables runtime polymorphism for member functions?", ["inline", "static", "virtual", "override"], 2),
        ("What symbol starts a destructor declaration in C++?", ["*", "~", "&", "!"], 1),
        ("What namespace contains the standard C++ library components?", ["std", "core", "sys", "cpp"], 0),
        ("Which C++11 keyword asks the compiler to infer a variable's data type?", ["var", "auto", "infer", "type_of"], 1)
    ],
    "Machine Learning": [
        ("Which type of ML algorithm learns from labeled training data?", ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "Self-Taught"], 0),
        ("Which technique splits data to evaluate model performance on unseen examples?", ["Train/Test Split", "Feature Scaling", "One-Hot Encoding", "Imputation"], 0),
        ("Which algorithm is commonly used for binary or multiclass classification?", ["Linear Regression", "Logistic Regression", "K-Means", "PCA"], 1),
        ("What problem occurs when a model performs extremely well on training data but poorly on test data?", ["Underfitting", "Overfitting", "Convergence", "Data Drift"], 1),
        ("Which metric measures the proportion of true positives among all predicted positives?", ["Recall", "Precision", "F1 Score", "Specificity"], 1),
        ("Which unsupervised learning algorithm groups data points into K clusters?", ["K-Nearest Neighbors", "K-Means", "Decision Trees", "Random Forest"], 1),
        ("What is the purpose of regularisation techniques like L1 (Lasso) and L2 (Ridge)?", ["Speed up training", "Prevent overfitting", "Normalize labels", "Reduce data volume"], 1),
        ("What does gradient descent minimize during model training?", ["Learning Rate", "Loss/Cost Function", "Accuracy", "Epochs"], 1),
        ("Which Python library is the foundational standard for classic machine learning algorithms?", ["Flask", "Scikit-Learn", "Matplotlib", "BeautifulSoup"], 1),
        ("What does ROC-AUC measure in binary classification models?", ["Separation ability across thresholds", "Data imbalance", "Training time", "Feature correlation"], 0)
    ],
    "Data Analysis": [
        ("Which Pandas function loads a comma-separated values file into a DataFrame?", ["read_table()", "read_csv()", "load_csv()", "open_csv()"], 1),
        ("Which statistical measure represents the middle value in a sorted distribution?", ["Mean", "Median", "Mode", "Variance"], 1),
        ("Which Pandas method removes rows containing missing or null values?", ["dropna()", "fillna()", "drop()", "clean()"], 0),
        ("Which chart type is best suited for showing the distribution of a single numerical variable?", ["Pie Chart", "Histogram", "Scatter Plot", "Heatmap"], 1),
        ("What does a correlation coefficient near +1.0 indicate?", ["No relationship", "Strong positive linear relationship", "Strong negative relationship", "Random noise"], 1),
        ("Which Pandas method computes descriptive statistics like mean, std, and quartiles?", ["summary()", "describe()", "stats()", "info()"], 1),
        ("Which operation combines two DataFrames along a common key column?", ["concat()", "merge()", "append()", "stack()"], 1),
        ("What is an outlier in a dataset?", ["The average data point", "An observation abnormally far from other values", "A duplicate row", "A missing value"], 1),
        ("Which Python library is built on NumPy and optimized for creating static/interactive charts?", ["Requests", "Matplotlib", "SymPy", "PyPDF"], 1),
        ("What is the primary objective of exploratory data analysis (EDA)?", ["Deploying to production", "Understanding underlying patterns and anomalies", "Compressing files", "Writing SQL triggers"], 1)
    ]
}

# 10 Broad Assessment Questions across 5 Competency Domains
BROAD_ASSESSMENT_QUESTIONS = [
    # Technical Skills
    {"id": 1, "category": "Technical Skills", "text": "How proficient are you at writing, debugging, and testing software code in your primary programming language?"},
    {"id": 2, "category": "Technical Skills", "text": "How comfortably can you formulate SQL queries, work with relational schemas, or manage database data?"},
    
    # Problem Solving
    {"id": 3, "category": "Problem Solving", "text": "How effectively can you decompose an ambiguous, complex engineering problem into modular, executable steps?"},
    {"id": 4, "category": "Problem Solving", "text": "When encountering unexpected bugs or runtime anomalies, how systematically do you isolate and resolve root causes?"},
    
    # Communication
    {"id": 5, "category": "Communication", "text": "How clearly can you present technical architectures and project outcomes to both technical and non-technical stakeholders?"},
    {"id": 6, "category": "Communication", "text": "How effectively do you document your codebase, write clean commit messages, and collaborate during code reviews?"},
    
    # Domain Knowledge
    {"id": 7, "category": "Domain Knowledge", "text": "How well do you understand industry-standard software design patterns, data pipelines, and production practices?"},
    {"id": 8, "category": "Domain Knowledge", "text": "How successfully have you translated theoretical coursework concepts into working real-world capstone projects?"},
    
    # Learning Ability
    {"id": 9, "category": "Learning Ability", "text": "When required to adopt a newly released framework or unfamiliar API, how rapidly can you independently master it?"},
    {"id": 10, "category": "Learning Ability", "text": "How actively do you engage in continuous self-directed learning, technical documentation reading, and skill enhancement?"}
]

RATING_OPTIONS = [
    ("1", "Beginner (1/5)"),
    ("2", "Elementary (2/5)"),
    ("3", "Intermediate (3/5)"),
    ("4", "Advanced (4/5)"),
    ("5", "Expert (5/5)")
]


def calculate_proficiency_level(score):
    """Maps score percentage (0-100) to standard academic proficiency tier."""
    if score >= 90:
        return "Expert"
    elif score >= 70:
        return "Advanced"
    elif score >= 40:
        return "Intermediate"
    else:
        return "Beginner"


def grade_technical_assessment(skill, answers):
    """
    Evaluates submitted technical answers against the correct answer keys.
    Returns:
        dict: {skill, score, level, correct, total, answers_feedback}
    """
    canonical_map = {k.lower(): k for k in TECHNICAL_QUESTION_BANK}
    norm_skill = canonical_map.get(skill.strip().lower())
    if not norm_skill:
        raise ValueError(f"No technical assessment available for skill: {skill}")

    questions = TECHNICAL_QUESTION_BANK[norm_skill]
    total = len(questions)
    correct_count = 0
    feedback = []

    for idx, (q_text, opts, ans_idx) in enumerate(questions, 1):
        raw_val = answers.get(str(idx))
        try:
            sel_idx = int(raw_val)
        except (TypeError, ValueError):
            sel_idx = -1

        is_correct = (sel_idx == ans_idx)
        if is_correct:
            correct_count += 1

        feedback.append({
            "id": idx,
            "question": q_text,
            "options": opts,
            "selected": sel_idx,
            "correct_answer": ans_idx,
            "is_correct": is_correct
        })

    score = round((correct_count / total) * 100)
    level = calculate_proficiency_level(score)

    return {
        "skill": norm_skill,
        "score": score,
        "level": level,
        "correct": correct_count,
        "total": total,
        "feedback": feedback
    }


def grade_overall_assessment(answers):
    """
    Evaluates the 10-question 5-domain competency assessment.
    Returns:
        dict: {overall_score, category_scores, strengths, weaknesses, recommendations}
    """
    domain_totals = {
        "Technical Skills": [],
        "Problem Solving": [],
        "Communication": [],
        "Domain Knowledge": [],
        "Learning Ability": []
    }

    all_values = []
    for q in BROAD_ASSESSMENT_QUESTIONS:
        raw = answers.get(str(q["id"]))
        try:
            val = int(raw)
            if val < 1 or val > 5:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError(f"Please provide a valid rating (1-5) for question {q['id']}")

        all_values.append(val)
        domain_totals[q["category"]].append(val)

    overall = round((sum(all_values) / (len(all_values) * 5)) * 100)
    
    cat_scores = {}
    for cat, vals in domain_totals.items():
        cat_scores[cat] = round((sum(vals) / (len(vals) * 5)) * 100)

    # Calculate strengths and weaknesses based on category scores
    sorted_domains = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [d[0] for d in sorted_domains if d[1] >= 65]
    if not strengths:
        strengths = [sorted_domains[0][0]]

    weaknesses = [d[0] for d in sorted_domains if d[1] < 60]
    if not weaknesses:
        weaknesses = [sorted_domains[-1][0]]

    # Generate explainable recommendations
    recommendations = []
    for w in weaknesses:
        if w == "Technical Skills":
            recommendations.append("Strengthen core coding and algorithmic proficiency through hands-on technical problem sets.")
        elif w == "Problem Solving":
            recommendations.append("Practice decomposing complex modular software problems and debugging real-world error traces.")
        elif w == "Communication":
            recommendations.append("Engage in peer technical reviews, project presentations, and open-source documentation writing.")
        elif w == "Domain Knowledge":
            recommendations.append("Build capstone projects aligning with modern production architectures and engineering standards.")
        elif w == "Learning Ability":
            recommendations.append("Dedicate weekly time to independently exploring new engineering tools, libraries, and official docs.")

    return {
        "overall": overall,
        "categories": cat_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "correct": round(overall / 10),
        "total": 10
    }
