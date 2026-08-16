from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    snapshot_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_base_topic: str
    model_path: Path
    data_dir: Path
    public_dir: Path
    poll_interval_seconds: float
    overloaded_interval_seconds: float
    request_timeout_seconds: float
    model_threshold: float
    aggregate_threshold: float
    positives_required: int
    window_size: int
    snooze_seconds: int
    retention_days: int
    max_input_pixels: int
    roi: tuple[float, float, float, float]
    shadow_mode: bool
    web_port: int

    @classmethod
    def from_environment(cls) -> "Settings":
        roi_values = tuple(float(value) for value in os.getenv("ROI", "0,0,1,1").split(","))
        if len(roi_values) != 4 or any(value < 0 or value > 1 for value in roi_values):
            raise ValueError("ROI must contain four normalized values between 0 and 1")
        if roi_values[0] >= roi_values[2] or roi_values[1] >= roi_values[3]:
            raise ValueError("ROI must be x1,y1,x2,y2 with positive width and height")

        return cls(
            snapshot_url=os.getenv(
                "SNAPSHOT_URL",
                "http://192.168.178.130:8080/?action=snapshot",
            ),
            mqtt_host=os.getenv("MQTT_HOST", "core-mosquitto"),
            mqtt_port=_int("MQTT_PORT", 1883),
            mqtt_username=os.getenv("MQTT_USERNAME") or None,
            mqtt_password=os.getenv("MQTT_PASSWORD") or None,
            mqtt_base_topic=os.getenv("MQTT_BASE_TOPIC", "spaghetti_ai").rstrip("/"),
            model_path=Path(os.getenv("MODEL_PATH", "/app/model/model-weights.onnx")),
            data_dir=Path(os.getenv("DATA_DIR", "/data/spaghetti-ai")),
            public_dir=Path(os.getenv("PUBLIC_DIR", "/homeassistant/www/spaghetti-ai")),
            poll_interval_seconds=_float("POLL_INTERVAL_SECONDS", 5),
            overloaded_interval_seconds=_float("OVERLOADED_INTERVAL_SECONDS", 10),
            request_timeout_seconds=_float("REQUEST_TIMEOUT_SECONDS", 4),
            model_threshold=_float("MODEL_THRESHOLD", 0.25),
            aggregate_threshold=_float("AGGREGATE_THRESHOLD", 0.65),
            positives_required=_int("POSITIVES_REQUIRED", 3),
            window_size=_int("WINDOW_SIZE", 5),
            snooze_seconds=_int("SNOOZE_SECONDS", 900),
            retention_days=_int("RETENTION_DAYS", 7),
            max_input_pixels=_int("MAX_INPUT_PIXELS", 320),
            roi=roi_values,
            shadow_mode=_bool("SHADOW_MODE", True),
            web_port=_int("WEB_PORT", 8099),
        )
