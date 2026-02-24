"""Activity and workout tools."""

from oura_mcp_server.api.client import get_daily_activity, get_workouts
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.models.activity import ActivitySummary, Workout
from oura_mcp_server.utils.dates import parse_date_range


@mcp.tool()
async def oura_get_activity(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get daily activity summary with steps, calories, and movement scores.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns activity score, steps, calories, active time breakdown.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=7)
    result = await get_daily_activity(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No activity data found for {start} to {end}."

    summaries = [ActivitySummary.from_api(d) for d in items]
    lines = [f"Daily Activity ({start} to {end}) — {len(summaries)} day(s)", ""]
    for s in summaries:
        lines.append(s.format())
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def oura_get_workout(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get workout sessions with type, duration, intensity, and calories.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns detected and manual workout sessions.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=7)
    result = await get_workouts(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No workouts found for {start} to {end}."

    workouts = [Workout.from_api(d) for d in items]
    lines = [f"Workouts ({start} to {end}) — {len(workouts)} session(s)", ""]
    for w in workouts:
        lines.append(w.format())
        lines.append("")
    return "\n".join(lines)
