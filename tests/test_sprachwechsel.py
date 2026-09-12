"""Sprachwechsel ohne Neuaufbau.

Bis 1.1.4 riss der Sprachwechsel die ganze Oberflaeche ab und baute sie neu
auf. Weil Tk jedes Element einzeln zeichnet, sah man dabei rund 300 ms lang
jeden Zwischenstand. Jetzt bleiben die Widgets stehen und nur ihre Texte werden
ausgetauscht - wie beim Farbschema.

Der strengste Test vergleicht eine umgeschaltete Oberflaeche Text fuer Text mit
einer, die gleich in der Zielsprache aufgebaut wurde. Vergisst jemand bei einer
neuen Beschriftung beschriften(), bleibt sie beim Umschalten in der alten
Sprache stehen - und genau das faellt dort auf.
"""

import sys

import pytest

# -- ohne Fenster --------------------------------------------------------------


def test_uebersetzter_text_kennt_seinen_schluessel(qr, deutsch):
    text = qr._("Version {version}").format(version="9.9")
    assert text == "Version 9.9"
    assert isinstance(text, str)
    assert text.schluessel == "Version {version}"
    assert text.werte == {"version": "9.9"}


def test_verketteter_text_ist_ein_gewoehnlicher_string(qr, deutsch):
    """Nur was direkt aus _() kommt, traegt einen Schluessel."""
    assert type("  " + qr._("QR-Code")) is str


def test_beschriftung_ohne_uebersetzung_wird_nicht_gemerkt(qr):
    gesetzt = []
    qr.BESCHRIFTUNGEN.clear()
    qr.beschriftung_merken(gesetzt.append, "#000000")          # etwa ein Farbwert
    assert gesetzt == ["#000000"]
    assert qr.BESCHRIFTUNGEN == []


def test_texte_auffrischen_bildet_den_text_neu(qr):
    gesetzt = []
    vorher = qr._.language
    qr.BESCHRIFTUNGEN.clear()
    try:
        qr._.language = "de"
        qr.beschriftung_merken(gesetzt.append,
                               qr._("Version {version}").format(version="9.9"))
        qr._.language = "en"
        qr.texte_auffrischen()
    finally:
        qr._.language = vorher
        qr.BESCHRIFTUNGEN.clear()
    englisch = qr.TRANSLATIONS["en"]["Version {version}"].format(version="9.9")
    assert gesetzt == ["Version 9.9", englisch]


# -- mit Fenster ---------------------------------------------------------------


@pytest.fixture
def tk_modul(qr):
    tk = pytest.importorskip("tkinter")
    from tkinter import ttk

    pytest.importorskip("PIL.ImageTk")
    from PIL import ImageTk

    qr._tk, qr._ttk, qr._ImageTk = tk, ttk, ImageTk
    qr.widgets_bereitstellen()
    qr.apply_theme("light")
    vorher = qr._.language
    yield tk
    qr._.language = vorher


def fenster_bauen(qr, tk, sprache):
    qr._.language = sprache
    try:
        wurzel = tk.Tk()
    except tk.TclError as exc:                  # kein Bildschirm vorhanden
        pytest.skip(f"kein Fenster moeglich: {exc}")
    app = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    wurzel.update()
    return wurzel, app


def alle_texte(tk, wurzel, app):
    """Jeder sichtbare Text der Oberflaeche, in Aufbaureihenfolge."""
    texte = []

    def sammeln(eltern):
        for kind in eltern.winfo_children():
            klasse = kind.winfo_class()
            # Nur echte Optionen abfragen: Tk akzeptiert Abkuerzungen, und bei
            # ttk-Eingabefeldern waere "text" die fuer "textvariable".
            optionen = kind.keys()
            if klasse == "TCombobox":
                texte.append((klasse, kind.get()))
            else:
                if "text" in optionen and str(kind.cget("text")):
                    texte.append((klasse, str(kind.cget("text"))))
                if "textvariable" in optionen and str(kind.cget("textvariable")):
                    texte.append((klasse, kind.getvar(str(kind.cget("textvariable")))))
            sammeln(kind)

    sammeln(wurzel)
    texte += [("Reiter", app.reiter.tab(i, "text")) for i in range(app.reiter.index("end"))]
    return texte


