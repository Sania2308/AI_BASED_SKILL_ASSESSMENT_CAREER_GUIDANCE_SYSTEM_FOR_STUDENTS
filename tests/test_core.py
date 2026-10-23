import os
import unittest
import tempfile
import json
from app import create_app
from app.db import get_direct_db, init_db
from app.services.nlp_parser import parse_and_extract_skills
from app.services.assessment_engine import grade_technical_assessment, grade_overall_assessment
from app.services.recommendation import calculate_career_matches, perform_skill_gap_analysis
from app.services.crypto_verification import generate_verification_hash, verify_hash_record
from app.services.gis_service import generate_safe_approximate_coords

class SkillGuideCoreTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-secret-key"
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db(self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass

    def register_and_login_user(self, name="Test Student", email="student@test.edu", password="password123"):
        self.client.post("/signup", data={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": password,
            "course": "B.Tech CSE",
            "year": "3rd Year"
        }, follow_redirects=True)
        return self.client.post("/login", data={"email": email, "password": password}, follow_redirects=True)

    # 1. Test Authentication Workflow (Signup, Login, Logout)
    def test_authentication_workflow(self):
        # Signup
        res = self.client.post("/signup", data={
            "name": "Jane Doe",
            "email": "jane@university.edu",
            "password": "securepassword",
            "confirm_password": "securepassword",
            "course": "Information Technology",
            "year": "4th Year"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Jane Doe", res.data)

        # Logout
        res_logout = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b"Sign In", res_logout.data)

        # Login again
        res_login = self.client.post("/login", data={
            "email": "jane@university.edu",
            "password": "securepassword"
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Welcome back, Jane Doe", res_login.data)

    # 2. Test Rule-Based NLP Skill Extraction
    def test_nlp_skill_extraction(self):
        sample_resume = """
        Experienced Computer Science student proficient in Python, SQL, and Data Analysis.
        Built web interfaces using HTML, CSS, JavaScript and Flask.
        Strong background in Machine Learning, Git, and Problem Solving.
        """
        result = parse_and_extract_skills(sample_resume)
        skills = result["skills"]

        self.assertIn("Python", skills)
        self.assertIn("SQL", skills)
        self.assertIn("Data Analysis", skills)
        self.assertIn("HTML", skills)
        self.assertIn("CSS", skills)
        self.assertIn("JavaScript", skills)
        self.assertIn("Machine Learning", skills)
        self.assertIn("Git", skills)
        self.assertIn("Problem Solving", skills)

        # Categorization check
        self.assertIn("Programming", result["categorized"])
        self.assertIn("Python", result["categorized"]["Programming"])
        self.assertIn("Databases", result["categorized"])
        self.assertIn("SQL", result["categorized"]["Databases"])

    # 3. Test Technical Skill Assessment Grading
    def test_technical_assessment_grading(self):
        # Python test with 10 correct answers
        perfect_answers = {
            "1": "2", "2": "2", "3": "1", "4": "1", "5": "0",
            "6": "1", "7": "2", "8": "0", "9": "1", "10": "0"
        }
        res = grade_technical_assessment("Python", perfect_answers)
        self.assertEqual(res["score"], 100)
        self.assertEqual(res["level"], "Expert")
        self.assertEqual(res["correct"], 10)

        # Partial answers
        partial_answers = {
            "1": "2", "2": "2", "3": "1", "4": "1", "5": "0",
            "6": "0", "7": "0", "8": "1", "9": "0", "10": "1"
        }
        res_part = grade_technical_assessment("Python", partial_answers)
        self.assertEqual(res_part["score"], 50)
        self.assertEqual(res_part["level"], "Intermediate")

    # 4. Test 5-Domain Broad Assessment Grading
    def test_broad_competency_assessment(self):
        answers = {str(i): "4" for i in range(1, 11)}  # 4/5 across all 10 questions
        res = grade_overall_assessment(answers)
        self.assertEqual(res["overall"], 80)
        self.assertEqual(res["categories"]["Technical Skills"], 80)
        self.assertEqual(res["categories"]["Problem Solving"], 80)
        self.assertEqual(res["categories"]["Learning Ability"], 80)
        self.assertIn("Technical Skills", res["strengths"])

    # 5. Test 13-Track Career Recommendation Engine
    def test_career_recommendation_engine(self):
        extracted = ["Python", "SQL", "Data Analysis", "Excel", "Statistics"]
        verified = {
            "Python": {"score": 85, "level": "Advanced"},
            "SQL": {"score": 90, "level": "Expert"}
        }
        assessment = {
            "technical": 80, "problem_solving": 85, "communication": 75,
            "domain_knowledge": 80, "learning_ability": 85
        }
        recommendations = calculate_career_matches(extracted, verified, assessment, preferred_career="Data Analyst")

        self.assertEqual(len(recommendations), 13)
        top = recommendations[0]
        self.assertIn(top["name"], ["Data Analyst", "Data Scientist"])
        self.assertGreaterEqual(top["match"], 60)
        self.assertIn("Python", "".join(top["matching_skills"]))
        self.assertTrue(top["reason"])

    # 6. Test Skill Gap Analysis
    def test_skill_gap_analysis(self):
        extracted = ["Python", "SQL"]
        verified = {"Python": {"score": 85, "level": "Advanced"}}
        gap = perform_skill_gap_analysis("Data Analyst", extracted, verified)

        self.assertEqual(gap["career_name"], "Data Analyst")
        self.assertGreater(gap["readiness_pct"], 0)
        have_names = [h["skill"] for h in gap["already_have"]]
        self.assertIn("Python", have_names)
        missing_names = [m["skill"] for m in gap["missing"]]
        self.assertIn("Power BI", missing_names)

    # 7. Test Cryptographic SHA-256 Prototype Verification
    def test_crypto_verification(self):
        token = generate_verification_hash(1, "Test Student", "Python", 85, "Advanced")
        self.assertTrue(token["verification_hash"])
        self.assertTrue(token["verification_id"].startswith("SG-"))
        self.assertEqual(len(token["verification_hash"]), 64)

        # Insert into test DB and query
        with self.app.app_context():
            conn = get_direct_db(self.db_path)
            conn.execute("""
                INSERT INTO verification_records (user_id, record_type, item_name, score, level, verification_hash, metadata_json, created_at)
                VALUES (1, 'skill_badge', 'Python', 85, 'Advanced', ?, '{}', '2026-10-21T12:00:00')
            """, (token["verification_hash"],))
            conn.commit()

            verified = verify_hash_record(conn, token["verification_hash"])
            self.assertIsNotNone(verified)
            self.assertEqual(verified["item_name"], "Python")

    # 8. Test Safe GIS Coordinate Generator
    def test_gis_coordinates(self):
        lat1, lng1, zone1 = generate_safe_approximate_coords(1)
        lat2, lng2, zone2 = generate_safe_approximate_coords(2)

        self.assertAlmostEqual(lat1, 12.97, delta=0.5)
        self.assertAlmostEqual(lng1, 77.59, delta=0.5)
        self.assertTrue(zone1)
        # Deterministic check: same user gets exact same coordinates
        lat1_repeat, lng1_repeat, _ = generate_safe_approximate_coords(1)
        self.assertEqual(lat1, lat1_repeat)
        self.assertEqual(lng1, lng1_repeat)

    # 9. Test End-to-End Roadmap and Skill Swap API
    def test_e2e_roadmap_and_swap_api(self):
        self.register_and_login_user("Swap Student", "swap@test.edu", "pass123")

        # Submit technical test via API
        tech_res = self.client.post("/api/submit-technical/Python", json={
            "answers": {str(i): "2" if i in [1,2,7] else ("1" if i in [3,4,6,9] else "0") for i in range(1, 11)}
        })
        self.assertEqual(tech_res.status_code, 200)

        # Update roadmap step
        road_res = self.client.post("/api/update-roadmap-step", json={
            "career_name": "Data Analyst",
            "step_id": 1,
            "status": "Completed"
        })
        self.assertEqual(road_res.status_code, 200)
        self.assertIn("completion_pct", road_res.get_json())

        # Update profile
        prof_res = self.client.post("/profile", data={
            "name": "Swap Student Renamed",
            "email": "swap@test.edu",
            "course": "B.Tech CSE",
            "year": "4th Year",
            "bio": "Passionate about full-stack AI and Data Science",
            "preferred_career": "Data Analyst"
        }, follow_redirects=True)
        self.assertEqual(prof_res.status_code, 200)
        self.assertIn(b"Swap Student Renamed", prof_res.data)

        # Report route check
        rep_res = self.client.get("/report")
        self.assertEqual(rep_res.status_code, 200)
        self.assertIn(b"Career Assessment", rep_res.data)

if __name__ == "__main__":
    unittest.main()
