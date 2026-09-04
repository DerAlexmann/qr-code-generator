"""Optionen, Farben, Dateinamen und die Stapeldatei."""

import pytest

# -- Pruefung der Optionen -------------------------------------------------

def test_vorgaben_sind_gueltig(qr):
    opts = qr.optionen_pruefen(qr.QROptionen())
    assert opts.format in qr.FORMATE
    assert opts.fehlerkorrektur in qr.FEHLERKORREKTUR
    assert qr.MIN_KANTE <= opts.groesse <= qr.MAX_KANTE
    assert opts.rand >= 4, "die Norm verlangt mindestens vier Module Ruhezone"


@pytest.mark.parametrize("feld,wert,wortlaut", [
    ("format", "XYZ", "Unbekanntes Format"),
    ("fehlerkorrektur", "Z", "Unbekannte Fehlerkorrektur"),
    ("groesse", 5, "Größe"),
    ("groesse", 99999, "Größe"),
    ("rand", -1, "Rand"),
    ("rand", 99, "Rand"),
    ("version", 0, "Version"),
    ("version", 41, "Version"),
    ("qualitaet", 0, "Qualität"),
    ("vordergrund", "kein-farbwert", "nicht lesbar"),
])
def test_ungueltige_angaben_werden_abgelehnt(qr, deutsch, feld, wert, wortlaut):
    with pytest.raises(qr.QRFehler, match=wortlaut):
        qr.optionen_pruefen(qr.QROptionen(**{feld: wert}))


def test_pruefung_veraendert_das_original_nicht(qr):
    """optionen_pruefen liefert eine Kopie - der Aufrufer behaelt seinen Stand."""
    original = qr.QROptionen(format="ICO", groesse=1024)
    geprueft = qr.optionen_pruefen(original)
    assert original.groesse == 1024
    assert geprueft.groesse == 256


# -- Farben ----------------------------------------------------------------

def test_farbangaben_in_verschiedenen_schreibweisen(qr):
    assert qr.farbe_pruefen("#000000", "Test") == (0, 0, 0)
    assert qr.farbe_pruefen("#FFFFFF", "Test") == (255, 255, 255)
    assert qr.farbe_pruefen("black", "Test") == (0, 0, 0)
    assert qr.farbe_pruefen("navy", "Test") == (0, 0, 128)


def test_kontrastwarnung(qr, deutsch):
    assert qr.kontrast_warnung(qr.QROptionen()) is None

    zu_wenig = qr.kontrast_warnung(qr.QROptionen(vordergrund="#888888", hintergrund="#999999"))
    assert zu_wenig and "Kontrast" in zu_wenig

    invertiert = qr.kontrast_warnung(qr.QROptionen(vordergrund="#FFFFFF", hintergrund="#000000"))
    assert invertiert and "heller" in invertiert


# -- Dateinamen ------------------------------------------------------------

@pytest.mark.parametrize("inhalt,erwartet", [
    ("https://example.org/pfad?a=1", "example.org_pfad_a_1"),
    ("mailto:info@example.org", "mailto_info_example.org"),
    ("Hallo Welt", "Hallo_Welt"),
    ("", "qr"),
    ("   ", "qr"),
])
def test_dateiname_aus_inhalt(qr, inhalt, erwartet):
    assert qr.dateiname_vorschlagen(inhalt) == erwartet


def test_dateiname_ohne_pfadwechsel(qr):
    """Ein Inhalt darf nicht aus dem Zielordner herausfuehren."""
    for boesartig in ("../../etc/passwd", r"..\..\windows\system32", "/absolut/pfad"):
        name = qr.dateiname_vorschlagen(boesartig)
        assert ".." not in name
        assert "/" not in name and "\\" not in name


def test_unter_windows_gesperrte_namen(qr):
    for gesperrt in ("CON", "PRN", "AUX", "NUL", "COM1", "LPT9"):
        assert qr.dateiname_vorschlagen(gesperrt).startswith("qr_")


def test_dateiname_wird_gekuerzt(qr):
    assert len(qr.dateiname_vorschlagen("A" * 500)) <= 48


def test_stapelnummer(qr):
    assert qr.dateiname_vorschlagen("Test", 7).endswith("_007")


def test_endung_ergaenzen(qr):
    png = qr.FORMATE["PNG"]
    svg = qr.FORMATE["SVG"]
    assert qr.endung_ergaenzen("code", png) == "code.png"
    assert qr.endung_ergaenzen("code.png", png) == "code.png"
    # Ein Punkt im Namen macht noch keine Endung - das war ein echter Fehler.
    assert qr.endung_ergaenzen("mailto_info_example.org", svg) == "mailto_info_example.org.svg"
    # Eine fremde Endung bleibt stehen, die richtige kommt dazu.
    assert qr.endung_ergaenzen("code.png", svg) == "code.png.svg"


def test_freier_pfad_nummeriert(qr, tmp_path):
    erste = tmp_path / "code.png"
    erste.write_bytes(b"x")
    assert qr.freier_pfad(str(erste)).endswith("code_2.png")

    (tmp_path / "code_2.png").write_bytes(b"x")
    assert qr.freier_pfad(str(erste)).endswith("code_3.png")


def test_speichern_legt_fehlende_ordner_an(qr, tmp_path):
    ziel = tmp_path / "neu" / "tiefer" / "code.png"
    pfad, _ = qr.qr_speichern("Ordnertest", str(ziel), qr.QROptionen())
    assert pfad == str(ziel)
    assert ziel.is_file()


# -- Stapeldatei -----------------------------------------------------------

def test_stapeldatei_lesen(qr, tmp_path):
    datei = tmp_path / "liste.txt"
    datei.write_text(
        "# Kommentar\n"
        "https://example.org | webseite\n"
        "\n"
        "Nur Inhalt\n"
        "   Mit Leerraum   |   name   \n",
        encoding="utf-8")

    eintraege = qr.stapel_eintraege_lesen(str(datei))
    assert eintraege == [
        ("https://example.org", "webseite"),
        ("Nur Inhalt", None),
        ("Mit Leerraum", "name"),
    ]


def test_leere_stapeldatei(qr, deutsch, tmp_path):
    datei = tmp_path / "leer.txt"
    datei.write_text("# nur ein Kommentar\n\n", encoding="utf-8")
    with pytest.raises(qr.QRFehler, match="keine verwertbaren Zeilen"):
        qr.stapel_eintraege_lesen(str(datei))


def test_fehlende_stapeldatei(qr, deutsch, tmp_path):
    with pytest.raises(qr.QRFehler, match="nicht lesbar"):
        qr.stapel_eintraege_lesen(str(tmp_path / "gibtsnicht.txt"))
