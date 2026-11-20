# naukri-mcp: Model Context Protocol (MCP) Server for Naukri.com

Production **Model Context Protocol (MCP)** Server providing **63 specialized tools**, resources, and prompts for **Naukri.com**. Designed to be deployed with zero required environment variables and connected to AI assistants such as **Claude Web**, **Claude Desktop**, **Cursor**, and **Antigravity**.

---

## 🌟 Key Architecture Highlights

- **Standalone & Portable Repository:** Self-contained with zero hardcoded paths and no dependency on external candidate files or data folders.
- **Zero-Config Multi-Tenant Deployment:** Deploy on Railway, Render, Fly.io, or any container host with **zero environment variables required**.
- **Personalized SSE URL Connection:** Each user passes their credentials dynamically via URL query parameters (`https://<domain>/sse?rt=YOUR_NAUK_RT_COOKIE`) or custom HTTP headers (`X-Naukri-RT`, etc.).
- **Smart Session Caching:** Access tokens (`nauk_at`) and session credentials are bound to each client's session and cached in memory. The assistant **never repeatedly asks for tokens** across turns or chats, only prompting if the token is missing or has actually expired on Naukri.
- **63 Comprehensive Tools:** Complete CloudGateway API coverage across profile management, IT skills, 18+ projects, accomplishments, recruiter communications, analytics, and job applications.

---

## 🚀 1-Click / Docker Deployment on Railway

Anyone can fork or clone this repository and deploy it immediately without configuring secrets or environment variables during deployment.

