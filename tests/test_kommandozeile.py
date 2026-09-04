"""Kommandozeile: Argumente, Rueckgabewerte und die erzeugten Dateien."""

import locale
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "qr_generator.py"
ZEICHENSATZ = locale.getpreferredencoding(False)


def aufrufen(*argumente):
    """Ruft das Skript als eigenen Prozess auf - so, wie ein Anwender es tut.

    Die Ausgabe wird als Bytes eingesammelt und erst hier dekodiert. Python
    schreibt auf der Konsole in deren Zeichensatz, unter Windows also meist
    cp1252 oder cp850 und nicht UTF-8; ein festes encoding= liesse den Test an
    den Umlauten scheitern statt an der Sache. Die Zusicherungen unten pruefen
    deshalb nur Zeichenfolgen, die in jedem Zeichensatz gleich aussehen.
    """
    ergebnis = subprocess.run([sys.executable, str(SCRIPT), *argumente],
                              capture_output=True)
    ergebnis.stdout = ergebnis.stdout.decode(ZEICHENSATZ, errors="replace")
    ergebnis.stderr = ergebnis.stderr.decode(ZEICHENSATZ, errors="replace")
    return ergebnis


def test_version(qr):
    ergebnis = aufrufen("--version")
    assert ergebnis.returncode == 0
    assert qr.VERSION in ergebnis.stdout


def test_hilfe_nennt_alle_formate(qr):
    ergebnis = aufrufen("--help")
    assert ergebnis.returncode == 0
    for name in qr.FORMATE:
        assert name in ergebnis.stdout


def test_formatuebersicht(qr):
    ergebnis = aufrufen("--formate")
    assert ergebnis.returncode == 0
    for name in qr.FORMATE:
        assert name in ergebnis.stdout
    for kuerzel in qr.FEHLERKORREKTUR:
        assert kuerzel in ergebnis.stdout


def test_ohne_inhalt_schlaegt_fehl(qr):
    ergebnis = aufrufen("")
    assert ergebnis.returncode == 2
    assert ergebnis.stderr.strip()


def test_datei_wird_geschrieben(qr, tmp_path):
    ziel = tmp_path / "code.png"
    ergebnis = aufrufen("https://example.org", "-o", str(ziel))
    assert ergebnis.returncode == 0
    assert ziel.is_file() and ziel.stat().st_size > 100


def test_format_aus_der_endung(qr, tmp_path):
    ziel = tmp_path / "code.svg"
    assert aufrufen("Endungstest", "-o", str(ziel)).returncode == 0
    assert ziel.read_text(encoding="utf-8").lstrip().startswith("<?xml")


def test_still_gibt_nichts_aus(qr, tmp_path):
    ergebnis = aufrufen("Leise", "-a", str(tmp_path), "-q")
    assert ergebnis.returncode == 0
    assert ergebnis.stdout == ""


def test_vorhandene_datei_wird_nummeriert(qr, tmp_path):
    ziel = tmp_path / "code.png"
    assert aufrufen("Erster", "-o", str(ziel)).returncode == 0
    assert aufrufen("Zweiter", "-o", str(ziel)).returncode == 0
    assert (tmp_path / "code_2.png").is_file()


def test_ueberschreiben(qr, tmp_path):
    ziel = tmp_path / "code.png"
    assert aufrufen("Erster", "-o", str(ziel)).returncode == 0
    assert aufrufen("Zweiter", "-o", str(ziel), "--ueberschreiben").returncode == 0
    assert not (tmp_path / "code_2.png").exists()


def test_stapelverarbeitung(qr, tmp_path):
    liste = tmp_path / "liste.txt"
    liste.write_text("https://example.org | webseite\n"
                     "mailto:info@example.org\n"
                     "Dritter Eintrag\n", encoding="utf-8")
    ausgabe = tmp_path / "aus"

    ergebnis = aufrufen("--stapel", str(liste), "-a", str(ausgabe), "-f", "SVG")
    assert ergebnis.returncode == 0
    dateien = sorted(p.name for p in ausgabe.iterdir())
    assert len(dateien) == 3
    assert all(name.endswith(".svg") for name in dateien), dateien
    assert "webseite.svg" in dateien


def test_inhalt_aus_datei(qr, tmp_path):
    quelle = tmp_path / "inhalt.txt"
    quelle.write_text("Inhalt aus einer Datei", encoding="utf-8")
    ziel = tmp_path / "code.png"
    assert aufrufen("--datei", str(quelle), "-o", str(ziel)).returncode == 0
    assert ziel.is_file()


def test_ico_hinweis_bei_zu_grosser_angabe(qr, tmp_path):
    ergebnis = aufrufen("Zu gross", "-f", "ICO", "-s", "1024", "-a", str(tmp_path))
    assert ergebnis.returncode == 0
    assert "256" in ergebnis.stdout


@pytest.mark.parametrize("sprache", ["de", "en"])
def test_sprache_der_ausgabe(qr, tmp_path, sprache):
    ergebnis = aufrufen("Sprachtest", "-a", str(tmp_path), "--sprache", sprache)
    assert ergebnis.returncode == 0
    erwartet = "Gespeichert" if sprache == "de" else "Saved"
    assert erwartet in ergebnis.stdout


def test_unbekanntes_format_wird_abgelehnt(qr, tmp_path):
    ergebnis = aufrufen("Test", "-f", "GIBTSNICHT", "-a", str(tmp_path))
    assert ergebnis.returncode != 0
