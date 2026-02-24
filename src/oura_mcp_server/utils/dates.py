"""Date utilities for Oura MCP server."""

from datetime import datetime, timedelta


def get_date_ago(days: int) -> str:
    """Get date string N days ago in YYYY-MM-DD format."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def get_date_ahead(days: int) -> str:
    """Get date string N days from now in YYYY-MM-DD format."""
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def get_today() -> str:
    """Get today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def parse_date_range(
    start_date: str | None,
    end_date: str | None,
    default_days_back: int = 30,
) -> tuple[str, str]:
    """Resolve date range with defaults."""
    if not start_date:
        start_date = get_date_ago(default_days_back)
    if not end_date:
        end_date = get_today()
    return start_date, end_date


def validate_date(date_str: str) -> str:
    """Validate YYYY-MM-DD format. Raises ValueError if invalid."""
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def days_between(start: str, end: str) -> int:
    """Number of days between two YYYY-MM-DD dates."""
    d1 = datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.strptime(end, "%Y-%m-%d")
    return abs((d2 - d1).days)