@pytest.mark.parametrize(("von", "nach"), [("de", "en"), ("en", "de")])
def test_umgeschaltet_gleicht_frisch_aufgebaut(qr, tk_modul, von, nach):
    tk = tk_modul
    wurzel, app = fenster_bauen(qr, tk, von)
    try:
        qr._.language = nach
        app._texte_auffrischen()
        wurzel.update()
        umgeschaltet = alle_texte(tk, wurzel, app)
        breite = wurzel.winfo_width()
    finally:
        wurzel.destroy()

    wurzel, app = fenster_bauen(qr, tk, nach)
    try:
        frisch = alle_texte(tk, wurzel, app)
        abweichend = [(a, b) for a, b in zip(umgeschaltet, frisch) if a != b]
        assert not abweichend, f"nach dem Umschalten anders als frisch: {abweichend[:5]}"
        assert len(umgeschaltet) == len(frisch)
        assert breite == wurzel.winfo_width()
    finally:
        wurzel.destroy()


def test_sprachwechsel_behaelt_widgets_und_eingaben(qr, tk_modul):
    tk = tk_modul
    wurzel, app = fenster_bauen(qr, tk, "de")
    try:
        eingabe = app.eingabe
        app.var_format.set("SVG")
        app.var_stapel.set(True)
        app.reiter.select(2)
        wurzel.update()

        qr._.language = "en"
        app._texte_auffrischen()
        wurzel.update()

        assert app.eingabe is eingabe and eingabe.winfo_exists()
        assert eingabe.get("1.0", "end-1c") == "https://example.org"
        assert app.var_format.get() == "SVG"
        assert app.var_stapel.get() is True
        assert app.reiter.index("current") == 2
        assert app.reiter.tab(1, "text").strip() == qr.TRANSLATIONS["en"]["Erklärungen"]
    finally:
        wurzel.destroy()


# -- angehaltenes Zeichnen (nur Windows) -----------------------------------------

nur_windows = pytest.mark.skipif(sys.platform != "win32",
                                 reason="WM_SETREDRAW gibt es nur unter Windows")


def sichtbar(wurzel):
    """WM_SETREDRAW(FALSE) nimmt dem Fenster das WS_VISIBLE - daran ist es zu erkennen."""
    import ctypes
    return bool(ctypes.windll.user32.IsWindowVisible(wurzel.winfo_id()))


@nur_windows
def test_waehrend_des_wechsels_ist_das_zeichnen_angehalten(qr, tk_modul, monkeypatch):
    wurzel, app = fenster_bauen(qr, tk_modul, "de")
    echt, beobachtet = qr.texte_auffrischen, []

    def spion():
        beobachtet.append(sichtbar(wurzel))
        echt()

    monkeypatch.setattr(qr, "texte_auffrischen", spion)
    try:
        qr._.language = "en"
        app._texte_auffrischen()
        wurzel.update()
        assert beobachtet == [False], "beim Austausch der Texte muss das Zeichnen ruhen"
        assert sichtbar(wurzel), "danach muss wieder gezeichnet werden"
    finally:
        wurzel.destroy()


@nur_windows
def test_zeichnen_laeuft_auch_nach_einem_fehler_weiter(qr, tk_modul, monkeypatch):
    """Sonst bliebe das Fenster nach einer Ausnahme dauerhaft eingefroren."""
    wurzel, app = fenster_bauen(qr, tk_modul, "de")

    def kaputt():
        raise RuntimeError("absichtlich")

    monkeypatch.setattr(qr, "texte_auffrischen", kaputt)
    try:
        with pytest.raises(RuntimeError):
            app._texte_auffrischen()
        assert sichtbar(wurzel)
    finally:
        wurzel.destroy()
