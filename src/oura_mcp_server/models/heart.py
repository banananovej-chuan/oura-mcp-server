"""Heart rate data models."""

from dataclasses import dataclass
from typing import Any

from oura_mcp_server.utils.formatting import format_hr


@dataclass
class HeartRateData:
    """Heart rate data point from /heartrate."""

    bpm: int
    source: str
    timestamp: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "HeartRateData":
        return cls(
            bpm=data.get("bpm", 0),
            source=data.get("source", "unknown"),
            timestamp=data.get("timestamp", ""),
        )

    def format(self) -> str:
        time_str = self.timestamp[11:16] if len(self.timestamp) > 16 else self.timestamp
        return f"  {time_str}: {format_hr(self.bpm)} ({self.source})"
