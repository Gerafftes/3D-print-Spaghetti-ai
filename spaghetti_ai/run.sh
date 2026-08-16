#!/bin/sh
set -eu

options=/data/options.json
export SNAPSHOT_URL="$(jq -r '.snapshot_url' "$options")"
configured_mqtt_username="$(jq -r '.mqtt_username // empty' "$options")"
if [ -z "$configured_mqtt_username" ] && [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    mqtt_service="$(curl --fail --silent --show-error \
        --header "Authorization: Bearer $SUPERVISOR_TOKEN" \
        http://supervisor/services/mqtt)"
    export MQTT_HOST="$(printf '%s' "$mqtt_service" | jq -r '.data.host')"
    export MQTT_PORT="$(printf '%s' "$mqtt_service" | jq -r '.data.port')"
    export MQTT_USERNAME="$(printf '%s' "$mqtt_service" | jq -r '.data.username')"
    export MQTT_PASSWORD="$(printf '%s' "$mqtt_service" | jq -r '.data.password')"
else
    export MQTT_HOST="$(jq -r '.mqtt_host' "$options")"
    export MQTT_PORT="$(jq -r '.mqtt_port' "$options")"
    export MQTT_USERNAME="$configured_mqtt_username"
    export MQTT_PASSWORD="$(jq -r '.mqtt_password // empty' "$options")"
fi
export ROI="$(jq -r '.roi' "$options")"
export POLL_INTERVAL_SECONDS="$(jq -r '.poll_interval_seconds' "$options")"
export AGGREGATE_THRESHOLD="$(jq -r '.aggregate_threshold' "$options")"
export SHADOW_MODE="$(jq -r '.shadow_mode' "$options")"
export PUBLIC_DIR=/homeassistant/www/spaghetti-ai
export DATA_DIR=/data/spaghetti-ai

exec spaghetti-ai
