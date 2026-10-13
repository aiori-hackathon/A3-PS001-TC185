from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Deque, Iterable, Optional


class EventType(str, Enum):
    REWRITE = "rewrite"
    RENAME = "rename"


@dataclass(frozen=True)
class FileEvent:
    event_type: EventType
    file_path: str
    timestamp: datetime


@dataclass(frozen=True)
class Alert:
    message: str
    rewrite_events: int
    rename_events: int
    window_seconds: int
    triggered_at: datetime


class ControlledWorkload:
    """Represents only the controlled Android test workload."""

    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class EarlyWarningDetector:
    def __init__(
        self,
        workload: ControlledWorkload,
        window_seconds: int = 10,
        rewrite_threshold: int = 3,
        rename_threshold: int = 2,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if rewrite_threshold <= 0:
            raise ValueError("rewrite_threshold must be positive")
        if rename_threshold <= 0:
            raise ValueError("rename_threshold must be positive")

        self.workload = workload
        self.window_seconds = window_seconds
        self.rewrite_threshold = rewrite_threshold
        self.rename_threshold = rename_threshold
        self._events: Deque[FileEvent] = deque()
        self._latest_alert: Optional[Alert] = None

    @property
    def latest_alert(self) -> Optional[Alert]:
        return self._latest_alert

    def process_event(self, event: FileEvent) -> Optional[Alert]:
        self._events.append(event)
        self._trim_old_events(event.timestamp)

        rewrite_count = sum(1 for e in self._events if e.event_type == EventType.REWRITE)
        rename_count = sum(1 for e in self._events if e.event_type == EventType.RENAME)

        if rewrite_count >= self.rewrite_threshold and rename_count >= self.rename_threshold:
            alert = Alert(
                message=(
                    "Suspicious rapid file rewrite + rename behavior detected in controlled "
                    "Android test workload"
                ),
                rewrite_events=rewrite_count,
                rename_events=rename_count,
                window_seconds=self.window_seconds,
                triggered_at=event.timestamp,
            )
            self._latest_alert = alert
            self.workload.stop()
            self._events.clear()
            return alert

        return None

    def process_events(self, events: Iterable[FileEvent]) -> Optional[Alert]:
        for event in events:
            alert = self.process_event(event)
            if alert is not None:
                return alert
        return None

    def _trim_old_events(self, current_time: datetime) -> None:
        cutoff = current_time - timedelta(seconds=self.window_seconds)
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()