### Quick Railway Deployment:
1. Push this repository to your GitHub account.
2. In [Railway](https://railway.app), click **New Project** &rarr; **Deploy from GitHub repo**.
3. Select this repository. Railway automatically detects the `Dockerfile`.
4. Deploy! Railway assigns a public domain (e.g. `https://naukri-mcp-production.up.railway.app`) and dynamically provides the `$PORT` environment variable.
5. Done! Visit your Railway URL in the browser to view the interactive server landing page and `/health` probe.

### Run with Docker Locally:
```bash
docker build -t naukri-mcp .
docker run -p 8000:8000 naukri-mcp
```

---

## 🔌 Connecting to AI Clients

### 1. Claude Web & Claude Desktop (SSE Remote Mode)

Add this server to your Claude MCP configuration (e.g. `claude_desktop_config.json` or Claude Web Connectors):

```json
{
  "mcpServers": {
    "naukri": {
      "url": "https://your-railway-app.up.railway.app/sse?rt=YOUR_NAUK_RT_COOKIE"
    }
  }
}
```

#### URL Query Parameters:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `rt` / `nauk_rt` | string | **Yes** | Your `nauk_rt` refresh cookie from naukri.com. |
| `resume` | string | *Optional* | Public HTTP/HTTPS URL to your candidate `master_resume.json`. |
| `pdf` | string | *Optional* | Public HTTP/HTTPS URL to download your tailored resume PDF for 1-click uploads. |

#### Custom HTTP Headers (Alternative):
If your MCP client supports custom headers:
- `X-Naukri-RT`: `YOUR_NAUK_RT_COOKIE`
- `X-Master-Resume`: `https://example.com/master_resume.json`
- `X-Resume-Pdf`: `https://example.com/resume.pdf`

---

### How to Get Your `nauk_rt` Cookie in 30 Seconds

1. Log in to [naukri.com](https://www.naukri.com) in your browser.
2. Open Developer Tools (`F12` or `Cmd+Option+I` on macOS).
3. Navigate to **Application** (Chrome/Edge) or **Storage** (Firefox) &rarr; **Cookies** &rarr; `https://www.naukri.com`.
4. Copy the value of the **`nauk_rt`** cookie.

> [!NOTE]
> `nauk_rt` is a long-lived refresh token. The server automatically exchanges it for fresh short-lived access tokens (`nauk_at`) and keeps them renewed in memory.

---

### 2. Local stdio Mode (Claude Desktop / CLI)

For local development or single-user desktop setups:

```bash
git clone https://github.com/your-username/naukri_mcp.git
cd naukri_mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "naukri": {
      "command": "python",
      "args": ["-m", "naukri_mcp"],
      "env": {
        "NAUK_RT": "your_nauk_rt_cookie_value"
      }
    }
  }
}
```

---

## 🛠️ Available MCP Tools (63 Total)

### Profile & Positioning Tools
- `get_profile`: Query live sections (`headline`, `summary`, `skills`, `notice`, `career`, `itskills`, `projects`, `educations`, `employments`, `languages`, `personal`, or `all`).
- `update_headline`: Update resume headline (e.g. `Senior Full Stack Engineer | Python, React`).
- `update_summary`: Update candidate summary (auto-trimmed to max 1000 characters).
- `update_key_skills`: Update key skills CSV tags.
- `update_notice_period`: Update notice period (0 for Serving Notice, 15, 30, 60, 90 days).
- `update_location`: Update current candidate city using standardized city IDs.
- `update_career_profile`: Update desired industry, functional area, role, job types, and shifts.
- `update_job_search_status`: Update active job search status (`actively_looking`, `open_to_offers`, `not_looking`).
- `touch_profile_pulse`: Touch timestamp without altering profile content to keep "Profile Updated: Today" badge active.
- `sync_full_profile`: Synchronize entire candidate profile and 18+ projects from master resume facts in one pass.

### Experience, Skills & Education
- `update_work_experience`: Mutate work history entries (designation, employer, CTC, dates, responsibilities).
- `update_it_skills`: Update technical IT skills matrix with versions, last used year, and experience.
- `add_it_skill`: Add an individual IT skill entry.
- `update_projects`: Sync complete client and personal project portfolios.
- `add_project`: Add an individual client/personal project.
- `update_educations`: Sync university and higher education degrees.
- `update_schools`: Update 10th and 12th schooling records.
- `update_languages`: Update spoken languages and proficiencies (`read`, `write`, `speak`).
- `add_language`: Add a single language entry.

### Accomplishments & Additions
- `update_certifications`: Sync professional certifications (AWS, GCP, CKA, etc.).
- `update_online_profiles`: Add or update online links (GitHub, LinkedIn, Portfolio).
- `update_work_samples`: Add or update live application and code samples.
- `update_publications`: Add or update research papers and tech articles.
- `update_presentations`: Add or update conference slide decks.
- `update_patents`: Add or update patent filings.
- `update_accomplishments`: Multi-section synchronizer for all accomplishment categories.

### Resumes & Photos
- `upload_resume`: Upload PDF resume from local path, download URL, or base64.
- `upload_photo`: Upload candidate profile photo (JPEG/PNG).
- `delete_resume`: Remove uploaded resume from profile.
- `delete_photo`: Remove candidate profile photo.

### Job Search & Applications
- `search_jobs`: Query job openings with keywords, city, and experience filters.
- `get_job_details`: Inspect full Job Description (JD), employer facts, and screening questionnaire.
- `apply_to_job`: Submit application directly (1-click) or with AI-resolved answers array.

### Recruiter Analytics & Communications
- `get_profile_analytics`: Inspect 30-day recruiter search appearances, profile views, and completeness.
- `get_recruiter_inbox`: Fetch recruiter messages, interview calls, and unread inquiries.
- `get_notification_summary`: Check application updates, recruiter views, and shortlist alerts.
- `get_salary_components`: Inspect breakup of base vs variable CTC.
- `get_blocked_companies` / `block_company`: Prevent current employers or specific recruiters from viewing profile.

### Deletion Tools (Audited & Safe)
- `delete_project`, `delete_employment`, `delete_it_skill`, `delete_education`, `delete_school`, `delete_online_profile`, `delete_work_sample`, `delete_publication`, `delete_presentation`, `delete_patent`, `delete_certification`, `delete_language`, `delete_profile_item`.

---

## 📚 MCP Resources

- `naukri://candidate/master-resume`: Authenticated source of truth for candidate facts, skills, and projects.
- `naukri://rules/platform-guidelines`: Naukri API schemas, accomplishment quotas (max 5), and date constraints.
- `naukri://profile/current`: Real-time candidate profile state across all sections.
- `naukri://analytics/dashboard`: Search appearance counts, profile views, and recruiter trend graphs.
- `naukri://inbox/recruiter-mails`: Recruiter messages, interview invitations, and status summary.
- `naukri://taxonomy/versions`: Standardized entity taxonomies for certifications, cities, and languages.

---

## 🧪 Running Automated Tests

```bash
# Run unit tests
python -m unittest discover -s tests -p 'test_*.py'

# Run strict type checking with pyrefly
pyrefly check --preset strict .
```

---

## 📄 License

MIT License.
