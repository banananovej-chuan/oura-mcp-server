"""Readiness tools."""

from oura_mcp_server.api.client import get_daily_readiness
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.models.readiness import ReadinessSummary
from oura_mcp_server.utils.dates import parse_date_range


@mcp.tool()
async def oura_get_readiness(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get readiness score and contributor breakdown.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns readiness score, temperature deviation, and contributor details.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=7)
    result = await get_daily_readiness(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No readiness data found for {start} to {end}."

    summaries = [ReadinessSummary.from_api(d) for d in items]
    lines = [f"Daily Readiness ({start} to {end}) — {len(summaries)} day(s)", ""]
    for s in summaries:
        lines.append(s.format())
        lines.append("")
    return "\n".join(lines)
