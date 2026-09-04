# Sicherheitsrichtlinie

## Unterstützte Versionen

| Version | Unterstützt |
|---|---|
| 1.1.x   | ✅ |
| < 1.1   | ❌ |

Es wird immer nur die jeweils aktuelle Version gepflegt.

## Eine Sicherheitslücke melden

Bitte melden Sie Sicherheitslücken **nicht** als öffentliches Issue.

Nutzen Sie stattdessen die private Meldefunktion von GitHub:

**[Report a vulnerability](https://github.com/DerAlexmann/qr-code-generator/security/advisories/new)**
(im Repository unter *Security → Advisories*)

Der Bericht ist dabei nur für Sie und die Projektverantwortlichen sichtbar. Die
Behebung kann im selben Advisory besprochen werden, ohne dass die Lücke vorher
öffentlich wird. Einen weiteren Meldeweg gibt es bewusst nicht – so bleibt alles
an einer Stelle und nachvollziehbar.

Hilfreich für die Meldung:

- Beschreibung der Lücke und der möglichen Auswirkung
- Schritte zum Nachstellen, gern mit einer Beispieldatei
- Betriebssystem und Python-Version, bei der EXE deren Version
- Falls vorhanden: ein Vorschlag zur Behebung

**Was Sie erwarten können:** eine Eingangsbestätigung innerhalb von 7 Tagen und
eine erste Einschätzung innerhalb von 30 Tagen. Nach der Behebung wird die Lücke
öffentlich gemacht; auf Wunsch mit Nennung der meldenden Person.

Dies ist ein Freizeitprojekt ohne Bug-Bounty-Programm.

## Womit das Programm umgeht – Einschätzung des Risikos

Der QR-Code-Generator läuft vollständig lokal. Er stellt **keine
Netzwerkverbindung** her, sendet keine Telemetrie und lädt nichts nach. Er
*liest* auch keine QR-Codes – er erzeugt sie nur. Trotzdem lohnt ein Blick auf
die Stellen, an denen Daten von außen verarbeitet werden:

| Bereich | Hinweis |
|---|---|
| **Inhalt des QR-Codes** | Wird als Text kodiert und niemals ausgeführt oder aufgelöst. Das Programm ruft insbesondere keine eingegebene Adresse ab. |
| **Was im Code landet** | Ein QR-Code ist keine Verschlüsselung. Jeder, der ihn scannt, liest den Inhalt im Klartext – WLAN-Passwörter oder Zugangsdaten sind darin also für jeden sichtbar, der den Code sieht. |
| **Textdateien** | `--datei` und `--stapel` lesen reinen Text (UTF-8). Es wird nichts interpretiert oder ausgeführt. |
| **Dateinamen aus Inhalten** | Ohne `-o` entsteht der Dateiname aus dem Inhalt. Er wird dabei auf harmlose Zeichen beschränkt, Pfadwechsel (`..`, `/`, `\`) werden entfernt und unter Windows gesperrte Namen wie `CON` entschärft. Geschrieben wird nur in den angegebenen Zielordner. |
| **Überschreiben** | Vorhandene Dateien werden nicht überschrieben, sondern durchnummeriert. Nur `--ueberschreiben` hebt das auf. Eine Löschfunktion gibt es nicht. |
| **Bildausgabe** | Erfolgt über Pillow. Sicherheitslücken in Bildbibliotheken sind ein bekanntes Thema – halten Sie `Pillow` aktuell. |
| **Konfigurationsdatei** | `qr-code-generator.json` enthält nur Sprache und Farbschema, keine persönlichen Daten und keine Inhalte. |
| **Gebündelte EXE** | Enthält `qrcode`, `Pillow` und Tcl/Tk in der beim Bauen aktuellen Fassung. Sicherheitsaktualisierungen dieser Bibliotheken erreichen die EXE erst mit einer neuen Veröffentlichung; wer das eng verfolgen möchte, führt das Skript besser mit einem selbst gepflegten Python aus. |

## Abhängigkeiten aktuell halten

```bash
pip install --upgrade -r requirements.txt
```

Im Repository hält [Dependabot](.github/dependabot.yml) die Abhängigkeiten und
die Versionen der GitHub-Actions monatlich nach.
