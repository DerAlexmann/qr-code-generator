"""Das Fenster erscheint erst, wenn es fertig aufgebaut und platziert ist.

Hintergrund: Beim Aufbau ruft die Oberflaeche update_idletasks() auf, um
Groessen zu messen. Dabei zeigte Windows das Fenster schon an seiner
Standardposition an; erst danach setzte geometry() die Mitte, und das Fenster
sprang sichtbar ueber den Bildschirm.

Ebenso sprang ein verschobenes Fenster nach einem Sprachwechsel zurueck in
die Mitte, weil der Neuaufbau dieselbe Einpassung wie der Start benutzte.

Und selbst an Ort und Stelle blitzte es beim Sprachwechsel auf: wm resizable
legt unter Windows das aeussere Fenster neu an, auch ohne Aenderung.
"""

import sys

import pytest


@pytest.fixture
def wurzel(qr):
    tk = pytest.importorskip("tkinter")
    from tkinter import ttk

    pytest.importorskip("PIL.ImageTk")
    from PIL import ImageTk

    qr._tk, qr._ttk, qr._ImageTk = tk, ttk, ImageTk
    qr.widgets_bereitstellen()
    qr.apply_theme("light")

    try:
        fenster = tk.Tk()
    except tk.TclError as exc:                  # kein Bildschirm vorhanden
        pytest.skip(f"kein Fenster moeglich: {exc}")
    yield fenster
    fenster.destroy()


def test_fenster_ist_beim_platzieren_noch_unsichtbar(qr, wurzel):
    """Wenn die Position gesetzt wird, darf noch nichts zu sehen sein."""
    sichtbar_beim_platzieren = []
    echt = wurzel.geometry

    def spion(*args):
        if args:                                # nur Setzen, nicht Abfragen
            sichtbar_beim_platzieren.append(bool(wurzel.winfo_ismapped()))
        return echt(*args)

    wurzel.geometry = spion
    qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")

    assert sichtbar_beim_platzieren == [False]


def test_fenster_ist_nach_dem_aufbau_sichtbar(qr, wurzel):
    """Verborgen aufbauen darf nicht heissen, verborgen zu bleiben."""
    qr.QRApp(wurzel, qr.QROptionen())
    wurzel.update()
    assert wurzel.state() == "normal"
    assert wurzel.winfo_ismapped()


def test_fenster_liegt_im_arbeitsbereich(qr, wurzel):
    app = qr.QRApp(wurzel, qr.QROptionen())
    wurzel.update()
    rand_x, rand_y, breite, hoehe = app.arbeitsflaeche
    assert breite > 0 and hoehe > 0
    assert rand_x <= wurzel.winfo_x() and wurzel.winfo_x() + wurzel.winfo_width() <= rand_x + breite
    assert rand_y <= wurzel.winfo_y() and wurzel.winfo_y() + wurzel.winfo_height() <= rand_y + hoehe


def test_sprachwechsel_laesst_das_fenster_sichtbar(qr, wurzel):
    """Der Neuaufbau nach einem Sprachwechsel geht einen anderen Weg als der Start."""
    app = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    wurzel.update()
    app._texte_auffrischen()
    wurzel.update()
    assert wurzel.state() == "normal"
    assert app.eingabe.get("1.0", "end-1c") == "https://example.org"


def test_sprachwechsel_behaelt_die_position(qr, wurzel):
    """Ein beiseitegeschobenes Fenster bleibt nach dem Sprachwechsel, wo es ist."""
    app = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    rand_x, rand_y, _breite, _hoehe = app.arbeitsflaeche
    wurzel.geometry(f"+{rand_x + 40}+{rand_y + 30}")
    wurzel.update()
    vorher = (wurzel.winfo_x(), wurzel.winfo_y())

    app._texte_auffrischen()
    wurzel.update()
    assert (wurzel.winfo_x(), wurzel.winfo_y()) == vorher


def test_sprachwechsel_ruft_resizable_nicht_auf(qr, wurzel):
    """Ohne Änderung kein wm resizable - es würde das Fenster neu anlegen."""
    app = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    wurzel.update()
    aufrufe = []
    echt = wurzel.resizable

    def spion(*args):
        if args:                                # nur Setzen, nicht Abfragen
            aufrufe.append(args)
        return echt(*args)

    wurzel.resizable = spion
    app._texte_auffrischen()
    wurzel.update()
    assert aufrufe == []


@pytest.mark.skipif(sys.platform != "win32", reason="prüft das Windows-Fensterhandle")
def test_sprachwechsel_behaelt_das_windows_fenster(qr, wurzel):
    """Das äußere Windows-Fenster bleibt dasselbe - es blitzt nichts auf."""
    import ctypes

    app = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    wurzel.update()

    def huelle():
        return ctypes.windll.user32.GetParent(wurzel.winfo_id())

    vorher = huelle()
    app._texte_auffrischen()
    wurzel.update()
    assert huelle() == vorher
    assert ctypes.windll.user32.IsWindowVisible(huelle())


@pytest.mark.parametrize("ecke", ["rechts unten", "links oben"])
def test_sprachwechsel_holt_das_fenster_auf_den_bildschirm(qr, wurzel, ecke):
    """Ragt das Fenster über den Rand, rückt es gerade so weit herein."""
    app = qr.QRApp(wurzel, qr.QROptionen(), "https://example.org")
    rand_x, rand_y, breite, hoehe = app.arbeitsflaeche
    if ecke == "rechts unten":
        wurzel.geometry(f"+{rand_x + breite - 120}+{rand_y + hoehe - 90}")
    else:
        wurzel.geometry(f"+{rand_x - 200}+{rand_y - 150}")
    wurzel.update()

    app._texte_auffrischen()
    wurzel.update()
    # Aussenmasse samt Rahmen: die Innenflaeche plus der Abstand zum Rahmen
    links = wurzel.winfo_rootx() - wurzel.winfo_x()
    oben = wurzel.winfo_rooty() - wurzel.winfo_y()
    assert wurzel.winfo_x() >= rand_x and wurzel.winfo_y() >= rand_y
    assert wurzel.winfo_x() + wurzel.winfo_width() + 2 * links <= rand_x + breite
    assert wurzel.winfo_y() + wurzel.winfo_height() + oben + links <= rand_y + hoehe
