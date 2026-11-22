"""
Naukri MCP Server implementation using official FastMCP / MCPServer SDK.
Provides Tools, Resources, and Prompts in a unified, optimized 6-tool architecture.
"""
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Literal

from starlette.requests import Request
from starlette.responses import Response, JSONResponse, HTMLResponse

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except Exception:
    from mcp.server.fastmcp import FastMCP  # type: ignore

from naukri_mcp.tools import profile, resume, photo, duplicates, analytics, taxonomy, jobs, delete

# Initialize the FastMCP server with unified 6-tool architecture
mcp = FastMCP(
    "naukri-mcp",
    instructions=(
        "Naukri MCP Server (Unified 6-Tool Architecture): Production MCP server for Naukri candidate profile "
        "management, smart job search and applications, recruiter interactions, and session maintenance.\n\n"
        "CORE TOOLS (Total 6 Tools):\n"
        "1. `manage_profile`: Candidate profile inspection, section updates (headline, summary, skills, experience, "
        "education, personal details, accomplishments), activity pulse, resume & photo management, duplicate auditing, and safe item deletions.\n"
        "2. `search_jobs`: Search live jobs on Naukri by keyword, location, and experience, categorized by application flow.\n"
        "3. `get_job_details`: Inspect comprehensive job descriptions, requirements, and screening questionnaires for one or more job IDs.\n"
        "4. `apply_to_jobs`: Submit job applications for single or multiple jobs with questionnaire answers.\n"
        "5. `manage_recruiter_interactions`: Recruiter inbox & emails, search appearance analytics, notifications, salary insights, employer blocking, and taxonomy autosuggest.\n"
        "6. `manage_session`: Verify active session authentication or renew access token."
    )
)


# ---------------------------------------------------------------------------
# CUSTOM HTTP ROUTES (Health, Landing Page)
# ---------------------------------------------------------------------------

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    """Public health check endpoint for monitoring and cloud container platforms."""
    return JSONResponse({
        "status": "healthy",
        "service": "naukri-mcp",
        "version": "2.0.0"
    })


