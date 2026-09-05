"""Stapelmodus mit leerer oder leerraumhaltiger Eingabe.

Hintergrund: _zeilen_holen() laesst Leerzeilen weg und kann deshalb eine leere
Liste liefern. Die Vorschau griff darauf mit [0] zu und stuerzte mit einem
IndexError ab, sobald der Stapelmodus bei leerem Feld eingeschaltet wurde.
"""

import pytest


@pytest.fixture
def app(qr):
    """Ein aufgebautes Fenster; wird nach dem Test wieder abgeraeumt."""
    tk = pytest.importorskip("tkinter")
    from tkinter import ttk

    pytest.importorskip("PIL.ImageTk")
    from PIL import ImageTk

    qr._tk, qr._ttk, qr._ImageTk = tk, ttk, ImageTk
    qr.widgets_bereitstellen()
    qr.apply_theme("light")

    try:
        wurzel = tk.Tk()
    except tk.TclError as exc:                  # kein Bildschirm vorhanden
        pytest.skip(f"kein Fenster moeglich: {exc}")

    fenster = qr.QRApp(wurzel, qr.QROptionen())     # bewusst ohne Starttext
    wurzel.update()
    yield fenster
    wurzel.destroy()


def test_stapel_bei_leerem_feld(qr, app):
    """Der gemeldete Absturz: Stapelmodus einschalten, Feld ist leer."""
    assert app.eingabe.get("1.0", "end-1c") == ""
    app.var_stapel.set(True)
    app._neu_zeichnen()                          # darf nicht werfen
    assert app.vorschau_bild is None


def test_stapel_nach_dem_loeschen_des_textes(qr, app):
    app.eingabe.insert("1.0", "https://example.org")
    app.var_stapel.set(True)
    app._neu_zeichnen()
    assert app.vorschau_bild is not None

    app.eingabe.delete("1.0", "end")
    app._neu_zeichnen()
    assert app.vorschau_bild is None


@pytest.mark.parametrize("inhalt", ["", "   ", "\n", "\n\n\n", "  \n \t \n  "])
def test_stapel_mit_reinem_leerraum(qr, app, inhalt):
    app.var_stapel.set(True)
    app.eingabe.delete("1.0", "end")
    app.eingabe.insert("1.0", inhalt)
    app._neu_zeichnen()
    assert app.vorschau_bild is None


def test_leerzeilen_zwischen_inhalten_stoeren_nicht(qr, app):
    """Leerzeilen werden uebersprungen, die Vorschau zeigt die erste echte Zeile."""
    app.var_stapel.set(True)
    app.eingabe.insert("1.0", "\n\n  \nhttps://example.org\n\n\nzweite Zeile\n")
    app._neu_zeichnen()

    assert app.vorschau_bild is not None
    assert "2" in app.var_info.get(), app.var_info.get()   # zwei Codes im Stapel


def test_umschalten_hin_und_her_bei_leerem_feld(qr, app):
    """Mehrfaches Umschalten darf in keiner Richtung stolpern."""
    for an in (True, False, True, False, True):
        app.var_stapel.set(an)
        app._neu_zeichnen()
    assert app.vorschau_bild is None


def test_speichern_meldet_statt_abzustuerzen(qr, app, monkeypatch):
    """Auch der Speichern-Weg muss die leere Liste verkraften."""
    gemeldet = []

    class Attrappe:
        @staticmethod
        def showinfo(_titel, text, **_kw):
            gemeldet.append(text)

        @staticmethod
        def askdirectory(**_kw):
            raise AssertionError("es darf gar nicht erst nach einem Ordner gefragt werden")

    app.var_stapel.set(True)
    app._stapel_speichern(qr.QROptionen(), Attrappe, Attrappe)
    assert gemeldet and "Zeile" in gemeldet[0]
