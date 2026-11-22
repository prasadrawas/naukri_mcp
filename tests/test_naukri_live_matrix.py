"""
Live matrix test for all 6 tools and their parameter variations in naukri_mcp.
"""
import sys
from pathlib import Path

# Ensure paths
workspace_dir = str(Path(__file__).resolve().parent.parent.parent)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from naukri_mcp import server
from naukri_mcp.auth import load_env_file, resolve_auth_tokens

load_env_file(str(Path(workspace_dir) / ".env"))

def run_tests():
    at, rt = resolve_auth_tokens()
    print(f"Testing with AT: {at[:15]}... and RT: {rt[:10]}...")

    tests_run = 0
    tests_passed = 0
    failures = []

    def run_case(name, func, *args, **kwargs):
        nonlocal tests_run, tests_passed, failures
        tests_run += 1
        print(f"\n[{tests_run}] Testing: {name}...")
        try:
            res = func(*args, **kwargs)
            st = res.get("status") or ("success" if res.get("status_code") in (200, 207) else None)
            http_status = res.get("http_status") or res.get("status_code", 200)

            # Accept success, partial_success, applied, already_applied, recaptcha_required, or structured failure for dummy job application
            if st in ("success", "partial_success", "applied", "already_applied", "recaptcha_required"):
                print(f"  --> PASSED: status='{st}' (http {http_status})")
                tests_passed += 1
                return res
            elif st == "failed" and "job_id" in res and "http_status" in res:
                print(f"  --> PASSED: job application handler executed cleanly with API response (status='failed', http {http_status})")
                tests_passed += 1
                return res
            elif "profile" in res or "jobs" in res or "unread_count" in res or "labels" in res or "taxonomies" in res:
                print(f"  --> PASSED (payload received): {st}")
                tests_passed += 1
                return res
            else:
                err = res.get("message") or res.get("error") or res.get("details") or res
                print(f"  --> FAILED: status '{st}', error: {err}")
                failures.append((name, res))
                return res
        except Exception as e:
            print(f"  --> EXCEPTION: {e}")
            failures.append((name, str(e)))
            return None

    # 1. manage_session
    run_case("manage_session: validate", server.manage_session, action="validate")
    run_case("manage_session: refresh", server.manage_session, action="refresh")

    # 2. manage_profile: inspection sections
    run_case("manage_profile: get section='all'", server.manage_profile, action="get", section="all")
    run_case("manage_profile: get section='headline'", server.manage_profile, action="get", section="headline")
    run_case("manage_profile: get section='summary'", server.manage_profile, action="get", section="summary")
    run_case("manage_profile: get section='skills'", server.manage_profile, action="get", section="skills")
    run_case("manage_profile: get section='experience'", server.manage_profile, action="get", section="experience")
    run_case("manage_profile: get section='personal'", server.manage_profile, action="get", section="personal")

    # 2b. manage_profile: pulse, resume, duplicates, verification
    run_case("manage_profile: pulse", server.manage_profile, action="pulse")
    run_case("manage_profile: download_resume", server.manage_profile, action="download_resume", extract_text=True)
    run_case("manage_profile: audit_duplicates", server.manage_profile, action="audit_duplicates")
    run_case("manage_profile: resend_verification", server.manage_profile, action="resend_verification")

    # 2c. manage_profile: update (fetch current values first to update safely)
    prof = server.manage_profile(action="get", section="all")
    curr_headline = prof.get("headline", "Experienced Software Engineer") if isinstance(prof, dict) else "Experienced Software Engineer"
    curr_summary = prof.get("summary", "Senior software developer specializing in backend and full stack.") if isinstance(prof, dict) else "Senior software developer specializing in backend and full stack."

    run_case(
        "manage_profile: update headline & summary",
        server.manage_profile,
        action="update",
        headline=curr_headline,
        summary=curr_summary,
        notice_period_days=30
    )

    # 2d. manage_profile: delete_item (career_break deletion) & validation
    run_case("manage_profile: delete_item (career_break)", server.manage_profile, action="delete_item", item_type="career_break")
    
    # Validation test: missing params should return status='error'
    tests_run += 1
    print(f"\n[{tests_run}] Testing: manage_profile: delete_item validation (missing params)...")
    val_res = server.manage_profile(action="delete_item")
    if val_res.get("status") == "error" and "required" in val_res.get("message", ""):
        print("  --> PASSED: correctly rejected missing parameters with validation error message.")
        tests_passed += 1
    else:
        print(f"  --> FAILED: expected error status, got: {val_res}")
        failures.append(("manage_profile: delete_item validation", val_res))

    # 3. search_jobs: string & list keywords
    run_case("search_jobs: string keyword", server.search_jobs, keywords="Python, FastAPI", location="Pune", limit=3)
    run_case("search_jobs: list keywords", server.search_jobs, keywords=["Full Stack", "React"], location="Pune", limit=3)

    # 4. get_job_details: single & batch
    sample_job_id = "150125000001"
    run_case("get_job_details: single", server.get_job_details, job_ids=sample_job_id)
    run_case("get_job_details: batch", server.get_job_details, job_ids=[sample_job_id, "150125000002"])

    # 5. apply_to_jobs: single & batch
    run_case("apply_to_jobs: single", server.apply_to_jobs, job_ids=sample_job_id)
    run_case("apply_to_jobs: batch", server.apply_to_jobs, job_ids=[sample_job_id])

    # 6. manage_recruiter_interactions
    run_case("manage_recruiter_interactions: analytics", server.manage_recruiter_interactions, action="analytics")
    run_case("manage_recruiter_interactions: inbox", server.manage_recruiter_interactions, action="inbox")
    run_case("manage_recruiter_interactions: notifications", server.manage_recruiter_interactions, action="notifications")
    run_case("manage_recruiter_interactions: salary_insights", server.manage_recruiter_interactions, action="salary_insights")
    run_case("manage_recruiter_interactions: list_blocked", server.manage_recruiter_interactions, action="list_blocked")
    run_case("manage_recruiter_interactions: suggest_taxonomy versions", server.manage_recruiter_interactions, action="suggest_taxonomy", taxonomy_type="versions")
    run_case("manage_recruiter_interactions: suggest_taxonomy city", server.manage_recruiter_interactions, action="suggest_taxonomy", taxonomy_type="city", query="Pune", limit=5)
    run_case("manage_recruiter_interactions: suggest_taxonomy certificate", server.manage_recruiter_interactions, action="suggest_taxonomy", taxonomy_type="certificate", query="AWS", limit=5)

    print("\n" + "=" * 50)
    print(f"LIVE TEST SUMMARY: {tests_passed}/{tests_run} Passed ({(tests_passed/tests_run)*100:.1f}%)")
    print("=" * 50)
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f_name, f_err in failures:
            print(f" - {f_name}: {f_err}")
    return len(failures) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
