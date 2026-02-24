"""Tags tools."""

from oura_mcp_server.api.client import get_tags
from oura_mcp_server.mcp_instance import mcp
from oura_mcp_server.utils.dates import parse_date_range


@mcp.tool()
async def oura_get_tags(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get user-created tags including mood, symptoms, and notes.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.

    Returns all tags with timestamps and associated data.
    """
    start, end = parse_date_range(start_date, end_date, default_days_back=30)
    result = await get_tags(start, end)

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return f"No tags found for {start} to {end}."

    lines = [f"Tags ({start} to {end}) — {len(items)} tag(s)", ""]
    for tag in items:
        day = tag.get("day", "")
        tag_text = tag.get("tag_type_code", tag.get("text", "unknown"))
        timestamp = tag.get("timestamp", "")
        time_str = timestamp[11:16] if len(timestamp) > 16 else ""
        comment = tag.get("comment")

        line = f"  {day}"
        if time_str:
            line += f" {time_str}"
        line += f" — {tag_text}"
        if comment:
            line += f" ({comment})"
        lines.append(line)
    return "\n".join(lines)
