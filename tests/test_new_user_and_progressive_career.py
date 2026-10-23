import os
import unittest
import tempfile
import json
from app import create_app
from app.db import init_db, get_direct_db
from app.services.recommendation import calculate_career_matches

class NewUserAndProgressiveCareerTestCase(unittest.TestCase):
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

    def test_complete_new_user_lifecycle(self):
        # 1. Register brand new student
        res_signup = self.client.post("/signup", data={
            "name": "New Student",
            "email": "brandnew@university.edu",
            "password": "password123",
            "confirm_password": "password123",
            "course": "Computer Science",
            "year": "1st Year"
        }, follow_redirects=True)
        self.assertEqual(res_signup.status_code, 200)

        # Direct database verification: New user starts with 0 skill points
        conn = get_direct_db(self.db_path)
        user = conn.execute("SELECT * FROM users WHERE email = 'brandnew@university.edu'").fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user["skill_points"], 0)

        # Verify initial dashboard state
        dash_res = self.client.get("/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        dash_html = dash_res.data.decode("utf-8")

        # Required metrics must be 0 or 0%
        self.assertIn("0 pts", dash_html)
        self.assertIn("Overall Skill Score</span>\n            <span class=\"stat-data-value\">0%</span>", dash_html)
        self.assertIn("Technical Score</span>\n            <span class=\"stat-data-value\">0%</span>", dash_html)
        self.assertIn("Problem Solving</span>\n            <span class=\"stat-data-value\">0%</span>", dash_html)
        self.assertIn("Communication</span>\n            <span class=\"stat-data-value\">0%</span>", dash_html)
        self.assertIn("Roadmap Progress</span>\n            <span class=\"stat-data-value\">0%</span>", dash_html)

        # Career recommendation gating
        self.assertIn("Not Available", dash_html)
        self.assertIn("Complete your assessment to discover your career matches.", dash_html)
        self.assertIn("Your career insight will appear after you complete your skill assessment and resume analysis.", dash_html)
        self.assertIn("Complete your resume analysis and assessment to receive personalized skill recommendations.", dash_html)

        # No default 15% career score awarded
        self.assertNotIn("15% Compatibility", dash_html)
        self.assertNotIn("15% Match", dash_html)

        # Charts API returns empty / zero state for unassessed student
        charts_res = self.client.get("/api/dashboard-charts")
        self.assertEqual(charts_res.status_code, 200)
        charts_data = json.loads(charts_res.data.decode("utf-8"))
        self.assertFalse(charts_data["has_data"])
        self.assertEqual(charts_data["radar"]["data"], [0, 0, 0, 0, 0])
        self.assertEqual(charts_data["bar"]["student"], [0, 0, 0, 0, 0])
        self.assertEqual(charts_data["doughnut"]["readiness"], 0)

        # Roadmap page shows gated empty state before assessment
        roadmap_res = self.client.get("/roadmap")
        self.assertEqual(roadmap_res.status_code, 200)
        roadmap_html = roadmap_res.data.decode("utf-8")
        self.assertIn("Your personalized learning roadmap will be generated after career assessment.", roadmap_html)
        
        # Verify 0 roadmap progress rows were created in DB
        roadmap_rows = conn.execute("SELECT COUNT(*) FROM roadmap_progress WHERE user_id = ?", (user["id"],)).fetchone()[0]
        self.assertEqual(roadmap_rows, 0)

        # =================================================================
        # STEP A: Add resume skills and confirm preliminary recommendations
        # =================================================================
        extract_res = self.client.post("/api/extract-text-skills", data={
            "text": "Student proficient in Python, SQL, and Data Analysis."
        })
        self.assertEqual(extract_res.status_code, 200)
        ext_json = json.loads(extract_res.data.decode("utf-8"))
        self.assertGreaterEqual(ext_json["count"], 2)

        # Skill points must increase by +10 for resume analysis
        user_after_resume = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_after_resume["skill_points"], 10)

        # Test duplicate prevention: re-submitting resume text must not award duplicate points
        self.client.post("/api/extract-text-skills", data={"text": "Student proficient in Python and SQL."})
        user_dup_check = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_dup_check["skill_points"], 10)

        # Check dashboard in State 2 (Preliminary Career Match)
        dash_res_2 = self.client.get("/dashboard")
        dash_html_2 = dash_res_2.data.decode("utf-8")
        self.assertIn("Preliminary Career Match", dash_html_2)
        self.assertIn("Skills Detected</span>\n            <span class=\"stat-data-value\">3</span>", dash_html_2)

        # =================================================================
        # STEP B: Complete overall assessment and confirm recommendations update
        # =================================================================
        test_answers = {str(i): "4" for i in range(1, 11)}
        assess_res = self.client.post("/api/submit-overall", json={"answers": test_answers})
        self.assertEqual(assess_res.status_code, 200)

        # Skill points must increase by +20 (10 + 20 = 30)
        user_after_assess = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_after_assess["skill_points"], 30)

        # Re-submitting overall assessment must not award duplicate points
        self.client.post("/api/submit-overall", json={"answers": test_answers})
        user_dup_assess = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_dup_assess["skill_points"], 30)

        # Check dashboard in State 3 (Career Match)
        dash_res_3 = self.client.get("/dashboard")
        dash_html_3 = dash_res_3.data.decode("utf-8")
        self.assertIn("Career Match", dash_html_3)

        # Charts API now reflects real data
        charts_res_3 = self.client.get("/api/dashboard-charts")
        charts_data_3 = json.loads(charts_res_3.data.decode("utf-8"))
        self.assertTrue(charts_data_3["has_data"])
        self.assertGreater(charts_data_3["doughnut"]["readiness"], 0)

        # =================================================================
        # STEP C: Complete technical assessment and confirm verified career readiness
        # =================================================================
        perfect_python = {
            "1": "2", "2": "2", "3": "1", "4": "1", "5": "0",
            "6": "1", "7": "2", "8": "0", "9": "1", "10": "0"
        }
        tech_res = self.client.post("/api/technical-assessment/Python", json={"answers": perfect_python})
        self.assertEqual(tech_res.status_code, 200)

        # Skill points must increase by +30 (30 + 30 = 60)
        user_after_tech = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_after_tech["skill_points"], 60)

        # Retaking same technical test must not award duplicate points
        self.client.post("/api/technical-assessment/Python", json={"answers": perfect_python})
        user_dup_tech = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_dup_tech["skill_points"], 60)

        # Check dashboard in State 4 (Verified Career Readiness)
        dash_res_4 = self.client.get("/dashboard")
        dash_html_4 = dash_res_4.data.decode("utf-8")
        self.assertIn("Verified Career Readiness", dash_html_4)
        self.assertIn("Verified Skills</span>\n            <span class=\"stat-data-value\">1</span>", dash_html_4)

        # =================================================================
        # STEP D: Confirm skill points increase only after actual completed actions
        # =================================================================
        # Profile completion: updating profile with bio gives +10 points (60 + 10 = 70)
        self.client.post("/profile", data={
            "name": "New Student",
            "email": "brandnew@university.edu",
            "course": "Computer Science",
            "year": "1st Year",
            "bio": "Enthusiastic computer science student passionate about algorithms and data.",
            "preferred_career": "Data Analyst"
        }, follow_redirects=True)
        user_after_prof = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_after_prof["skill_points"], 70)

        # Updating profile again does not duplicate points
        self.client.post("/profile", data={
            "name": "New Student Updated",
            "email": "brandnew@university.edu",
            "course": "Computer Science",
            "year": "1st Year",
            "bio": "Updated bio text for testing.",
            "preferred_career": "Data Analyst"
        }, follow_redirects=True)
        user_dup_prof = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_dup_prof["skill_points"], 70)

        # Roadmap milestone completion: completing step 1 gives +10 points (70 + 10 = 80)
        self.client.post("/api/update-roadmap-step", json={
            "career_name": "Data Analyst",
            "step_id": 1,
            "status": "Completed"
        })
        user_after_step = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_after_step["skill_points"], 80)

        # Re-marking or toggling step 1 does not duplicate points
        self.client.post("/api/update-roadmap-step", json={
            "career_name": "Data Analyst",
            "step_id": 1,
            "status": "Completed"
        })
        user_dup_step = conn.execute("SELECT skill_points FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.assertEqual(user_dup_step["skill_points"], 80)
