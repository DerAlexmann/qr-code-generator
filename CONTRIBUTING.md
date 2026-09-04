# Mitwirken am QR-Code-Generator

Danke für das Interesse! Fehlerberichte, Übersetzungen, neue Ausgabeformate und
Verbesserungen sind alle willkommen. Beiträge auf Deutsch und Englisch sind
gleichermaßen in Ordnung.

*Contributions in English are equally welcome – just open the issue or pull
request in whichever language you are comfortable with.*

---

## Entwicklungsumgebung einrichten

```bash
git clone https://github.com/DerAlexmann/qr-code-generator.git
cd qr-code-generator
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
```

Programm starten:

```bash
python qr_generator.py
```

---

## Vor jedem Pull Request

```bash
ruff check .            # Linting
python -m pytest        # Tests
```

Beides läuft auch automatisch in der CI (siehe `.github/workflows/ci.yml`) –
lokal geht es nur schneller.

Bitte zusätzlich das Programm starten und den geänderten Bereich einmal von Hand
durchspielen. Die Tests prüfen die Datenstrukturen und die erzeugten Dateien,
nicht die Bedienung.

> [!IMPORTANT]
> Wer an der Erzeugung der Codes etwas ändert, sollte einen fertigen QR-Code
> **tatsächlich mit einem Lesegerät scannen**. Ein Code kann tadellos aussehen
> und trotzdem unlesbar sein; die Tests können das nicht ersetzen.

---

## Aufbau des Projekts

Die Anwendung ist **eine einzige Datei**, `qr_generator.py`. Das ist Absicht:
Herunterladen, starten, fertig – ohne Installation. Bitte diesen Aufbau
beibehalten. Daneben liegt nur `QR-Code-Generator.pyw`, ein kurzer Starter für
den Doppelklick unter Windows.

Grober Aufbau der Datei von oben nach unten:

| Abschnitt | Inhalt |
|---|---|
| Abhängigkeiten | `qrcode` und `Pillow`, jeweils über ein `HAS_...`-Flag |
| `THEMES` | Farbpaletten hell/dunkel, `apply_theme()` |
| Sprachumschaltung | `Translator`, Einstellungen lesen und schreiben |
| Ablageort | `programm_ordner()` – Skript- bzw. EXE-Ordner |
| Format- und Optionstabellen | `FORMATE`, `FEHLERKORREKTUR`, `QROptionen` |
| Prüfung | `optionen_pruefen()`, `kontrast_warnung()` |
| Erzeugung | `matrix_erzeugen()`, `bild_erzeugen()`, `svg_erzeugen()` |
| Speichern | `qr_speichern()`, `endung_ergaenzen()`, `dateiname_vorschlagen()` |
| Kommandozeile | `argumente_parser()`, `cli_main()` |
| Bausteine der Oberfläche | `faerben()`, `FlatButton`, `make_card`, `ScrollBereich` |
| `QRApp` | Hauptfenster mit den drei Reitern |
| `TRANSLATIONS` | Sprachtabelle, ganz am Ende |

### Stil

- Schreibweise wie im Rest der Datei: vier Leerzeichen Einrückung, Zeilen bis
  100 Zeichen, sprechende deutsche Bezeichner.
- Kommentare kommen ohne Umlaute aus, sichtbare Texte benutzen sie normal.
- Neue Abhängigkeiten nur, wenn es gar nicht anders geht.
- Die Kernfunktionen kennen keine Oberfläche: Sie nehmen `QROptionen` entgegen
  und geben Daten zurück. Nur so bleiben Kommandozeile und Fenster gleichwertig.

---

## Ein Ausgabeformat hinzufügen

1. In `FORMATE` einen `Format`-Eintrag anlegen: Endung, Beschreibung und die
   Fähigkeiten (`vektor`, `alpha`, `max_kante`, `pillow_name`).
2. Falls das Format Besonderheiten beim Speichern braucht, `speicherargumente()`
   ergänzen; für Farbmodus und Transparenz ist `bild_fuer_format()` zuständig.
3. Die Beschreibung in `TRANSLATIONS` übersetzen – sie erscheint im Reiter
   „Erklärungen" und bei `--formate`.
4. Einen erzeugten Code mit einem Lesegerät prüfen. Verlustbehaftete Formate
   sind hier heikler als verlustfreie.

Auswahlfeld, Hilfetexte und die Formatübersicht lesen alle aus `FORMATE` und
aktualisieren sich von selbst.

---

## Eine Sprache hinzufügen oder verbessern

Quellsprache ist Deutsch: der deutsche Text im Code **ist** der Schlüssel.

1. Kürzel und Anzeigename in `LANGUAGE_NAMES` eintragen, z. B. `"fr": "Français"`.
2. In `TRANSLATIONS` einen Eintrag `"fr": { ... }` anlegen und übersetzen.

