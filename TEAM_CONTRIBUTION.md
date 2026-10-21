# SkillGuide – 50% Completion Team Contribution

This division is for the current 50% prototype. Each member should understand their own files and the overall workflow.

## Member 1 – Frontend & UI

### Main files
- `templates/base.html`
- `templates/auth.html`
- `templates/dashboard.html`
- `templates/profile.html`
- `static/style.css`

### Prepare
- Common SkillGuide layout and sidebar
- Login and signup interface
- Dashboard cards and score display
- Profile page and profile editing interface
- Styling, cards, buttons and responsive layout

### Viva explanation
> I worked mainly on the frontend. I developed the SkillGuide interface, authentication screens, dashboard and profile pages, and connected the UI with Flask template data so the logged-in user's information is displayed dynamically.

## Member 2 – Backend, AI/NLP & Assessment

### Main files
- `app.py`
- `templates/assessment.html`
- `static/app.js`

### Prepare
- Flask application and routes
- SQLite database
- User authentication
- NLP-based skill extraction
- Assessment questions and scoring
- Career matching logic

### NLP explanation
> The student provides resume or skill text. The current prototype normalizes the text and compares it with a predefined skill vocabulary using regular-expression text matching. Detected skills are stored in SQLite.

### Assessment explanation
The system accepts 10 answers on a 1–5 scale, calculates an overall percentage and calculates scores for Technical Skills, Problem Solving, Communication and Domain Knowledge.

## Member 3 – GIS, Data Analytics, Skill Swap & Blockchain Prototype

### Main files
- `templates/skill_swap.html`
- `templates/career.html`
- `templates/dashboard.html`
- `static/app.js`
- Relevant assessment/data sections of `app.py`

### Prepare
- Assessment score visualization/data analytics
- Interactive Leaflet GIS map
- OpenStreetMap integration
- Peer-to-peer Skill Swap interface
- Blockchain verification/badge prototype

### GIS explanation
> We use Leaflet with OpenStreetMap to provide an interactive map for the Skill Swap prototype. The current 50% version uses sample peer coordinates and does not collect the student's precise location.

### Blockchain explanation
> The current 50% version contains the blockchain verification interface and hash concept as a prototype. Actual smart-contract/blockchain-network integration is planned for a later implementation stage.

## Shared work

All three members should also prepare:
- Project objective and problem statement
- Overall architecture and workflow
- Testing/demo flow
- Literature review
- Project presentation
- Basic understanding of the other two members' modules

## Overall workflow

Signup/Login → Dashboard → Skill/Resume Text → NLP Skill Extraction → Skill Assessment → Score & Analytics → Career Matching → Skill Gap/Career View → Skill Swap → GIS Map → Blockchain Verification Prototype
