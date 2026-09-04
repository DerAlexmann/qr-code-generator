"""Ausgabeformate: Tabelle, Endungen und das tatsaechliche Schreiben."""

import pytest
from PIL import Image


def test_jedes_format_ist_vollstaendig_beschrieben(qr):
    for name, info in qr.FORMATE.items():
        assert info.name == name
        assert info.endung.startswith(".")
        assert info.beschreibung
        # Rasterformate brauchen einen Pillow-Namen, Vektorformate nicht.
        assert bool(info.pillow_name) != info.vektor


def test_endungen_sind_eindeutig(qr):
    endungen = [info.endung for info in qr.FORMATE.values()]
    assert len(endungen) == len(set(endungen))


def test_endung_findet_das_format_zurueck(qr):
    for name, info in qr.FORMATE.items():
        assert qr.format_aus_pfad("irgendwo/datei" + info.endung) == name
    assert qr.format_aus_pfad("datei.jpeg") == "JPEG"
    assert qr.format_aus_pfad("datei.unbekannt") is None


@pytest.mark.parametrize("name", list("PNG SVG JPEG WEBP TIFF BMP GIF ICO PDF EPS".split()))
def test_jedes_format_schreibt_eine_datei(qr, tmp_path, name):
    opts = qr.optionen_pruefen(qr.QROptionen(format=name, groesse=256))
    pfad, ergebnis = qr.qr_speichern("https://example.org", str(tmp_path / "code"), opts)

    assert pfad.endswith(qr.FORMATE[name].endung)
    assert ergebnis.module > 0
    inhalt = open(pfad, "rb").read()
    assert len(inhalt) > 100, "die Datei darf nicht leer sein"

    if name == "SVG":
        assert inhalt.lstrip().startswith(b"<?xml")
    elif name == "PDF":
        assert inhalt.startswith(b"%PDF")
    elif name == "EPS":
        assert inhalt.startswith(b"%!PS")
    else:
        with Image.open(pfad) as bild:
            assert bild.size == (opts.groesse, opts.groesse)


def test_ico_wird_begrenzt(qr):
    """ICO kann nicht mehr als 256 Pixel - die Angabe wird gekappt, nicht abgelehnt."""
    opts = qr.optionen_pruefen(qr.QROptionen(format="ICO", groesse=1024))
    assert opts.groesse == 256


def test_transparenz_nur_wo_moeglich(qr):
    for name, info in qr.FORMATE.items():
        opts = qr.optionen_pruefen(qr.QROptionen(format=name, transparent=True))
        assert opts.transparent == info.alpha, name


def test_jpeg_bekommt_keinen_alphakanal(qr, tmp_path):
    opts = qr.optionen_pruefen(qr.QROptionen(format="JPEG", groesse=256, transparent=True))
    pfad, _ = qr.qr_speichern("Ohne Alpha", str(tmp_path / "code"), opts)
    with Image.open(pfad) as bild:
        assert bild.mode == "RGB"


def test_png_behaelt_transparenz(qr, tmp_path):
    opts = qr.optionen_pruefen(qr.QROptionen(format="PNG", groesse=256, transparent=True))
    pfad, _ = qr.qr_speichern("Mit Alpha", str(tmp_path / "code"), opts)
    with Image.open(pfad) as bild:
        assert bild.mode == "RGBA"
        assert bild.getpixel((0, 0))[3] == 0


def test_dpi_landet_in_der_datei(qr, tmp_path):
    opts = qr.optionen_pruefen(qr.QROptionen(format="PNG", groesse=256, dpi=600))
    pfad, _ = qr.qr_speichern("Aufloesung", str(tmp_path / "code"), opts)
    with Image.open(pfad) as bild:
        breite, hoehe = bild.info.get("dpi", (0, 0))
        assert round(breite) == 600 and round(hoehe) == 600