Regeln:

- Nicht übersetzte Zeilen erscheinen automatisch auf Deutsch. Eine
  unvollständige Tabelle ist also unproblematisch – lieber wenige gute
  Übersetzungen als viele maschinelle.
- Platzhalter in geschweiften Klammern – `{pfad}`, `{format}`, `{fehler}` … –
  müssen in der Übersetzung unverändert vorkommen. Ihre Reihenfolge im Satz ist
  frei. `python -m pytest` prüft das.
- Auch die Beschreibungen in `FORMATE` und `FEHLERKORREKTUR` werden zur Laufzeit
  übersetzt, obwohl sie nicht wörtlich in einem `_( ... )` stehen. Der Test
  `test_uebersetzungen.py` sammelt beides ein.

---

## Ein Farbschema hinzufügen

In `THEMES` eine weitere Palette anlegen, die **exakt dieselben** Schlüssel
enthält wie die vorhandenen. `apply_theme()` schreibt die Werte per
`globals().update()` in die Modulvariablen; der übrige Code benutzt einfach
`BG`, `CARD`, `TEXT` … und muss vom Umschalten nichts wissen.

Genau wegen dieses Musters ist die Ruff-Regel `F821` (undefined name) in
`pyproject.toml` abgeschaltet – die Farbnamen entstehen erst zur Laufzeit.

> [!IMPORTANT]
> **Neue Widgets bitte über `faerben( ... )` anlegen.** Die Funktion merkt sich
> zu jedem Widget, welche Rolle seine Farben haben (`bg="CARD"`, `fg="TEXT"` …).
> Ein Wechsel des Farbschemas färbt daraufhin die vorhandenen Bedienelemente um,
> statt das Fenster neu aufzubauen – das war vorher als Zucken sichtbar. Ein
> Widget, das mit fest eingesetzten Farben angelegt wird, bleibt beim Umschalten
> in der alten Farbe stehen.

---

## Commits

Kurze, aussagekräftige Betreffzeile im Imperativ, gern mit Präfix:

```
formate: JPEG-Qualität war nicht einstellbar
i18n: französische Übersetzung ergänzt
docs: Installationshinweis für Linux
```

---

## Eigenständige EXE bauen

`.github/workflows/release.yml` baut bei einem Versions-Tag automatisch eine
Windows-EXE mit PyInstaller. Lokal geht das so:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "QR-Code-Generator" --copy-metadata qrcode qr_generator.py
```

> [!NOTE]
> Im `--onefile`-Modus entpackt PyInstaller das Programm bei jedem Start in
> einen temporären Ordner und löscht ihn beim Beenden wieder. Damit die
> Einstellungen das überleben, fragt `programm_ordner()` `sys.frozen` ab und
> legt `qr-code-generator.json` im gepackten Zustand **neben der EXE** ab statt
> neben `__file__`. Aus demselben Grund beginnt der Speichern-Dialog dort.
> `tests/test_ablageort.py` wacht darüber.

> [!NOTE]
> `--copy-metadata qrcode` nimmt die Paketdaten mit, aus denen der Reiter
> „Info & Copyright" die Versionsnummer liest: `qrcode` führt seit Fassung 8
> kein `__version__` mehr. Ohne den Schalter steht dort „eingebettet" statt der
> Nummer – funktional ändert das nichts. `Pillow` braucht ihn nicht, weil es
> seine Version selbst mitführt.

> [!NOTE]
> `--windowed` unterdrückt das Konsolenfenster hinter der Oberfläche. Die
> Kommandozeile funktioniert in dieser Fassung weiterhin und schreibt auch
> Dateien, nur ihre Meldungen sieht man dann nicht. Wer die EXE vor allem im
> Terminal einsetzt, lässt den Schalter weg.

---

## Verhaltenskodex

Für dieses Projekt gilt der [Verhaltenskodex](CODE_OF_CONDUCT.md).

## Lizenz und Entstehung

Mit einem Beitrag stimmen Sie zu, dass er unter der [MIT-Lizenz](LICENSE)
veröffentlicht wird.

Copyright © 2026 Alexander Unverhau · **Erstellt mit Unterstützung von
Claude AI (Anthropic)**, siehe [NOTICE](NOTICE). Der Hinweis auf die
KI-Unterstützung steht der Transparenz halber überall dort, wo auch der
Copyright-Vermerk steht. Wer den Kopf von `qr_generator.py`, den Reiter
*Info & Copyright* oder die `NOTICE` bearbeitet, sollte ihn deshalb bitte stehen
lassen. Die `LICENSE` bleibt bewusst wortgleich beim MIT-Text, damit GitHub die
Lizenz weiterhin automatisch erkennt.
