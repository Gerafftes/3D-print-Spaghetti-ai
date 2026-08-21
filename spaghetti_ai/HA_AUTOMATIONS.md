# Home-Assistant-Aktivierung (Vorlage)

Vor dem Aktivieren produktiver Automationen muss ein vollständiges Home-Assistant-Backup erstellt und verifiziert werden. Die Automationen sollten bis nach zwei vollständigen Shadow-Drucken und einem kontrollierten Pause-/Fortsetzen-Test ausgeschaltet bleiben.

Eine kopierbare, absichtlich deaktivierte Alarmvorlage liegt in [`HA_AUTOMATIONS.yaml.example`](HA_AUTOMATIONS.yaml.example). Die Datei mit `.example`-Endung wird von Home Assistant nicht geladen.

- `automation.spaghetti_ai_alarm_aufs_iphone`: `off`
- `automation.spaghetti_ai_entscheidung_vom_iphone`: `off`

## Alarm

- Trigger: MQTT `spaghetti_ai/alert`
- Ziel: `notify.mobile_app_<your_device>`
- Bild: `/local/spaghetti-ai/<event-id>.jpg` (annotierte Kopie mit rotem Rahmen um erkannte Bereiche)
- Aktionen: `SPAGHETTI_PAUSE`, `SPAGHETTI_CONTINUE`
- Fester Notification-Tag verhindert doppelte Meldungen.

## Weiterdrucken

- Trigger: Event `mobile_app_notification_action`, Aktion `SPAGHETTI_CONTINUE`
- MQTT-Payload `continue` an `spaghetti_ai/decision`
- Der Dienst unterdrückt neue Alarme für 15 Minuten.

## Pausieren

- Trigger: Event `mobile_app_notification_action`, Aktion `SPAGHETTI_PAUSE`
- Voraussetzung: `button.<your_printer_pause_entity>` ist verfügbar.
- Aktion: `button.press` ausschließlich auf diese Entität.
- Bei nicht verfügbarer Steuerung folgt eine Fehlermeldung; es gibt keinen Rohbefehls-Fallback.
- Erst nach einem erfolgreichen kurzen Testdruck wird diese Automation eingeschaltet.

## Fortsetzen

- Trigger: Event `mobile_app_notification_action`, Aktion `SPAGHETTI_RESUME`
- Voraussetzung: `button.<your_printer_continue_entity>` ist verfügbar.
- Aktion: `button.press` ausschließlich auf diese Entität.
- Die Automation bleibt bis zum kontrollierten Pause-/Fortsetzen-Test ausgeschaltet.
