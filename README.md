# 3D Print Spaghetti AI

Lokale, CPU-basierte Spaghetti-Erkennung für den FlashForge Guider 2S. Der Dienst liest ausschließlich Einzelbilder der Kamera, wertet sie mit dem Obico-Fehlererkennungsmodell aus und meldet bestätigte Ereignisse über MQTT an Home Assistant.

## Sicherheitsmodell

- `SHADOW_MODE=true` ist der Standard. Treffer werden gespeichert und unter `spaghetti_ai/shadow_alert` protokolliert, aber nicht an die Benachrichtigungsautomation übergeben.
- Der Erkennungsdienst enthält keinerlei FlashForge-Steuerprotokoll und kann den Drucker nicht selbst anhalten.
- Erst Home Assistant darf nach einer expliziten Handy-Aktion den vorhandenen Pause-Button betätigen.
- Die Abort-Entität und rohe Druckerbefehle werden nicht verwendet.

## Erkennung

- Snapshot: `http://192.168.178.130:8080/?action=snapshot`
- Abfrageintervall: 5 Sekunden; bei langsamer Inferenz automatisch 10 Sekunden.
- Modelleingabe: maximal 320 Pixel an der längsten Kante, optionaler normalisierter ROI.
- Alarm: mindestens 3 positive Bilder im Fenster der letzten 5 und mittlere positive Konfidenz mindestens 0,65.
- Zustände: `normal`, `suspect`, `alerted`, `snoozed`.
- Aufbewahrung: Original, Annotation und JSON-Metadaten für 7 Tage.
- ONNX Runtime nutzt genau einen CPU-Thread und keine CPU-Memory-Arena. Der lokale ARM64-Smoke-Test lag bei rund 0,29 Sekunden je Bild und etwa 405 MiB Maximalbelegung; auf dem Raspberry Pi wird dies vor Produktionsfreigabe erneut gemessen.

## HTTP und MQTT

HTTP auf Port 8099:

- `/health`
- `/status`
- `/latest.jpg`
- `/alerts/latest.jpg`

MQTT:

- `spaghetti_ai/alert` – bestätigter Produktionsalarm
- `spaghetti_ai/shadow_alert` – bestätigter Shadow-Alarm
- `spaghetti_ai/decision` – `continue` oder `pause`
- `spaghetti_ai/status/*` – Onlinezustand, Status und Score

## Installation in Home Assistant

Das Repository kann unter **Einstellungen → Apps → App-Store → Repositories** hinzugefügt werden:

```text
https://github.com/Gerafftes/3d-print-spaghetti-ai
```

Danach erscheint **3D Print Spaghetti AI** im App-Store. Die erste Installation startet immer im Shadow-Modus und kann den Drucker nicht steuern.

## Lokale Entwicklung

```sh
cd spaghetti_ai
python3.11 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
python -m unittest discover -s tests -v
```

Der Container lädt das fest benannte Obico-Modell beim Build und verifiziert SHA-256 `0a6ebd8e30dbf6a450c50f9c0a5406f04ba7eb1c99fd5996e888c78bb383b9aa`.

## Home-Assistant-App

Der Unterordner `spaghetti_ai/` enthält die Home-Assistant-App und startet absichtlich mit `shadow_mode: true`. Danach folgen zwei vollständige normale Shadow-Drucke, bevor Benachrichtigungen oder Druckersteuerung aktiviert werden.

Die App bindet Home Assistants Konfigurationsordner gemäß aktueller App-Spezifikation unter `/homeassistant` ein und schreibt ausschließlich Alarmbilder nach `/homeassistant/www/spaghetti-ai`.

MQTT-Zugangsdaten werden standardmäßig über Home Assistants Supervisor-Service-Discovery bezogen. Manuelle Zugangsdaten in den App-Optionen überschreiben diese Erkennung nur, wenn ausdrücklich ein Benutzername eingetragen ist.

## Herkunft und Lizenz

Das Modellformat und die CPU-Nachverarbeitung basieren auf Obicos `ml_api` in Revision `49c0bc7001a3fd8d56297fc3032ba287bfe1d50b`:

- https://github.com/TheSpaghettiDetective/obico-server/tree/49c0bc7001a3fd8d56297fc3032ba287bfe1d50b/ml_api
- Modell: `model-weights-5a6b1be1fa.onnx`

Dieses Projekt steht deshalb unter **GNU Affero General Public License v3.0 only**. Siehe `LICENSE`.
