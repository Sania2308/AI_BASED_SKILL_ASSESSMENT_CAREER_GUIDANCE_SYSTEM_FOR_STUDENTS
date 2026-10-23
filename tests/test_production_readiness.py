import os
import unittest
import tempfile
import io
import json
from app import create_app
from app.db import init_db, get_direct_db
from app.services.nlp_parser import parse_and_extract_skills
from app.services.recommendation import calculate_career_matches
from app.services.gamification import award_skill_points

class ProductionReadinessTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-prod-key-2026",
            "IS_PRODUCTION": True
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

    def register_user(self, name, email, password, course="Computer Science", year="3rd Year"):
        self.client.get("/logout", follow_redirects=True)
        res = self.client.post("/signup", data={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": password,
            "course": course,
            "year": year
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def login_user(self, email, password):
        self.client.get("/logout", follow_redirects=True)
        res = self.client.post("/login", data={
            "email": email,
            "password": password
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        return res

    def logout_user(self):
        return self.client.get("/logout", follow_redirects=True)

    # 1. Health check endpoint
    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")

    # 2. Duplicate point protection
    def test_duplicate_point_protection(self):
        self.register_user("Gamer", "gamer@test.edu", "pass123")
        self.login_user("gamer@test.edu", "pass123")
        conn = get_direct_db(self.db_path)
        user = conn.execute("SELECT id FROM users WHERE email = 'gamer@test.edu'").fetchone()
        user_id = user["id"]

        # Award first time
        tot1, aw1 = award_skill_points(conn, user_id, "upload_resume", reference_id="resume_analysis")
        self.assertEqual(aw1, 10)
        self.assertEqual(tot1, 10)

        # Repeating/refreshing same action must award 0 additional points
        tot2, aw2 = award_skill_points(conn, user_id, "upload_resume", reference_id="resume_analysis")
        self.assertEqual(aw2, 0)
        self.assertEqual(tot2, 10)

    # 3. File upload validations & error handling
    def test_invalid_upload_handling(self):
        self.register_user("Uploader", "up@test.edu", "pass123")
        self.login_user("up@test.edu", "pass123")

        # Unsupported extension (.exe)
        bad_data = {
            "resume_file": (io.BytesIO(b"binary executable"), "malicious.exe")
        }
        res = self.client.post("/api/upload-resume", data=bad_data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported file format", res.get_json()["error"])

        # Empty/whitespace txt
        empty_data = {
            "resume_file": (io.BytesIO(b"   "), "empty.txt")
        }
        res_empty = self.client.post("/api/upload-resume", data=empty_data, content_type="multipart/form-data")
        self.assertEqual(res_empty.status_code, 400)

    # 4. Critical Multi-User Isolation & Skill Swap Matching Test
    def test_multi_user_data_isolation_and_skill_swap(self):
        # Register Student A
        self.register_user("Alice Smith", "alice@test.edu", "passwordA")
        # Register Student B
        self.register_user("Bob Jones", "bob@test.edu", "passwordB")
        # Register Student C
        self.register_user("Charlie Brown", "charlie@test.edu", "passwordC")

        conn = get_direct_db(self.db_path)
        u_alice = conn.execute("SELECT id FROM users WHERE email = 'alice@test.edu'").fetchone()
        u_bob = conn.execute("SELECT id FROM users WHERE email = 'bob@test.edu'").fetchone()
        u_charlie = conn.execute("SELECT id FROM users WHERE email = 'charlie@test.edu'").fetchone()

        self.assertIsNotNone(u_alice)
        self.assertIsNotNone(u_bob)
        self.assertIsNotNone(u_charlie)

        alice_id, bob_id, charlie_id = u_alice["id"], u_bob["id"], u_charlie["id"]

        # Alice verifies Python (score 90, Expert) and wants to learn React
        conn.execute("""
            INSERT INTO skill_assessments (user_id, skill, score, level, correct, total, taken_at)
            VALUES (?, 'Python', 90, 'Expert', 9, 10, '2026-10-22T10:00:00')
        """, (alice_id,))
        conn.execute("INSERT INTO learning_skills (user_id, skill) VALUES (?, 'React')", (alice_id,))

        # Bob verifies React (score 85, Advanced) and wants to learn Python
        conn.execute("""
            INSERT INTO skill_assessments (user_id, skill, score, level, correct, total, taken_at)
            VALUES (?, 'React', 85, 'Advanced', 8, 10, '2026-10-22T11:00:00')
        """, (bob_id,))
        conn.execute("INSERT INTO learning_skills (user_id, skill) VALUES (?, 'Python')", (bob_id,))

        # Charlie has no verified skills and wants to learn Java
        conn.execute("INSERT INTO learning_skills (user_id, skill) VALUES (?, 'Java')", (charlie_id,))
        conn.commit()

        # Login as Alice and check Skill Swap
        self.login_user("alice@test.edu", "passwordA")
        swap_res = self.client.get("/skill-swap")
        self.assertEqual(swap_res.status_code, 200)
        swap_html = swap_res.data.decode("utf-8")

        # Bob should appear because Bob has technically verified React (Alice's learning skill)
        self.assertIn("Bob Jones", swap_html)
        self.assertIn("React", swap_html)

        # Alice must NEVER see herself in matching peers
        self.assertNotIn("Alice Smith", swap_html.split("Peer Matches")[1] if "Peer Matches" in swap_html else "")

        # Charlie should NOT appear because Charlie does not have verified React
        self.assertNotIn("Charlie Brown", swap_html)

        # Data Isolation Check: Alice's dashboard must NOT show Bob's skills
        dash_res = self.client.get("/dashboard")
        dash_html = dash_res.data.decode("utf-8")
        self.assertIn("Alice Smith", dash_html)
        self.assertNotIn("Bob Jones", dash_html)

        # Logout Alice, Login Bob
        self.logout_user()
        self.login_user("bob@test.edu", "passwordB")
        bob_swap = self.client.get("/skill-swap")
        bob_html = bob_swap.data.decode("utf-8")

        # Alice should appear for Bob (Alice has verified Python, Bob wants Python)
        self.assertIn("Alice Smith", bob_html)
        self.assertIn("Python", bob_html)
        self.assertNotIn("Bob Jones", bob_html.split("Peer Matches")[1] if "Peer Matches" in bob_html else "")

    # 5. Admin role authorization check
    def test_admin_authorization(self):
        # Student cannot access /admin
        self.register_user("Regular Student", "student@test.edu", "pass123")
        self.login_user("student@test.edu", "pass123")
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 403)

        # Admin user can access /admin
        self.logout_user()
        self.login_user("admin@skillguide.edu", "admin123")
        res_admin = self.client.get("/admin")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Institutional Administration Portal", res_admin.data)

    # 6. Cryptographic verification ledger check
    def test_verification_ledger(self):
        self.register_user("Cert Student", "cert@test.edu", "pass123")
        self.login_user("cert@test.edu", "pass123")
        res = self.client.get("/verification")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"tamper-evident", res.data.lower())
        self.assertIn(b"Verification Ledger", res.data)

if __name__ == "__main__":
    unittest.main()
