"""
Unit tests for naukri-mcp server tools and utilities.
"""
import unittest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from naukri_mcp.auth import decode_jwt_exp, resolve_auth_tokens
from naukri_mcp.utils import resolve_json_source, resolve_pdf_source
from naukri_mcp.serializers import (
    normalize_title,
    build_headline_payload,
    build_summary_payload,
    build_key_skills_payload,
    build_notice_period_payload,
    build_application_payload
)
from naukri_mcp.server import mcp


class TestNaukriMCPServer(unittest.TestCase):

    def test_server_metadata(self):
        self.assertEqual(mcp.name, "naukri-mcp")
        tools = mcp._tool_manager.list_tools() if hasattr(mcp, "_tool_manager") else []
        self.assertGreaterEqual(len(tools), 20)

    def test_resolve_json_source_dict(self):
        d = {"test": 123}
        self.assertEqual(resolve_json_source(d), d)

    def test_resolve_json_source_string(self):
        s = '{"skills": ["Python", "FastAPI"]}'
        res = resolve_json_source(s)
        self.assertEqual(res.get("skills"), ["Python", "FastAPI"])

    def test_resolve_pdf_source_bytes(self):
        b = b"%PDF-1.4 sample content"
        data, name = resolve_pdf_source(b)
        self.assertEqual(data, b)
        self.assertEqual(name, "resume.pdf")

    def test_resolve_pdf_source_base64(self):
        import base64
        raw = b"%PDF-1.4 dummy resume"
        b64 = base64.b64encode(raw).decode("utf-8")
        data, name = resolve_pdf_source(b64)
        self.assertEqual(data, raw)
        self.assertEqual(name, "resume.pdf")

    def test_serializers(self):
        hl = build_headline_payload("Senior AI Engineer", "pid123")
        self.assertEqual(hl["profileId"], "pid123")
        self.assertEqual(hl["profile"]["resumeHeadline"], "Senior AI Engineer")

        np = build_notice_period_payload(30, "pid123")
        self.assertEqual(np["profile"]["noticePeriod"]["value"], "1 Month")

        from naukri_mcp.serializers import build_employment_payload
        emp = build_employment_payload([{"company": "Tech Corp", "position": "Senior Dev", "isCurrent": True}], "pid123")
        self.assertEqual(len(emp["employments"]), 1)
        self.assertEqual(emp["employments"][0]["organization"], "Tech Corp")

        app = build_application_payload("job101", "pid123", answers=[{"id": "q1", "answer": "30 Days"}])
        self.assertEqual(app["applyDetails"]["jobId"], "job101")
        self.assertEqual(len(app["applyDetails"]["questionnaire"]), 1)

        from naukri_mcp.serializers import (
            build_online_profiles_payload,
            build_work_samples_payload,
            build_publications_payload,
            build_presentations_payload,
            build_patents_payload,
            build_certifications_payload
        )
        op = build_online_profiles_payload([{"profile": "LinkedIn", "url": "https://linkedin.com"}], "pid123")
        self.assertEqual(len(op["onlineProfiles"]), 1)
        self.assertEqual(op["onlineProfiles"][0]["profile"], "LinkedIn")

        cert = build_certifications_payload([{"course": "AWS Solutions Architect", "vendor": "AWS"}], "pid123")
        self.assertEqual(len(cert["certifications"]), 1)
        self.assertEqual(cert["certifications"][0]["course"], "AWS Solutions Architect")

    def test_refresh_session_token_tool_exists(self):
        from naukri_mcp.server import refresh_session_token
        self.assertTrue(callable(refresh_session_token))
        res = refresh_session_token(nauk_rt="")
        self.assertIn(res.get("status"), ("success", "error"))

    def test_delete_tools_exist(self):
        from naukri_mcp.tools.delete import (
            delete_project,
            delete_employment,
            delete_it_skill,
            delete_education,
            delete_school,
            delete_online_profile,
            delete_work_sample,
            delete_publication,
            delete_presentation,
            delete_patent,
            delete_certification,
            delete_language,
            delete_resume,
            delete_profile_item
        )
        self.assertTrue(callable(delete_project))
        self.assertTrue(callable(delete_employment))
        self.assertTrue(callable(delete_it_skill))
        self.assertTrue(callable(delete_education))
        self.assertTrue(callable(delete_school))
        self.assertTrue(callable(delete_online_profile))
        self.assertTrue(callable(delete_work_sample))
        self.assertTrue(callable(delete_publication))
        self.assertTrue(callable(delete_presentation))
        self.assertTrue(callable(delete_patent))
        self.assertTrue(callable(delete_certification))
        self.assertTrue(callable(delete_language))
        self.assertTrue(callable(delete_resume))
        self.assertTrue(callable(delete_profile_item))

    def test_education_serializers(self):
        from naukri_mcp.serializers import build_educations_payload, build_schools_payload
        edu_payload = build_educations_payload([
            {
                "educationType": {"id": "1", "value": "UG"},
                "course": {"id": 12, "value": "B.Tech / B.E."},
                "specialisation": {"id": 550, "value": "CSE"},
                "entityInstitute": {"id": "90011161", "value": "PICT"},
                "yearOfStart": 2016,
                "yearOfCompletion": 2020
            }
        ], "pid_123")
        self.assertEqual(len(edu_payload["educations"]), 1)
        self.assertEqual(edu_payload["educations"][0]["courseType"], "F")
        self.assertEqual(edu_payload["educations"][0]["yearOfCompletion"], 2020)

        sch_payload = build_schools_payload([
            {
                "educationType": {"id": "10", "value": "Class X"},
                "schoolBoard": {"id": 1, "value": "CBSE"},
                "schoolCompletionYear": 2014,
                "schoolLevel": 1
            }
        ], "pid_123")
        self.assertEqual(len(sch_payload["schools"]), 1)
        self.assertEqual(sch_payload["schools"][0]["schoolLevel"], 1)
        self.assertEqual(sch_payload["schools"][0]["schoolCompletionYear"], 2014)

    def test_new_profile_serializers(self):
        from naukri_mcp.serializers import (
            build_personal_details_payload,
            build_languages_payload,
            build_job_search_status_payload,
            build_disability_payload,
            build_work_permit_payload,
            build_career_break_payload
        )
        # Personal details
        pd = build_personal_details_payload("pid_123", gender="Female", marital_status="Single", birth_date="1998-06-15", address="Baner", hometown="Pune")
        self.assertEqual(pd["profile"]["gender"], "F")
        self.assertEqual(pd["profile"]["maritalStatus"]["id"], "N")
        self.assertEqual(pd["profile"]["birthDate"], "1998-06-15")

        # Languages
        langs = build_languages_payload([{"lang": "English", "proficiency": "Proficient", "read": True, "write": True, "speak": True}], "pid_123")
        self.assertEqual(len(langs["languages"]), 1)
        self.assertEqual(langs["languages"][0]["lang"], "English")
        self.assertIn("read", langs["languages"][0]["ability"])

        # Job search status
        jss = build_job_search_status_payload("Actively searching jobs", "pid_123")
        self.assertEqual(jss["extendedProfile"]["jbSearchStatus"]["data"][0]["id"], 1)

        # Disability
        dis = build_disability_payload(False, "pid_123")
        self.assertEqual(dis["profile"]["disability"]["isDisabled"], "B")

        # Work permit
        wp = build_work_permit_payload("pid_123", us_work_status="Citizen", countries=["USA", "Canada"])
        self.assertEqual(wp["profile"]["workStatus"]["id"], 1)
        self.assertEqual(len(wp["profile"]["workStatusOtherId"]), 2)

        # Career break
        cb = build_career_break_payload("pid_123", has_break=True, reason="Personal", start_date="2024-09-01", end_date="2024-11-01")
        self.assertTrue(cb["extendedProfile"]["careerBreak"]["data"][0]["comingFromBreak"])
        self.assertEqual(cb["extendedProfile"]["careerBreak"]["data"][0]["reasonOfBreak"]["id"], 5)

    def test_new_tools_exist(self):
        from naukri_mcp.server import (
            update_personal_details,
            update_it_skills,
            add_it_skill,
            update_languages,
            add_language,
            update_job_search_status,
            update_disability,
            delete_disability,
            update_work_permit,
            update_career_break,
            delete_career_break,
            delete_photo,
            resend_email_verification
        )
        self.assertTrue(callable(update_personal_details))
        self.assertTrue(callable(update_it_skills))
        self.assertTrue(callable(add_it_skill))
        self.assertTrue(callable(update_languages))
        self.assertTrue(callable(add_language))
        self.assertTrue(callable(update_job_search_status))
        self.assertTrue(callable(update_disability))
        self.assertTrue(callable(delete_disability))
        self.assertTrue(callable(update_work_permit))
        self.assertTrue(callable(update_career_break))
        self.assertTrue(callable(delete_career_break))
        self.assertTrue(callable(delete_photo))
        self.assertTrue(callable(resend_email_verification))


if __name__ == "__main__":
    unittest.main()

