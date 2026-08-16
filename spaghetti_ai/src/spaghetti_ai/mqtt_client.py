from __future__ import annotations

import json
import logging
from typing import Callable

import paho.mqtt.client as mqtt


LOGGER = logging.getLogger(__name__)


class MqttBridge:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        base_topic: str,
        on_decision: Callable[[str], None],
    ) -> None:
        self.base_topic = base_topic
        self._host = host
        self._port = port
        self._on_decision = on_decision
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="spaghetti-ai")
        if username:
            self._client.username_pw_set(username, password)
        self._client.will_set(f"{base_topic}/status/online", "OFF", retain=True)
        self._client.on_connect = self._handle_connect
        self._client.on_message = self._handle_message

    def start(self) -> None:
        self._client.connect_async(self._host, self._port, keepalive=60)
        self._client.loop_start()

    def stop(self) -> None:
        self.publish("status/online", "OFF", retain=True)
        self._client.disconnect()
        self._client.loop_stop()

    def publish(self, suffix: str, payload, *, retain: bool = False) -> None:
        value = payload if isinstance(payload, str) else json.dumps(payload, separators=(",", ":"))
        self._client.publish(f"{self.base_topic}/{suffix}", value, qos=1, retain=retain)

    def publish_discovery(self) -> None:
        device = {
            "identifiers": ["spaghetti_ai_guider_2s"],
            "name": "3D Print Spaghetti AI",
            "manufacturer": "Open source / Obico model",
            "model": "Guider 2S failure detector",
        }
        entities = {
            "binary_sensor/online": {
                "name": "Online",
                "device_class": "connectivity",
                "state_topic": f"{self.base_topic}/status/online",
                "payload_on": "ON",
                "payload_off": "OFF",
            },
            "binary_sensor/suspect": {
                "name": "Spaghetti-Verdacht",
                "device_class": "problem",
                "state_topic": f"{self.base_topic}/status/suspect",
                "payload_on": "ON",
                "payload_off": "OFF",
            },
            "sensor/score": {
                "name": "Spaghetti Score",
                "state_topic": f"{self.base_topic}/status/score",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "sensor/state": {
                "name": "Erkennungszustand",
                "state_topic": f"{self.base_topic}/status/state",
            },
        }
        for object_path, config in entities.items():
            domain, object_id = object_path.split("/")
            payload = {
                **config,
                "unique_id": f"spaghetti_ai_{object_id}",
                "availability_topic": f"{self.base_topic}/status/online",
                "payload_available": "ON",
                "payload_not_available": "OFF",
                "device": device,
            }
            topic = f"homeassistant/{domain}/spaghetti_ai/{object_id}/config"
            self._client.publish(topic, json.dumps(payload), qos=1, retain=True)

    def _handle_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code != 0:
            LOGGER.error("MQTT connection failed: %s", reason_code)
            return
        client.subscribe(f"{self.base_topic}/decision", qos=1)
        self.publish_discovery()
        self.publish("status/online", "ON", retain=True)

    def _handle_message(self, client, userdata, message) -> None:
        try:
            payload = message.payload.decode("utf-8")
            try:
                parsed = json.loads(payload)
                decision = parsed.get("decision", "") if isinstance(parsed, dict) else str(parsed)
            except json.JSONDecodeError:
                decision = payload
            if decision in {"continue", "pause"}:
                self._on_decision(decision)
        except Exception:
            LOGGER.exception("Failed to process MQTT decision")
