"""Heart rate tools."""

from oura_mcp_server.api.client import get_heart_rate
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.models.heart import HeartRateData
from oura_mcp_server.utils.dates import parse_date_range, get_today
from oura_mcp_server.utils.formatting import format_hr


@mcp.tool()
async def oura_get_heart_rate(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get heart rate data with 5-minute interval readings.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to today.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns heart rate readings with timestamps and source (rest/sleep/workout).
    Includes summary statistics (min, max, average, resting).
    """
    if not start_date:
        start_date = get_today()
    if not end_date:
        end_date = start_date
    result = await get_heart_rate(start_date, end_date)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No heart rate data found for {start_date} to {end_date}."

    readings = [HeartRateData.from_api(d) for d in items]

    # Summary stats
    bpms = [r.bpm for r in readings]
    avg_hr = sum(bpms) / len(bpms)
    min_hr = min(bpms)
    max_hr = max(bpms)

    # Resting HR (from "rest" source readings)
    rest_bpms = [r.bpm for r in readings if r.source in ("rest", "sleep")]
    resting_hr = sum(rest_bpms) / len(rest_bpms) if rest_bpms else None

    lines = [
        f"Heart Rate ({start_date} to {end_date}) — {len(readings)} readings",
        "",
        "Summary:",
        f"  Average: {format_hr(avg_hr)}",
        f"  Min: {format_hr(min_hr)}",
        f"  Max: {format_hr(max_hr)}",
        f"  Resting: {format_hr(resting_hr)}",
        "",
        f"Readings ({len(readings)} data points):",
    ]

    # Show a sample of readings (every Nth to keep output manageable)
    if len(readings) > 50:
        step = len(readings) // 25
        lines.append(f"  (showing every {step}th reading)")
        for i in range(0, len(readings), step):
            lines.append(readings[i].format())
    else:
        for r in readings:
            lines.append(r.format())

    return "\n".join(lines)
