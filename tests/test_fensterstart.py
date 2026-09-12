"""Das Fenster erscheint erst, wenn es fertig aufgebaut und platziert ist.

Hintergrund: Beim Aufbau ruft die Oberflaeche update_idletasks() auf, um
Groessen zu messen. Dabei zeigte Windows das Fenster schon an seiner
Standardposition an; erst danach setzte geometry() die Mitte, und das Fenster
sprang sichtbar ueber den Bildschirm.
"""

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
    app._neu_aufbauen()
    wurzel.update()
    assert wurzel.state() == "normal"
    assert app.eingabe.get("1.0", "end-1c") == "https://example.org"
