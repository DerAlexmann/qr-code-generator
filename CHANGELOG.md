# Änderungsprotokoll

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern folgen der [Semantischen Versionierung](https://semver.org/lang/de/).

## [Unveröffentlicht]

<!-- Neue Einträge hier sammeln, bis die nächste Version getaggt wird. -->

## [1.1.4] – 2026-09-12

### Behoben

- **Beim Sprachwechsel blitzt das Fenster nicht mehr auf.** Der Neuaufbau
  setzte jedes Mal erneut, ob das Fenster in der Größe veränderbar ist. Unter
  Windows legt Tk dafür das äußere Fenster neu an – auch dann, wenn sich an der
  Einstellung nichts ändert. Das Fenster verschwand dadurch kurz und kam mit der
  Öffnen-Animation von Windows wieder. Die Einstellung wird jetzt nur noch
  gesetzt, wenn sie sich tatsächlich ändert. Beim Sprachwechsel ändert sich
  damit nur noch die Breite, weil die Beschriftungen je nach Sprache
  unterschiedlich viel Platz brauchen.

## [1.1.3] – 2026-09-12

### Behoben

- **Das Fenster springt beim Start nicht mehr über den Bildschirm.** Beim
  Aufbau misst die Oberfläche die Größe ihrer Elemente mit
  `update_idletasks()`. Dabei zeigte Windows das Fenster bereits an seiner
  Standardposition an, und erst danach wurde es in die Mitte gesetzt. Jetzt
  bleibt es verborgen, bis es fertig aufgebaut und platziert ist, und erscheint
  gleich an der richtigen Stelle.
- **Nach einem Sprachwechsel bleibt das Fenster, wo es ist.** Der Neuaufbau
  benutzte dieselbe Einpassung wie der Start und setzte ein beiseitegeschobenes
  Fenster zurück in die Mitte. Jetzt behält es seine Position. Nur wenn es mit
  der neuen Größe über den Bildschirmrand ragen würde, rückt es gerade so weit
  herein; die Titelleiste bleibt dabei immer erreichbar.

### Geändert

- **Das Fenster öffnet sich auf dem Monitor, auf dem der Mauszeiger steht.**
  Bisher entschied darüber, wo Windows das noch unfertige Fenster abgelegt
  hatte. Ein verborgenes Fenster liegt aber noch auf keinem Monitor, deshalb
  zählt jetzt die Stelle, an der doppelgeklickt wurde. Beim Sprachwechsel
  zählt der Monitor, auf dem das Fenster gerade liegt. Mit nur einem
  Bildschirm ändert sich nichts.

## [1.1.2] – 2026-09-05

### Behoben

- **Absturz beim Einschalten des Stapelmodus mit leerem Eingabefeld.** Die
  Vorschau griff auf die erste Zeile zu, ohne zu prüfen, ob es überhaupt eine
  gibt: `_zeilen_holen()` lässt Leerzeilen weg und liefert bei leerem Feld oder
  reinem Leerraum eine leere Liste. Das Ergebnis war ein `IndexError` im
  Tkinter-Rückruf. Betroffen war jeder Weg dorthin – Häkchen bei leerem Feld
  setzen, den Text bei gesetztem Häkchen löschen oder nur Leerzeilen eingeben.
  Die Vorschau bleibt in diesen Fällen jetzt einfach leer.

## [1.1.1] – 2026-09-04

### Geändert

- **Unmögliche Einstellungen sind in der Oberfläche nicht mehr wählbar**, statt
  hinterher korrigiert zu werden. Bei Formaten ohne Transparenz ist das
  Häkchen ausgegraut; der zuletzt geäußerte Wunsch bleibt gemerkt und kehrt
  zurück, sobald wieder ein Format mit Transparenz gewählt ist. Die
  Größenauswahl endet beim Maximum des Formats – bei ICO also bei 256 Pixeln –,
  ein bereits eingetragener größerer Wert wird beim Formatwechsel
  heruntergesetzt. Von Hand eingetippte Werte für Größe, Rand und Auflösung
  werden beim Verlassen des Feldes in den erlaubten Bereich geholt, nicht
  schon während des Tippens.

### Behoben

- Die Oberfläche wies nicht darauf hin, wenn eine Einstellung angepasst werden
  musste – etwa ICO auf 256 Pixel begrenzt oder Transparenz bei GIF und JPEG
  weggelassen. Die Ausgabedatei war korrekt, aber die Statuszeile schwieg dazu,
  obwohl README und der Reiter „Erklärungen" genau diesen Hinweis versprachen.
  Die Beschreibung der Anpassungen steht jetzt in `anpassungen_beschreiben()`
  und wird von der Oberfläche **und** der Kommandozeile gleichlautend benutzt.
  Sie bleibt als Auffangnetz für die Kommandozeile und für den Moment zwischen
  Tippen und Feldwechsel.

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
