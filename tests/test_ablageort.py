"""Ablageort der Einstellungen - besonders im gepackten Zustand.

Unter PyInstaller mit --onefile entpackt sich das Programm in einen temporaeren
Ordner, den PyInstaller beim Beenden wieder loescht. Wuerden die Einstellungen
dort landen, waeren Sprache und Farbschema nach jedem Start wieder vergessen.
"""

import json
import os
import sys
from pathlib import Path


def test_ohne_buendelung_neben_dem_skript(qr):
    erwartet = Path(qr.__file__).resolve().parent
    assert Path(qr.programm_ordner()).resolve() == erwartet
    assert Path(qr.config_path()).name == qr.CONFIG_NAME


def test_ist_eingefroren_erkennt_den_normalfall(qr):
    assert qr.ist_eingefroren() is False


def test_gepackt_neben_der_exe(qr, monkeypatch, tmp_path):
    """Mit sys.frozen zaehlt der Ordner der EXE, nicht der von __file__."""
    exe = tmp_path / "QR-Code-Generator.exe"
    exe.write_bytes(b"nur eine Attrappe")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))

    assert qr.ist_eingefroren() is True
    assert Path(qr.programm_ordner()) == tmp_path
    assert Path(qr.config_path()) == tmp_path / qr.CONFIG_NAME


def test_gepackt_nicht_im_entpackordner(qr, monkeypatch, tmp_path):
    """Der Entpackordner (_MEIPASS) darf die Einstellungen nicht aufnehmen."""
    entpackt = tmp_path / "_MEI123456"
    entpackt.mkdir()
    neben_exe = tmp_path / "Programm"
    neben_exe.mkdir()

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(entpackt), raising=False)
    monkeypatch.setattr(sys, "executable", str(neben_exe / "QR-Code-Generator.exe"))

    assert Path(qr.programm_ordner()) == neben_exe
    assert str(entpackt) not in qr.config_path()


def test_einstellungen_schreiben_und_lesen(qr, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "Programm.exe"))

    assert qr.save_config({"language": "en", "theme": "dark"}) is True
    assert qr.load_config() == {"language": "en", "theme": "dark"}
    assert qr.startup_language() == "en"
    assert qr.startup_theme() == "dark"


def test_beschaedigte_einstellungen_werden_verkraftet(qr, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "Programm.exe"))
    Path(qr.config_path()).write_text("{kein gueltiges JSON", encoding="utf-8")

    assert qr.load_config() == {}
    assert qr.startup_theme() == qr.DEFAULT_THEME


def test_unbekannte_werte_werden_ignoriert(qr, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "Programm.exe"))
    Path(qr.config_path()).write_text(
        json.dumps({"language": "klingonisch", "theme": "neon"}), encoding="utf-8")

    assert qr.startup_theme() == qr.DEFAULT_THEME
    assert qr.startup_language() in {qr.SOURCE_LANGUAGE, *qr.TRANSLATIONS}


def test_nicht_beschreibbarer_ordner_wirft_nicht(qr, monkeypatch, tmp_path):
    """save_config meldet einen Fehlschlag, statt das Programm abzubrechen."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "gibtsnicht" / "Programm.exe"))
    assert qr.save_config({"theme": "dark"}) is False


def test_speicherordner_ist_nicht_das_arbeitsverzeichnis(qr, monkeypatch, tmp_path):
    """Beim Doppelklick kann das Arbeitsverzeichnis irgendwo liegen."""
    monkeypatch.chdir(tmp_path)
    assert Path(qr.programm_ordner()) != Path(os.getcwd())
