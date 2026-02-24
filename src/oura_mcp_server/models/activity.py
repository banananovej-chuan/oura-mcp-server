"""Activity data models."""

from dataclasses import dataclass
from typing import Any

from oura_mcp_server.utils.formatting import (
    format_duration,
    format_score,
    format_steps,
    format_calories,
)


@dataclass
class ActivitySummary:
    """Daily activity summary from /daily_activity."""

    day: str
    score: int | None
    active_calories: int | None
    total_calories: int | None
    steps: int | None
    equivalent_walking_distance: int | None
    high_activity_time: int | None
    medium_activity_time: int | None
    low_activity_time: int | None
    sedentary_time: int | None
    resting_time: int | None
    non_wear_time: int | None
    contributors: dict[str, Any]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "ActivitySummary":
        return cls(
            day=data.get("day", ""),
            score=data.get("score"),
            active_calories=data.get("active_calories"),
            total_calories=data.get("total_calories"),
            steps=data.get("steps"),
            equivalent_walking_distance=data.get("equivalent_walking_distance"),
            high_activity_time=data.get("high_activity_time"),
            medium_activity_time=data.get("medium_activity_time"),
            low_activity_time=data.get("low_activity_time"),
            sedentary_time=data.get("sedentary_time"),
            resting_time=data.get("resting_time"),
            non_wear_time=data.get("non_wear_time"),
            contributors=data.get("contributors", {}),
        )

    def format(self) -> str:
        lines = [
            f"Activity Summary — {self.day}",
            f"  Score: {format_score(self.score)}",
            f"  Steps: {format_steps(self.steps)}",
            f"  Active Calories: {format_calories(self.active_calories)}",
            f"  Total Calories: {format_calories(self.total_calories)}",
        ]
        if self.equivalent_walking_distance:
            km = self.equivalent_walking_distance / 1000
            lines.append(f"  Walking Distance: {km:.1f} km")
        lines.append("")
        lines.append("  Activity Time:")
        lines.append(f"    High:     {format_duration(self.high_activity_time)}")
        lines.append(f"    Medium:   {format_duration(self.medium_activity_time)}")
        lines.append(f"    Low:      {format_duration(self.low_activity_time)}")
        lines.append(f"    Sedentary: {format_duration(self.sedentary_time)}")
        if self.contributors:
            lines.append("")
            lines.append("  Contributors:")
            for key, val in self.contributors.items():
                if val is not None:
                    lines.append(f"    {key.replace('_', ' ').title()}: {val}")
        return "\n".join(lines)


@dataclass
class Workout:
    """Workout session from /workout."""

    id: str
    day: str
    activity: str
    start_datetime: str | None
    end_datetime: str | None
    duration: float | None  # seconds
    calories: float | None
    distance: float | None  # meters
    intensity: str | None
    label: str | None
    source: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Workout":
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            activity=data.get("activity", "unknown"),
            start_datetime=data.get("start_datetime"),
            end_datetime=data.get("end_datetime"),
            duration=data.get("duration"),
            calories=data.get("calories"),
            distance=data.get("distance"),
            intensity=data.get("intensity"),
            label=data.get("label"),
            source=data.get("source"),
        )

    def format(self) -> str:
        lines = [
            f"Workout — {self.day}: {self.activity}",
        ]
        if self.label:
            lines.append(f"  Label: {self.label}")
        if self.start_datetime and self.end_datetime:
            start = self.start_datetime[11:16] if len(self.start_datetime) > 16 else self.start_datetime
            end = self.end_datetime[11:16] if len(self.end_datetime) > 16 else self.end_datetime
            lines.append(f"  Time: {start} → {end}")
        lines.append(f"  Duration: {format_duration(self.duration)}")
        if self.calories:
            lines.append(f"  Calories: {format_calories(self.calories)}")
        if self.distance:
            km = self.distance / 1000
            lines.append(f"  Distance: {km:.2f} km")
        if self.intensity:
            lines.append(f"  Intensity: {self.intensity}")
        if self.source:
            lines.append(f"  Source: {self.source}")
        return "\n".join(lines)
