"""
Comprehensive end-to-end integration test against the running live API server.
Simulates all frontend actions performed in Dashboard 01 - 08.
"""
import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def request(path, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_data = json.loads(content)
        except:
            err_data = {"error": content}
        return e.code, err_data

def run_tests():
    print("=== STARTING FULL API INTEGRATION TEST ===")
    
    # 1. Health check
    code, res = request("/")
    assert code == 200, f"Health check failed: {code} {res}"
    print("[PASS] 1. Backend Health Check OK:", res)
    
    # 2. Register
    test_email = f"test_student_{int(time.time())}@example.com"
    reg_payload = {
        "full_name": "Antigravity Test Candidate",
        "email": test_email,
        "password": "Password123!"
    }
    code, res = request("/auth/register", method="POST", body=reg_payload)
    assert code == 201, f"Register failed: {code} {res}"
    token = res["access_token"]
    student_id = res["student_id"]
    print(f"[PASS] 2. Registered student id={student_id}, email={test_email}")
    
    # 3. Login
    login_payload = {"email": test_email, "password": "Password123!"}
    code, res = request("/auth/login", method="POST", body=login_payload)
    assert code == 200, f"Login failed: {code} {res}"
    token = res["access_token"]
    print("[PASS] 3. Login successful with JWT token")
    
    # 4. Auth Me
    code, res = request("/auth/me", token=token)
    assert code == 200 and res["email"] == test_email, f"Me check failed: {code} {res}"
    print("[PASS] 4. /auth/me returns valid student profile")
    
    # 5. Update Profile (Name & Phone)
    update_payload = {"full_name": "Antigravity Engineer", "phone": "+91 9876543210"}
    code, res = request(f"/students/{student_id}", method="PUT", body=update_payload, token=token)
    assert code == 200 and res["phone"] == "+91 9876543210", f"Update student failed: {code} {res}"
    print("[PASS] 5. Updated profile name and phone number")
    
    # 6. Update Skills
    skills_payload = {
        "skills": [
            {"name": "Python", "category": "programming", "proficiency": "advanced"},
            {"name": "FastAPI", "category": "framework", "proficiency": "intermediate"},
            {"name": "PostgreSQL", "category": "tool", "proficiency": "intermediate"},
            {"name": "Machine Learning", "category": "programming", "proficiency": "intermediate"}
        ]
    }
    code, res = request(f"/students/{student_id}/skills", method="PUT", body=skills_payload, token=token)
    assert code == 200 and len(res) == 4, f"Update skills failed: {code} {res}"
    print(f"[PASS] 6. Added {len(res)} skills to student profile")
    
    # 7. Job Search - results are wrapped in SemanticSearchResult with nested job object
    code, res = request("/jobs/search?q=Machine+Learning&top_k=5", token=token)
    assert code == 200 and len(res) > 0, f"Job search failed: {code} {res}"
    first_result = res[0]
    first_job = first_result.get("job", first_result)  # handle both wrapped and flat
    print(f"[PASS] 7. Semantic Job Search returned {len(res)} results. First: '{first_job['title']}' at '{first_job['company']}' (similarity: {first_result.get('similarity', 'N/A')})")
    
    # 8. Save Job - route: POST /students/{id}/saved-jobs with JSON body
    save_payload = {"job_posting_id": first_job["id"]}
    code, res = request(f"/students/{student_id}/saved-jobs", method="POST", body=save_payload, token=token)
    assert code in (200, 201), f"Save job failed: {code} {res}"
    print(f"[PASS] 8. Saved job bookmark (job_id={first_job['id']})") 
    
    # 9. List Saved Jobs - route: GET /students/{id}/saved-jobs
    code, res = request(f"/students/{student_id}/saved-jobs", token=token)
    assert code == 200 and len(res) >= 1, f"List saved jobs failed: {code} {res}"
    print(f"[PASS] 9. Retrieved {len(res)} saved jobs")
    
    # 10. Apply to Job - route: POST /students/{id}/applications
    apply_payload = {"job_posting_id": first_job["id"]}
    code, res = request(f"/students/{student_id}/applications", method="POST", body=apply_payload, token=token)
    assert code == 201, f"Apply failed: {code} {res}"
    app_id = res["id"]
    print(f"[PASS] 10. Applied to job (application_id={app_id}, status={res['status']})")
    
    # 11. List Applications - route: GET /students/{id}/applications, returns flat list
    code, res = request(f"/students/{student_id}/applications", token=token)
    assert code == 200 and isinstance(res, list) and len(res) >= 1, f"List applications failed: {code} {res}"
    print(f"[PASS] 11. Retrieved application list with {len(res)} entries")
    
    # 12. Check Notifications - route: GET /students/{id}/notifications
    code, res = request(f"/students/{student_id}/notifications", token=token)
    assert code == 200, f"Notifications check failed: {code} {res}"
    total = res.get("total", len(res)) if isinstance(res, dict) else len(res)
    print(f"[PASS] 12. Notification bell check passed (total active items: {total})")
    
    # 13. Start Mock Interview (Domain Practice) - route: POST /students/{id}/interviews
    interview_payload = {"domain": "Machine Learning"}
    code, res = request(f"/students/{student_id}/interviews", method="POST", body=interview_payload, token=token)
    assert code == 201, f"Start interview failed: {code} {res}"
    set_id = res["id"]
    q_count = len(res.get('questions', []))
    print(f"[PASS] 13. Started AI mock interview set id={set_id} with {q_count} domain questions")
    
    print("\n=======================================================")
    print("ALL 13 API WORKFLOWS TESTED AND PASSED PERFECTLY!")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
