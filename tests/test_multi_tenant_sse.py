"""
Tests for multi-tenant SSE transport, session isolation, token caching,
and personalized query parameters/headers in naukri-mcp.
"""
import unittest
import asyncio
import time
from typing import override
from urllib.parse import quote
from starlette.testclient import TestClient

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
import uvicorn

from naukri_mcp.server import mcp, get_app, app
from naukri_mcp.auth import (
    SESSION_STORE,
    TOKEN_CACHE,
    current_session_id,
    current_session_rt,
    current_session_resume_url,
    current_session_pdf_url,
    resolve_auth_tokens,
    clean_stale_sessions
)


class TestMultiTenantSSE(unittest.TestCase):
    @override
    def setUp(self):
        # Clear stores before each test
        SESSION_STORE.clear()
        TOKEN_CACHE.clear()

    def test_health_endpoint(self):
        """Verify /health returns HTTP 200 with service info."""
        client = TestClient(app)
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "naukri-mcp")

    def test_root_index_endpoint(self):
        """Verify / returns HTTP 200 HTML documentation."""
        client = TestClient(app)
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("content-type", ""))
        self.assertIn("Naukri MCP Server", resp.text)
        self.assertIn("Connect to Claude Web", resp.text)

    def test_cors_preflight(self):
        """Verify OPTIONS requests return 200 with CORS headers for Claude Web."""
        client = TestClient(app)
        resp = client.options(
            "/sse",
            headers={
                "Origin": "https://claude.ai",
                "Access-Control-Request-Method": "GET"
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "*")

    def test_root_redirect_with_query_params(self):
        """Verify root URL with rt query parameter redirects to /sse."""
        client = TestClient(app)
        resp = client.get("/?rt=dummy_token_123", follow_redirects=False)
        self.assertEqual(resp.status_code, 307)
        self.assertEqual(resp.headers.get("location"), "/sse?rt=dummy_token_123")

    def test_stale_session_cleanup(self):
        """Verify old inactive sessions are purged from memory."""
        now = time.time()
        SESSION_STORE["active_sess"] = {"rt": "abc", "last_seen": now}
        SESSION_STORE["stale_sess"] = {"rt": "xyz", "last_seen": now - 100000}

        clean_stale_sessions(max_age_seconds=86400)
        self.assertIn("active_sess", SESSION_STORE)
        self.assertNotIn("stale_sess", SESSION_STORE)

    def test_token_cache_reuse(self):
        """Verify cached valid tokens are reused without network calls."""
        fake_rt = "fake_refresh_token_12345"
        fake_at = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE5OTk5OTk5OTksInN1YiI6InRlc3QifQ.signature"
        TOKEN_CACHE[fake_rt] = {"at": fake_at, "exp": 1999999999}

        current_session_rt.set(fake_rt)
        at, rt = resolve_auth_tokens()
        self.assertEqual(at, fake_at)
        self.assertEqual(rt, fake_rt)

    def test_missing_token_raises_actionable_error(self):
        """Verify missing token raises clear actionable PermissionError when no credentials exist."""
        import os
        from unittest.mock import patch
        current_session_rt.set("")
        with patch.dict(os.environ, {"NAUK_AT": "", "NAUK_RT": ""}, clear=True):
            with self.assertRaises(PermissionError) as ctx:
                resolve_auth_tokens()
            self.assertIn("Naukri session token (nauk_rt) is required", str(ctx.exception))
            self.assertIn("refresh_session_token", str(ctx.exception))


class TestLiveSSEClientIsolation(unittest.IsolatedAsyncioTestCase):
    @override
    async def asyncSetUp(self):
        SESSION_STORE.clear()
        TOKEN_CACHE.clear()
        self.port = 8995
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(self.server.serve())
        await asyncio.sleep(0.5)

    @override
    async def asyncTearDown(self):
        self.server.should_exit = True
        await self.server_task

    async def test_multi_client_credential_isolation(self):
        """Verify two distinct clients with different query parameters get isolated credentials."""
        user_a_rt = "RT_USER_A_COOKIE_VALUE"
        user_b_rt = "RT_USER_B_COOKIE_VALUE"
        resume_a = "https://example.com/resumes/user_a.json"
        resume_b = "https://example.com/resumes/user_b.json"

        # Prime fake tokens into TOKEN_CACHE so tool calls succeed without real Naukri credentials
        TOKEN_CACHE[user_a_rt] = {"at": "AT_USER_A", "exp": int(time.time()) + 3600}
        TOKEN_CACHE[user_b_rt] = {"at": "AT_USER_B", "exp": int(time.time()) + 3600}

        # Client A connection
        url_a = f"http://127.0.0.1:{self.port}/sse?rt={user_a_rt}&resume={quote(resume_a)}"
        async with sse_client(url_a) as (read_a, write_a):
            async with ClientSession(read_a, write_a) as session_a:
                await session_a.initialize()
                # Inspect candidate master resume resource
                res_a = await session_a.read_resource("naukri://candidate/master-resume")
                self.assertIsNotNone(res_a)

        # Client B connection
        url_b = f"http://127.0.0.1:{self.port}/sse?rt={user_b_rt}&resume={quote(resume_b)}"
        async with sse_client(url_b) as (read_b, write_b):
            async with ClientSession(read_b, write_b) as session_b:
                await session_b.initialize()
                res_b = await session_b.read_resource("naukri://candidate/master-resume")
                self.assertIsNotNone(res_b)

        # Verify session store contains both sessions with distinct credentials
        sessions = list(SESSION_STORE.values())
        rts = [s.get("rt") for s in sessions]
        self.assertIn(user_a_rt, rts)
        self.assertIn(user_b_rt, rts)


if __name__ == "__main__":
    unittest.main()
