from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from uuid import uuid4

import cv2
import numpy as np

from .camera import SnapshotClient
from .config import Settings
from .detector import Detection, ObicoOnnxDetector
from .mqtt_client import MqttBridge
from .state_machine import DetectionStateMachine
from .storage import EventStorage
from .web import start_web_server


LOGGER = logging.getLogger(__name__)


def annotate_alert_image(
    image: np.ndarray,
    detections: list[Detection],
    roi_offset: tuple[int, int],
    roi_scale: float,
) -> np.ndarray:
    """Draw readable red boxes for detector coordinates on the camera image."""
    if roi_scale <= 0:
        raise ValueError("roi_scale must be positive")

    image_height, image_width = image.shape[:2]
    if image_height == 0 or image_width == 0:
        raise ValueError("image must not be empty")

    annotated = image.copy()
    left, top = roi_offset
    for detection in detections:
        x1 = int(round(left + detection.x1 / roi_scale))
        y1 = int(round(top + detection.y1 / roi_scale))
        x2 = int(round(left + detection.x2 / roi_scale))
        y2 = int(round(top + detection.y2 / roi_scale))
        x1, x2 = sorted(
            (max(0, min(x1, image_width - 1)), max(0, min(x2, image_width - 1)))
        )
        y1, y2 = sorted(
            (max(0, min(y1, image_height - 1)), max(0, min(y2, image_height - 1)))
        )

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 4)
        label = f"Spaghetti {detection.confidence:.0%}"
        (label_width, label_height), baseline = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            2,
        )
        label_bottom = min(image_height - 1, max(y1, label_height + baseline + 6))
        label_top = max(0, label_bottom - label_height - baseline - 6)
        label_right = min(image_width - 1, x1 + label_width + 8)
        cv2.rectangle(
            annotated,
            (x1, label_top),
            (label_right, label_bottom),
            (0, 0, 255),
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (
                min(image_width - 1, x1 + 4),
                max(label_height, label_bottom - baseline - 3),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return annotated


class SpaghettiService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage = EventStorage(settings.data_dir, settings.public_dir, settings.retention_days)
        self.state_machine = DetectionStateMachine(
            window_size=settings.window_size,
            positives_required=settings.positives_required,
            aggregate_threshold=settings.aggregate_threshold,
            snooze_seconds=settings.snooze_seconds,
        )
        self.detector = ObicoOnnxDetector(settings.model_path, settings.model_threshold)
        self.camera = SnapshotClient(settings.snapshot_url, settings.request_timeout_seconds)
        self.mqtt = MqttBridge(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_username,
            password=settings.mqtt_password,
            base_topic=settings.mqtt_base_topic,
            on_decision=self._handle_decision,
        )
        self.last_score = 0.0
        self.last_error: str | None = None
        self.last_frame_at: str | None = None

    def run(self) -> None:
        self.mqtt.start()
        server = start_web_server(
            self.settings.web_port,
            latest_path=self.settings.data_dir / "latest.jpg",
            latest_alert=self.storage.latest_alert,
            status=self.status,
        )
        self.storage.prune()
        try:
            while True:
                started = time.monotonic()
                try:
                    self._process_frame()
                    self.last_error = None
                except Exception as error:
                    self.last_error = str(error)
                    LOGGER.exception("Frame processing failed")
                elapsed = time.monotonic() - started
                interval = (
                    self.settings.overloaded_interval_seconds
                    if elapsed > self.settings.poll_interval_seconds * 0.5
                    else self.settings.poll_interval_seconds
                )
                time.sleep(max(0.1, interval - elapsed))
        finally:
            server.shutdown()
            self.mqtt.stop()

    def status(self) -> dict:
        return {
            "state": self.state_machine.state.value,
            "score": round(self.last_score, 4),
            "shadow_mode": self.settings.shadow_mode,
            "last_frame_at": self.last_frame_at,
            "last_error": self.last_error,
        }

    def _process_frame(self) -> None:
        raw = self.camera.fetch()
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Camera returned an invalid JPEG")
        self.storage.save_latest(raw)

        roi_image, roi_offset, roi_scale = self._prepare_roi(image)
        detections = self.detector.detect(roi_image)
        score = max((detection.confidence for detection in detections), default=0.0)
        self.last_score = score
        self.last_frame_at = datetime.now(timezone.utc).isoformat()
        transition = self.state_machine.process(score)
        self._publish_status(transition.state.value, score, transition.positive_count > 0)

        if transition.should_alert:
            self._store_and_publish_alert(
                image=image,
                raw=raw,
                detections=detections,
                roi_offset=roi_offset,
                roi_scale=roi_scale,
                aggregate_confidence=transition.aggregate_confidence,
            )

    def _prepare_roi(self, image):
        height, width = image.shape[:2]
        x1, y1, x2, y2 = self.settings.roi
        left, top = int(x1 * width), int(y1 * height)
        right, bottom = int(x2 * width), int(y2 * height)
        roi = image[top:bottom, left:right]
        scale = min(1.0, self.settings.max_input_pixels / max(roi.shape[:2]))
        if scale < 1.0:
            roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return roi, (left, top), scale

    def _store_and_publish_alert(
        self,
        *,
        image,
        raw: bytes,
        detections: list[Detection],
        roi_offset: tuple[int, int],
        roi_scale: float,
        aggregate_confidence: float,
    ) -> None:
        now = datetime.now(timezone.utc)
        event_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        annotated = annotate_alert_image(image, detections, roi_offset, roi_scale)
        success, encoded = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
        if not success:
            raise ValueError("Failed to encode annotated alert image")
        metadata = {
            "event_id": event_id,
            "created_at": now.isoformat(),
            "aggregate_confidence": round(aggregate_confidence, 4),
            "maximum_confidence": round(self.last_score, 4),
            "shadow_mode": self.settings.shadow_mode,
            "detections": [detection.__dict__ for detection in detections],
        }
        self.storage.save_alert(
            event_id,
            original=raw,
            annotated=encoded.tobytes(),
            metadata=metadata,
        )
        self.storage.prune()
        payload = {
            **metadata,
            "image": f"/local/spaghetti-ai/{event_id}.jpg",
        }
        if self.settings.shadow_mode:
            self.mqtt.publish("shadow_alert", payload)
        else:
            self.mqtt.publish("alert", payload)

    def _publish_status(self, state: str, score: float, suspect: bool) -> None:
        self.mqtt.publish("status/state", state, retain=True)
        self.mqtt.publish("status/score", f"{score * 100:.1f}", retain=True)
        self.mqtt.publish("status/suspect", "ON" if suspect else "OFF", retain=True)

    def _handle_decision(self, decision: str) -> None:
        if decision == "continue":
            self.state_machine.continue_printing()
        elif decision == "pause":
            self.state_machine.acknowledge_pause()
        self.mqtt.publish("decision_ack", {"decision": decision, "accepted": True})
