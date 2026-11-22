# naukri-mcp: Model Context Protocol (MCP) Server for Naukri.com

Production **Model Context Protocol (MCP)** Server providing a consolidated **unified 6-tool architecture** for **Naukri.com**. Designed to be deployed with zero required environment variables and connected seamlessly to modern AI assistants including **Claude Web**, **Google Gemini**, **Claude Desktop**, **Cursor**, and **Antigravity**.

---

## 🌟 Key Architecture Highlights

- **Consolidated 6-Tool Architecture:** Replaced 64 fine-grained tools with 6 high-level, parameterized tools. Reduces LLM context schema overhead by **~85%**, drastically speeding up LLM response times.
- **Single-Approval Permission Flow:** In web-based AI clients like Gemini Web and Claude Web that prompt for per-tool approval, approving `manage_profile` once unlocks all profile reading, updating, pulsing, resume parsing, and duplicate management without queueing dozens of modal permission interruptions.
- **Standalone & Portable Repository:** Completely self-contained with zero hardcoded local filesystem paths or machine-specific tokens.
- **Dual Transport Support (Streamable HTTP & SSE):** Supports both the modern **Streamable HTTP** specification (`/mcp` and `/sse` via `POST`) and legacy **HTTP+SSE** (`/sse` via `GET`), with full cross-origin CORS support.
- **Zero-Config Multi-Tenant Deployment:** Deploy on Railway, Render, Fly.io, or any container host with **zero environment variables required**.
- **Personalized URL Query Parameter Connection:** Each user passes their credentials dynamically via URL query parameters (`https://<domain>/mcp?rt=YOUR_NAUK_RT_COOKIE`) or custom HTTP headers (`X-Naukri-RT`, etc.).
- **Smart Session Caching:** Access tokens (`nauk_at`) and session credentials are bound to each client's session and cached in memory. The assistant never repeatedly asks for tokens across turns or chats.

---

## 🛠️ The 6 Unified MCP Tools

| # | Tool Name | Responsibilities | Key Actions / Parameters |
|---|---|---|---|
| 1 | `manage_profile` | Full candidate profile management: view profile details, update profile fields, touch activity pulse, sync master resume, upload/download resume & photo, audit duplicates, and safely delete profile items. | `action`: `'get'`, `'update'`, `'pulse'`, `'sync_master'`, `'audit_duplicates'`, `'delete_item'`, `'upload_resume'`, `'download_resume'`, `'delete_resume'`, `'upload_photo'`, `'delete_photo'`, `'resend_verification'`<br>`section`, `headline`, `summary`, `key_skills`, `notice_period_days`, `location`, `career_profile`, `work_experience`, `projects`, `educations`, `schools`, `it_skills`, `personal_details`, `languages`, `job_search_status`, `disability`, `work_permit`, `career_break`, `accomplishments`, `add_item`, `item_type`, `item_id`, `source`, `output_path`, `extract_text` |
| 2 | `search_jobs` | Parametric live job discovery on Naukri categorized by application flow (1-Click Direct vs Screening Questionnaire). | `keywords` (string or list), `location`, `experience`, `limit`, `job_age_days` |
| 3 | `get_job_details` | Retrieve comprehensive job description, technical requirements, company facts, and screening questionnaire schema for one or more job IDs. | `job_ids` (single int/str or list of IDs) |
| 4 | `apply_to_jobs` | Stateless job application submission for single or batch jobs with questionnaire answers. | `job_ids` (single int/str or list of IDs), `answers` (list of `{"questionId": str, "answer": str}`) |
| 5 | `manage_recruiter_interactions` | Candidate visibility analytics, recruiter communication inbox, notifications, salary insights, employer blocking, and central taxonomies. | `action`: `'analytics'`, `'inbox'`, `'notifications'`, `'salary_insights'`, `'list_blocked'`, `'block_company'`, `'suggest_taxonomy'`<br>`company_id`, `company_name`, `taxonomy_type` (`'certificate'`, `'city'`, `'language'`, `'country'`, `'versions'`), `query`, `limit` |
| 6 | `manage_session` | Session verification, token expiration inspection, and automatic token renewal. | `action`: `'validate'`, `'refresh'`<br>`nauk_rt` (optional override) |

