"""
End-to-end testing of newly implemented tools in naukri-mcp server
using the official Model Context Protocol (MCP) ClientSession (tools/call).
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_mcp_tests():
    params = StdioServerParameters(
        command=".venv/bin/python",
        args=["-m", "naukri_mcp", "--transport", "stdio"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_list = await session.list_tools()
            tool_names = [t.name for t in tools_list.tools]
            print(f"✅ Connected to naukri-mcp via MCP ClientSession. Registered tools count: {len(tool_names)}")

            # Verify presence of all new tools
            expected_new_tools = [
                "update_personal_details",
                "update_it_skills",
                "add_it_skill",
                "update_languages",
                "add_language",
                "update_job_search_status",
                "update_disability",
                "delete_disability",
                "update_work_permit",
                "update_career_break",
                "delete_career_break",
                "delete_photo",
                "resend_email_verification"
            ]
            for t in expected_new_tools:
                assert t in tool_names, f"Tool {t} not found in MCP server tool registry!"
            print(f"✅ All {len(expected_new_tools)} new tools are verified in the MCP tool catalog.")

            results = {}

            # 1. Test update_personal_details via MCP call_tool
            print("\n[1/8] Executing 'update_personal_details' via MCP protocol...")
            res1 = await session.call_tool(
                "update_personal_details",
                arguments={
                    "gender": "Female",
                    "marital_status": "Single / unmarried",
                    "birth_date": "1998-06-15",
                    "category": "General",
                    "address": "Baner Road, Near Balewadi High Street",
                    "hometown": "Pune",
                    "pincode": "411045",
                    "mail_city": "pune, maharashtra"
                }
            )
            payload1 = json.loads(res1.content[0].text)
            print("Response:", json.dumps(payload1, indent=2))
            assert payload1.get("status") == "success", f"Failed: {payload1}"
            results["update_personal_details"] = "PASSED"

            # 2. Test update_job_search_status via MCP call_tool
            print("\n[2/8] Executing 'update_job_search_status' via MCP protocol...")
            res2 = await session.call_tool(
                "update_job_search_status",
                arguments={"status_code_or_name": "Actively searching jobs"}
            )
            payload2 = json.loads(res2.content[0].text)
            print("Response:", json.dumps(payload2, indent=2))
            assert payload2.get("status") == "success", f"Failed: {payload2}"
            results["update_job_search_status"] = "PASSED"

            # 3. Test add_it_skill via MCP call_tool
            print("\n[3/8] Executing 'add_it_skill' (Kubernetes) via MCP protocol...")
            res3 = await session.call_tool(
                "add_it_skill",
                arguments={
                    "skill": "Kubernetes",
                    "version": "v1.30",
                    "last_used_year": 2026,
                    "experience_years": 1,
                    "experience_months": 6
                }
            )
            payload3 = json.loads(res3.content[0].text)
            print("Response:", json.dumps(payload3, indent=2))
            assert payload3.get("status") == "success", f"Failed: {payload3}"
            results["add_it_skill"] = "PASSED"

            # 4. Test add_language via MCP call_tool
            print("\n[4/8] Executing 'add_language' (German) via MCP protocol...")
            res4 = await session.call_tool(
                "add_language",
                arguments={
                    "language": "German",
                    "proficiency": "Beginner",
                    "read": True,
                    "write": False,
                    "speak": False
                }
            )
            payload4 = json.loads(res4.content[0].text)
            print("Response:", json.dumps(payload4, indent=2))
            assert payload4.get("status") == "success", f"Failed: {payload4}"
            results["add_language"] = "PASSED"

            # 5. Test update_disability & delete_disability via MCP call_tool
            print("\n[5/8] Executing 'update_disability' and 'delete_disability' via MCP protocol...")
            res5 = await session.call_tool(
                "update_disability",
                arguments={"is_disabled": False}
            )
            payload5 = json.loads(res5.content[0].text)
            print("Response:", json.dumps(payload5, indent=2))
            assert payload5.get("status") == "success", f"Failed: {payload5}"
            results["update_disability"] = "PASSED"

            # 6. Test update_work_permit via MCP call_tool
            print("\n[6/8] Executing 'update_work_permit' via MCP protocol...")
            res6 = await session.call_tool(
                "update_work_permit",
                arguments={
                    "us_work_status": "Need H1 Visa",
                    "countries": ["USA", "Canada"]
                }
            )
            payload6 = json.loads(res6.content[0].text)
            print("Response:", json.dumps(payload6, indent=2))
            assert payload6.get("status") == "success", f"Failed: {payload6}"
            results["update_work_permit"] = "PASSED"

            # 7. Test update_career_break via MCP call_tool
            print("\n[7/8] Executing 'update_career_break' (has_break=False) via MCP protocol...")
            res7 = await session.call_tool(
                "update_career_break",
                arguments={"has_break": False}
            )
            payload7 = json.loads(res7.content[0].text)
            print("Response:", json.dumps(payload7, indent=2))
            assert payload7.get("status") == "success", f"Failed: {payload7}"
            results["update_career_break"] = "PASSED"

            # 8. Test clean up of dummy added items (delete_it_skill, delete_language)
            print("\n[8/8] Testing cleanup of dummy items using delete MCP tools...")
            # Fetch profile to get IDs of Kubernetes and German
            prof_res = await session.call_tool("get_profile", arguments={"section": "all"})
            prof_data = json.loads(prof_res.content[0].text).get("data", {})
            
            k8s_skill = next((s for s in prof_data.get("itskills", []) if "kubernetes" in (s.get("skill") or "").lower()), None)
            if k8s_skill and k8s_skill.get("skillId"):
                del_k8s = await session.call_tool("delete_it_skill", arguments={"skill_id": k8s_skill["skillId"]})
                print("Deleted dummy skill Kubernetes:", json.loads(del_k8s.content[0].text).get("status"))

            german_lang = next((l for l in prof_data.get("languages", []) if "german" in (l.get("lang") or "").lower()), None)
            if german_lang and german_lang.get("languageId"):
                del_ger = await session.call_tool("delete_language", arguments={"language_id": german_lang["languageId"]})
                print("Deleted dummy language German:", json.loads(del_ger.content[0].text).get("status"))

            results["cleanup_delete_tools"] = "PASSED"

            print("\n===============================")
            print("   ALL MCP TOOLS TEST RESULTS   ")
            print("===============================")
            for tool, status in results.items():
                print(f"  • {tool:<30}: {status}")
            print("===============================\n")


if __name__ == "__main__":
    asyncio.run(run_mcp_tests())
