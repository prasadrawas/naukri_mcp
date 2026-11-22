"""
End-to-end testing of the unified 6-tool architecture in naukri-mcp server
using the official Model Context Protocol (MCP) ClientSession (tools/call).
"""
import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMCPProtocol(unittest.IsolatedAsyncioTestCase):

    async def test_mcp_session_list_and_call(self):
        env = os.environ.copy()
        params = StdioServerParameters(
            command=str(PROJECT_ROOT / ".venv" / "bin" / "python"),
            args=["-m", "naukri_mcp", "--transport", "stdio"],
            env=env
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_list = await session.list_tools()
                tool_names = [t.name for t in tools_list.tools]
                print(f"Connected via MCP ClientSession. Registered tools: {tool_names}")

                expected_tools = [
                    "manage_profile",
                    "search_jobs",
                    "get_job_details",
                    "apply_to_jobs",
                    "manage_recruiter_interactions",
                    "manage_session"
                ]
                self.assertEqual(len(tool_names), 6)
                for t in expected_tools:
                    self.assertIn(t, tool_names)

                # 1. Call manage_session: validate
                res1 = await session.call_tool("manage_session", arguments={"action": "validate"})
                payload1 = json.loads(res1.content[0].text)
                self.assertEqual(payload1.get("status"), "success")

                # 2. Call manage_recruiter_interactions: suggest_taxonomy
                res2 = await session.call_tool(
                    "manage_recruiter_interactions",
                    arguments={"action": "suggest_taxonomy", "taxonomy_type": "city", "query": "Pune", "limit": 2}
                )
                payload2 = json.loads(res2.content[0].text)
                self.assertEqual(payload2.get("status"), "success")

                # 3. Call manage_profile: get section='headline'
                res3 = await session.call_tool(
                    "manage_profile",
                    arguments={"action": "get", "section": "headline"}
                )
                payload3 = json.loads(res3.content[0].text)
                self.assertIn("headline", payload3)

                # 4. Call search_jobs
                res4 = await session.call_tool(
                    "search_jobs",
                    arguments={"keywords": "Python", "location": "Pune", "limit": 2}
                )
                payload4 = json.loads(res4.content[0].text)
                self.assertIn(payload4.get("status"), ("success", "recaptcha_required"))

                # 5. Call get_job_details
                res5 = await session.call_tool(
                    "get_job_details",
                    arguments={"job_ids": "150125000001"}
                )
                payload5 = json.loads(res5.content[0].text)
                self.assertIn(payload5.get("status"), ("success", "partial_success"))

                # 6. Call apply_to_jobs (batch mode test)
                res6 = await session.call_tool(
                    "apply_to_jobs",
                    arguments={"job_ids": ["150125000001"]}
                )
                payload6 = json.loads(res6.content[0].text)
                self.assertEqual(payload6.get("status"), "success")
                self.assertEqual(payload6.get("count"), 1)


if __name__ == "__main__":
    unittest.main()
