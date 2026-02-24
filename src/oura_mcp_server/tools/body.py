"""Body tools — SpO2, resilience."""

from oura_mcp_server.api.client import get_daily_spo2, get_daily_resilience
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.models.body import SpO2, Resilience
from oura_mcp_server.utils.dates import parse_date_range


@mcp.tool()
async def oura_get_spo2(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get blood oxygen (SpO2) readings.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns average SpO2 percentage for each day.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=7)
    result = await get_daily_spo2(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No SpO2 data found for {start} to {end}."

    readings = [SpO2.from_api(d) for d in items]
    lines = [f"Blood Oxygen (SpO2) ({start} to {end}) — {len(readings)} day(s)", ""]
    for r in readings:
        lines.append(r.format())
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def oura_get_resilience(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get stress resilience data.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns resilience level and contributor breakdown.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=7)
    result = await get_daily_resilience(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No resilience data found for {start} to {end}."

    readings = [Resilience.from_api(d) for d in items]
    lines = [f"Resilience ({start} to {end}) — {len(readings)} day(s)", ""]
    for r in readings:
        lines.append(r.format())
        lines.append("")
    return "\n".join(lines)
