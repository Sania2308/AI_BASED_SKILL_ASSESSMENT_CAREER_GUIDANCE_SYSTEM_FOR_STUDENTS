import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys

def run_live_verification():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Test Login Page
    resp = opener.open('http://127.0.0.1:5000/login')
    assert resp.status == 200, f'Login page failed: {resp.status}'
    print('[PASS] 1. Login Page Rendered (200 OK)')

    # 2. Signup / Login
    signup_data = urllib.parse.urlencode({
        'name': 'Live Verification Student',
        'email': 'live_verifier@university.edu',
        'password': 'password123',
        'confirm_password': 'password123',
        'course': 'Computer Science Engineering',
        'year': '4th Year'
    }).encode()
    resp = opener.open('http://127.0.0.1:5000/signup', data=signup_data)
    assert resp.status == 200, 'Signup failed'
    print('[PASS] 2. Student Authentication & Session Active (200 OK)')

    # 3. Dashboard
    resp = opener.open('http://127.0.0.1:5000/dashboard')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'AI Career Insight' in html
    assert 'skillRadarChart' in html
    print('[PASS] 3. Dashboard with AI Career Insight & Chart Elements (200 OK)')

    # 4. Charts API
    resp = opener.open('http://127.0.0.1:5000/api/dashboard-charts')
    charts = json.loads(resp.read().decode('utf-8'))
    assert 'radar' in charts and 'bar' in charts and 'doughnut' in charts and 'line' in charts
    print('[PASS] 4. Chart.js 4-Series Analytics JSON API (200 OK)')

    # 5. Assessment Workspace
    resp = opener.open('http://127.0.0.1:5000/assessment')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'Resume Analyzer' in html
    assert 'Technical Skill Verification' in html
    assert 'Broad 5-Domain' in html
    print('[PASS] 5. Assessment Workspace Page (200 OK)')

    # 6. NLP Skill Extraction API
    extract_data = urllib.parse.urlencode({
        'text': 'Proficient in Python, SQL, JavaScript, HTML, CSS, Machine Learning, Data Analysis and Docker.'
    }).encode()
    resp = opener.open('http://127.0.0.1:5000/api/extract-text-skills', data=extract_data)
    skills_json = json.loads(resp.read().decode('utf-8'))
    assert skills_json['count'] >= 5
    print(f'[PASS] 6. Rule-Based NLP Skill Extraction ({skills_json["count"]} skills identified)')

    # 7. Technical Questions Bank (10 skills available)
    resp = opener.open('http://127.0.0.1:5000/api/technical-questions/Python')
    q_data = json.loads(resp.read().decode('utf-8'))
    assert q_data['total'] == 10
    print('[PASS] 7. Technical Assessment Question Bank (10 MCQs loaded)')

    # 8. Career Guidance & 13 Pathways
    resp = opener.open('http://127.0.0.1:5000/career')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'Skill Gap Analysis' in html
    assert '13 Career Guidance Pathways' in html
    print('[PASS] 8. Career Guidance & 13 Pathways Gap Analysis (200 OK)')

    # 9. Learning Roadmap & Curated Resources
    resp = opener.open('http://127.0.0.1:5000/roadmap')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert '8-Step Career Milestones' in html
    assert 'Curated Learning Resources' in html
    print('[PASS] 9. Learning Roadmap & Curated Resource Cards (200 OK)')

    # 10. Peer-to-Peer Skill Swap
    resp = opener.open('http://127.0.0.1:5000/skill-swap')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'Peer-to-Peer Skill Swap' in html
    print('[PASS] 10. Skill Swap Exchange Workflow (200 OK)')

    # 11. GIS Skill Map & Leaflet Markers
    resp = opener.open('http://127.0.0.1:5000/gis-map')
    assert resp.status == 200
    resp_gis = opener.open('http://127.0.0.1:5000/api/gis-markers')
    gis_data = json.loads(resp_gis.read().decode('utf-8'))
    assert 'markers' in gis_data
    print(f'[PASS] 11. GIS Leaflet Map & Spatial Filter API ({gis_data["count"]} peers located)')

    # 12. Blockchain Verification Prototype Explorer
    resp = opener.open('http://127.0.0.1:5000/verification')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'Blockchain Prototype' in html
    print('[PASS] 12. Cryptographic SHA-256 Ledger Explorer (200 OK)')

    # 13. Achievements & Leaderboard
    resp = opener.open('http://127.0.0.1:5000/achievements')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'Academic Badges Catalog' in html
    assert 'Campus Student Leaderboard' in html
    print('[PASS] 13. Gamification Badges & Campus Leaderboard (200 OK)')

    # 14. Student Profile
    resp = opener.open('http://127.0.0.1:5000/profile')
    assert resp.status == 200
    print('[PASS] 14. Student Profile & Academic Details (200 OK)')

    # 15. Printable Career Dossier Report
    resp = opener.open('http://127.0.0.1:5000/report')
    assert resp.status == 200
    html = resp.read().decode('utf-8')
    assert 'Career Assessment' in html
    print('[PASS] 15. Printable Career Assessment Dossier (200 OK)')

    # 16. Admin Dashboard (Admin role check)
    admin_cj = http.cookiejar.CookieJar()
    admin_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(admin_cj))
    admin_login_data = urllib.parse.urlencode({'email': 'admin@skillguide.edu', 'password': 'admin123'}).encode()
    admin_opener.open('http://127.0.0.1:5000/login', data=admin_login_data)
    resp_admin = admin_opener.open('http://127.0.0.1:5000/admin')
    assert resp_admin.status == 200
    admin_html = resp_admin.read().decode('utf-8')
    assert 'Institutional Administration Portal' in admin_html
    print('[PASS] 16. Institutional Administrator Dashboard (200 OK)')

    print('\n======================================================')
    print('ALL 16 LIVE SERVER WORKFLOW TESTS PASSED CLEANLY (100%)')
    print('======================================================')

if __name__ == '__main__':
    run_live_verification()
