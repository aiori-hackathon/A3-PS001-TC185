import unittest
from datetime import datetime, timedelta

from early_warning_detector import ControlledWorkload, EarlyWarningDetector, EventType, FileEvent


class EarlyWarningDetectorTests(unittest.TestCase):
    def _event(self, event_type: EventType, second: int) -> FileEvent:
        base = datetime(2026, 1, 1, 0, 0, 0)
        return FileEvent(
            event_type=event_type,
            file_path="/data/local/tmp/test.txt",
            timestamp=base + timedelta(seconds=second),
        )

    def test_detects_rapid_rewrite_and_rename_and_stops_controlled_workload(self) -> None:
        workload = ControlledWorkload()
        detector = EarlyWarningDetector(workload=workload, window_seconds=10, rewrite_threshold=3, rename_threshold=2)

        events = [
            self._event(EventType.REWRITE, 0),
            self._event(EventType.REWRITE, 2),
            self._event(EventType.RENAME, 3),
            self._event(EventType.REWRITE, 5),
            self._event(EventType.RENAME, 6),
        ]

        alert = detector.process_events(events)

        self.assertIsNotNone(alert)
        assert alert is not None
        self.assertIn("Suspicious rapid file rewrite + rename behavior", alert.message)
        self.assertGreaterEqual(alert.rewrite_events, 3)
        self.assertGreaterEqual(alert.rename_events, 2)
        self.assertTrue(workload.stopped)

    def test_does_not_alert_for_activity_outside_time_window(self) -> None:
        workload = ControlledWorkload()
        detector = EarlyWarningDetector(workload=workload, window_seconds=2, rewrite_threshold=2, rename_threshold=1)

        events = [
            self._event(EventType.REWRITE, 0),
            self._event(EventType.RENAME, 1),
            self._event(EventType.REWRITE, 5),
        ]

        alert = detector.process_events(events)

        self.assertIsNone(alert)
        self.assertFalse(workload.stopped)


if __name__ == "__main__":
    unittest.main()
