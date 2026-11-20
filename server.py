"""
Naukri MCP Server implementation using official FastMCP / MCPServer SDK.
Provides Tools, Resources, and Prompts.
"""
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from starlette.requests import Request
from starlette.responses import Response, JSONResponse, HTMLResponse

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except Exception:
    from mcp.server.fastmcp import FastMCP  # type: ignore

from naukri_mcp.tools import profile, resume, photo, duplicates, analytics, taxonomy, jobs, delete

# Initialize the FastMCP server
mcp = FastMCP(
    "naukri-mcp",
    instructions=(
        "Naukri MCP Server: Manage Naukri candidate profiles, upload resumes, "
        "inspect recruiter views, search jobs, submit applications, and manage items.\n"
        "CAUTION: Deletion permanently removes items from the live candidate profile. "
        "AI assistants MUST exercise extreme caution and confirm user intent before invoking delete tools."
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
        "version": "1.0.0"
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
    <h1>Naukri MCP Server</h1>
    <p>Production Model Context Protocol (MCP) server providing 63 tools for automated Naukri candidate profile management, recruiter visibility optimization, and smart job applications.</p>
    
    <div class="card">
        <h3>Connect to Claude Web / Claude Desktop / Cursor</h3>
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
# MCP TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def refresh_session_token(
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Refresh and renew the Naukri access token (NAUK_AT) using the refresh token (NAUK_RT).

    :param nauk_rt: Optional refresh token string (defaults to session RT or NAUK_RT in environment).
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
            "message": (
                "No NAUK_RT refresh token provided or found in session/environment. "
                "Please provide your 'nauk_rt' cookie from naukri.com."
            )
        }

    new_at, new_rt = refresh_token_via_nauk_rt(rt)
    if new_at:
        effective_rt = new_rt or rt
        current_session_rt.set(effective_rt)
        sess_id = current_session_id.get()
        if sess_id:
            SESSION_STORE.setdefault(sess_id, {})["rt"] = effective_rt
        return {
            "status": "success",
            "message": "Naukri access token refreshed successfully.",
            "expires_in_seconds": decode_jwt_exp(new_at) - int(time.time()),
            "token_preview": f"{new_at[:25]}...{new_at[-15:]}"
        }
    return {
        "status": "error",
        "message": "Failed to refresh token using NAUK_RT. The cookie may be invalid or expired on Naukri."
    }


@mcp.tool()
def get_profile(
    section: str = "all",
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch live Naukri candidate profile data.

    :param section: Section to inspect ('all', 'headline', 'summary', 'skills', 'notice', 'career', 'itskills', 'projects', 'educations', 'employments', 'languages', 'personal').
    :param nauk_at: Optional bearer token (defaults to NAUK_AT in environment).
    :param nauk_rt: Optional refresh token.
    """
    return profile.get_profile(section=section, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_headline(
    headline: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate resume headline on Naukri.

    :param headline: New headline text (e.g. 'Senior Full Stack Engineer | 5.3+ YOE | Python, FastAPI, React 19').
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_headline(headline=headline, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_summary(
    summary: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate profile summary (automatically trimmed to max 1000 chars).

    :param summary: Profile summary text.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_summary(summary=summary, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_key_skills(
    skills_csv: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update key skills comma-separated tags on candidate profile.

    :param skills_csv: Comma-separated skills (e.g. 'Python, FastAPI, Docker, PostgreSQL, React').
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_key_skills(skills_csv=skills_csv, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_notice_period(
    days: int,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate notice period on Naukri.

    :param days: Notice period in days (0 for Serving Notice, 15, 30 for 1 Month, 60 for 2 Months, 90 for 3 Months).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_notice_period(days=days, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_location(
    city_id: int,
    city_name: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate current location/city.

    :param city_id: Standardized city ID (e.g. 139 for Pune). Use search_taxonomy to find IDs.
    :param city_name: City name string.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_location(city_id=city_id, city_name=city_name, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_career_profile(
    expected_ctc: int,
    preferred_cities: List[Any],
    target_roles: List[Any],
    desired_job_types: Optional[List[str]] = None,
    desired_employment_types: Optional[List[str]] = None,
    department: Optional[Any] = None,
    role_category: Optional[Any] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate career preferences, expected annual CTC in INR, preferred locations, target roles,
    desired job types ('permanent', 'contractual'), and desired employment types ('Full Time', 'Part Time').

    :param expected_ctc: Expected CTC in integer INR (e.g. 1200000 for 12 LPA).
    :param preferred_cities: List of city dicts or names, e.g. [{'id': 139, 'value': 'Pune'}] or ['Pune'].
    :param target_roles: List of target role dicts or names, e.g. [{'id': 265, 'value': 'Full Stack Developer'}].
    :param desired_job_types: List of desired job types (e.g. ['permanent']).
    :param desired_employment_types: List of desired employment types (e.g. ['Full Time']).
    :param department: Optional department dict or string (e.g. {'id': 5, 'value': 'Engineering - Software & QA'}).
    :param role_category: Optional role category dict or string (e.g. {'id': 1028, 'value': 'Software Development'}).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_career_profile(
        expected_ctc=expected_ctc,
        preferred_cities=preferred_cities,
        target_roles=target_roles,
        desired_job_types=desired_job_types,
        desired_employment_types=desired_employment_types,
        department=department,
        role_category=role_category,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def update_work_experience(
    work_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update employment / work experience history on candidate profile.

    :param work_list: List of work experience dicts, each with keys like:
                     'company', 'position', 'startDate' (YYYY-MM-DD), 'endDate', 'isCurrent' (bool),
                     'highlights' (list of achievements), 'technologies' (list of skills).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_work_experience(work_list=work_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_projects(
    projects_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update or create multiple projects on candidate profile.

    :param projects_list: List of project dicts ('projectTitle', 'clientName', 'projectDetails', 'role', 'teamSize', 'skills', 'startDate', 'endDate').
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_projects(projects_list=projects_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def add_project(
    project_data: Dict[str, Any],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a single project to candidate profile.

    :param project_data: Project dict with keys: 'projectTitle', 'clientName', 'projectDetails', 'role', 'teamSize', 'skills', 'startDate', 'endDate'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.add_project(project_data=project_data, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_educations(
    educations_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update higher education entries (Graduation, Masters/Post-Graduation, Doctorate/PhD).

    :param educations_list: List of education dicts with 'educationType' ('UG', 'PG', 'PPG'), 'course', 'specialisation', 'entityInstitute', 'yearOfStart', 'yearOfCompletion'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_educations(educations_list=educations_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_schools(
    schools_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update school education entries (Class X, Class XII).

    :param schools_list: List of school dicts with 'educationType' ('Class X', 'Class XII'), 'schoolBoard', 'schoolCompletionYear', 'schoolMedium', 'schoolPercentage'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_schools(schools_list=schools_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_personal_details(
    gender: Optional[str] = None,
    marital_status: Optional[str] = None,
    birth_date: Optional[str] = None,
    category: Optional[str] = None,
    address: Optional[str] = None,
    hometown: Optional[str] = None,
    pincode: Optional[str] = None,
    mail_city: Optional[str] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate personal details (Gender, Marital status, DOB, Category, Address, Hometown, Pincode).

    :param gender: 'Male', 'Female', 'Transgender' (or 'M', 'F', 'T').
    :param marital_status: 'Single / unmarried', 'Married'.
    :param birth_date: Date of birth (YYYY-MM-DD).
    :param category: Caste/Category ('General', 'OBC', 'SC', 'ST').
    :param address: Full street/contact address.
    :param hometown: Hometown city name.
    :param pincode: Postal code (e.g. '411045').
    :param mail_city: Mail city and state (e.g. 'pune, maharashtra').
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_personal_details(
        gender=gender,
        marital_status=marital_status,
        birth_date=birth_date,
        category=category,
        address=address,
        hometown=hometown,
        pincode=pincode,
        mail_city=mail_city,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def update_it_skills(
    skills_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update or add structured entries in candidate IT skills table with version, last used year, and experience.

    :param skills_list: List of dicts with 'skill'/'name', 'version', 'last_used_year', 'exp_years', 'exp_months'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_it_skills(skills_list=skills_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def add_it_skill(
    skill: str,
    version: str = "Latest",
    last_used_year: int = 2026,
    experience_years: int = 2,
    experience_months: int = 0,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add or update a single IT skill entry in candidate IT skills table.

    :param skill: Name of skill (e.g. 'Python', 'FastAPI', 'Docker').
    :param version: Version label (e.g. '3.12', 'v26', 'Cloud').
    :param last_used_year: Year last used (e.g. 2026).
    :param experience_years: Total years of experience with the skill.
    :param experience_months: Total months of experience with the skill.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.add_it_skill(
        skill=skill,
        version=version,
        last_used_year=last_used_year,
        experience_years=experience_years,
        experience_months=experience_months,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def update_languages(
    languages_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update or add candidate languages with proficiency and abilities (read, write, speak).

    :param languages_list: List of dicts with 'lang'/'language', 'proficiency' ('Beginner'/'Proficient'/'Expert'), and 'ability' list or 'read', 'write', 'speak' booleans.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_languages(languages_list=languages_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def add_language(
    language: str,
    proficiency: str = "Proficient",
    read: bool = True,
    write: bool = True,
    speak: bool = True,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add or update a single language in candidate profile.

    :param language: Language name (e.g. 'English', 'Hindi', 'Marathi', 'German').
    :param proficiency: 'Beginner', 'Proficient', or 'Expert'.
    :param read: Can read.
    :param write: Can write.
    :param speak: Can speak.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.add_language(
        language=language,
        proficiency=proficiency,
        read=read,
        write=write,
        speak=speak,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def update_job_search_status(
    status_code_or_name: Any,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update job search availability status.

    :param status_code_or_name: 1 / 'Actively searching jobs', 2 / 'Casual job seeker', 3 / 'Not looking for jobs'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_job_search_status(status_code_or_name=status_code_or_name, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_disability(
    is_disabled: bool = False,
    disability_type: Optional[str] = None,
    percentage: Optional[int] = None,
    details: Optional[str] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate differently abled / disability profile section.

    :param is_disabled: Boolean indicating if differently abled.
    :param disability_type: Category of disability (e.g. 'Physical', 'Visual', 'Hearing').
    :param percentage: Percentage of disability (e.g. 40).
    :param details: Description or reason.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_disability(
        is_disabled=is_disabled,
        disability_type=disability_type,
        percentage=percentage,
        details=details,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def delete_disability(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clear differently abled / disability status from candidate profile.
    CAUTION: Modifies live candidate profile. Confirm user intent before invoking.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.delete_disability(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_work_permit(
    us_work_status: Optional[str] = None,
    countries: Optional[List[str]] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update US work authorization status and international country work permits.

    :param us_work_status: US status (e.g. 'Citizen', 'Green Card', 'Have H1 Visa', 'Need H1 Visa').
    :param countries: List of countries candidate holds work permits for (e.g. ['USA', 'United Kingdom', 'Canada']).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_work_permit(
        us_work_status=us_work_status,
        countries=countries,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def update_career_break(
    has_break: bool = True,
    reason: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate career break status, reason, and dates.

    :param has_break: True if candidate has a career break, False otherwise.
    :param reason: Reason for career break (e.g. 'Higher studies', 'Medical', 'Caregiving').
    :param start_date: Start date of break (YYYY-MM-DD or YYYY-MM).
    :param end_date: End date of break (YYYY-MM-DD or YYYY-MM).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_career_break(
        has_break=has_break,
        reason=reason,
        start_date=start_date,
        end_date=end_date,
        nauk_at=nauk_at,
        nauk_rt=nauk_rt
    )


@mcp.tool()
def delete_career_break(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Remove career break from candidate profile.
    CAUTION: Modifies live candidate profile. Confirm user intent before invoking.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.delete_career_break(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def resend_email_verification(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger resending of the verification email link to the candidate's registered inbox.
    Helps fulfill the final profile completeness requirement.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.resend_email_verification(nauk_at=nauk_at, nauk_rt=nauk_rt)



@mcp.tool()
def touch_profile_pulse(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Touch profile headline to activate the 'Profile Updated: Today' recruiter visibility badge.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.touch_profile_pulse(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def sync_full_profile(
    resume_source: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronize full profile sections from a master resume JSON (accepts local file path or remote HTTP/HTTPS URL).

    :param resume_source: Local filesystem path, remote HTTP/HTTPS URL, or raw JSON string of master resume.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.sync_full_profile(resume_source=resume_source, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_online_profiles(
    profiles_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate online professional profiles (e.g. LinkedIn, GitHub, Behance, Portfolio).

    :param profiles_list: List of dicts, each with 'profile' (e.g. 'LinkedIn') and 'url'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_online_profiles(profiles_list=profiles_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_work_samples(
    samples_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate work sample links (e.g. GitHub repos, design portfolios).

    :param samples_list: List of dicts, each with 'title' and 'url'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_work_samples(samples_list=samples_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_publications(
    publications_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate research publications, white papers, or journal entries.

    :param publications_list: List of dicts, each with 'title' and 'url'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_publications(publications_list=publications_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_presentations(
    presentations_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate presentation links (e.g. SlideShare, SpeakerDeck).

    :param presentations_list: List of dicts, each with 'title' and 'url'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_presentations(presentations_list=presentations_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_patents(
    patents_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate patents filed or issued.

    :param patents_list: List of dicts, each with 'title' and 'url'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_patents(patents_list=patents_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_certifications(
    certifications_list: List[Dict[str, Any]],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update candidate certifications and official accreditations.

    :param certifications_list: List of dicts, each with 'course' (name) and 'vendor' (issuer body).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_certifications(certifications_list=certifications_list, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def update_accomplishments(
    accomplishments: Dict[str, Any],
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update all accomplishments at once: online profiles, work samples, publications, presentations, patents, and certifications.

    :param accomplishments: Dict containing optional keys: 'onlineProfiles', 'workSamples', 'publications', 'presentations', 'patents', 'certifications'.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return profile.update_accomplishments(accomplishments=accomplishments, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def upload_resume(
    source: Optional[str] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload and attach a PDF resume to candidate's Naukri profile.

    :param source: Local PDF file path, remote HTTP/HTTPS download URL, base64-encoded PDF string, or None (to use RESUME_PDF_PATH env).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return resume.upload_resume(source=source, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def upload_photo(
    source: Optional[str] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a professional profile photo / display avatar to the candidate's Naukri profile.
    Boosts profile completeness score by +5% and activates recruiter avatar badge.

    :param source: Optional local image file path (JPEG/PNG), base64 string, or None (generates professional avatar automatically).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return photo.upload_photo(source=source, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def audit_profile_duplicates(
    canonical_skills: Optional[List[str]] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Audit live profile for duplicate project entries and duplicate or obsolete IT skills.

    :param canonical_skills: Optional list of valid skills. Any skill not in this list is flagged as obsolete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return duplicates.audit_duplicates(canonical_skills=canonical_skills, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_project(
    project_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a specific project entry from the candidate profile by its projectId.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param project_id: The unique projectId to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_project(project_id=project_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_employment(
    employment_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a specific employment / work experience entry by its employmentId.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param employment_id: The unique employmentId to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_employment(employment_id=employment_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_it_skill(
    skill_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a specific IT skill entry from the structured skills table by its skillId.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param skill_id: The unique skillId to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_it_skill(skill_id=skill_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_education(
    education_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a specific graduation / post-graduation education entry by its educationId.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param education_id: The unique educationId to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_education(education_id=education_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_school(
    school_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a 10th or 12th class school entry by its schoolId.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param school_id: The unique schoolId to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_school(school_id=school_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_online_profile(
    profile_item_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete an online professional profile link (LinkedIn, GitHub) by its ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param profile_item_id: The unique ID of the online profile to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_online_profile(profile_item_id=profile_item_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_work_sample(
    sample_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a work sample link (GitHub repo, Behance) by its ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param sample_id: The unique ID of the work sample to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_work_sample(sample_id=sample_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_publication(
    publication_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a research publication or white paper entry by its ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param publication_id: The unique ID of the publication to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_publication(publication_id=publication_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_presentation(
    presentation_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete an online presentation link by its ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param presentation_id: The unique ID of the presentation to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_presentation(presentation_id=presentation_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_patent(
    patent_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a patent filing or grant by its ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param patent_id: The unique ID of the patent to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_patent(patent_id=patent_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_certification(
    certification_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a certification entry by its certificationId.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param certification_id: The unique certificationId to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_certification(certification_id=certification_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_language(
    language_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a language entry by its language ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param language_id: The unique language ID to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_language(language_id=language_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_resume(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete the uploaded resume document file from the candidate profile.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_resume(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def delete_photo(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete the uploaded candidate display photo from the candidate profile.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return photo.delete_photo(nauk_at=nauk_at, nauk_rt=nauk_rt)



@mcp.tool()
def delete_profile_item(
    item_type: str,
    item_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generic delete tool: Delete any specific item/subresource from candidate profile by type and ID.
    CAUTION: Permanent deletion. Confirm user intent before invoking.

    :param item_type: One of 'projects', 'employments', 'itskills', 'educations', 'schools',
                      'onlineProfiles', 'workSamples', 'publications', 'presentations',
                      'patents', 'certifications', 'languages'.
    :param item_id: The unique ID string of the item to delete.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return delete.delete_profile_item(item_type=item_type, item_id=item_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def get_profile_analytics(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch recruiter search appearances, profile views, profile completeness score,
    and a prioritized list of missing profile sections.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return analytics.get_profile_analytics(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def get_recruiter_inbox(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch recruiter messages, interview invitations, and unread communication count.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return analytics.get_recruiter_inbox(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def get_notification_summary(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch active notification counters (recommended jobs count, pending profile actions).

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return analytics.get_notification_summary(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def get_salary_components(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve Naukri compensation breakdown labels (Fixed, Variable, Stocks, ESOPs, RSUs).

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return analytics.get_salary_labels(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def get_blocked_companies(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve list of companies blocked from viewing candidate profile.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return analytics.get_blocked_companies(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def block_company(
    company_id: str,
    company_name: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Block a company so its recruiters cannot see candidate profile.

    :param company_id: Numerical company ID.
    :param company_name: Name of the company.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return analytics.block_company(company_id=company_id, company_name=company_name, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def search_taxonomy(
    entity_type: str = "certificate",
    query: str = "",
    limit: int = 20,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search standardized Naukri entities by keyword to retrieve official IDs.

    :param entity_type: 'certificate' (4,000+ certifications), 'city' (5,800+ cities), 'language', 'country', 'state'.
    :param query: Keyword to search (e.g. 'AWS', 'Pune', 'English').
    :param limit: Max items to return (default 20).
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return taxonomy.search_taxonomy(entity_type=entity_type, query=query, limit=limit, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def get_taxonomy_versions(
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all 32 central entity taxonomies available in Naukri and their current versions.

    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return taxonomy.get_taxonomy_versions(nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def search_jobs(
    keywords: str,
    location: str = "Pune",
    experience: int = 5,
    limit: int = 20,
    job_age_days: int = 3,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search live jobs on Naukri and categorize by Apply Flow (Category 1 Direct vs Category 2 Questionnaire).

    :param keywords: Comma-separated query string (e.g. 'Python, FastAPI, Full Stack').
    :param location: Target city or location string (default 'Pune').
    :param experience: Minimum years of experience (default 5).
    :param limit: Maximum jobs to return (default 20).
    :param job_age_days: Freshness filter in days (default 3).
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
    job_id: str,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve full job description, requirements, and screening questionnaire schema for a job ID.

    :param job_id: Numerical job ID from Naukri.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return jobs.get_job_details(job_id=job_id, nauk_at=nauk_at, nauk_rt=nauk_rt)


@mcp.tool()
def apply_to_job(
    job_id: str,
    answers: Optional[List[Dict[str, Any]]] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit an application to a Naukri job (Category 1 Direct Apply or Category 2 Questionnaire).
    Pure stateless: does not modify local disk files.

    :param job_id: Numerical job ID from Naukri.
    :param answers: Optional list of questionnaire answers, each dict with {'questionId': str, 'answer': str}.
    :param nauk_at: Optional bearer token.
    :param nauk_rt: Optional refresh token.
    """
    return jobs.apply_to_job(job_id=job_id, answers=answers, nauk_at=nauk_at, nauk_rt=nauk_rt)


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
    Categorized directory of all 63 MCP tools with functional grouping and safety tiers.
    """
    directory = {
        "total_tools": 63,
        "categories": {
            "session_and_auth": {
                "tools": ["refresh_session_token"],
                "tier": "safe_read"
            },
            "profile_core_mutations": {
                "tools": [
                    "update_headline", "update_summary", "update_key_skills",
                    "update_notice_period", "update_location", "update_career_profile",
                    "update_personal_details", "update_job_search_status"
                ],
                "tier": "mutation"
            },
            "experience_and_skills": {
                "tools": [
                    "update_work_experience", "update_projects", "add_project",
                    "update_it_skills", "add_it_skill"
                ],
                "tier": "mutation"
            },
            "education_and_schools": {
                "tools": ["update_educations", "update_schools"],
                "tier": "mutation"
            },
            "diversity_and_qualifications": {
                "tools": [
                    "update_languages", "add_language", "update_disability",
                    "update_work_permit", "update_career_break"
                ],
                "tier": "mutation"
            },
            "accomplishments": {
                "tools": [
                    "update_online_profiles", "update_work_samples", "update_publications",
                    "update_presentations", "update_patents", "update_certifications",
                    "update_accomplishments"
                ],
                "tier": "quota_capped_mutation"
            },
            "media_and_artifacts": {
                "tools": ["upload_resume", "upload_photo"],
                "tier": "mutation"
            },
            "pulse_and_analytics": {
                "tools": [
                    "touch_profile_pulse", "resend_email_verification", "sync_full_profile",
                    "get_profile_analytics", "get_recruiter_inbox", "get_notification_summary",
                    "get_salary_components"
                ],
                "tier": "safe_read_or_pulse"
            },
            "inspection_and_taxonomy": {
                "tools": [
                    "get_profile", "search_taxonomy", "get_taxonomy_versions",
                    "get_blocked_companies"
                ],
                "tier": "safe_read"
            },
            "job_discovery_and_applications": {
                "tools": ["search_jobs", "get_job_details", "apply_to_job", "block_company"],
                "tier": "external_or_application"
            },
            "destructive_deletions": {
                "tools": [
                    "audit_profile_duplicates", "delete_project", "delete_employment",
                    "delete_it_skill", "delete_education", "delete_school",
                    "delete_online_profile", "delete_work_sample", "delete_publication",
                    "delete_presentation", "delete_patent", "delete_certification",
                    "delete_language", "delete_disability", "delete_career_break",
                    "delete_resume", "delete_photo", "delete_profile_item"
                ],
                "tier": "destructive_requires_confirmation"
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
        "1. Call 'get_profile_analytics' to inspect recruiter search appearances, profile views, and incomplete sections.\n"
        "2. Call 'get_profile' with section='headline' and section='summary' to inspect existing copy.\n"
        "3. Provide actionable suggestions to improve recruiter search appearances and achieve 100% profile completeness.\n"
        "SAFETY NOTE: If recommending removal of duplicate or obsolete items, be extremely cautious with delete tools. Always confirm with the user before calling any deletion tool."
    )


@mcp.prompt()
def manage_profile_deletions() -> str:
    """Prompt template for safely reviewing and deleting profile items with caution."""
    return (
        "CRITICAL CAUTION: You are about to manage deletions on a live candidate profile.\n"
        "Deleting projects, employments, education, or skills permanently removes them from Naukri.\n"
        "1. First call 'get_profile' for the relevant section (e.g. section='projects') to list existing items and their unique IDs.\n"
        "2. Display the exact items to the user with their titles, dates, and IDs.\n"
        "3. Explicitly ask for user confirmation before deleting.\n"
        "4. Only upon explicit confirmation, invoke the specific delete tool (e.g. 'delete_project', 'delete_employment', 'delete_it_skill').\n"
        "5. Re-fetch the section to confirm clean deletion."
    )


@mcp.prompt()
def resolve_screening_questionnaire(job_id: str) -> str:
    """Prompt template to retrieve job questionnaire and resolve answers truthfully."""
    return (
        f"You are assisting a candidate with applying for Naukri Job ID {job_id}.\n"
        f"1. Call 'get_job_details' with job_id='{job_id}' to retrieve the screening questionnaire.\n"
        "2. Review the questions (e.g. notice period, CTC, experience, specific technologies).\n"
        "3. Formulate concise, truthful answers matching candidate facts.\n"
        "4. Call 'apply_to_job' with the resolved answers array to submit the application."
    )


@mcp.prompt()
def job_search_and_apply(keywords: str, location: str = "Pune", experience: int = 5) -> str:
    """Prompt template for automated job search and application workflow."""
    return (
        f"Search and evaluate jobs on Naukri for keywords: '{keywords}' in '{location}' with {experience} YOE.\n"
        "1. Call 'search_jobs' to find matching open positions.\n"
        "2. Categorize results into Category 1 (Direct 1-Click Apply) and Category 2 (Questionnaire).\n"
        "3. For Category 1 jobs, call 'apply_to_job' directly.\n"
        "4. For Category 2 jobs, call 'get_job_details', resolve the screening questions, and submit.\n"
        "5. Output a structured summary table showing applied jobs and any skipped positions."
    )


@mcp.prompt()
def tailor_and_update_profile(target_role: str = "Full Stack Developer") -> str:
    """Prompt template to synchronize candidate master resume with Naukri profile for a target role."""
    return (
        f"You are synchronizing and tailoring the candidate's Naukri profile for target role: '{target_role}'.\n"
        "1. Read resource 'naukri://candidate/master-resume' to obtain authenticated candidate facts, projects, and skills.\n"
        "2. Read resource 'naukri://rules/platform-guidelines' to review accomplishment quotas (max 5 items) and date rules.\n"
        "3. Inspect current live state via 'get_profile(section=\"all\")'.\n"
        "4. Update core positioning via 'update_headline', 'update_summary', 'update_key_skills', and 'update_career_profile'.\n"
        "5. Synchronize IT skills via 'update_it_skills' ensuring proper version and non-zero experience fields.\n"
        "6. Confirm all updates by reading resource 'naukri://profile/current'."
    )


@mcp.prompt()
def daily_profile_refresh() -> str:
    """Prompt template for daily candidate visibility maintenance and recruiter communications audit."""
    return (
        "Perform daily Naukri candidate profile maintenance to maximize recruiter visibility:\n"
        "1. Call 'touch_profile_pulse' to refresh the profile modification timestamp and bump search ranking.\n"
        "2. Read resource 'naukri://inbox/recruiter-mails' and call 'get_recruiter_inbox' to audit unread recruiter messages.\n"
        "3. Call 'get_notification_summary' to check recruiter views, shortlist alerts, and job recommendation updates.\n"
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
        "5. Upon explicit user confirmation, call 'apply_to_job' with the answers to submit."
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

            # If incoming request carries session id, update session store
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
