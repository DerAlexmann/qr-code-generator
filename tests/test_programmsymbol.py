"""Das Programmsymbol: die .ico selbst und der Weg in die Titelleiste.

Die .ico liegt im Projektordner und wird von icon_erzeugen.py gezeichnet. Sie
steht in .gitignore hinter einer Ausnahme - ohne die waere sie als eine der
vielen Probeausgaben durchgerutscht, die das Programm beim Ausprobieren im
eigenen Ordner hinterlaesst.
"""

import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
GROESSEN = {16, 24, 32, 48, 64, 128, 256}


@pytest.fixture
def symbol(qr):
    pfad = WURZEL / qr.SYMBOLDATEI
    if not pfad.is_file():
        pytest.fail(f"Programmsymbol fehlt: {pfad} - 'python icon_erzeugen.py' erzeugt es neu.")
    return pfad


def test_symbol_enthaelt_alle_groessen(symbol):
    """Vom Reiter der Taskleiste bis zur grossen Kachel im Explorer."""
    pytest.importorskip("PIL.Image")
    from PIL import Image

    with Image.open(symbol) as bild:
        vorhanden = {b for b, _h in bild.ico.sizes()}
    assert vorhanden == GROESSEN, sorted(vorhanden)


def test_symbol_ist_blau_mit_weissem_sinnbild(symbol):
    """Hausfarbe und Sinnbild - nicht nur irgendeine Datei mit der Endung."""
    pytest.importorskip("PIL.Image")
    from PIL import Image

    with Image.open(symbol) as bild:
        bild.size = (256, 256)
        gross = bild.convert("RGBA")

    farben = {farbe for _anzahl, farbe in gross.getcolors(maxcolors=100000)}
    assert (47, 125, 225, 255) in farben, "das Akzentblau fehlt"
    assert (255, 255, 255, 255) in farben, "das weisse Sinnbild fehlt"
    # Die Ecken bleiben frei - die Flaeche ist abgerundet, kein volles Quadrat.
    assert gross.getpixel((0, 0))[3] == 0


def test_fehlendes_symbol_haelt_das_fenster_nicht_auf(qr, monkeypatch, tmp_path):
    """Ohne .ico startet das Programm trotzdem - nur eben mit der Tk-Feder."""
    tk = pytest.importorskip("tkinter")
    qr._tk = tk
    monkeypatch.setattr(qr, "programm_ordner", lambda: str(tmp_path))

    class Attrappe:
        @staticmethod
        def iconbitmap(**_kw):
            raise AssertionError("ohne Datei darf gar nicht erst gesetzt werden")

    qr.fenstersymbol_setzen(Attrappe)


@pytest.mark.skipif(sys.platform != "win32", reason="iconbitmap(default=) ist Windows-Sache")
def test_symbol_wird_gesetzt_wenn_es_daliegt(qr, symbol):
    """Der Normalfall: die .ico liegt neben dem Script und wird genommen."""
    gesetzt = []

    class Attrappe:
        @staticmethod
        def iconbitmap(**kw):
            gesetzt.append(kw.get("default"))

    qr.fenstersymbol_setzen(Attrappe)
    assert gesetzt == [str(symbol)]
