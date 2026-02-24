"""Correlation and advanced analysis tools."""

import math
from statistics import mean, stdev

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


def _pearson(x: list[float], y: list[float]) -> float | None:
    """Calculate Pearson correlation coefficient. Returns None if insufficient data."""
    n = len(x)
    if n < 3 or len(y) != n:
        return None
    mx, my = mean(x), mean(y)
    sx, sy = stdev(x), stdev(y)
    if sx == 0 or sy == 0:
        return None
    r = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / ((n - 1) * sx * sy)
    return max(-1.0, min(1.0, r))


def _interpret_r(r: float | None) -> str:
    """Interpret Pearson r value in plain language."""
    if r is None:
        return "insufficient data"
    abs_r = abs(r)
    if abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.4:
        strength = "moderate"
    elif abs_r >= 0.2:
        strength = "weak"
    else:
        return "no meaningful correlation"
    direction = "positive" if r > 0 else "negative"
    return f"{strength} {direction} correlation"


# Metric extraction functions
async def _get_metric_data(metric: str, start: str, end: str) -> dict[str, float]:
    """Fetch a named metric and return {day: value} dict."""
    if metric in ("sleep_score",):
        data = await get_daily_sleep(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        return {d["day"]: d["score"] for d in items if d.get("score") is not None}

    if metric in ("readiness_score",):
        data = await get_daily_readiness(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        return {d["day"]: d["score"] for d in items if d.get("score") is not None}

    if metric in ("steps",):
        data = await get_daily_activity(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        return {d["day"]: d["steps"] for d in items if d.get("steps") is not None}

    if metric in ("active_calories",):
        data = await get_daily_activity(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        return {d["day"]: d["active_calories"] for d in items if d.get("active_calories") is not None}

    if metric in ("activity_score",):
        data = await get_daily_activity(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        return {d["day"]: d["score"] for d in items if d.get("score") is not None}

    if metric in ("hrv", "average_hrv"):
        data = await get_sleep_periods(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        result = {}
        for d in items:
            if d.get("type") == "long_sleep" and d.get("average_hrv") is not None:
                result[d["day"]] = d["average_hrv"]
        return result

    if metric in ("resting_hr", "lowest_heart_rate"):
        data = await get_sleep_periods(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        result = {}
        for d in items:
            if d.get("type") == "long_sleep" and d.get("lowest_heart_rate") is not None:
                result[d["day"]] = d["lowest_heart_rate"]
        return result

    if metric in ("deep_sleep_duration",):
        data = await get_sleep_periods(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        result = {}
        for d in items:
            if d.get("type") == "long_sleep" and d.get("deep_sleep_duration") is not None:
                result[d["day"]] = d["deep_sleep_duration"] / 60  # to minutes
        return result

    if metric in ("total_sleep_duration",):
        data = await get_sleep_periods(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        result = {}
        for d in items:
            if d.get("type") == "long_sleep" and d.get("total_sleep_duration") is not None:
                result[d["day"]] = d["total_sleep_duration"] / 60  # to minutes
        return result

    if metric in ("efficiency",):
        data = await get_sleep_periods(start, end)
        items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
        result = {}
        for d in items:
            if d.get("type") == "long_sleep" and d.get("efficiency") is not None:
                result[d["day"]] = d["efficiency"]
        return result

    return {}


VALID_METRICS = [
    "sleep_score", "readiness_score", "steps", "active_calories",
    "activity_score", "hrv", "resting_hr", "deep_sleep_duration",
    "total_sleep_duration", "efficiency",
]


@mcp.tool()
async def oura_correlate(
    metric_a: str,
    metric_b: str,
    days: int = 30,
) -> str:
    """Correlate any two Oura metrics with Pearson coefficient.

    Args:
        metric_a: First metric name. Options: sleep_score, readiness_score, steps,
                  active_calories, activity_score, hrv, resting_hr,
                  deep_sleep_duration, total_sleep_duration, efficiency
        metric_b: Second metric name (same options as metric_a).
        days: Number of days to analyze (default 30).

    Returns Pearson correlation coefficient and plain-language interpretation.
    """
    if metric_a not in VALID_METRICS:
        return f"Invalid metric_a: '{metric_a}'. Valid options: {', '.join(VALID_METRICS)}"
    if metric_b not in VALID_METRICS:
        return f"Invalid metric_b: '{metric_b}'. Valid options: {', '.join(VALID_METRICS)}"

    start = get_date_ago(days)
    end = get_today()

    data_a = await _get_metric_data(metric_a, start, end)
    data_b = await _get_metric_data(metric_b, start, end)

    # Align by day
    common_days = sorted(set(data_a.keys()) & set(data_b.keys()))
    if len(common_days) < 3:
        return f"Insufficient overlapping data ({len(common_days)} days). Need at least 3."

    x = [data_a[d] for d in common_days]
    y = [data_b[d] for d in common_days]

    r = _pearson(x, y)
    interpretation = _interpret_r(r)

    lines = [
        f"Correlation: {metric_a} vs {metric_b}",
        f"Period: {start} to {end} ({len(common_days)} days with data)",
        "",
        f"Pearson r: {r:.3f}" if r is not None else "Pearson r: N/A",
        f"Interpretation: {interpretation}",
        "",
        f"{metric_a}: avg={mean(x):.1f}, min={min(x):.1f}, max={max(x):.1f}",
        f"{metric_b}: avg={mean(y):.1f}, min={min(y):.1f}, max={max(y):.1f}",
    ]

    return "\n".join(lines)


@mcp.tool()
async def oura_sleep_activity_correlation(days: int = 30) -> str:
    """Analyze how physical activity affects next-night sleep quality.

    Args:
        days: Number of days to analyze (default 30).

    Compares daily activity metrics (steps, active calories) against the
    following night's sleep score, efficiency, and deep sleep duration.
    """
    start = get_date_ago(days)
    end = get_today()

    activity_data = await get_daily_activity(start, end)
    sleep_data = await get_daily_sleep(start, end)
    sleep_period_data = await get_sleep_periods(start, end)

    act_items = activity_data.get("data", []) if isinstance(activity_data, dict) and not activity_data.get("error") else []
    slp_items = sleep_data.get("data", []) if isinstance(sleep_data, dict) and not sleep_data.get("error") else []
    period_items = sleep_period_data.get("data", []) if isinstance(sleep_period_data, dict) and not sleep_period_data.get("error") else []

    # Build lookup dicts
    activity_by_day = {d["day"]: d for d in act_items}
    sleep_by_day = {d["day"]: d for d in slp_items}
    deep_by_day = {}
    for p in period_items:
        if p.get("type") == "long_sleep" and p.get("deep_sleep_duration") is not None:
            deep_by_day[p["day"]] = p["deep_sleep_duration"] / 60

    # Pair activity day N with sleep day N+1
    from datetime import datetime, timedelta

    pairs_steps = []
    pairs_cals = []
    pairs_deep = []

    for act_day, act in activity_by_day.items():
        next_day = (datetime.strptime(act_day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        if next_day in sleep_by_day and act.get("steps") and sleep_by_day[next_day].get("score"):
            pairs_steps.append((act["steps"], sleep_by_day[next_day]["score"]))
        if next_day in sleep_by_day and act.get("active_calories") and sleep_by_day[next_day].get("score"):
            pairs_cals.append((act["active_calories"], sleep_by_day[next_day]["score"]))
        if next_day in deep_by_day and act.get("steps"):
            pairs_deep.append((act["steps"], deep_by_day[next_day]))

    lines = [
        f"Sleep-Activity Correlation — Last {days} Days",
        "",
        "How does today's activity affect tonight's sleep?",
        "",
    ]

    if len(pairs_steps) >= 3:
        x, y = zip(*pairs_steps)
        r = _pearson(list(x), list(y))
        lines.append(f"Steps → Sleep Score (next night):")
        lines.append(f"  Pearson r: {r:.3f}" if r is not None else "  Pearson r: N/A")
        lines.append(f"  {_interpret_r(r)}")
        lines.append(f"  Data points: {len(pairs_steps)}")
    else:
        lines.append("Steps → Sleep Score: insufficient data")

    lines.append("")

    if len(pairs_cals) >= 3:
        x, y = zip(*pairs_cals)
        r = _pearson(list(x), list(y))
        lines.append(f"Active Calories → Sleep Score (next night):")
        lines.append(f"  Pearson r: {r:.3f}" if r is not None else "  Pearson r: N/A")
        lines.append(f"  {_interpret_r(r)}")
    else:
        lines.append("Active Calories → Sleep Score: insufficient data")

    lines.append("")

    if len(pairs_deep) >= 3:
        x, y = zip(*pairs_deep)
        r = _pearson(list(x), list(y))
        lines.append(f"Steps → Deep Sleep Duration (next night):")
        lines.append(f"  Pearson r: {r:.3f}" if r is not None else "  Pearson r: N/A")
        lines.append(f"  {_interpret_r(r)}")
    else:
        lines.append("Steps → Deep Sleep Duration: insufficient data")

    return "\n".join(lines)


@mcp.tool()
async def oura_hrv_analysis(days: int = 30) -> str:
    """Analyze HRV trend with baseline, anomaly detection, and recovery trajectory.

    Args:
        days: Number of days to analyze (default 30).

    Returns rolling 7-day average, standard deviation, anomaly flagging,
    and recovery trajectory assessment.
    """
    start = get_date_ago(days)
    end = get_today()
    data = await get_sleep_periods(start, end)

    items = data.get("data", []) if isinstance(data, dict) and not data.get("error") else []
    if not items:
        return f"No HRV data found for the last {days} days."

    # Extract HRV from long_sleep periods
    hrv_data: list[tuple[str, int]] = []
    for p in items:
        if p.get("type") == "long_sleep" and p.get("average_hrv") is not None:
            hrv_data.append((p["day"], p["average_hrv"]))

    if len(hrv_data) < 3:
        return f"Insufficient HRV data ({len(hrv_data)} nights). Need at least 3."

    hrv_data.sort(key=lambda x: x[0])
    days_list = [d[0] for d in hrv_data]
    vals = [d[1] for d in hrv_data]

    avg_hrv = mean(vals)
    std_hrv = stdev(vals) if len(vals) >= 2 else 0

    # Rolling 7-day average
    rolling: list[tuple[str, float]] = []
    for i in range(len(vals)):
        window = vals[max(0, i - 6):i + 1]
        rolling.append((days_list[i], mean(window)))

    # Anomaly detection (>1.5 std from baseline)
    anomalies = []
    for day, val in hrv_data:
        if std_hrv > 0 and abs(val - avg_hrv) > 1.5 * std_hrv:
            direction = "high" if val > avg_hrv else "low"
            anomalies.append((day, val, direction))

    # Trend (last 7 vs first 7)
    if len(vals) >= 14:
        first_week = mean(vals[:7])
        last_week = mean(vals[-7:])
        trend_diff = last_week - first_week
        trend = "improving" if trend_diff > 2 else "declining" if trend_diff < -2 else "stable"
    elif len(vals) >= 4:
        mid = len(vals) // 2
        first = mean(vals[:mid])
        second = mean(vals[mid:])
        trend_diff = second - first
        trend = "improving" if trend_diff > 2 else "declining" if trend_diff < -2 else "stable"
    else:
        trend = "insufficient data"
        trend_diff = 0

    lines = [
        f"HRV Analysis — Last {days} Days ({len(hrv_data)} nights)",
        "",
        "Baseline:",
        f"  Average HRV: {avg_hrv:.0f} ms",
        f"  Std Dev: {std_hrv:.1f} ms",
        f"  Min: {min(vals)} ms",
        f"  Max: {max(vals)} ms",
        "",
        f"Trend: {trend} ({trend_diff:+.1f} ms)",
        f"  Current (last 3 nights): {mean(vals[-3:]):.0f} ms",
        "",
    ]

    if anomalies:
        lines.append(f"Anomalies ({len(anomalies)}):")
        for day, val, direction in anomalies:
            lines.append(f"  {day}: {val} ms (unusually {direction})")
        lines.append("")

    lines.append("Rolling 7-Day Average:")
    for day, avg in rolling:
        lines.append(f"  {day}: {avg:.0f} ms")

    return "\n".join(lines)


@mcp.tool()
async def oura_weekly_report(weeks: int = 4) -> str:
    """Generate comprehensive weekly digest with week-over-week comparison.

    Args:
        weeks: Number of weeks to include (default 4).

    Returns avg sleep score, avg readiness, total steps, avg resting HR,
    HRV trend, best/worst days, and week-over-week comparison.
    """
    days = weeks * 7
    start = get_date_ago(days)
    end = get_today()

    sleep_data = await get_daily_sleep(start, end)
    activity_data = await get_daily_activity(start, end)
    readiness_data = await get_daily_readiness(start, end)
    sleep_period_data = await get_sleep_periods(start, end)

    slp_items = sleep_data.get("data", []) if isinstance(sleep_data, dict) and not sleep_data.get("error") else []
    act_items = activity_data.get("data", []) if isinstance(activity_data, dict) and not activity_data.get("error") else []
    rdy_items = readiness_data.get("data", []) if isinstance(readiness_data, dict) and not readiness_data.get("error") else []
    period_items = sleep_period_data.get("data", []) if isinstance(sleep_period_data, dict) and not sleep_period_data.get("error") else []

    # Build lookup dicts
    sleep_by_day = {d["day"]: d for d in slp_items}
    activity_by_day = {d["day"]: d for d in act_items}
    readiness_by_day = {d["day"]: d for d in rdy_items}
    hrv_by_day = {}
    hr_by_day = {}
    for p in period_items:
        if p.get("type") == "long_sleep":
            if p.get("average_hrv") is not None:
                hrv_by_day[p["day"]] = p["average_hrv"]
            if p.get("lowest_heart_rate") is not None:
                hr_by_day[p["day"]] = p["lowest_heart_rate"]

    # Group by ISO week
    from datetime import datetime
    week_data: dict[str, dict[str, list]] = {}

    all_days = sorted(set(
        list(sleep_by_day.keys()) + list(activity_by_day.keys()) + list(readiness_by_day.keys())
    ))

    for day in all_days:
        dt = datetime.strptime(day, "%Y-%m-%d")
        iso = dt.isocalendar()
        week_key = f"{iso[0]}-W{iso[1]:02d}"
        if week_key not in week_data:
            week_data[week_key] = {
                "sleep_scores": [], "readiness_scores": [],
                "steps": [], "hrv": [], "resting_hr": [], "days": [],
            }
        wd = week_data[week_key]
        wd["days"].append(day)
        if day in sleep_by_day and sleep_by_day[day].get("score"):
            wd["sleep_scores"].append(sleep_by_day[day]["score"])
        if day in readiness_by_day and readiness_by_day[day].get("score"):
            wd["readiness_scores"].append(readiness_by_day[day]["score"])
        if day in activity_by_day and activity_by_day[day].get("steps"):
            wd["steps"].append(activity_by_day[day]["steps"])
        if day in hrv_by_day:
            wd["hrv"].append(hrv_by_day[day])
        if day in hr_by_day:
            wd["resting_hr"].append(hr_by_day[day])

    lines = [
        f"Weekly Report — Last {weeks} Weeks",
        "",
    ]

    sorted_weeks = sorted(week_data.keys())
    prev_week = None

    for wk in sorted_weeks:
        wd = week_data[wk]
        lines.append(f"{'='*40}")
        lines.append(f"Week {wk} ({wd['days'][0]} to {wd['days'][-1]})")
        lines.append(f"{'='*40}")

        if wd["sleep_scores"]:
            avg_sleep = mean(wd["sleep_scores"])
            lines.append(f"  Sleep Score: {avg_sleep:.0f}/100")
        if wd["readiness_scores"]:
            avg_rdy = mean(wd["readiness_scores"])
            lines.append(f"  Readiness Score: {avg_rdy:.0f}/100")
        if wd["steps"]:
            total_steps = sum(wd["steps"])
            avg_steps = mean(wd["steps"])
            lines.append(f"  Total Steps: {format_steps(total_steps)}")
            lines.append(f"  Avg Steps/Day: {format_steps(int(avg_steps))}")
        if wd["hrv"]:
            lines.append(f"  Avg HRV: {mean(wd['hrv']):.0f} ms")
        if wd["resting_hr"]:
            lines.append(f"  Avg Resting HR: {format_hr(mean(wd['resting_hr']))}")

        # Week-over-week comparison
        if prev_week is not None:
            pw = week_data[prev_week]
            diffs = []
            if wd["sleep_scores"] and pw["sleep_scores"]:
                d = mean(wd["sleep_scores"]) - mean(pw["sleep_scores"])
                diffs.append(f"Sleep {d:+.0f}")
            if wd["steps"] and pw["steps"]:
                d = ((mean(wd["steps"]) - mean(pw["steps"])) / mean(pw["steps"]) * 100) if mean(pw["steps"]) else 0
                diffs.append(f"Steps {d:+.0f}%")
            if wd["hrv"] and pw["hrv"]:
                d = mean(wd["hrv"]) - mean(pw["hrv"])
                diffs.append(f"HRV {d:+.1f}ms")
            if diffs:
                lines.append(f"  vs Last Week: {', '.join(diffs)}")

        prev_week = wk
        lines.append("")

    return "\n".join(lines)
