"""Sleep tools — daily summary and detailed period data."""

from oura_mcp_server.api.client import get_daily_sleep, get_sleep_periods
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.models.sleep import SleepSummary, SleepPeriod
from oura_mcp_server.utils.dates import parse_date_range


@mcp.tool()
async def oura_get_sleep(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get daily sleep summary with score, duration, and stage breakdown.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns sleep score, contributor breakdown for each day.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=7)
    result = await get_daily_sleep(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No sleep data found for {start} to {end}."

    summaries = [SleepSummary.from_api(d) for d in items]
    lines = [f"Daily Sleep ({start} to {end}) — {len(summaries)} day(s)", ""]
    for s in summaries:
        lines.append(s.format())
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def oura_get_sleep_period(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get detailed sleep period data including HR, HRV, and sleep stages timeline.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 1 day ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns detailed per-period data: bedtime, stages, heart rate, HRV, efficiency.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=1)
    result = await get_sleep_periods(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No sleep period data found for {start} to {end}."

    periods = [SleepPeriod.from_api(d) for d in items]
    lines = [f"Sleep Periods ({start} to {end}) — {len(periods)} period(s)", ""]
    for p in periods:
        lines.append(p.format())
        lines.append("")
    return "\n".join(lines)
