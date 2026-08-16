# Geplante Home-Assistant-Aktivierung

Die Automationen wurden am 13. August 2026 über die Home-Assistant-Config-API angelegt, nicht durch direktes Bearbeiten von YAML-Dateien. Vorher wurde das vollständige Backup `Vor_Spaghetti_AI_2026-08-13` mit ID `201741f6` erstellt und verifiziert. Solange der aktuelle Druck läuft und die FlashForge-Integration `unavailable` ist, bleiben alle produktiven Automationen ausgeschaltet.

- `automation.spaghetti_ai_alarm_aufs_iphone`: `off`, noch nie ausgelöst
- `automation.spaghetti_ai_entscheidung_vom_iphone`: `off`, noch nie ausgelöst

## Alarm

- Trigger: MQTT `spaghetti_ai/alert`
- Ziel: `notify.mobile_app_iphone_von_johann`
- Bild: `/local/spaghetti-ai/<event-id>.jpg`
- Aktionen: `SPAGHETTI_PAUSE`, `SPAGHETTI_CONTINUE`
- Fester Notification-Tag verhindert doppelte Meldungen.

## Weiterdrucken

- Trigger: Event `mobile_app_notification_action`, Aktion `SPAGHETTI_CONTINUE`
- MQTT-Payload `continue` an `spaghetti_ai/decision`
- Der Dienst unterdrückt neue Alarme für 15 Minuten.

## Pausieren

- Trigger: Event `mobile_app_notification_action`, Aktion `SPAGHETTI_PAUSE`
- Voraussetzung: `button.cab_guider_ii_series_pause` ist verfügbar.
- Aktion: `button.press` ausschließlich auf diese Entität.
- Bei nicht verfügbarer Steuerung folgt eine Fehlermeldung; es gibt keinen Rohbefehls-Fallback.
- Erst nach einem erfolgreichen kurzen Testdruck wird diese Automation eingeschaltet.

## Fortsetzen

- Trigger: Event `mobile_app_notification_action`, Aktion `SPAGHETTI_RESUME`
- Voraussetzung: `button.cab_guider_ii_series_continue` ist verfügbar.
- Aktion: `button.press` ausschließlich auf diese Entität.
- Die Automation bleibt bis zum kontrollierten Pause-/Fortsetzen-Test ausgeschaltet.
