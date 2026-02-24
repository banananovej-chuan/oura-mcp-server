"""Sleep data models."""

from dataclasses import dataclass
from typing import Any

from oura_mcp_server.utils.formatting import format_duration, format_score, format_hr


@dataclass
class SleepSummary:
    """Daily sleep summary from /daily_sleep."""

    day: str
    score: int | None
    timestamp: str | None
    contributors: dict[str, Any]
    # Durations in seconds
    total_sleep_duration: int | None
    deep_sleep_duration: int | None
    rem_sleep_duration: int | None
    light_sleep_duration: int | None
    awake_time: int | None
    efficiency: int | None
    restfulness: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "SleepSummary":
        contributors = data.get("contributors", {})
        return cls(
            day=data.get("day", ""),
            score=data.get("score"),
            timestamp=data.get("timestamp"),
            contributors=contributors,
            total_sleep_duration=contributors.get("total_sleep"),
            deep_sleep_duration=contributors.get("deep_sleep"),
            rem_sleep_duration=contributors.get("rem_sleep"),
            light_sleep_duration=None,
            awake_time=None,
            efficiency=contributors.get("efficiency"),
            restfulness=contributors.get("restfulness"),
        )

    def format(self) -> str:
        lines = [
            f"Sleep Summary — {self.day}",
            f"  Score: {format_score(self.score)}",
        ]
        if self.contributors:
            lines.append("  Contributors:")
            for key, val in self.contributors.items():
                if val is not None:
                    lines.append(f"    {key.replace('_', ' ').title()}: {val}")
        return "\n".join(lines)


@dataclass
class SleepPeriod:
    """Individual sleep period from /sleep."""

    id: str
    day: str
    bedtime_start: str | None
    bedtime_end: str | None
    type: str  # "long_sleep", "late_nap", etc.
    total_sleep_duration: int | None
    deep_sleep_duration: int | None
    rem_sleep_duration: int | None
    light_sleep_duration: int | None
    awake_time: int | None
    efficiency: int | None
    average_heart_rate: float | None
    lowest_heart_rate: int | None
    average_hrv: int | None
    latency: int | None
    sleep_phase_5_min: str | None  # encoded sleep stages
    heart_rate: dict | None
    hrv: dict | None
    readiness_score_delta: float | None
    time_in_bed: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "SleepPeriod":
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            bedtime_start=data.get("bedtime_start"),
            bedtime_end=data.get("bedtime_end"),
            type=data.get("type", "unknown"),
            total_sleep_duration=data.get("total_sleep_duration"),
            deep_sleep_duration=data.get("deep_sleep_duration"),
            rem_sleep_duration=data.get("rem_sleep_duration"),
            light_sleep_duration=data.get("light_sleep_duration"),
            awake_time=data.get("awake_time"),
            efficiency=data.get("efficiency"),
            average_heart_rate=data.get("average_heart_rate"),
            lowest_heart_rate=data.get("lowest_heart_rate"),
            average_hrv=data.get("average_hrv"),
            latency=data.get("latency"),
            sleep_phase_5_min=data.get("sleep_phase_5_min"),
            heart_rate=data.get("heart_rate"),
            hrv=data.get("hrv"),
            readiness_score_delta=data.get("readiness_score_delta"),
            time_in_bed=data.get("time_in_bed"),
        )

    def format(self) -> str:
        lines = [
            f"Sleep Period — {self.day} ({self.type})",
        ]
        if self.bedtime_start and self.bedtime_end:
            start = self.bedtime_start[11:16] if len(self.bedtime_start) > 16 else self.bedtime_start
            end = self.bedtime_end[11:16] if len(self.bedtime_end) > 16 else self.bedtime_end
            lines.append(f"  Bedtime: {start} → {end}")
        lines.append(f"  Total Sleep: {format_duration(self.total_sleep_duration)}")
        lines.append(f"  Time in Bed: {format_duration(self.time_in_bed)}")
        lines.append(f"  Efficiency: {self.efficiency}%" if self.efficiency else "  Efficiency: N/A")
        lines.append("")
        lines.append("  Sleep Stages:")
        lines.append(f"    Deep:  {format_duration(self.deep_sleep_duration)}")
        lines.append(f"    REM:   {format_duration(self.rem_sleep_duration)}")
        lines.append(f"    Light: {format_duration(self.light_sleep_duration)}")
        lines.append(f"    Awake: {format_duration(self.awake_time)}")
        lines.append("")
        lines.append("  Heart Rate:")
        lines.append(f"    Average: {format_hr(self.average_heart_rate)}")
        lines.append(f"    Lowest:  {format_hr(self.lowest_heart_rate)}")
        lines.append(f"    Average HRV: {self.average_hrv} ms" if self.average_hrv else "    Average HRV: N/A")
        if self.latency is not None:
            lines.append(f"  Sleep Latency: {format_duration(self.latency)}")
        return "\n".join(lines)
