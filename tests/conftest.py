"""Gemeinsame Testvorbereitung.

Das Programm ist eine einzelne Datei neben diesem Ordner. Sie wird hier einmal
pro Testlauf ueber importlib geladen. Beim Import entsteht noch kein Fenster -
tkinter wird erst in gui_starten() geladen. Die Tests laufen deshalb auch auf
einem Rechner ohne Bildschirm.
"""

import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
SCRIPT = WURZEL / "qr_generator.py"


@pytest.fixture(scope="session")
def qr():
    """Der geladene QR-Code-Generator als Modul."""
    assert SCRIPT.is_file(), f"Skript nicht gefunden: {SCRIPT}"

    # Der Loader wird ausdruecklich mitgegeben - dieselbe Vorsichtsmassnahme
    # wie in der Bild-Toolbox. Sie kostet nichts und haelt den Testaufbau
    # unabhaengig davon, welche Endungen Python auf der jeweiligen Plattform
    # als Quelldatei kennt.
    loader = SourceFileLoader("qr_generator", str(SCRIPT))
    spec = importlib.util.spec_from_file_location("qr_generator", SCRIPT, loader=loader)
    assert spec is not None and spec.loader is not None, (
        f"Konnte fuer {SCRIPT} keine Modulspezifikation erzeugen."
    )

    module = importlib.util.module_from_spec(spec)
    sys.modules["qr_generator"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def deutsch(qr):
    """Setzt die Sprache fuer einen Test auf Deutsch und danach zurueck."""
    vorher = qr._.language
    qr._.language = qr.SOURCE_LANGUAGE
    yield
    qr._.language = vorher
