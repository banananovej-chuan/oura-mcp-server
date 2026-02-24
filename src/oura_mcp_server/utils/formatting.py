"""Oura-specific formatting utilities."""


def format_duration(seconds: int | float | None) -> str:
    """Format seconds into human-readable duration (e.g. '7h 32m')."""
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def format_score(score: int | float | None, label: str = "") -> str:
    """Format a score with optional label."""
    if score is None:
        return f"{label}: N/A" if label else "N/A"
    val = f"{int(score)}/100"
    return f"{label}: {val}" if label else val


def format_hr(bpm: int | float | None) -> str:
    """Format heart rate value."""
    if bpm is None:
        return "N/A"
    return f"{int(bpm)} bpm"


def format_percentage(value: float | None) -> str:
    """Format a percentage value."""
    if value is None:
        return "N/A"
    return f"{value:.0f}%"


def format_steps(steps: int | None) -> str:
    """Format step count with comma separator."""
    if steps is None:
        return "N/A"
    return f"{steps:,}"


def format_calories(cal: int | float | None) -> str:
    """Format calorie count."""
    if cal is None:
        return "N/A"
    return f"{int(cal)} kcal"
