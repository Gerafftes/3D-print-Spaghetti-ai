# 3D Print Spaghetti AI

Die App überwacht den Guider 2S ausschließlich über Kamera-Snapshots und meldet bestätigte Druckfehler per MQTT an Home Assistant.

## Sicherer Start

Die Standardoption `shadow_mode: true` bleibt für die ersten zwei vollständigen Testdrucke aktiv. In diesem Modus werden Treffer nur gespeichert und ausgewertet; es gibt keine Benachrichtigung und keine Druckersteuerung.

## Standardwerte

- Snapshot: `http://PRINTER_IP:8080/?action=snapshot`
- Intervall: 5 Sekunden
- Bestätigung: 3 positive Bilder aus den letzten 5
- Mindestwert: 0,65
- Aufbewahrung: 7 Tage

MQTT-Zugangsdaten werden automatisch über Home Assistants Supervisor-Service-Discovery bezogen. Alarmbilder landen unter `/local/spaghetti-ai/` und sind damit über Home Assistant erreichbar.

## Produktionsfreigabe

Erst nach zwei fehlerfreien Shadow-Drucken und einem kontrollierten kurzen Pause-/Fortsetzen-Test darf `shadow_mode` ausgeschaltet werden. Die Abort-Funktion wird nicht verwendet.
