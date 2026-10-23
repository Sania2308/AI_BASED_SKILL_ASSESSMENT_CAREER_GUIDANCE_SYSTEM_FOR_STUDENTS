import re
import os
from pypdf import PdfReader
from docx import Document
from app.config import SKILL_TAXONOMY, SKILL_TO_CATEGORY, ALL_SKILLS

def extract_text_from_file(file_storage):
    """
    Safely extracts plain text from PDF, DOCX, or TXT file uploads.
    Does not write permanent file if stream reading is supported.
    """
    filename = file_storage.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    text = ""
    try:
        if ext == "pdf":
            reader = PdfReader(file_storage.stream)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        elif ext == "docx":
            doc = Document(file_storage.stream)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            text = "\n".join(paragraphs)

        elif ext in ["txt", "text"]:
            raw_bytes = file_storage.stream.read()
            # Try utf-8 first, fallback to latin-1
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = raw_bytes.decode("latin-1", errors="ignore")
    except Exception as e:
        raise ValueError(f"Error parsing {ext.upper()} document: {str(e)}")

    return text.strip()


def parse_and_extract_skills(raw_text):
    """
    Transparent Rule-Based NLP Skill Extraction Engine:
    - Normalizes document text into tokenized stream.
    - Matches terms using word-boundary regular expressions against the controlled skill taxonomy.
    - Categorizes identified skills by engineering domain.
    - Explainable for university viva examination (no black-box claims).
    """
    if not raw_text or not raw_text.strip():
        return {
            "skills": [],
            "categorized": {},
            "count": 0,
            "engine": "Transparent Rule-Based NLP Pattern Matcher"
        }

    # Normalize spaces and lowercase for search, but preserve special characters like C++, C#, .NET
    text = raw_text

    found_skills = []
    found_set = set()

    for skill in ALL_SKILLS:
        skill_lower = skill.lower()
        if skill_lower in found_set:
            continue

        # Handle special language identifiers like C, C++, C#
        if skill == "C":
            # Word boundary check avoiding accidental matching in words like 'a', 'c'
            pattern = r"(?<![a-zA-Z0-9_])C(?![a-zA-Z0-9_+#])"
            if re.search(pattern, text):
                found_skills.append(skill)
                found_set.add(skill_lower)
        elif skill == "C++":
            pattern = r"(?<![a-zA-Z0-9_])C\+\+(?![a-zA-Z0-9_])"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
                found_set.add(skill_lower)
        elif skill == "C#":
            pattern = r"(?<![a-zA-Z0-9_])C#(?![a-zA-Z0-9_])"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
                found_set.add(skill_lower)
        elif skill == "R":
            pattern = r"(?<![a-zA-Z0-9_])R(?![a-zA-Z0-9_+#])"
            if re.search(pattern, text):
                found_skills.append(skill)
                found_set.add(skill_lower)
        elif skill == "Go":
            pattern = r"(?<![a-zA-Z0-9_])(?:Golang|Go language|Go programming)(?![a-zA-Z0-9_])"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
                found_set.add(skill_lower)
        else:
            escaped = re.escape(skill_lower)
            pattern = rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
                found_set.add(skill_lower)

    # Sort found skills
    found_skills = sorted(found_skills)

    # Group into categories
    categorized = {}
    for s in found_skills:
        cat = SKILL_TO_CATEGORY.get(s.lower(), "Other")
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(s)

    return {
        "skills": found_skills,
        "categorized": categorized,
        "count": len(found_skills),
        "engine": "Transparent Controlled-Vocabulary NLP Matcher"
    }
