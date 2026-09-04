"""Farbschemata: gleiche Schluessel, gueltige Werte, sauberes Umschalten."""

import re

FARBE = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_alle_paletten_haben_dieselben_schluessel(qr):
    paletten = list(qr.THEMES.values())
    erste = set(paletten[0])
    for name, palette in qr.THEMES.items():
        assert set(palette) == erste, f"Palette '{name}' weicht ab"


def test_alle_farbwerte_sind_gueltig(qr):
    for name, palette in qr.THEMES.items():
        for schluessel, wert in palette.items():
            assert FARBE.match(wert), f"{name}.{schluessel} = {wert!r}"


def test_vorgabeschema_existiert(qr):
    assert qr.DEFAULT_THEME in qr.THEMES


def test_apply_theme_setzt_die_modulvariablen(qr):
    vorher = qr.CURRENT_THEME
    try:
        for name, palette in qr.THEMES.items():
            qr.apply_theme(name)
            assert qr.CURRENT_THEME == name
            for schluessel, wert in palette.items():
                assert getattr(qr, schluessel) == wert
    finally:
        qr.apply_theme(vorher)


def test_unbekanntes_schema_faellt_auf_die_vorgabe_zurueck(qr):
    vorher = qr.CURRENT_THEME
    try:
        qr.apply_theme("gibtsnicht")
        assert qr.CURRENT_THEME == qr.DEFAULT_THEME
    finally:
        qr.apply_theme(vorher)


def relative_helligkeit(hexwert):
    """Relative Leuchtdichte nach WCAG 2.1, mit sRGB-Gammakorrektur.

    Bewusst nicht dieselbe vereinfachte Rechnung wie in kontrast_warnung():
    dort genuegt eine grobe Abschaetzung fuer einen Hinweis, hier soll der
    Wert mit den ueblichen Barrierefreiheitsstufen vergleichbar sein.
    """
    def kanal(wert):
        wert /= 255
        return wert / 12.92 if wert <= 0.04045 else ((wert + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hexwert[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)


def kontrast(vorne, hinten):
    hell = max(relative_helligkeit(vorne), relative_helligkeit(hinten))
    dunkel = min(relative_helligkeit(vorne), relative_helligkeit(hinten))
    return (hell + 0.05) / (dunkel + 0.05)


def test_hell_und_dunkel_unterscheiden_sich_deutlich(qr):
    """Der Seitenhintergrund muss sich zwischen den Schemata klar unterscheiden."""
    assert relative_helligkeit(qr.THEMES["light"]["BG"]) > 0.7
    assert relative_helligkeit(qr.THEMES["dark"]["BG"]) < 0.05


def test_schrift_hebt_sich_vom_grund_ab(qr):
    """In jedem Schema muss TEXT auf CARD gut lesbar sein (WCAG-Stufe AAA)."""
    for name, palette in qr.THEMES.items():
        verhaeltnis = kontrast(palette["TEXT"], palette["CARD"])
        assert verhaeltnis >= 7.0, f"Palette '{name}': nur {verhaeltnis:.1f}:1"


def test_nebentext_bleibt_lesbar(qr):
    """MUTED darf blasser sein, muss aber die Stufe AA halten."""
    for name, palette in qr.THEMES.items():
        verhaeltnis = kontrast(palette["MUTED"], palette["CARD"])
        assert verhaeltnis >= 4.5, f"Palette '{name}': nur {verhaeltnis:.1f}:1"


def test_schrift_auf_farbflaechen(qr):
    """ON_ACCENT steht auf ACCENT - etwa im Knopf 'Speichern unter ...'."""
    for name, palette in qr.THEMES.items():
        verhaeltnis = kontrast(palette["ON_ACCENT"], palette["ACCENT"])
        assert verhaeltnis >= 3.0, f"Palette '{name}': nur {verhaeltnis:.1f}:1"
