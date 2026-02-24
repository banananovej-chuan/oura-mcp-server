"""Body data models (SpO2, Resilience)."""

from dataclasses import dataclass
from typing import Any

from oura_mcp_server.utils.formatting import format_percentage


@dataclass
class SpO2:
    """Blood oxygen data from /daily_spo2."""

    day: str
    spo2_percentage: dict[str, float | None] | None
    breathing_disturbance_index: float | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "SpO2":
        return cls(
            day=data.get("day", ""),
            spo2_percentage=data.get("spo2_percentage") or {},
            breathing_disturbance_index=data.get("breathing_disturbance_index"),
        )

    def format(self) -> str:
        lines = [f"SpO2 — {self.day}"]
        if self.spo2_percentage:
            avg = self.spo2_percentage.get("average")
            if avg is not None:
                lines.append(f"  Average: {format_percentage(avg)}")
        else:
            lines.append("  SpO2: N/A")
        if self.breathing_disturbance_index is not None:
            lines.append(f"  Breathing Disturbance Index: {self.breathing_disturbance_index}")
        return "\n".join(lines)


@dataclass
class Resilience:
    """Stress resilience data from /daily_resilience."""

    day: str
    level: str | None
    contributors: dict[str, Any]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Resilience":
        return cls(
            day=data.get("day", ""),
            level=data.get("level"),
            contributors=data.get("contributors", {}),
        )

    def format(self) -> str:
        lines = [
            f"Resilience — {self.day}",
            f"  Level: {self.level or 'N/A'}",
        ]
        if self.contributors:
            lines.append("  Contributors:")
            for key, val in self.contributors.items():
                if val is not None:
                    lines.append(f"    {key.replace('_', ' ').title()}: {val}")
        return "\n".join(lines)
