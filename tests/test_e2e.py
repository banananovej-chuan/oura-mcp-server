"""End-to-end test of the Oura Ring MCP Server.

Uses the MCP Python SDK client to connect to the server via stdio,
lists tools, and calls each tool verifying real API responses.

Requires: OURA_ACCESS_TOKEN set in .env or environment.

Usage:
    python tests/test_e2e.py          # run via local .venv
    python tests/test_e2e.py --uvx    # run via uvx (like a real user)
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_DIR = Path(__file__).parent.parent
SERVER_PYTHON = str(PROJECT_DIR / ".venv" / "bin" / "python")


def load_env() -> dict[str, str]:
    """Load .env file and merge with current environment."""
    env = dict(os.environ)
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip("'\"")
    return env


def get_server_params(use_uvx: bool = False) -> StdioServerParameters:
    """Build server params for local venv or uvx mode."""
    env = load_env()
    if use_uvx:
        uvx_path = shutil.which("uvx") or str(Path.home() / ".local" / "bin" / "uvx")
        return StdioServerParameters(
            command=uvx_path,
            args=["oura-mcp-server"],
            env=env,
        )
    return StdioServerParameters(
        command=SERVER_PYTHON,
        args=["-m", "oura_mcp_server"],
        cwd=str(PROJECT_DIR),
        env={**env, "PYTHONPATH": str(PROJECT_DIR / "src")},
    )


async def run_e2e(use_uvx: bool = False):
    results = []
    passed = 0
    failed = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal passed, failed
        if ok:
            passed += 1
        else:
            failed += 1
        results.append((name, "PASS" if ok else "FAIL", detail))
        icon = "+" if ok else "!"
        print(f"  [{icon}] {name}" + (f" — {detail}" if detail else ""))

    mode = "uvx (PyPI)" if use_uvx else "local .venv"
    print("=" * 60)
    print(f"Oura Ring MCP Server — E2E Test ({mode})")
    print("=" * 60)

    server_params = get_server_params(use_uvx)

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. Initialize
            print("\n## MCP Protocol")
            result = await session.initialize()
            check(
                "Initialize",
                result.serverInfo.name == "oura",
                f"server={result.serverInfo.name}",
            )

            # 2. List tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            tool_names = [t.name for t in tools]
            check("List tools", len(tools) == 20, f"got {len(tools)} tools")

            expected_tools = [
                "oura_auth_status", "oura_get_profile", "oura_get_ring_config",
                "oura_get_sleep", "oura_get_sleep_period",
                "oura_get_activity", "oura_get_workout",
                "oura_get_readiness",
                "oura_get_heart_rate",
                "oura_get_spo2", "oura_get_resilience",
                "oura_get_tags",
                "oura_sleep_trend", "oura_activity_trend",
                "oura_readiness_trend", "oura_recovery_status",
                "oura_correlate", "oura_sleep_activity_correlation",
                "oura_hrv_analysis", "oura_weekly_report",
            ]
            missing = [t for t in expected_tools if t not in tool_names]
            check("All tools registered", not missing, f"missing: {missing}" if missing else "all 20 present")

            tools_with_desc = [t for t in tools if t.description]
            check("Tool descriptions", len(tools_with_desc) == 20, f"{len(tools_with_desc)}/20")

            # Helper to call a tool and get text
            async def call(name: str, args: dict | None = None) -> str:
                r = await session.call_tool(name, arguments=args or {})
                texts = [c.text for c in r.content if hasattr(c, "text")]
                return "\n".join(texts)

            # 3. Auth
            print("\n## Auth")
            text = await call("oura_auth_status")
            check("oura_auth_status", "Authenticated" in text, text.split("\n")[0][:60])

            # 4. Profile
            print("\n## Profile & Ring")
            text = await call("oura_get_profile")
            has_profile = "Profile" in text
            check("oura_get_profile", has_profile, text.split("\n")[0][:60])

            text = await call("oura_get_ring_config")
            has_ring = "Ring" in text or "Configuration" in text or "No ring" in text or "Error" in text
            check("oura_get_ring_config", has_ring, text.split("\n")[0][:60])

            # 5. Sleep
            print("\n## Sleep")
            text = await call("oura_get_sleep")
            has_sleep = "Sleep" in text
            check("oura_get_sleep (default)", has_sleep, f"{len(text)} chars")

            text = await call("oura_get_sleep_period")
            has_period = "Sleep Period" in text or "No sleep" in text
            check("oura_get_sleep_period (default)", has_period, text.split("\n")[0][:60])

            # 6. Activity
            print("\n## Activity")
            text = await call("oura_get_activity")
            has_activity = "Activity" in text
            check("oura_get_activity (default)", has_activity, f"{len(text)} chars")

            text = await call("oura_get_workout")
            has_workout = "Workout" in text or "No workout" in text
            check("oura_get_workout (default)", has_workout, text.split("\n")[0][:60])

            # 7. Readiness & Heart
            print("\n## Readiness & Heart Rate")
            text = await call("oura_get_readiness")
            has_readiness = "Readiness" in text
            check("oura_get_readiness (default)", has_readiness, text.split("\n")[0][:60])

            text = await call("oura_get_heart_rate")
            has_hr = "Heart Rate" in text or "No heart" in text
            check("oura_get_heart_rate (default)", has_hr, text.split("\n")[0][:60])

            # 8. Body & Tags
            print("\n## Body & Tags")
            text = await call("oura_get_spo2")
            has_spo2 = "SpO2" in text or "No SpO2" in text or "Error" in text
            check("oura_get_spo2", has_spo2, text.split("\n")[0][:60])

            text = await call("oura_get_resilience")
            has_resilience = "Resilience" in text or "No resilience" in text or "Error" in text
            check("oura_get_resilience", has_resilience, text.split("\n")[0][:60])

            text = await call("oura_get_tags")
            has_tags = "Tag" in text or "No tag" in text
            check("oura_get_tags", has_tags, text.split("\n")[0][:60])

            # 9. Analytics
            print("\n## Analytics")
            text = await call("oura_sleep_trend", {"days": 30})
            has_trend = "Sleep Trend" in text or "No sleep" in text
            check("oura_sleep_trend (30d)", has_trend, text.split("\n")[0][:60])

            text = await call("oura_activity_trend", {"days": 30})
            has_act_trend = "Activity Trend" in text or "No activity" in text
            check("oura_activity_trend (30d)", has_act_trend, text.split("\n")[0][:60])

            text = await call("oura_readiness_trend", {"days": 14})
            has_rdy_trend = "Readiness Trend" in text or "No readiness" in text
            check("oura_readiness_trend (14d)", has_rdy_trend, text.split("\n")[0][:60])

            text = await call("oura_recovery_status")
            has_recovery = "Recovery" in text
            check("oura_recovery_status", has_recovery, text.split("\n")[0][:60])

            # 10. Correlations & Advanced
            print("\n## Correlations & Advanced Analysis")
            text = await call("oura_correlate", {"metric_a": "sleep_score", "metric_b": "steps", "days": 30})
            has_corr = "Correlation" in text or "Insufficient" in text
            check("oura_correlate (sleep vs steps)", has_corr, text.split("\n")[0][:60])

            text = await call("oura_sleep_activity_correlation", {"days": 30})
            has_sa_corr = "Sleep-Activity" in text or "insufficient" in text
            check("oura_sleep_activity_correlation", has_sa_corr, text.split("\n")[0][:60])

            text = await call("oura_hrv_analysis", {"days": 30})
            has_hrv = "HRV Analysis" in text or "No HRV" in text or "Insufficient" in text
            check("oura_hrv_analysis (30d)", has_hrv, text.split("\n")[0][:60])

            text = await call("oura_weekly_report", {"weeks": 4})
            has_report = "Weekly Report" in text
            check("oura_weekly_report (4 weeks)", has_report, text.split("\n")[0][:60])

            # 11. Error Handling
            print("\n## Error Handling")
            text = await call("oura_get_sleep", {"start_date": "invalid-date"})
            check("Invalid date format", "Error" in text or "error" in text.lower(), text.split("\n")[0][:60])

            text = await call("oura_correlate", {"metric_a": "nonexistent", "metric_b": "steps", "days": 30})
            check("Invalid metric", "Invalid" in text, text.split("\n")[0][:60])

    # Summary
    print("\n" + "=" * 60)
    print(f"E2E Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    if failed > 0:
        print("\nFailed tests:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f"  {name}: {detail}")

    return failed == 0


if __name__ == "__main__":
    use_uvx = "--uvx" in sys.argv
    ok = asyncio.run(run_e2e(use_uvx=use_uvx))
    sys.exit(0 if ok else 1)