---

## 🚀 1-Click / Docker Deployment on Railway

Deploy immediately without configuring secrets or environment variables during deployment:

### Quick Railway Deployment:
1. Fork or push this repository to your GitHub account.
2. In [Railway](https://railway.app), click **New Project** &rarr; **Deploy from GitHub repo**.
3. Select `naukri_mcp`. Railway automatically detects the `Dockerfile`.
4. Deploy! Railway assigns a public HTTPS domain (e.g. `https://naukrimcp-production.up.railway.app`) and dynamically provides the `$PORT` environment variable.
5. Visit your Railway URL in the browser to view the interactive server landing page and `/health` probe.

### Run with Docker Locally:
```bash
docker build -t naukri-mcp .
docker run -p 8000:8000 naukri-mcp
```

---

## 🔌 Connecting to AI Clients

### 1. Claude AI Web (Custom Connectors)
1. In **Claude AI**, go to **Settings** &rarr; **Connectors** (or open the chat tools menu and click **Add custom connector**).
2. Fill in the fields:
   - **Name:** `Naukri MCP`
   - **URL:** Use the Streamable HTTP endpoint with your `rt` token:
     ```text
     https://<YOUR-RAILWAY-APP>.up.railway.app/mcp?rt=YOUR_NAUK_RT_COOKIE
     ```
     *(Note: `/sse?rt=...` is also supported)*
3. When prompted with *"Couldn't determine how this server signs in"*, click **Continue anyway**.
4. Under **Authentication**, select **No sign-in** *(because your token is already authenticated via the URL parameter)*.
5. Click **Add**. All 6 tools are registered immediately!

---

### 2. Google Gemini & Antigravity
Add `naukri-mcp` to your MCP configuration (`mcp_config.json` or `settings.json`):
```json
{
  "mcpServers": {
    "naukri": {
      "url": "https://<YOUR-RAILWAY-APP>.up.railway.app/mcp?rt=YOUR_NAUK_RT_COOKIE"
    }
  }
}
```

---

### 3. Claude Desktop & Cursor (Remote Mode)
Add to `claude_desktop_config.json` or `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "naukri": {
      "url": "https://<YOUR-RAILWAY-APP>.up.railway.app/sse?rt=YOUR_NAUK_RT_COOKIE"
    }
  }
}
```

#### URL Query Parameters:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `rt` / `nauk_rt` | string | **Yes** | Your `nauk_rt` refresh cookie from naukri.com. |
| `resume` | string | *Optional* | Public HTTP/HTTPS URL to candidate `master_resume.json`. |
| `pdf` | string | *Optional* | Public HTTP/HTTPS URL to download tailored resume PDF for 1-click uploads. |

#### Custom HTTP Headers (Alternative):
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

### 4. Local stdio Mode (Single Developer / CLI)
```bash
git clone https://github.com/prasadrawas/naukri_mcp.git
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

## 📚 MCP Resources

- `naukri://candidate/master-resume`: Authenticated source of truth for candidate facts, skills, and projects.
- `naukri://rules/platform-guidelines`: Naukri API schemas, accomplishment quotas (max 5), and date constraints.
- `naukri://profile/current`: Real-time candidate profile state across all sections.
- `naukri://analytics/dashboard`: Search appearance counts, profile views, and recruiter trend graphs.
- `naukri://inbox/recruiter-mails`: Recruiter messages, interview invitations, and status summary.
- `naukri://taxonomy/versions`: Standardized entity taxonomies for certifications, cities, and languages.
- `naukri://tools/directory`: Functional directory and schema metadata for the unified 6 MCP tools.

---

## 🧪 Testing Matrix (100% Pass Rate)

```bash
# Run unit tests across all tools, serializers, and multi-tenant middleware
python -m unittest discover naukri_mcp/tests

# Run live parameter matrix test against live Naukri CloudGateway endpoints
python naukri_mcp/tests/test_naukri_live_matrix.py
```

---

## 📄 License

MIT License.
