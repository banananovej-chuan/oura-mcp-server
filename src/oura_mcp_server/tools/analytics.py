"""Analytics tools — trends, recovery status."""

from statistics import mean

from oura_mcp_server.api.client import (
    get_daily_sleep,
    get_daily_activity,
    get_daily_readiness,
    get_sleep_periods,
    get_heart_rate,
)
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.utils.dates import get_date_ago, get_today
from oura_mcp_server.utils.formatting import (
    format_duration,
    format_score,
    format_steps,
    format_calories,
    format_hr,
)


@mcp.tool()
async def oura_sleep_trend(days: int = 30) -> str:
    """Analyze multi-day sleep trends with averages and consistency.

    Args:
        days: Number of days to analyze (default 30).

    Returns average sleep score, duration trend, efficiency, stage breakdown,
    and consistency metrics.
    """
    start = get_date_ago(days)
    end = get_today()
    result = await get_daily_sleep(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No sleep data found for the last {days} days."

    scores = [d["score"] for d in items if d.get("score") is not None]

    lines = [
        f"Sleep Trend — Last {days} Days ({len(items)} days with data)",
        "",
        "Scores:",
        f"  Average: {mean(scores):.0f}/100" if scores else "  Average: N/A",
        f"  Best: {max(scores)}/100" if scores else "  Best: N/A",
        f"  Worst: {min(scores)}/100" if scores else "  Worst: N/A",
    ]

    if len(scores) >= 2:
        from statistics import stdev
        lines.append(f"  Std Dev: {stdev(scores):.1f} (consistency)")

    # Trend: compare first half vs second half
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = mean(scores[:mid])
        second_half = mean(scores[mid:])
        diff = second_half - first_half
        trend = "improving" if diff > 2 else "declining" if diff < -2 else "stable"
        lines.append(f"  Trend: {trend} ({diff:+.1f} pts)")

    # Day-by-day
    lines.append("")
    lines.append("Daily Scores:")
    for d in items:
        score = d.get("score")
        day = d.get("day", "")
        lines.append(f"  {day}: {format_score(score)}")

    return "\n".join(lines)


@mcp.tool()
async def oura_activity_trend(days: int = 30) -> str:
    """Analyze multi-day activity trends with averages.

    Args:
        days: Number of days to analyze (default 30).

    Returns average steps, calories burned, active time trends.
    """
    start = get_date_ago(days)
    end = get_today()
    result = await get_daily_activity(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No activity data found for the last {days} days."

    scores = [d["score"] for d in items if d.get("score") is not None]
    steps_list = [d["steps"] for d in items if d.get("steps") is not None]
    active_cals = [d["active_calories"] for d in items if d.get("active_calories") is not None]
    high_times = [d["high_activity_time"] for d in items if d.get("high_activity_time") is not None]
    medium_times = [d["medium_activity_time"] for d in items if d.get("medium_activity_time") is not None]

    lines = [
        f"Activity Trend — Last {days} Days ({len(items)} days with data)",
        "",
        "Averages:",
    ]
    if scores:
        lines.append(f"  Activity Score: {mean(scores):.0f}/100")
    if steps_list:
        lines.append(f"  Steps: {format_steps(int(mean(steps_list)))}")
        lines.append(f"  Total Steps: {format_steps(sum(steps_list))}")
    if active_cals:
        lines.append(f"  Active Calories: {format_calories(mean(active_cals))}")
    if high_times:
        lines.append(f"  High Activity: {format_duration(int(mean(high_times)))}/day")
    if medium_times:
        lines.append(f"  Medium Activity: {format_duration(int(mean(medium_times)))}/day")

    # Trend
    if len(steps_list) >= 4:
        mid = len(steps_list) // 2
        first_half = mean(steps_list[:mid])
        second_half = mean(steps_list[mid:])
        diff_pct = ((second_half - first_half) / first_half * 100) if first_half else 0
        trend = "increasing" if diff_pct > 5 else "decreasing" if diff_pct < -5 else "stable"
        lines.append(f"\n  Steps Trend: {trend} ({diff_pct:+.0f}%)")

    # Daily breakdown
    lines.append("")
    lines.append("Daily Steps:")
    for d in items:
        day = d.get("day", "")
        s = d.get("steps")
        sc = d.get("score")
        lines.append(f"  {day}: {format_steps(s)} (score: {format_score(sc)})")

    return "\n".join(lines)


@mcp.tool()
async def oura_readiness_trend(days: int = 14) -> str:
    """Analyze multi-day readiness score trends.

    Args:
        days: Number of days to analyze (default 14).

    Returns readiness score trend, contributor breakdown, and consistency.
    """
    start = get_date_ago(days)
    end = get_today()
    result = await get_daily_readiness(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No readiness data found for the last {days} days."

    scores = [d["score"] for d in items if d.get("score") is not None]

    lines = [
        f"Readiness Trend — Last {days} Days ({len(items)} days with data)",
        "",
        "Scores:",
        f"  Average: {mean(scores):.0f}/100" if scores else "  Average: N/A",
        f"  Best: {max(scores)}/100" if scores else "  Best: N/A",
        f"  Worst: {min(scores)}/100" if scores else "  Worst: N/A",
    ]

    if len(scores) >= 2:
        from statistics import stdev
        lines.append(f"  Std Dev: {stdev(scores):.1f}")

    # Top contributors aggregate
    all_contributors: dict[str, list[int]] = {}
    for d in items:
        for key, val in d.get("contributors", {}).items():
            if val is not None:
                all_contributors.setdefault(key, []).append(val)

    if all_contributors:
        lines.append("")
        lines.append("Average Contributors:")
        sorted_contribs = sorted(
            all_contributors.items(), key=lambda x: mean(x[1]), reverse=True
        )
        for key, vals in sorted_contribs:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {mean(vals):.0f}")

    # Daily
    lines.append("")
    lines.append("Daily Scores:")
    for d in items:
        day = d.get("day", "")
        score = d.get("score")
        lines.append(f"  {day}: {format_score(score)}")

    return "\n".join(lines)


@mcp.tool()
async def oura_recovery_status() -> str:
    """Get today's combined recovery snapshot: readiness + sleep + HRV.

    Returns a unified view of readiness score, last night's sleep quality,
    and HRV baseline for quick recovery assessment.
    """
    today = get_today()
    yesterday = get_date_ago(1)

    # Fetch all data in parallel-ish (sequential for simplicity, all fast)
    readiness_data = await get_daily_readiness(today, today)
    sleep_data = await get_daily_sleep(yesterday, today)
    sleep_periods = await get_sleep_periods(yesterday, today)

    lines = ["Recovery Status — Today", ""]

    # Readiness
    readiness_items = readiness_data.get("data", []) if isinstance(readiness_data, dict) and not readiness_data.get("error") else []
    if readiness_items:
        r = readiness_items[-1]
        score = r.get("score")
        lines.append(f"Readiness: {format_score(score)}")
        if score is not None:
            if score >= 85:
                lines.append("  Status: Optimal — ready for high-intensity training")
            elif score >= 70:
                lines.append("  Status: Good — normal training load appropriate")
            elif score >= 60:
                lines.append("  Status: Fair — consider lighter training")
            else:
                lines.append("  Status: Low — prioritize recovery")
    else:
        lines.append("Readiness: No data yet today")

    lines.append("")

    # Sleep
    sleep_items = sleep_data.get("data", []) if isinstance(sleep_data, dict) and not sleep_data.get("error") else []
    if sleep_items:
        s = sleep_items[-1]
        lines.append(f"Last Night's Sleep: {format_score(s.get('score'))}")
    else:
        lines.append("Sleep: No data")

    # HRV from sleep period
    period_items = sleep_periods.get("data", []) if isinstance(sleep_periods, dict) and not sleep_periods.get("error") else []
    if period_items:
        # Get the most recent long_sleep period
        long_sleeps = [p for p in period_items if p.get("type") == "long_sleep"]
        period = long_sleeps[-1] if long_sleeps else period_items[-1]
        avg_hrv = period.get("average_hrv")
        lowest_hr = period.get("lowest_heart_rate")
        avg_hr = period.get("average_heart_rate")
        lines.append("")
        lines.append("Overnight Biometrics:")
        lines.append(f"  Average HRV: {avg_hrv} ms" if avg_hrv else "  Average HRV: N/A")
        lines.append(f"  Lowest HR: {format_hr(lowest_hr)}")
        lines.append(f"  Average HR: {format_hr(avg_hr)}")

    return "\n".join(lines)
