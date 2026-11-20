"""
Resume upload and validation tool for naukri_mcp.
Supports local file path, remote HTTP URL, or base64 PDF strings.
"""
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Union

from naukri_mcp.auth import resolve_auth_tokens
from naukri_mcp.client import (
    RESUME_VALIDATE_URL,
    ADV_RESUME_URL_TMPL,
    RESUME_FORM_KEY,
    RESUME_FILE_KEY,
    DEFAULT_USER_AGENT,
    get_headers,
    make_api_request
)
from naukri_mcp.tools.profile import get_profile
from naukri_mcp.utils import resolve_pdf_source


def upload_resume(
    source: Optional[str] = None,
    nauk_at: Optional[str] = None,
    nauk_rt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload and attach a PDF resume to candidate's Naukri profile.

    :param source: Local PDF file path, remote HTTP/HTTPS download URL, base64-encoded PDF string, or None (to use RESUME_PDF_PATH env).
    :param nauk_at: Optional bearer access token (falls back to NAUK_AT).
    :param nauk_rt: Optional refresh token.
    """
    at, rt = resolve_auth_tokens(nauk_at, nauk_rt)
    prof_res = get_profile(section="headline", nauk_at=at, nauk_rt=rt)
    pid = prof_res.get("profile_id", "")
    if not pid:
        return {"status": "error", "message": "Could not retrieve candidate profile ID."}

    try:
        pdf_bytes, filename = resolve_pdf_source(source)
    except Exception as e:
        return {"status": "error", "message": f"Failed to resolve PDF source: {e}"}

    file_size = len(pdf_bytes)

    # Step 1: Upload to filevalidation.naukri.com
    boundary = f"----geckoformboundary{int(time.time()*1000)}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="formKey"\r\n\r\n{RESUME_FORM_KEY}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + pdf_bytes + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="fileName"\r\n\r\n{filename}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="uploadCallback"\r\n\r\ntrue\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="fileKey"\r\n\r\n{RESUME_FILE_KEY}\r\n'
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    file_headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "appId": "105",
        "systemId": "fileupload",
        "Origin": "https://www.naukri.com",
        "Referer": "https://www.naukri.com/",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }

    try:
        req = urllib.request.Request(RESUME_VALIDATE_URL, data=body, headers=file_headers, method="POST")
        with urllib.request.urlopen(req, timeout=25) as resp:
            _ = resp.status
    except Exception as e:
        return {"status": "error", "message": f"Resume validation service upload failed: {e}"}

    # Step 2: Attach to advResume in CloudGateway
    adv_url = ADV_RESUME_URL_TMPL.format(profile_id=pid)
    attach_payload = {
        "textCV": {
            "formKey": RESUME_FORM_KEY,
            "fileKey": RESUME_FILE_KEY,
            "textCvContent": None
        }
    }
    attach_headers = get_headers(at, rt, is_mutation=True)
    attach_headers["AppId"] = "105"
    attach_headers["SystemId"] = "105"

    status, resp_data = make_api_request(
        adv_url,
        method="POST",
        headers=attach_headers,
        data=json.dumps(attach_payload).encode("utf-8")
    )

    if status in (200, 201):
        return {
            "status": "success",
            "filename": filename,
            "file_size_bytes": file_size,
            "message": "Resume uploaded and attached to Naukri profile successfully."
        }

    return {
        "status": "error",
        "http_status": status,
        "message": "Failed to attach validated resume to profile.",
        "details": resp_data
    }
