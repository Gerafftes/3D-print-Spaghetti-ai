from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil


class EventStorage:
    def __init__(self, data_dir: Path, public_dir: Path, retention_days: int) -> None:
        self.data_dir = data_dir
        self.public_dir = public_dir
        self.retention = timedelta(days=retention_days)
        self.alerts_dir = data_dir / "alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.public_dir.mkdir(parents=True, exist_ok=True)

    def save_latest(self, jpeg: bytes) -> Path:
        destination = self.data_dir / "latest.jpg"
        self._atomic_write(destination, jpeg)
        return destination

    def save_alert(
        self,
        event_id: str,
        *,
        original: bytes,
        annotated: bytes,
        metadata: dict,
    ) -> dict[str, Path]:
        event_dir = self.alerts_dir / event_id
        event_dir.mkdir(parents=True, exist_ok=False)
        original_path = event_dir / "original.jpg"
        annotated_path = event_dir / "annotated.jpg"
        metadata_path = event_dir / "event.json"
        public_path = self.public_dir / f"{event_id}.jpg"
        self._atomic_write(original_path, original)
        self._atomic_write(annotated_path, annotated)
        self._atomic_write(
            metadata_path,
            json.dumps(metadata, indent=2, sort_keys=True).encode("utf-8"),
        )
        shutil.copyfile(annotated_path, public_path)
        self._atomic_write(self.data_dir / "latest-alert-id", event_id.encode("utf-8"))
        return {
            "original": original_path,
            "annotated": annotated_path,
            "metadata": metadata_path,
            "public": public_path,
        }

    def latest_alert(self) -> Path | None:
        marker = self.data_dir / "latest-alert-id"
        if not marker.exists():
            return None
        candidate = self.alerts_dir / marker.read_text().strip() / "annotated.jpg"
        return candidate if candidate.exists() else None

    def prune(self, now: datetime | None = None) -> int:
        cutoff = (now or datetime.now(timezone.utc)) - self.retention
        removed = 0
        for event_dir in self.alerts_dir.iterdir():
            if not event_dir.is_dir():
                continue
            modified = datetime.fromtimestamp(event_dir.stat().st_mtime, timezone.utc)
            if modified < cutoff:
                shutil.rmtree(event_dir)
                public_file = self.public_dir / f"{event_dir.name}.jpg"
                public_file.unlink(missing_ok=True)
                removed += 1
        return removed

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