@mcp.custom_route("/", methods=["GET", "POST", "OPTIONS", "HEAD"])
async def index_route(request: Request) -> Response:
    """Root info page or transparent redirect to /sse when called with token or SSE headers."""
    if request.method == "OPTIONS":
        return Response(status_code=200)

    # If request contains token query parameter or requests SSE stream, redirect to /sse
    if "rt" in request.query_params or "nauk_rt" in request.query_params or "text/event-stream" in request.headers.get("accept", ""):
        from starlette.responses import RedirectResponse
        target_url = "/sse"
        if request.scope.get("query_string"):
            target_url += "?" + request.scope["query_string"].decode("utf-8")
        return RedirectResponse(url=target_url, status_code=307)

    host = request.headers.get("host", "localhost:8000")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    base_url = f"{scheme}://{host}"
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Naukri MCP Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 820px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #2d3748; }}
        h1 {{ color: #1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-top: 10px; }}
        code {{ background: #edf2f7; padding: 3px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: #d53f8c; }}
        pre {{ background: #1a202c; color: #f7fafc; padding: 16px; border-radius: 8px; overflow-x: auto; }}
        pre code {{ background: none; color: inherit; padding: 0; }}
        .badge {{ display: inline-block; background: #38a169; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card {{ background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 22px; margin-top: 24px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        a {{ color: #3182ce; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <span class="badge">Running</span>
    <h1>Naukri MCP Server (Unified 6-Tool Architecture)</h1>
    <p>Production Model Context Protocol (MCP) server providing 6 consolidated tools for automated Naukri candidate profile management, recruiter visibility optimization, and smart job applications.</p>
    
    <div class="card">
        <h3>Connect to Claude Web / Claude Desktop / Cursor / Gemini</h3>
        <p>Add this server to your MCP configuration with your personalized SSE URL:</p>
        <pre><code>{{
  "mcpServers": {{
    "naukri": {{
      "url": "{base_url}/sse?rt=YOUR_NAUK_RT_COOKIE"
    }}
  }}
}}</code></pre>
        <h4>URL Parameters:</h4>
        <ul>
            <li><code>?rt=&lt;token&gt;</code>: (Required) Your <code>nauk_rt</code> refresh cookie from naukri.com.</li>
            <li><code>&amp;resume=&lt;url&gt;</code>: (Optional) HTTP/HTTPS URL to your candidate master resume JSON.</li>
            <li><code>&amp;pdf=&lt;url&gt;</code>: (Optional) HTTP/HTTPS URL to download your PDF resume for 1-click uploads.</li>
        </ul>
        <p>Custom HTTP headers are also supported: <code>X-Naukri-RT</code>, <code>X-Master-Resume</code>, <code>X-Resume-Pdf</code>.</p>
    </div>

    <div class="card">
        <h3>Core Tools (Unified 6-Tool Architecture):</h3>
        <ul>
            <li><code>manage_profile</code>: Get profile, update any section, pulse recruiter rank, sync master resume, upload/download resume & photo, audit duplicates, delete items.</li>
            <li><code>search_jobs</code>: Search jobs by keywords, location, experience with categorization.</li>
            <li><code>get_job_details</code>: Comprehensive job specifications and screening questionnaires (single or batch).</li>
            <li><code>apply_to_jobs</code>: Submit job applications for single or multiple jobs with questionnaire answers.</li>
            <li><code>manage_recruiter_interactions</code>: Analytics, inbox, notifications, salary insights, blocked employers, and taxonomy search.</li>
            <li><code>manage_session</code>: Validate session authentication and renew access token.</li>
        </ul>
    </div>

    <div class="card">
        <h3>How to get your <code>nauk_rt</code> cookie:</h3>
        <ol>
            <li>Log in to <a href="https://www.naukri.com" target="_blank">naukri.com</a> in your browser.</li>
            <li>Open Developer Tools (F12 or Cmd+Option+I) &rarr; <strong>Application</strong> / <strong>Storage</strong> &rarr; <strong>Cookies</strong> &rarr; <code>https://www.naukri.com</code>.</li>
            <li>Copy the value of the <code>nauk_rt</code> cookie.</li>
        </ol>
    </div>

    <div class="card">
        <h3>Server Status &amp; Diagnostics</h3>
        <p><a href="/health"><code>/health</code></a> &mdash; Health probe endpoint for container orchestrators and uptime checks.</p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------------------------
# MCP TOOLS (Unified 6-Tool Architecture)
# ---------------------------------------------------------------------------

@mcp.tool()
def manage_profile(
    action: Literal[
        "get",
        "update",
        "pulse",
        "sync_master",
        "audit_duplicates",
        "delete_item",
        "upload_resume",
        "download_resume",
        "delete_resume",
        "upload_photo",
        "delete_photo",
        "resend_verification"
    ] = "get",
    section: str = "all",
    headline: Optional[str] = None,
    summary: Optional[str] = None,
    key_skills: Optional[List[str]] = None,
    notice_period_days: Optional[int] = None,
    location: Optional[Dict[str, Any]] = None,
    career_profile: Optional[Dict[str, Any]] = None,
    work_experience: Optional[List[Dict[str, Any]]] = None,
    projects: Optional[List[Dict[str, Any]]] = None,
    educations: Optional[List[Dict[str, Any]]] = None,
    schools: Optional[List[Dict[str, Any]]] = None,
    it_skills: Optional[List[Dict[str, Any]]] = None,
    personal_details: Optional[Dict[str, Any]] = None,
    languages: Optional[List[Dict[str, Any]]] = None,
    job_search_status: Optional[str] = None,
    disability: Optional[Dict[str, Any]] = None,
    work_permit: Optional[Dict[str, Any]] = None,
    career_break: Optional[Dict[str, Any]] = None,
    accomplishments: Optional[Dict[str, Any]] = None,
    add_item: Optional[Dict[str, Any]] = None,
    item_type: Optional[str] = None,
    item_id: Optional[str] = None,
    source: Optional[str] = None,
    output_path: Optional[str] = None,
    extract_text: bool = True,
    include_base64: bool = False,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Candidate profile management: view profile details, update profile fields, boost recruiter search ranking,
    synchronize master resume, manage resume documents and photo, audit duplicates, and safely delete profile items.

    :param action: Operation to perform:
                   - 'get': Retrieve candidate profile details (specify 'section', default: 'all').
                   - 'update': Modify provided profile fields leaving unspecified fields unchanged.
                   - 'pulse': Touch profile pulse to bump modification timestamp and boost search rank.
                   - 'sync_master': Synchronize profile from master resume source.
                   - 'audit_duplicates': Audit and detect duplicate profile entries.
                   - 'delete_item': Delete specific profile entity by item_type and item_id.
                   - 'upload_resume': Upload PDF resume from file path, URL, or base64.
                   - 'download_resume': Download active resume PDF and extract text.
                   - 'delete_resume': Delete uploaded resume document.
                   - 'upload_photo': Upload profile display photo.
                   - 'delete_photo': Delete profile display photo.
                   - 'resend_verification': Resend profile email verification.
    :param section: Profile section to inspect when action='get' ('all', 'headline', 'summary', 'skills', 'experience', 'projects', 'education', 'personal').
    :param headline: Professional resume headline (action='update').
    :param summary: Profile summary text (action='update').
    :param key_skills: List of key skill strings (action='update').
    :param notice_period_days: Official notice period in days (0 for Serving Notice, 15, 30, 60, 90) (action='update').
    :param location: Dict with 'city_id' and 'city_name' (e.g. {'city_id': 139, 'city_name': 'Pune'}) (action='update').
    :param career_profile: Career preferences dict (expected_ctc, preferred_cities, target_roles, desired_job_types) (action='update').
    :param work_experience: List of employment history dicts (action='update').
    :param projects: List of project dicts (action='update').
    :param educations: List of education/degree dicts (action='update').
    :param schools: List of 10th/12th school records (action='update').
    :param it_skills: List of IT skills with experience and lastUsed (action='update').
    :param personal_details: Dict with gender, marital_status, birth_date, hometown, pincode, etc. (action='update').
    :param languages: List of languages with proficiency (action='update').
    :param job_search_status: Search status ('actively_looking', 'casually_exploring', 'not_looking') (action='update').
    :param disability: Dict with disability details (action='update').
    :param work_permit: Dict with US status and authorized country list (action='update').
    :param career_break: Dict with break details, reason, start_date, end_date (action='update').
    :param accomplishments: Dict of accomplishments (onlineProfiles, workSamples, publications, presentations, patents, certifications) (action='update').
    :param add_item: Dict with 'type' ('project'|'it_skill'|'language') and item fields to add a single item without replacing list (action='update').
    :param item_type: Entity type for action='delete_item' ('projects', 'employments', 'itskills', 'educations', 'schools', 'languages', 'disability', 'career_break').
    :param item_id: Unique record ID string to delete for action='delete_item'.
    :param source: File path, URL, or base64 data for upload actions (upload_resume, upload_photo, sync_master).
    :param output_path: Local filesystem destination path when action='download_resume'.
    :param extract_text: Whether to parse text from PDF when action='download_resume' (default True).
    :param include_base64: Whether to return base64 payload when action='download_resume' (default False).
    """
    if action == "get":
        return profile.get_profile(section=section, nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "pulse":
        return profile.touch_profile_pulse(nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "sync_master":
        return profile.sync_full_profile(resume_source=source or "", nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "audit_duplicates":
        return duplicates.audit_profile_duplicates(nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "delete_item":
        norm_type = (item_type or "").strip().lower()
        if norm_type in ("disability",):
            return profile.delete_disability(nauk_at=nauk_at, nauk_rt=nauk_rt)
        elif norm_type in ("career_break", "careerbreak", "break"):
            return profile.delete_career_break(nauk_at=nauk_at, nauk_rt=nauk_rt)
        elif norm_type and item_id:
            return delete.delete_profile_item(item_type=item_type, item_id=item_id, nauk_at=nauk_at, nauk_rt=nauk_rt)
        else:
            return {
                "status": "error",
                "message": "Both item_type and item_id are required for action='delete_item' (e.g. item_type='projects', item_id='12345')."
            }

    elif action == "upload_resume":
        return resume.upload_resume(source=source, nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "download_resume":
        return resume.download_resume(
            output_path=output_path,
            extract_text=extract_text,
            include_base64=include_base64,
            nauk_at=nauk_at,
            nauk_rt=nauk_rt
        )

    elif action == "delete_resume":
        return delete.delete_resume(nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "upload_photo":
        return photo.upload_photo(source=source, nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "delete_photo":
        return delete.delete_photo(nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "resend_verification":
        return profile.resend_email_verification(nauk_at=nauk_at, nauk_rt=nauk_rt)

    elif action == "update":
        updates_performed = []
        errors = []

        if headline is not None:
            res = profile.update_headline(headline=headline, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("headline")
            else:
                errors.append({"section": "headline", "error": res})

        if summary is not None:
            res = profile.update_summary(summary=summary, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("summary")
            else:
                errors.append({"section": "summary", "error": res})

        if key_skills is not None:
            skills_val = ", ".join(key_skills) if isinstance(key_skills, list) else str(key_skills)
            res = profile.update_key_skills(skills_csv=skills_val, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("key_skills")
            else:
                errors.append({"section": "key_skills", "error": res})

        if notice_period_days is not None:
            res = profile.update_notice_period(days=notice_period_days, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("notice_period")
            else:
                errors.append({"section": "notice_period", "error": res})

        if location is not None:
            c_id = location.get("city_id") or location.get("id") or 139
            c_name = location.get("city_name") or location.get("city") or "Pune"
            res = profile.update_location(city_id=int(c_id), city_name=str(c_name), nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("location")
            else:
                errors.append({"section": "location", "error": res})

        if career_profile is not None:
            res = profile.update_career_profile(**career_profile, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("career_profile")
            else:
                errors.append({"section": "career_profile", "error": res})

        if work_experience is not None:
            res = profile.update_work_experience(work_list=work_experience, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("work_experience")
            else:
                errors.append({"section": "work_experience", "error": res})

        if projects is not None:
            res = profile.update_projects(projects_list=projects, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("projects")
            else:
                errors.append({"section": "projects", "error": res})

        if educations is not None:
            res = profile.update_educations(educations_list=educations, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("educations")
            else:
                errors.append({"section": "educations", "error": res})

        if schools is not None:
            res = profile.update_schools(schools_list=schools, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("schools")
            else:
                errors.append({"section": "schools", "error": res})

        if it_skills is not None:
            res = profile.update_it_skills(skills_list=it_skills, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("it_skills")
            else:
                errors.append({"section": "it_skills", "error": res})

        if personal_details is not None:
            res = profile.update_personal_details(**personal_details, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("personal_details")
            else:
                errors.append({"section": "personal_details", "error": res})

        if languages is not None:
            res = profile.update_languages(languages_list=languages, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("languages")
            else:
                errors.append({"section": "languages", "error": res})

        if job_search_status is not None:
            res = profile.update_job_search_status(status_code_or_name=job_search_status, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("job_search_status")
            else:
                errors.append({"section": "job_search_status", "error": res})

        if disability is not None:
            res = profile.update_disability(**disability, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("disability")
            else:
                errors.append({"section": "disability", "error": res})

        if work_permit is not None:
            res = profile.update_work_permit(**work_permit, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("work_permit")
            else:
                errors.append({"section": "work_permit", "error": res})

        if career_break is not None:
            res = profile.update_career_break(**career_break, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("career_break")
            else:
                errors.append({"section": "career_break", "error": res})

        if accomplishments is not None:
            res = profile.update_accomplishments(accomplishments=accomplishments, nauk_at=nauk_at, nauk_rt=nauk_rt)
            if res.get("status") == "success":
                updates_performed.append("accomplishments")
            else:
                errors.append({"section": "accomplishments", "error": res})

        if add_item is not None:
            item_kind = add_item.get("type", "").strip().lower()
            item_data = add_item.get("data") or {k: v for k, v in add_item.items() if k != "type"}
            if item_kind in ("project", "projects"):
                res = profile.add_project(project_data=item_data, nauk_at=nauk_at, nauk_rt=nauk_rt)
            elif item_kind in ("it_skill", "itskill", "skill", "skills"):
                res = profile.add_it_skill(**item_data, nauk_at=nauk_at, nauk_rt=nauk_rt)
            elif item_kind in ("language", "languages"):
                res = profile.add_language(**item_data, nauk_at=nauk_at, nauk_rt=nauk_rt)
            else:
                res = {"status": "error", "message": f"Unknown add_item type: '{item_kind}'"}

            if res.get("status") == "success":
                updates_performed.append(f"add_{item_kind}")
            else:
                errors.append({"section": f"add_{item_kind}", "error": res})

        return {
            "status": "success" if not errors else ("partial_success" if updates_performed else "error"),
            "updated_sections": updates_performed,
            "errors": errors if errors else None
        }

    return {"status": "error", "message": f"Unknown action: '{action}'"}


@mcp.tool()
def search_jobs(
    keywords: Union[str, List[str]],
    location: str = "Pune",
    experience: int = 5,
    limit: int = 20,
    job_age_days: int = 3,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search live jobs on Naukri and categorize results by application flow (1-Click Direct vs Screening Questionnaire).

    :param keywords: Comma-separated string or list of keyword queries (e.g. 'Python, FastAPI, Full Stack').
    :param location: Target city or location string (default 'Pune').
    :param experience: Minimum years of experience (default 5).
    :param limit: Maximum jobs to return (default 20).
    :param job_age_days: Only include jobs posted within the last N days (default 3).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return jobs.search_jobs(
        keywords=keywords,
        location=location,
        experience=experience,
        limit=limit,
        job_age_days=job_age_days,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def get_job_details(
    job_ids: Union[int, str, List[Union[int, str]]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve complete job description, requirements, company info, and screening questionnaire schema for one or more job IDs.
    Accepts a single job ID (e.g. "1234567") or a list of job IDs (e.g. ["1234567", "7654321"]).

    :param job_ids: Numerical job ID string/int or list of job IDs from Naukri.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    if isinstance(job_ids, list):
        results = []
        for jid in job_ids:
            res = jobs.get_job_details(job_id=str(jid).strip(), nauk_at=nauk_at, nauk_rt=nauk_rt)
            results.append(res)
        return {"status": "success", "count": len(results), "jobs": results}

    return jobs.get_job_details(job_id=str(job_ids).strip(), nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def apply_to_jobs(
    job_ids: Union[int, str, List[Union[int, str]]],
    answers: Optional[List[Dict[str, Any]]] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit job applications to one or more Naukri jobs with optional screening questionnaire answers.
    Accepts a single job ID or a list of job IDs.

    :param job_ids: Numerical job ID string/int or list of job IDs from Naukri.
    :param answers: Optional list of questionnaire answers, each dict with {'questionId': str, 'answer': str}.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    if isinstance(job_ids, list):
        results = []
        for jid in job_ids:
            res = jobs.apply_to_job(job_id=str(jid).strip(), answers=answers, nauk_at=nauk_at, nauk_rt=nauk_rt)
            results.append(res)
        return {"status": "success", "count": len(results), "results": results}

    return jobs.apply_to_job(job_id=str(job_ids).strip(), answers=answers, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def manage_recruiter_interactions(
    action: Literal[
        "analytics",
        "inbox",
        "notifications",
        "salary_insights",
        "list_blocked",
        "block_company",
        "suggest_taxonomy"
    ] = "analytics",
    company_id: Optional[str] = None,
    company_name: Optional[str] = None,
    taxonomy_type: str = "certificate",
    query: str = "",
    limit: int = 20,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Recruiter interactions, candidate visibility analytics, employer privacy, and central taxonomies.

    :param action: Operation to perform:
                   - 'analytics': Recruiter search appearances, profile views, completeness score, and missing sections.
                   - 'inbox': Recruiter messages, interview invitations, and unread communication counts.
                   - 'notifications': System notification counters and recommended job alerts.
                   - 'salary_insights': Compensation component breakdown labels (Fixed, Variable, Stocks/RSUs).
                   - 'list_blocked': List companies blocked from viewing your profile.
                   - 'block_company': Block an employer from seeing your profile (requires company_id & company_name).
                   - 'suggest_taxonomy': Search standardized entities (skills, certificates, cities, or versions).
    :param company_id: Company ID string (required for 'block_company').
    :param company_name: Company name string (required for 'block_company').
    :param taxonomy_type: One of 'certificate', 'city', 'language', 'country', 'state', or 'versions'.
    :param query: Search string for taxonomy autosuggest (action='suggest_taxonomy').
    :param limit: Maximum taxonomy results to return (default 20).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    if action == "analytics":
        return analytics.get_profile_analytics(nauk_at=nauk_at, nauk_rt=nauk_rt)
    elif action == "inbox":
        return analytics.get_recruiter_inbox(nauk_at=nauk_at, nauk_rt=nauk_rt)
    elif action == "notifications":
        return analytics.get_notification_summary(nauk_at=nauk_at, nauk_rt=nauk_rt)
    elif action == "salary_insights":
        return analytics.get_salary_labels(nauk_at=nauk_at, nauk_rt=nauk_rt)
    elif action == "list_blocked":
        return analytics.get_blocked_companies(nauk_at=nauk_at, nauk_rt=nauk_rt)
    elif action == "block_company":
        if not company_id or not company_name:
            return {"status": "error", "message": "Both company_id and company_name are required to block a company."}
        return analytics.block_company(company_id=company_id, company_name=company_name, nauk_at=nauk_at, nauk_rt=nauk_rt)
    elif action == "suggest_taxonomy":
        if taxonomy_type == "versions":
            return taxonomy.get_taxonomy_versions(nauk_at=nauk_at, nauk_rt=nauk_rt)
        return taxonomy.search_taxonomy(entity_type=taxonomy_type, query=query, limit=limit, nauk_at=nauk_at, nauk_rt=nauk_rt)

    return {"status": "error", "message": f"Unknown action: '{action}'"}


@mcp.tool()
def manage_session(
    action: Literal["validate", "refresh"] = "validate",
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Session verification, token expiration inspection, and automatic token renewal.

    :param action: 'validate' (inspect current token expiry and status),
                   'refresh' (renew access token NAUK_AT using refresh token NAUK_RT).
    :param nauk_rt: Optional override refresh token (defaults to session RT or NAUK_RT in environment).
    """
    from naukri_mcp.auth import (
        refresh_token_via_nauk_rt,
        load_env_file,
        decode_jwt_exp,
        current_session_rt,
        current_session_id,
        SESSION_STORE
    )
    load_env_file()
    rt = (nauk_rt or current_session_rt.get() or os.getenv("NAUK_RT", "")).strip()
    if not rt:
        return {
            "status": "error",
            "message": "No NAUK_RT refresh token provided in parameters, active session, or environment."
        }

    if action == "refresh":
        success, new_at = refresh_token_via_nauk_rt(rt)
        if success:
            exp_sec = decode_jwt_exp(new_at)
            sid = current_session_id.get()
            if sid and sid in SESSION_STORE:
                SESSION_STORE[sid]["at"] = new_at
                SESSION_STORE[sid]["last_seen"] = time.time()
            return {
                "status": "success",
                "message": "Naukri session token renewed successfully.",
                "nauk_at_preview": f"{new_at[:15]}...{new_at[-10:]}",
                "expires_at_timestamp": exp_sec,
                "expires_in_minutes": max(0, int((exp_sec - time.time()) / 60)) if exp_sec else None,
                "multi_tenant_session_id": sid or "local_environment"
            }
        return {
            "status": "error",
            "message": "Failed to refresh token via Naukri CloudGateway.",
            "hint": "Your NAUK_RT cookie may have expired or is invalid. Log in to naukri.com to obtain a fresh nauk_rt cookie."
        }
    else:  # validate
        current_at = os.getenv("NAUK_AT", "").strip()
        exp_sec = decode_jwt_exp(current_at) if current_at else 0
        is_expired = (exp_sec < time.time()) if exp_sec else True
        sid = current_session_id.get()
        return {
            "status": "success",
            "authenticated": bool(rt),
            "access_token_present": bool(current_at),
            "access_token_expired": is_expired,
            "expires_in_minutes": max(0, int((exp_sec - time.time()) / 60)) if exp_sec and not is_expired else 0,
            "multi_tenant_session_id": sid or "local_environment"
        }


# ---------------------------------------------------------------------------
# MCP RESOURCES
# ---------------------------------------------------------------------------

@mcp.resource("naukri://profile/current")
def resource_profile_current() -> str:
    """Live candidate profile JSON from Naukri CloudGateway."""
    data = profile.get_profile(section="all")
    return json.dumps(data, indent=2)


@mcp.resource("naukri://analytics/dashboard")
def resource_analytics_dashboard() -> str:
    """Live recruiter views, search appearances, and incompleteness audit."""
    data = analytics.get_profile_analytics()
    return json.dumps(data, indent=2)


@mcp.resource("naukri://inbox/recruiter-mails")
def resource_inbox_mails() -> str:
    """Live recruiter messages, interview invitations, and unread communications."""
    data = analytics.get_recruiter_inbox()
    return json.dumps(data, indent=2)


@mcp.resource("naukri://taxonomy/versions")
def resource_taxonomy_versions() -> str:
    """Registry of all 32 central taxonomies in Naukri."""
    data = taxonomy.get_taxonomy_versions()
    return json.dumps(data, indent=2)


@mcp.resource("naukri://candidate/master-resume")
def resource_candidate_master_resume() -> str:
    """
    Source of truth master resume and candidate profile facts (skills, projects, education,
    experience tenure, contact, and career preferences).
    Configurable via dynamic session resume URL/path, or MASTER_RESUME_PATH environment variable.
    """
    from naukri_mcp.auth import current_session_resume_url
    session_resume = current_session_resume_url.get().strip()
    if session_resume:
        if session_resume.startswith("http://") or session_resume.startswith("https://"):
            try:
                import urllib.request
                req = urllib.request.Request(session_resume, headers={"User-Agent": "Naukri-MCP/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode("utf-8")
            except Exception as e:
                return json.dumps({"error": f"Failed fetching master resume from session URL: {str(e)}"})
        p = Path(session_resume).expanduser().resolve()
        if p.exists() and p.is_file():
            try:
                return p.read_text(encoding="utf-8")
            except Exception as e:
                return json.dumps({"error": f"Failed reading master resume from {p}: {str(e)}"})

    custom_path = os.getenv("MASTER_RESUME_PATH", "").strip()
    candidate_paths = []
    if custom_path:
        candidate_paths.append(Path(custom_path).expanduser().resolve())

    # Fallback to local master_resume.json if placed in root/working directory
    candidate_paths.append(Path.cwd() / "master_resume.json")

    for p in candidate_paths:
        if p.exists() and p.is_file():
            try:
                return p.read_text(encoding="utf-8")
            except Exception as e:
                return json.dumps({"error": f"Failed reading master resume from {p}: {str(e)}"})

    return json.dumps({
        "error": "No master resume provided.",
        "hint": "Provide a resume URL via '?resume=https://...' in your MCP SSE URL, set the X-Master-Resume header, or configure MASTER_RESUME_PATH environment variable."
    })


@mcp.resource("naukri://rules/platform-guidelines")
def resource_platform_guidelines() -> str:
    """
    Naukri CloudGateway schemas, validation constraints, accomplishment quotas, and safety rules.
    """
    guidelines = {
        "platform_constraints": {
            "accomplishment_quota_limit": 5,
            "quota_capped_sections": [
                "onlineProfile",
                "workSample",
                "publication",
                "presentation",
                "patent",
                "certifications"
            ],
            "quota_handling_rule": "Naukri strictly rejects more than 5 items per accomplishment section with HTTP 400. In-place updates MUST query existing IDs first and pass 'id' in the payload to mutate rather than create duplicates.",
            "career_break_rule": "Career break dates must not overlap with any active or historical employment tenures.",
            "work_permit_format": "Expects 'workStatus' as {'id': int, 'value': str} (1 Citizen, 2 Green Card, 3 Have H1, 4 Need H1) and 'workStatusOtherId' as a list of country objects.",
            "it_skills_format": "Each skill entry expects 'skill', 'version', 'lastUsed' (integer year), and 'experienceTime' ({'year': int, 'month': int})."
        },
        "safety_and_anti_bot": {
            "recaptcha_boundary": "Naukri's public search API (jobapi/v3/search) enforces human verification (reCAPTCHA) on automated calls. Never attempt to automate or bypass CAPTCHAs. Direct users to search via browser or provide target Job IDs / URLs.",
            "irreversible_deletions": "All deletion tools permanently erase items from the live Naukri candidate account. Always confirm with the user before calling deletion tools."
        }
    }
    return json.dumps(guidelines, indent=2)


@mcp.resource("naukri://tools/directory")
def resource_tools_directory() -> str:
    """
    Categorized directory of the unified 6 MCP tools with functional grouping and safety tiers.
    """
    directory = {
        "total_tools": 6,
        "architecture": "Unified 6-Tool Architecture",
        "tools": {
            "manage_profile": {
                "actions": [
                    "get", "update", "pulse", "sync_master", "audit_duplicates",
                    "delete_item", "upload_resume", "download_resume", "delete_resume",
                    "upload_photo", "delete_photo", "resend_verification"
                ],
                "description": "Candidate profile inspection, section updates, activity pulse, resume & photo, and deletions."
            },
            "search_jobs": {
                "description": "Parametric search across Naukri open jobs categorized by apply flow."
            },
            "get_job_details": {
                "description": "Comprehensive job requirements, specs, and screening questionnaire schema (single or batch)."
            },
            "apply_to_jobs": {
                "description": "Stateless job application submission for single or batch jobs with questionnaire answers."
            },
            "manage_recruiter_interactions": {
                "actions": [
                    "analytics", "inbox", "notifications", "salary_insights",
                    "list_blocked", "block_company", "suggest_taxonomy"
                ],
                "description": "Recruiter communications, search appearance analytics, notifications, employer blocking, and taxonomies."
            },
            "manage_session": {
                "actions": ["validate", "refresh"],
                "description": "Multi-tenant session verification and access token renewal."
            }
        }
    }
    return json.dumps(directory, indent=2)


# ---------------------------------------------------------------------------
# MCP PROMPTS
# ---------------------------------------------------------------------------

@mcp.prompt()
def audit_profile() -> str:
    """Prompt template to inspect profile completeness and propose optimizations."""
    return (
        "You are an expert technical career advisor analyzing a candidate's Naukri profile.\n"
        "1. Call 'manage_recruiter_interactions' with action='analytics' to inspect recruiter search appearances, profile views, and incomplete sections.\n"
        "2. Call 'manage_profile' with action='get' and section='headline' to inspect existing headline and positioning.\n"
        "3. Provide actionable suggestions to improve recruiter search appearances and achieve 100% profile completeness.\n"
        "SAFETY NOTE: If recommending removal of duplicate or obsolete items, confirm with user before invoking delete actions."
    )


@mcp.prompt()
def manage_profile_deletions() -> str:
    """Prompt template for safely reviewing and deleting profile items with caution."""
    return (
        "CRITICAL CAUTION: You are about to manage deletions on a live candidate profile.\n"
        "Deleting projects, employments, education, or skills permanently removes them from Naukri.\n"
        "1. First call 'manage_profile' with action='get' (e.g. section='projects') to list existing items and their unique IDs.\n"
        "2. Display the exact items to the user with their titles, dates, and IDs.\n"
        "3. Explicitly ask for user confirmation before deleting.\n"
        "4. Only upon explicit confirmation, invoke 'manage_profile' with action='delete_item', item_type='<type>', and item_id='<id>'.\n"
        "5. Re-fetch the section to confirm clean deletion."
    )


@mcp.prompt()
def resolve_screening_questionnaire(job_id: str) -> str:
    """Prompt template to retrieve job questionnaire and resolve answers truthfully."""
    return (
        f"You are assisting a candidate with applying for Naukri Job ID {job_id}.\n"
        f"1. Call 'get_job_details' with job_ids='{job_id}' to retrieve the screening questionnaire.\n"
        "2. Review the questions (e.g. notice period, CTC, experience, specific technologies).\n"
        "3. Formulate concise, truthful answers matching candidate facts.\n"
        "4. Call 'apply_to_jobs' with the resolved answers array to submit the application."
    )


@mcp.prompt()
def job_search_and_apply(keywords: str, location: str = "Pune", experience: int = 5) -> str:
    """Prompt template for automated job search and application workflow."""
    return (
        f"Search and evaluate jobs on Naukri for keywords: '{keywords}' in '{location}' with {experience} YOE.\n"
        "1. Call 'search_jobs' to find matching open positions.\n"
        "2. Categorize results into Category 1 (Direct 1-Click Apply) and Category 2 (Questionnaire).\n"
        "3. For Category 1 jobs, call 'apply_to_jobs' directly.\n"
        "4. For Category 2 jobs, call 'get_job_details', resolve the screening questions, and submit via 'apply_to_jobs'.\n"
        "5. Output a structured summary table showing applied jobs and any skipped positions."
    )


@mcp.prompt()
def tailor_and_update_profile(target_role: str = "Full Stack Developer") -> str:
    """Prompt template to synchronize candidate master resume with Naukri profile for a target role."""
    return (
        f"You are synchronizing and tailoring the candidate's Naukri profile for target role: '{target_role}'.\n"
        "1. Read resource 'naukri://candidate/master-resume' to obtain authenticated candidate facts, projects, and skills.\n"
        "2. Read resource 'naukri://rules/platform-guidelines' to review accomplishment quotas and date rules.\n"
        "3. Inspect current live state via 'manage_profile(action=\"get\", section=\"all\")'.\n"
        "4. Update core positioning via 'manage_profile(action=\"update\", headline=\"...\", summary=\"...\", key_skills=[...])'.\n"
        "5. Confirm all updates by reading resource 'naukri://profile/current'."
    )


@mcp.prompt()
def daily_profile_refresh() -> str:
    """Prompt template for daily candidate visibility maintenance and recruiter communications audit."""
    return (
        "Perform daily Naukri candidate profile maintenance to maximize recruiter visibility:\n"
        "1. Call 'manage_profile' with action='pulse' to refresh the profile modification timestamp and bump search ranking.\n"
        "2. Read resource 'naukri://inbox/recruiter-mails' or call 'manage_recruiter_interactions' with action='inbox' to audit unread recruiter messages.\n"
        "3. Call 'manage_recruiter_interactions' with action='notifications' to check recruiter views and shortlist alerts.\n"
        "4. Read resource 'naukri://analytics/dashboard' to evaluate search appearance trends over the last 30 days.\n"
        "5. Summarize key actions and recruiter opportunities clearly for the candidate."
    )


@mcp.prompt()
def handle_job_application(job_id_or_url: str) -> str:
    """Prompt template for compliant, human-in-the-loop job evaluation and application workflow."""
    return (
        f"Evaluate and prepare an application for job reference: '{job_id_or_url}'.\n"
        "1. If a URL is provided, extract the numerical Job ID.\n"
        "2. Call 'get_job_details' with the Job ID to retrieve title, employer, requirements, and screening questionnaire.\n"
        "3. Read resource 'naukri://candidate/master-resume' to cross-reference candidate qualifications against requirements.\n"
        "4. Present the match score and draft answers for the screening questions to the user.\n"
        "5. Upon explicit user confirmation, call 'apply_to_jobs' with the answers to submit."
    )


# ---------------------------------------------------------------------------
# MULTI-TENANT MIDDLEWARE & ASGI APPLICATION
# ---------------------------------------------------------------------------

class SessionContextMiddleware:
    """
    MCP Server middleware intercepting incoming JSON-RPC calls (tools/call, prompts/get, resources/read).
    Resolves session_id from query parameters or headers, retrieves that session's credentials
    from SESSION_STORE, and injects them into contextvars.
    """
    async def __call__(self, ctx: Any, call_next: Any) -> Any:
        req = getattr(ctx, "request", None)
        if req:
            from naukri_mcp.auth import (
                current_session_id,
                current_session_rt,
                current_session_resume_url,
                current_session_pdf_url,
                SESSION_STORE
            )

            # Direct extraction from query params
            if hasattr(req, "query_params"):
                q_rt = req.query_params.get("rt", "") or req.query_params.get("nauk_rt", "")
                if q_rt:
                    current_session_rt.set(q_rt)
                q_res = req.query_params.get("resume", "") or req.query_params.get("resume_url", "")
                if q_res:
                    current_session_resume_url.set(q_res)
                q_pdf = req.query_params.get("pdf", "") or req.query_params.get("pdf_url", "")
                if q_pdf:
                    current_session_pdf_url.set(q_pdf)

            sess_id = ""
            if hasattr(req, "query_params"):
                sess_id = req.query_params.get("session_id", "").replace("-", "")
            if not sess_id and hasattr(req, "headers"):
                sess_id = req.headers.get("mcp-session-id", "").replace("-", "")

            if sess_id:
                current_session_id.set(sess_id)
                sess_data = SESSION_STORE.get(sess_id)
                if sess_data:
                    if sess_data.get("rt") and not current_session_rt.get():
                        current_session_rt.set(sess_data["rt"])
                    if sess_data.get("resume_url") and not current_session_resume_url.get():
                        current_session_resume_url.set(sess_data["resume_url"])
                    if sess_data.get("pdf_url") and not current_session_pdf_url.get():
                        current_session_pdf_url.set(sess_data["pdf_url"])
                    sess_data["last_seen"] = time.time()

            if hasattr(req, "headers"):
                h_rt = req.headers.get("x-naukri-rt", "")
                if h_rt:
                    current_session_rt.set(h_rt)
                    sid = current_session_id.get()
                    if sid:
                        SESSION_STORE.setdefault(sid, {})["rt"] = h_rt

        return await call_next(ctx)


mcp._lowlevel_server.middleware.append(SessionContextMiddleware())


class MultiTenantSessionMiddleware:
    """
    ASGI middleware intercepting incoming SSE connections and client requests:
    Extracts rt, resume, pdf from query parameters and headers.
    Captures session IDs from response bodies and headers to bind credentials in SESSION_STORE.
    """
    def __init__(self, app_target: Any) -> None:
        self.app_target = app_target

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") == "http":
            import urllib.parse
            import re
            from naukri_mcp.auth import SESSION_STORE, clean_stale_sessions
            clean_stale_sessions()

            qs = urllib.parse.parse_qs(scope.get("query_string", b"").decode("utf-8"))
            rt = qs.get("rt", [""])[0] or qs.get("nauk_rt", [""])[0]
            resume_url = qs.get("resume", [""])[0] or qs.get("resume_url", [""])[0] or qs.get("master_resume", [""])[0]
            pdf_url = qs.get("pdf", [""])[0] or qs.get("pdf_url", [""])[0] or qs.get("resume_pdf", [""])[0]

            raw_headers = scope.get("headers", [])
            headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in raw_headers}
            if not rt:
                rt = headers.get("x-naukri-rt", "")
            if not resume_url:
                resume_url = headers.get("x-master-resume", "")
            if not pdf_url:
                pdf_url = headers.get("x-resume-pdf", "")

            req_sess_id = headers.get("mcp-session-id", "") or qs.get("session_id", [""])[0]
            if req_sess_id and rt:
                req_sess_id = req_sess_id.replace("-", "")
                sess = SESSION_STORE.setdefault(req_sess_id, {})
                sess["rt"] = rt
                sess["last_seen"] = time.time()

            async def custom_send(message: Dict[str, Any]) -> None:
                if message.get("type") == "http.response.start":
                    resp_headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in message.get("headers", [])}
                    sess_id = resp_headers.get("mcp-session-id", "").replace("-", "")
                    if sess_id and rt:
                        SESSION_STORE[sess_id] = {
                            "rt": rt,
                            "resume_url": resume_url,
                            "pdf_url": pdf_url,
                            "created_at": time.time(),
                            "last_seen": time.time()
                        }
                elif message.get("type") == "http.response.body":
                    body_bytes = message.get("body", b"")
                    if b"session_id=" in body_bytes and rt:
                        m = re.search(r"session_id=([a-f0-9\-]+)", body_bytes.decode("utf-8", errors="ignore"))
                        if m:
                            sess_id = m.group(1).replace("-", "")
                            SESSION_STORE[sess_id] = {
                                "rt": rt,
                                "resume_url": resume_url,
                                "pdf_url": pdf_url,
                                "created_at": time.time(),
                                "last_seen": time.time()
                            }
                await send(message)

            await self.app_target(scope, receive, custom_send)
            return

        await self.app_target(scope, receive, send)


def get_app() -> Any:
    """Return unified Starlette app supporting both Streamable HTTP (/mcp) and SSE (/sse), with CORS."""
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Route
    from mcp.server.transport_security import TransportSecuritySettings

    sec = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    sse_subapp = mcp.sse_app(transport_security=sec)
    http_subapp = mcp.streamable_http_app(streamable_http_path="/mcp", transport_security=sec)

    http_handler = None
    for r in http_subapp.routes:
        if getattr(r, "path", "") == "/mcp":
            http_handler = r.endpoint
            break

    sse_handler = None
    for r in sse_subapp.routes:
        if getattr(r, "path", "") == "/sse":
            sse_handler = r.endpoint
            break

    routes = [
        Route("/sse", endpoint=sse_handler, methods=["GET", "HEAD"]),
        Route("/sse", endpoint=http_handler, methods=["POST"]),
        Route("/mcp", endpoint=http_handler, methods=["GET", "POST", "HEAD"]),
        Route("/", endpoint=http_handler, methods=["POST"]),
        *[r for r in sse_subapp.routes if getattr(r, "path", "") not in ("/sse", "/mcp")],
    ]

    unified_app = Starlette(
        routes=routes,
        lifespan=http_subapp.router.lifespan_context
    )

    wrapped_session_app = MultiTenantSessionMiddleware(unified_app)
    return CORSMiddleware(
        wrapped_session_app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


app = get_app()


# ---------------------------------------------------------------------------
# SERVER RUNNER
# ---------------------------------------------------------------------------

def run_server(transport: str = "stdio", port: Optional[int] = None, host: str = "0.0.0.0") -> None:
    """Run the FastMCP server in either stdio, sse, or streamable-http mode."""
    if port is None:
        port = int(os.getenv("PORT", 8000))

    if transport == "sse":
        import uvicorn
        import anyio
        print(f"Starting naukri-mcp in SSE mode on http://{host}:{port} ...")
        app_instance = get_app()
        config = uvicorn.Config(
            app_instance,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        anyio.run(server.serve)
    elif transport == "streamable-http":
        print(f"Starting naukri-mcp in streamable-http mode on http://{host}:{port} ...")
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="naukri-mcp: Model Context Protocol Server for Naukri.com")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio", help="Transport mode")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port for SSE mode (default: PORT env or 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE mode")
    args = parser.parse_args()

    run_server(transport=args.transport, port=args.port, host=args.host)
