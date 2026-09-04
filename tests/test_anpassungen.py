"""Angepasste Einstellungen muessen erklaert werden, nicht nur wirken.

optionen_pruefen() begrenzt stillschweigend aufs Machbare. Anfangs erfuhr das
nur die Kommandozeile; die Oberflaeche passte die Datei an, sagte aber nichts
dazu - obwohl README und der Reiter "Erklaerungen" genau das versprachen.
"""

import pytest


def test_ico_groesse_wird_gemeldet(qr, deutsch):
    gewuenscht = qr.QROptionen(format="ICO", groesse=1024)
    geprueft = qr.optionen_pruefen(gewuenscht)
    hinweise = qr.anpassungen_beschreiben(gewuenscht, geprueft)

    assert len(hinweise) == 1
    assert "ICO" in hinweise[0]
    assert "256" in hinweise[0]


def test_transparenz_wird_gemeldet(qr, deutsch):
    for name in ("GIF", "JPEG", "BMP", "PDF", "EPS"):
        gewuenscht = qr.QROptionen(format=name, transparent=True)
        geprueft = qr.optionen_pruefen(gewuenscht)
        hinweise = qr.anpassungen_beschreiben(gewuenscht, geprueft)

        assert len(hinweise) == 1, name
        assert name in hinweise[0]
        assert "Transparenz" in hinweise[0]


def test_beides_zugleich(qr, deutsch):
    """ICO kann Transparenz, aber keine 1024 Pixel - dann nur ein Hinweis."""
    gewuenscht = qr.QROptionen(format="ICO", groesse=1024, transparent=True)
    geprueft = qr.optionen_pruefen(gewuenscht)
    assert len(qr.anpassungen_beschreiben(gewuenscht, geprueft)) == 1

    # GIF kann beides nicht: zu gross und ohne Transparenz
    gewuenscht = qr.QROptionen(format="GIF", groesse=99999, transparent=True)
    with pytest.raises(qr.QRFehler):
        qr.optionen_pruefen(gewuenscht)      # 99999 px wird abgelehnt, nicht gekappt


def test_ohne_anpassung_keine_meldung(qr, deutsch):
    for gewuenscht in (qr.QROptionen(),
                       qr.QROptionen(format="PNG", groesse=1024, transparent=True),
                       qr.QROptionen(format="SVG", transparent=True),
                       qr.QROptionen(format="ICO", groesse=256)):
        geprueft = qr.optionen_pruefen(gewuenscht)
        assert qr.anpassungen_beschreiben(gewuenscht, geprueft) == []


def test_meldungen_sind_uebersetzt(qr):
    """Auch auf Englisch muss ein Text herauskommen, nicht der deutsche."""
    vorher = qr._.language
    try:
        gewuenscht = qr.QROptionen(format="ICO", groesse=1024, transparent=True)
        geprueft = qr.optionen_pruefen(gewuenscht)

        qr._.language = "de"
        deutsch = qr.anpassungen_beschreiben(gewuenscht, geprueft)
        qr._.language = "en"
        englisch = qr.anpassungen_beschreiben(gewuenscht, geprueft)

        assert deutsch and englisch
        assert deutsch != englisch
        assert "256" in englisch[0]
    finally:
        qr._.language = vorher


def test_kommandozeile_meldet_die_anpassung(qr, tmp_path):
    """Der Weg ueber die Kommandozeile muss weiterhin darauf hinweisen."""
    import locale
    import subprocess
    import sys
    from pathlib import Path

    skript = Path(qr.__file__).resolve()
    zeichensatz = locale.getpreferredencoding(False)

    for argumente, erwartet in (
            (["-f", "ICO", "-s", "1024"], "256"),
            (["-f", "GIF", "--transparent"], "GIF")):
        ergebnis = subprocess.run(
            [sys.executable, str(skript), "Anpassung", "-a", str(tmp_path), *argumente],
            capture_output=True)
        ausgabe = ergebnis.stdout.decode(zeichensatz, errors="replace")
        assert ergebnis.returncode == 0
        assert "Hinweis" in ausgabe or "Note" in ausgabe, ausgabe
        assert erwartet in ausgabe, ausgabe
