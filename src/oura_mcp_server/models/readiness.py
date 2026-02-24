"""Readiness data models."""

from dataclasses import dataclass
from typing import Any

from oura_mcp_server.utils.formatting import format_score


@dataclass
class ReadinessSummary:
    """Daily readiness summary from /daily_readiness."""

    day: str
    score: int | None
    temperature_deviation: float | None
    temperature_trend_deviation: float | None
    contributors: dict[str, Any]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "ReadinessSummary":
        return cls(
            day=data.get("day", ""),
            score=data.get("score"),
            temperature_deviation=data.get("temperature_deviation"),
            temperature_trend_deviation=data.get("temperature_trend_deviation"),
            contributors=data.get("contributors", {}),
        )

    def format(self) -> str:
        lines = [
            f"Readiness Summary — {self.day}",
            f"  Score: {format_score(self.score)}",
        ]
        if self.temperature_deviation is not None:
            lines.append(f"  Temperature Deviation: {self.temperature_deviation:+.1f}°C")
        if self.contributors:
            lines.append("")
            lines.append("  Contributors:")
            for key, val in self.contributors.items():
                if val is not None:
                    lines.append(f"    {key.replace('_', ' ').title()}: {val}")
        return "\n".join(lines)
