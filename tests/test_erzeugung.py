"""Erzeugung der QR-Codes: Matrix, Bild, SVG und die Groessenrechnung."""

import re

import pytest


def test_matrix_hat_ruhezone(qr):
    """Der Rand steht als leerer Rahmen um das eigentliche Muster."""
    opts = qr.optionen_pruefen(qr.QROptionen(rand=4))
    ergebnis = qr.matrix_erzeugen("https://example.org", opts)

    assert ergebnis.module == len(ergebnis.matrix)
    for zeile in ergebnis.matrix[:4]:
        assert not any(zeile), "die obersten vier Zeilen muessen leer sein"
    for zeile in ergebnis.matrix:
        assert not any(zeile[:4]), "die linken vier Spalten muessen leer sein"
        assert not any(zeile[-4:]), "die rechten vier Spalten muessen leer sein"


def test_rand_veraendert_die_kantenlaenge(qr):
    """Jedes Modul Rand kommt auf beiden Seiten dazu."""
    ohne = qr.matrix_erzeugen("Test", qr.optionen_pruefen(qr.QROptionen(rand=0)))
    mit = qr.matrix_erzeugen("Test", qr.optionen_pruefen(qr.QROptionen(rand=4)))
    assert mit.module == ohne.module + 8


def test_hoehere_fehlerkorrektur_braucht_mehr_module(qr):
    """L kommt mit weniger Modulen aus als H."""
    text = "https://example.org/ein-etwas-laengerer-pfad"
    klein = qr.matrix_erzeugen(text, qr.optionen_pruefen(qr.QROptionen(fehlerkorrektur="L")))
    gross = qr.matrix_erzeugen(text, qr.optionen_pruefen(qr.QROptionen(fehlerkorrektur="H")))
    assert gross.module > klein.module


@pytest.mark.parametrize("kante", [32, 47, 128, 333, 512, 1024])
def test_bild_hat_exakt_die_gewuenschte_kantenlaenge(qr, kante):
    """Auch krumme Werte ergeben genau diese Pixelzahl."""
    opts = qr.optionen_pruefen(qr.QROptionen(groesse=kante))
    bild = qr.bild_erzeugen(qr.matrix_erzeugen("Groessentest", opts), opts)
    assert bild.size == (kante, kante)


def test_bild_ist_schwarzweiss_und_hat_hellen_rand(qr):
    """Vorgabe ist schwarz auf weiss; die Ecke liegt in der Ruhezone."""
    opts = qr.optionen_pruefen(qr.QROptionen(groesse=290))
    bild = qr.bild_erzeugen(qr.matrix_erzeugen("Farbtest", opts), opts)
    assert bild.getpixel((0, 0))[:3] == (255, 255, 255)
    # getcolors() statt getdata(): liefert die Farbtabelle direkt und ist
    # nicht als veraltet gekennzeichnet.
    farben = {farbe for _anzahl, farbe in bild.convert("RGB").getcolors(maxcolors=16)}
    assert farben == {(0, 0, 0), (255, 255, 255)}


def test_transparenter_rand(qr):
    opts = qr.optionen_pruefen(qr.QROptionen(groesse=290, transparent=True))
    bild = qr.bild_erzeugen(qr.matrix_erzeugen("Transparenz", opts), opts)
    assert bild.getpixel((0, 0))[3] == 0


def test_modulgroesse_bleibt_ganzzahlig(qr):
    """Die Zwischenstufe wird ganzzahlig gezeichnet und erst dann skaliert."""
    assert qr.modulgroesse_bestimmen(29, 512) == 17
    assert qr.modulgroesse_bestimmen(29, 29) == 1
    assert qr.modulgroesse_bestimmen(177, 32) == 1     # nie kleiner als ein Pixel


def test_svg_beschreibt_dieselbe_matrix(qr):
    """Der erzeugte Pfad laesst sich verlustfrei zurueckrechnen."""
    opts = qr.optionen_pruefen(qr.QROptionen(format="SVG", groesse=600))
    ergebnis = qr.matrix_erzeugen("https://example.org/test?x=1&y=2", opts)
    svg = qr.svg_erzeugen(ergebnis, opts)

    n = ergebnis.module
    zurueck = [[False] * n for _ in range(n)]
    for x, y, breite in re.findall(r"M(\d+) (\d+)h(\d+)v1h-\3z", svg):
        for i in range(int(breite)):
            zurueck[int(y)][int(x) + i] = True

    assert zurueck == ergebnis.matrix
    assert f'viewBox="0 0 {n} {n}"' in svg
    assert 'width="600"' in svg


def test_svg_ohne_hintergrund_bei_transparenz(qr):
    opts = qr.optionen_pruefen(qr.QROptionen(format="SVG", transparent=True))
    ergebnis = qr.matrix_erzeugen("Transparenz", opts)
    assert "<rect" not in qr.svg_erzeugen(ergebnis, opts)


def test_inhalt_zu_lang(qr, deutsch):
    """Selbst Version 40 fasst nicht beliebig viel - die Meldung ist verstaendlich."""
    with pytest.raises(qr.QRFehler, match="zu lang"):
        qr.matrix_erzeugen("B" * 5000, qr.QROptionen())


def test_feste_version_zu_klein(qr, deutsch):
    with pytest.raises(qr.QRFehler, match="Version 1"):
        qr.matrix_erzeugen("Text" * 200, qr.QROptionen(version=1))


def test_leerer_inhalt(qr, deutsch):
    with pytest.raises(qr.QRFehler, match="kein Inhalt"):
        qr.matrix_erzeugen("", qr.QROptionen())
