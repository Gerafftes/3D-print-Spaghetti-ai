from datetime import datetime, timedelta, timezone
import os
import tempfile
import unittest
from pathlib import Path

from spaghetti_ai.storage import EventStorage


class EventStorageTest(unittest.TestCase):
    def test_alert_is_saved_and_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = EventStorage(root / "data", root / "public", retention_days=7)

            paths = storage.save_alert(
                "event-1",
                original=b"original",
                annotated=b"annotated",
                metadata={"event_id": "event-1"},
            )

            self.assertEqual(paths["original"].read_bytes(), b"original")
            self.assertEqual(paths["public"].read_bytes(), b"annotated")
            self.assertEqual(storage.latest_alert(), paths["annotated"])

    def test_old_alerts_are_pruned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = EventStorage(root / "data", root / "public", retention_days=7)
            paths = storage.save_alert(
                "old-event",
                original=b"original",
                annotated=b"annotated",
                metadata={},
            )
            old = datetime.now(timezone.utc) - timedelta(days=8)
            os.utime(paths["annotated"].parent, (old.timestamp(), old.timestamp()))

            self.assertEqual(storage.prune(datetime.now(timezone.utc)), 1)
            self.assertFalse(paths["public"].exists())
