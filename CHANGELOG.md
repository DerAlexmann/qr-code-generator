# Änderungsprotokoll

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern folgen der [Semantischen Versionierung](https://semver.org/lang/de/).

## [Unveröffentlicht]

<!-- Neue Einträge hier sammeln, bis die nächste Version getaggt wird. -->

### Behoben

- **Die erste Zeile von `qr_generator.py` nannte noch 1.1.7.** Die
  Versionsnummer steht dort ein zweites Mal, und beim Sprung auf 1.1.8 blieb
  sie stehen. Nichts liest diesen Dateikopf – Titelleiste, Infoseite,
  `--version` und die Dateieigenschaften der EXE lesen alle `VERSION` –, aber
  im Quellpaket von 1.1.8 steht dadurch eine falsche Angabe. Ein neuer Test in
  `tests/test_verpackung.py` vergleicht beide Stellen; im Release 1.1.8 selbst
  bleiben EXE, Quellpaket und Prüfsummen unberührt.
- **Auch der Kopf dieses Protokolls wird jetzt bewacht.** Die Versionsnummer
  stand an einer dritten Stelle ohne Wächter: Der neueste Abschnitt hier und
  `VERSION` konnten auseinanderlaufen, ohne dass etwas rot wird – dieselbe
  Fehlerklasse wie beim Dateikopf. Ein zweiter Test vergleicht beide.

### Geändert

- **Die fremde Action im Release-Workflow hängt an einem Commit-Hash.** Sie
  war an den Tag `v3` gebunden, und sie läuft in dem einen Job, der
  Schreibrecht auf das Repository hat. Ein Tag ist verschiebbar: Wer das
  Repository der Action übernimmt, könnte `v3` auf eigenen Code zeigen lassen
  und mit diesem Recht laufen. Ein Hash lässt sich nicht verschieben. Die
  Fassung steht als Kommentar dahinter, damit Dependabot sie weiter anhebt;
  die Actions von GitHub selbst bleiben beim Tag. Drei Tests wachen darüber:
  Jeder Verweis in **jeder** Workflow-Datei, der nicht mit `actions/` beginnt,
  muss an einem Hash hängen und seine Fassung im Kommentar nennen; mindestens
  eine fremde Action muss überhaupt gefunden werden; und `dependabot.yml` muss
  die Actions beobachten – ein Hash zieht nicht von allein nach, das ist der
  Preis für seine Festigkeit.

## [1.1.8] – 2026-10-31

Diese Version ändert am Programm selbst nichts. Sie holt nach, was zur
Auslieferung einer unsignierten EXE gehört: nachsehen zu können, was man
heruntergeladen hat, und zu wissen, was darin steckt.

### Hinzugefügt

- **Die EXE trägt ihre Versionsangaben.** Bis 1.1.7 waren Produktname,
  Version und Urheber in den Dateieigenschaften leer – PyInstaller legt ohne
  `--version-file` keine Versionsressource an. Wer die Datei heruntergeladen
  hatte, konnte nicht nachsehen, welche Fassung vor ihm lag. Die Angaben
  entstehen jetzt aus `VERSION` in `qr_generator.py`, derselben Stelle, aus der
  auch Titelleiste und Infoseite lesen; der Workflow liest sie aus der fertigen
  EXE zurück und bricht ab, wenn sie fehlen oder nicht zum Tag passen.
- **Eine Prüfsumme liegt dem Release bei.** `SHA256SUMS.txt` entsteht beim
  Bauen. Wer die unsignierte EXE vor dem ersten Start vergleichen möchte,
  findet den Wert dort statt in den Release-Notizen; beide READMEs nennen den
  Befehl dazu.
- **Lizenzen der Fremdkomponenten.** `DRITTANBIETER-LIZENZEN.md` listet
  zweisprachig auf, was in der EXE steckt – Python, Tcl/Tk, qrcode, Pillow mit
  seinen Bilddecodern, die Teile der Python-Laufzeit und den Bootloader von
  PyInstaller – jeweils mit Lizenz und geprüftem Link. Ausgelesen wurde das aus
  der fertigen EXE, nicht aus den Abhängigkeiten geschätzt. Ergebnis: Es ist
  **kein Bestandteil unter GPL oder LGPL** darin, der auf das Gesamtwerk
  durchschlägt; die EXE bleibt als Ganzes unter der MIT-Lizenz. Die
  vollständigen Lizenztexte hängen als
  `QR-Code-Generator-lizenztexte.zip` am Release – MIT, BSD, die zlib-Lizenz
  und die FreeType-Lizenz verlangen den Text selbst, nicht nur einen Verweis.
  Gesammelt werden sie beim Bauen aus den Paketen, die dafür installiert
  wurden, damit sie zur gebauten EXE passen.
- **Fester Bau.** `requirements-build.txt` nennt genaue Fassungen von
  PyInstaller, qrcode und Pillow. Derselbe Tag soll zweimal dieselbe EXE
  ergeben, und eine fehlerhafte neue Fassung soll kein Release kippen. Offen
  gesagt: Die Pakete, die pip dabei mitzieht, und das Laufzeitabbild von Python
  sind damit nicht festgelegt, und es sind keine Hash-Pins – Bit für Bit
  reproduzierbar ist der Bau also nicht. Ein eigener CI-Job baut in jedem Pull
  Request mit genau diesen Fassungen und schreibt damit eine echte Datei.
- **`tests/test_verpackung.py`** wacht über all das: Lizenztabelle in beiden
  Sprachen samt Lizenzangabe, Prüfsumme und ihr Format, Versionsressource mit
  ihren Werten, feste Fassungen und ihre Untergrenzen, Dependabot, der
  Entwurfsstatus des Releases, die Anhänge und der Hinweis zum ersten Start.
  Jeder dieser Wächter wurde einmal absichtlich rot gesetzt – 84
  Verschlechterungen, einzeln eingebaut und zurückgenommen. Was nicht rot
  wird, ist kein Wächter.

### Geändert

- **Der Release-Workflow lässt sich proben.** Der veröffentlichende Job hängt
  jetzt an einem Tag, die beiden Bau-Jobs nicht. Ein Lauf über
  `workflow_dispatch` baut und prüft damit vollständig durch, statt am
  fehlenden Tag-Namen zu scheitern – bisher war ein Probelauf zwangsläufig rot,
  und ein roter Lauf, der nichts bedeutet, wird irgendwann nicht mehr
  angesehen.
- Die laschen Vorgaben der Actions sind korrigiert: `if-no-files-found: error`
  statt `warn` und `fail_on_unmatched_files: true`. Bisher wäre ein Release
  stillschweigend ohne Prüfsumme oder Lizenzdatei entstanden, ohne dass etwas
  rot wird.
- Schrägstriche im Ref-Namen werden beim Packen ersetzt, damit ein Probelauf
  von einem Zweig wie `dependabot/pip/…` nicht am Pfad scheitert.
- **Der Rauchtest verlangt jetzt eine fertige Datei von der EXE.** Dass das
  Fenster nach zwanzig Sekunden noch steht, beweist wenig: Eine
  `--windowed`-EXE mit einem Fehler beim Start zeigt einen Meldungsdialog und
  läuft dabei weiter. Zusätzlich wird deshalb die Kommandozeile der EXE
  aufgerufen und ein geschriebener PNG-Code verlangt – damit ist belegt, dass
  qrcode, Pillow und die mitgenommenen Paketdaten im gepackten Zustand
  wirklich geladen werden.
- Jeder Anhang wird vor dem Hochladen einzeln verlangt.
  `if-no-files-found: error` schlägt erst an, wenn über alle Muster zusammen
  gar nichts gefunden wird – eine einzelne fehlende Prüfsumme hätte es nicht
  bemerkt.
- Schreibrechte hat nur noch der veröffentlichende Job. Die Bau-Jobs
  installieren Pakete und packen eine EXE; sie brauchen den Token nicht.
- `SHA256SUMS.txt` wird mit Unix-Zeilenende geschrieben. Mit dem
  Windows-Zeilenende las `sha256sum -c` unter Linux den Dateinamen mit einem
  angehängten Wagenrücklauf und fand die EXE nicht; `Get-FileHash` unter
  Windows war davon nicht betroffen.
- Das Quellpaket enthält jetzt auch `requirements-build.txt` und die beiden
  Hilfsskripte des Baus. `DRITTANBIETER-LIZENZEN.md` verweist auf
  `lizenztexte_sammeln.py` – ein Verweis auf eine Datei, die nicht mitkommt,
  ist kein Verweis.

## [1.1.7] – 2026-10-11

### Sicherheit

- **Ein Dateiname in der Stapeldatei kann nicht mehr aus dem Ausgabeordner
  herausschreiben.** Der Name hinter dem `|` wurde bisher ungeprüft übernommen.
  Eine Zeile wie `Inhalt | ..\woanders` schrieb damit neben den gewählten
  Ordner, ein absoluter Pfad hob `--ausgabeordner` ganz aus (`os.path.join`
  behält dann nur den zweiten Teil), und fehlende Verzeichnisse wurden dabei
  sogar angelegt – mit `--ueberschreiben` auch über vorhandene Dateien hinweg.
  Wer eine Stapelliste aus fremder Hand verarbeitet, hat so Dateien an Stellen
  bekommen, die er nicht gewählt hat. Der Name geht jetzt durch denselben
  Säuberer, der auch die aus dem Inhalt abgeleiteten Namen erzeugt und den die
  Oberfläche längst benutzt; aus Trennzeichen werden Unterstriche, von `..`
  bleibt nichts übrig.

### Geändert

- Eigene Dateinamen in der Stapeldatei werden wie abgeleitete Namen
  normalisiert: Leerzeichen und Sonderzeichen werden zu Unterstrichen, die
  Länge ist auf 48 Zeichen begrenzt. Aus `Aushang Eingang` wird damit
  `Aushang_Eingang.png`.

### Hinzugefügt

- **Eigenes Programmsymbol.** Die EXE trug bisher das Standardsymbol von
  PyInstaller und das Fenster die Feder von Tk. Beide zeigen jetzt einen
  stilisierten QR-Code in Weiß auf abgerundetem Akzentblau – dieselbe
  Handschrift wie bei den übrigen Werkzeugen. Gezeichnet wird er von
  `icon_erzeugen.py`; die `.ico` enthält alle Größen von 16 bis 256 Pixel,
  für 16 und 24 Pixel eine gröbere Fassung, weil die Ringe der Eckmarken in
  dieser Größe sonst zulaufen. Fehlt die Datei, startet das Programm
  unverändert – nur eben wieder mit der Feder.

### Entfernt

- Der Hinweis, woran sich Farbschema, Sprachumschaltung und Aufbau orientieren,
  steht nicht mehr im Reiter „Info & Copyright" und auch in keinem Kommentar
  mehr. Woher die Farbauswahl eines Programms stammt, ist für die Benutzung
  ohne Belang.

### Geändert

- Die Bildschirmfotos in beiden READMEs sind neu aufgenommen: mit dem neuen
  Programmsymbol in der Titelleiste und der aktuellen Versionsnummer.

## [1.1.5] – 2026-09-12

### Behoben

- **Der Sprachwechsel baut die Oberfläche nicht mehr neu auf.** Bisher wurde
  sie dafür komplett abgerissen und neu erstellt. Weil Tk jedes Element
  einzeln zeichnet, sah man dabei rund 300 ms lang jeden Zwischenstand: leere
  Flächen, eine schwarze Vorschau, Inhalt in der alten Breite, der sich dann
  auseinanderzog. Jetzt bleiben alle Bedienelemente stehen und nur ihre Texte
  werden ausgetauscht – so wie es der Wechsel des Farbschemas schon tut.
  Solange Texte, Layout und Fensterbreite nachziehen, lässt Windows das alte
  Bild stehen; gezeichnet wird erst, wenn alles fertig ist. Ohne dieses
  Anhalten wären beim Verschieben der längeren Beschriftungen noch kurze
  Doppelbilder zu sehen.
  Eingaben, Einstellungen, der gewählte Reiter und die Bildlaufposition
  bleiben dabei von selbst erhalten. Sichtbar ändert sich nur noch die
  Fensterbreite, weil die Beschriftungen je nach Sprache unterschiedlich viel
  Platz brauchen.

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
  beides in `qr-code-generator.json` neben dem Programm gespeichert
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
