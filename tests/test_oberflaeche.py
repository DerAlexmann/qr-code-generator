"""Die Oberflaeche laesst unmoegliche Einstellungen gar nicht erst zu.

Diese Tests bauen ein echtes Fenster auf und werden uebersprungen, wo keines
entstehen kann - etwa auf den Linux-Runnern der CI, die keinen Bildschirm
haben. Die uebrigen Testdateien kommen bewusst ohne Fenster aus.
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

    fenster = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    wurzel.update()
    yield fenster
    wurzel.destroy()


def ruhen(app, ms=350):
    """Laesst die verzoegerte Neuberechnung der Vorschau ablaufen."""
    app.master.after(ms, app.master.quit)
    app.master.mainloop()


# -- Transparenz -----------------------------------------------------------

def test_transparenzfeld_folgt_dem_format(qr, app):
    for name, info in qr.FORMATE.items():
        app.var_format.set(name)
        app.master.update()
        erwartet = "normal" if info.alpha else "disabled"
        assert str(app.feld_transparent.cget("state")) == erwartet, name


def test_transparenz_wird_bei_unmoeglichem_format_abgewaehlt(qr, app):
    app.var_format.set("PNG")
    app.var_transparent.set(True)
    app._transparenz_umgeschaltet()
    app.master.update()
    assert app.var_transparent.get() is True

    app.var_format.set("JPEG")
    app.master.update()
    assert app.var_transparent.get() is False, "JPEG darf nicht transparent aussehen"
    assert str(app.feld_transparent.cget("state")) == "disabled"


def test_transparenzwunsch_ueberlebt_den_ausflug(qr, app):
    """Nach dem Umweg ueber ein Format ohne Transparenz steht das Haekchen wieder."""
    app.var_format.set("PNG")
    app.var_transparent.set(True)
    app._transparenz_umgeschaltet()
    app.master.update()

    for zwischenstopp in ("JPEG", "GIF", "BMP"):
        app.var_format.set(zwischenstopp)
        app.master.update()
        assert app.var_transparent.get() is False, zwischenstopp

    app.var_format.set("PNG")
    app.master.update()
    assert app.var_transparent.get() is True


def test_ohne_wunsch_bleibt_es_abgewaehlt(qr, app):
    app.var_format.set("JPEG")
    app.master.update()
    app.var_format.set("PNG")
    app.master.update()
    assert app.var_transparent.get() is False


# -- Groesse ---------------------------------------------------------------

def test_auswahlliste_endet_beim_maximum_des_formats(qr, app):
    app.var_format.set("ICO")
    app.master.update()
    werte = [int(w) for w in app.feld_groesse.cget("values")]
    assert werte and max(werte) <= 256

    app.var_format.set("PNG")
    app.master.update()
    werte = [int(w) for w in app.feld_groesse.cget("values")]
    assert max(werte) == max(qr.GROESSEN_VORGABEN)


def test_zu_grosse_groesse_wird_beim_formatwechsel_gekappt(qr, app):
    app.var_groesse.set("1024")
    app.master.update()
    app.var_format.set("ICO")
    app.master.update()
    assert app.var_groesse.get() == "256"


def test_formatwechsel_erklaert_die_kappung(qr, app):
    """Die Statuszeile sagt es einmal - und beim naechsten Zeichnen nicht mehr."""
    vorher = qr._.language
    qr._.language = qr.SOURCE_LANGUAGE
    try:
        app.var_groesse.set("2048")
        ruhen(app)
        app.var_format.set("ICO")
        ruhen(app)
        assert "256" in app.var_status.get()

        app.eingabe.insert("end", "x")
        ruhen(app)
        assert app.var_status.get() == qr._("Bereit.")
    finally:
        qr._.language = vorher


def test_getippte_groesse_wird_begrenzt(qr, app):
    app.var_format.set("ICO")
    app.master.update()

    app.var_groesse.set("5000")
    app._groesse_begrenzen()
    assert app.var_groesse.get() == "256"

    app.var_format.set("PNG")
    app.master.update()
    app.var_groesse.set("99999")
    app._groesse_begrenzen()
    assert app.var_groesse.get() == str(qr.MAX_KANTE)

    app.var_groesse.set("1")
    app._groesse_begrenzen()
    assert app.var_groesse.get() == str(qr.MIN_KANTE)


def test_gueltige_groesse_bleibt_unangetastet(qr, app):
    app.var_groesse.set("777")
    app._groesse_begrenzen()
    assert app.var_groesse.get() == "777"


def test_unlesbare_eingabe_wird_nicht_stillschweigend_ersetzt(qr, app):
    """Bei Unsinn im Feld erklaert die Statuszeile das - geraten wird nicht."""
    app.var_groesse.set("abc")
    app._groesse_begrenzen()
    assert app.var_groesse.get() == "abc"

    ruhen(app)
    assert "Zahl" in app.var_status.get() or "number" in app.var_status.get()


# -- Rand und Auflösung ----------------------------------------------------

def test_rand_und_dpi_werden_begrenzt(qr, app):
    app.var_rand.set(99)
    app._zahl_begrenzen(app.var_rand, 0, 32)
    assert app.var_rand.get() == 32

    app.var_rand.set(-5)
    app._zahl_begrenzen(app.var_rand, 0, 32)
    assert app.var_rand.get() == 0

    app.var_dpi.set(5)
    app._zahl_begrenzen(app.var_dpi, 72, 1200)
    assert app.var_dpi.get() == 72

    app.var_dpi.set(99999)
    app._zahl_begrenzen(app.var_dpi, 72, 1200)
    assert app.var_dpi.get() == 1200


# -- Zusammenspiel ---------------------------------------------------------

def test_kein_hinweis_mehr_noetig_nach_der_vorbeugung(qr, app):
    """Was die Felder verhindern, muss anpassungen_beschreiben() nicht melden."""
    app.var_groesse.set("4096")
    app.master.update()
    app.var_format.set("ICO")
    app.var_transparent.set(True)
    ruhen(app)

    opts = app.optionen_holen()
    assert opts.groesse == 256
    assert qr.anpassungen_beschreiben(app.gewuenscht, opts) == []


def test_zuruecksetzen_stellt_alles_her(qr, app):
    app.var_format.set("ICO")
    app.var_transparent.set(True)
    app._transparenz_umgeschaltet()
    app.master.update()

    app.zuruecksetzen()
    app.master.update()
    vorgabe = qr.QROptionen()
    assert app.var_format.get() == vorgabe.format
    assert app.var_groesse.get() == str(vorgabe.groesse)
    assert app.var_transparent.get() is False
    assert app.transparenz_wunsch is False
