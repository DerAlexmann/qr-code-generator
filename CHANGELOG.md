# Änderungsprotokoll

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern folgen der [Semantischen Versionierung](https://semver.org/lang/de/).

## [Unveröffentlicht]

<!-- Neue Einträge hier sammeln, bis die nächste Version getaggt wird. -->

## [1.1] – 2026-09-04

Erste öffentliche Veröffentlichung. Version 1.0 blieb eine interne Vorstufe
ohne Farbschemata, Sprachumschaltung und Reiter.

### Hinzugefügt

- **QR-Codes aus beliebigem Text** – Adressen, Texte, Kontaktdaten, WLAN-Zugänge
- **Zehn Ausgabeformate** – PNG, SVG, JPEG, WEBP, TIFF, BMP, GIF, ICO, PDF und EPS
- **Freie Größenwahl** von 32 bis 10000 Pixel; gezeichnet wird mit ganzzahliger
  Modulgröße und ohne Weichzeichnen skaliert, damit die Modulkanten hart bleiben
- **Live-Vorschau**, die sich nach jeder Änderung selbst aktualisiert
- **Fehlerkorrektur L/M/Q/H**, einstellbarer Rand, Auflösung, Farben und Transparenz
- **Kontrastwarnung** in der Statuszeile bei schwer lesbaren Farbkombinationen
- **Stapelverarbeitung** – jede Zeile wird ein eigener Code, in der Oberfläche
  wie auf der Kommandozeile
- **Kommandozeile** mit Inhalt aus Argument, Datei oder Standardeingabe
- **Drei Reiter** – QR-Code, Erklärungen sowie Info & Copyright
- **Farbschemata hell und dunkel** und **Sprachumschaltung Deutsch/Englisch**,
  beides aus der Bild-Toolbox übernommen und in `qr-code-generator.json`
  neben dem Programm gespeichert
- **QR-Code-Generator.pyw** als Startdatei für den Doppelklick ohne Konsolenfenster

### Behoben

Während der Entwicklung gefundene Fehler, festgehalten, weil sie sich in
ähnlicher Form leicht wiederholen:

- Zu lange Inhalte lösten einen ungefangenen `ValueError` aus der automatischen
  Versionssuche aus statt einer verständlichen Meldung
- Dateinamen wie `mailto_info_example.org` galten wegen des Punktes als bereits
  vollständig und blieben ohne Dateiendung
- Die Vorschaufläche gab ihre Größe in Zeichen statt in Pixeln an, solange kein
  Bild gesetzt war – beim Start mit leerem Eingabefeld wurde das Fenster dadurch
  unbedienbar groß
- Das Fenster wurde über die virtuelle Breite aller Bildschirme zentriert und
  landete bei mehreren Monitoren auf der Naht
- Fehlende Bibliotheken meldete das Programm nur auf der Konsole, die beim
  Doppelklick sofort wieder verschwand
- Als gebündelte EXE hätten die Einstellungen im temporären Entpackordner
  gelegen, den PyInstaller beim Beenden löscht

### Geändert

- Der Wechsel des Farbschemas färbt die vorhandenen Bedienelemente um, statt die
  Oberfläche neu aufzubauen; die Vorschau wird bei gleicher Größe in das
  vorhandene Bild kopiert, wodurch das Blinken beim Farbwechsel entfällt

---

Licensed under MIT License
Copyright 2026 Alexander Unverhau
Created with assistance of Claude AI
