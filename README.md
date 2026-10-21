# SkillGuide - 50% Working Prototype

## Run
1. Open this folder in VS Code.
2. Activate the virtual environment.
3. Run `pip install -r requirements.txt`.
4. Run `python app.py`.
5. Open `http://127.0.0.1:5000`.

## Implemented
- Signup/login with SQLite persistence and password hashing.
- Same logged-in student's name across dashboard, header and profile.
- Editable profile page.
- Fully functional 10-question skill assessment with category scores saved to SQLite.
- Transparent resume skill extraction from text entered by the student.
- Dashboard updates from saved assessment and extracted skills.
- Career matching based on assessment/skills.
- Interactive draggable/zoomable Leaflet GIS map with sample peer markers.
- Skill swap and blockchain badge UI.

## How to explain the NLP prototype
The student supplies resume/skills text. The backend normalizes that text and compares it against a controlled skill vocabulary. Matching skills are stored in the database and displayed on the dashboard. It is not scraping hidden information from the website. This is a transparent baseline that can later be replaced by spaCy/NER or a trained NLP model.
