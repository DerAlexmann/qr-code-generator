"""
QR-Code-Generator 1.1 - QR-Codes aus Text erzeugen und als Bild speichern

Erzeugt QR-Codes fuer beliebige textbasierte Inhalte (Text, URLs, WLAN-Zugaenge,
Kontaktdaten, ...) und speichert sie in verschiedenen Bildformaten und Groessen.

Farbschema, Sprachumschaltung und Aufbau folgen der Bild-Toolbox, damit sich
beide Programme gleich anfuehlen.

Zwei Betriebsarten in einer Datei:
  * Ohne Argumente  -> grafische Oberflaeche (Tkinter) mit Live-Vorschau
  * Mit Argumenten  -> Kommandozeile, auch fuer Stapelverarbeitung

Licensed under MIT License
Copyright 2026 Alexander Unverhau
Created with assistance of Claude AI

Benoetigt:  pip install qrcode Pillow
"""

from __future__ import annotations

import argparse
import json
import locale
import os
import re
import sys
from dataclasses import dataclass, field, replace

# --------------------------------------------------------------------------
# Abhaengigkeiten
# --------------------------------------------------------------------------

try:
    import qrcode
    from qrcode.constants import (
        ERROR_CORRECT_H,
        ERROR_CORRECT_L,
        ERROR_CORRECT_M,
        ERROR_CORRECT_Q,
    )
    HAS_QRCODE = True
except ImportError:                                     # ohne qrcode geht nichts
    HAS_QRCODE = False
    qrcode = None
    ERROR_CORRECT_L = ERROR_CORRECT_M = ERROR_CORRECT_Q = ERROR_CORRECT_H = None

try:
    from PIL import Image, ImageColor, ImageDraw
    HAS_PIL = True
except ImportError:                          # dann bleibt nur noch SVG uebrig
    HAS_PIL = False
    Image = ImageColor = ImageDraw = None


PROGRAMM = "QR-Code-Generator"
VERSION = "1.1"


# --------------------------------------------------------------------------
# Farbschemata
#
# Die Paletten stammen aus der Bild-Toolbox, damit beide Programme gleich
# aussehen. apply_theme() schreibt die Werte der gewaehlten Palette in die
# Modulvariablen - der uebrige Code benutzt einfach BG, CARD, TEXT ... und
# muss vom Umschalten nichts wissen. Ein eigenes Schema entsteht durch eine
# weitere Palette mit denselben Namen.
# --------------------------------------------------------------------------

THEMES = {
    "light": {
        "BG": "#eef1f5",             # Seitenhintergrund
        "CARD": "#ffffff",           # Karten
        "CARD_ALT": "#fbfcfe",       # Text- und Listenflaechen in Karten
        "BORDER": "#d7dce4",
        "TEXT": "#1b2430",
        "MUTED": "#6c7684",          # Nebentext
        "HEADER": "#1d2330",         # Kopfzeile mit Titel und Umschaltern
        "HEADER_TEXT": "#c2cad8",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#69748c",
        "HEADER_HOVER": "#2b3346",
        "ACCENT": "#2f7de1",
        "ACCENT_DARK": "#1f66c4",
        "ON_ACCENT": "#ffffff",      # Schrift auf farbigen Flaechen
        "OK": "#2e9e5b",
        "OK_DARK": "#25864b",
        "WARN": "#e08b1f",
        "WARN_DARK": "#c4770f",
        "DANGER": "#d64545",
        "DANGER_DARK": "#b83a3a",
        "BTN_BG": "#e3e8f0",         # unauffaelliger Schalter
        "BTN_HOVER": "#d2d9e6",
        "BTN_TEXT": "#1b2430",
        "BTN_DISABLED": "#9aa3b0",
        "FIELD_BG": "#ffffff",       # Eingabefelder
        "TROUGH": "#e3e8f0",         # Rille von Schiebereglern
        "TAB_BG": "#e3e8f0",         # nicht gewaehlter Reiter
        "STATUS_BG": "#e4e8ef",
        "VIEWER_BG": "#2b3038",      # Flaeche hinter der Vorschau
        "VIEWER_TEXT": "#8b95a5",
    },
    "dark": {
        "BG": "#12161d",
        "CARD": "#1a1f28",
        "CARD_ALT": "#151a22",
        "BORDER": "#2c3441",
        "TEXT": "#e6eaf0",
        "MUTED": "#98a2b3",
        "HEADER": "#0e1218",
        "HEADER_TEXT": "#b8c2d0",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#6b7688",
        "HEADER_HOVER": "#212a38",
        "ACCENT": "#4a90e8",
        "ACCENT_DARK": "#3a7ad0",
        "ON_ACCENT": "#ffffff",
        "OK": "#3fb972",
        "OK_DARK": "#349b60",
        "WARN": "#e9a23b",
        "WARN_DARK": "#cc8a26",
        "DANGER": "#e05a5a",
        "DANGER_DARK": "#c44a4a",
        "BTN_BG": "#2a323f",
        "BTN_HOVER": "#353f4f",
        "BTN_TEXT": "#e6eaf0",
        "BTN_DISABLED": "#626c7a",
        "FIELD_BG": "#232b36",
        "TROUGH": "#2a323f",
        "TAB_BG": "#232b36",
        "STATUS_BG": "#0e1218",
        "VIEWER_BG": "#0d1014",
        "VIEWER_TEXT": "#7d8794",
    },
}

DEFAULT_THEME = "light"
CURRENT_THEME = DEFAULT_THEME


def apply_theme(name):
    """Farbwerte des gewaehlten Schemas in die Modulvariablen schreiben."""
    global CURRENT_THEME
    CURRENT_THEME = name if name in THEMES else DEFAULT_THEME
    globals().update(THEMES[CURRENT_THEME])


apply_theme(DEFAULT_THEME)      # legt BG, CARD, TEXT ... ueberhaupt erst an

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H1 = ("Segoe UI", 18, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 10)


# --------------------------------------------------------------------------
# Sprachumschaltung
#
# Wie in der Bild-Toolbox ist Deutsch die Quellsprache: im Code steht der
# deutsche Text, _("...") sucht ihn zur Laufzeit in der Sprachtabelle
# TRANSLATIONS (ganz unten in dieser Datei). Dort ist auch beschrieben, wie
# eine weitere Sprache dazukommt.
# --------------------------------------------------------------------------

SOURCE_LANGUAGE = "de"
CONFIG_NAME = "qr-code-generator.json"


class Translator:
    """Uebersetzt einen deutschen Quelltext in die eingestellte Sprache."""

    def __init__(self, language=SOURCE_LANGUAGE):
        self.language = language

    def __call__(self, text):
        if self.language == SOURCE_LANGUAGE:
            return text
        return TRANSLATIONS.get(self.language, {}).get(text, text)

    def available(self):
        """Sprachkuerzel -> Anzeigename, Quellsprache immer zuerst."""
        names = {SOURCE_LANGUAGE: LANGUAGE_NAMES[SOURCE_LANGUAGE]}
        for code in TRANSLATIONS:
            names[code] = LANGUAGE_NAMES.get(code, code)
        return names


_ = Translator()


def ist_eingefroren() -> bool:
    """Laeuft das Programm als gebuendelte EXE (PyInstaller & Co.)?"""
    return getattr(sys, "frozen", False)


def programm_ordner() -> str:
    """Ordner, in dem das Programm fuer den Anwender sichtbar liegt.

    Als PyInstaller-EXE mit --onefile entpackt sich das Programm in einen
    temporaeren Ordner (sys._MEIPASS), den PyInstaller beim Beenden wieder
    loescht - __file__ zeigt dorthin. Alles, was den Programmlauf ueberdauern
    soll, gehoert deshalb neben die EXE und nicht neben __file__.
    """
    if ist_eingefroren():
        return os.path.dirname(os.path.abspath(sys.executable))
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:                       # z. B. interaktive Eingabe
        return os.path.expanduser("~")


def config_path():
    """Ablageort der Einstellungen - neben dem Programm."""
    return os.path.join(programm_ordner(), CONFIG_NAME)


def paket_version(modul, verteilung: str) -> str:
    """Versionsnummer einer geladenen Bibliothek, so gut es geht.

    Nicht jedes Paket fuehrt ein __version__ (qrcode hat es ab Fassung 8
    abgelegt), deshalb zusaetzlich der Umweg ueber die Paketdaten. In einer
    gebuendelten EXE stecken diese Daten nur dann mit drin, wenn beim Bauen
    --copy-metadata angegeben wurde; sonst bleibt die Nummer eben leer.
    """
    fassung = getattr(modul, "__version__", "")
    if fassung:
        return str(fassung)
    try:
        from importlib.metadata import PackageNotFoundError, version
        return version(verteilung)
    except (ImportError, PackageNotFoundError, ValueError):
        return ""


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as datei:
            daten = json.load(datei)
        return daten if isinstance(daten, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(daten):
    try:
        with open(config_path(), "w", encoding="utf-8") as datei:
            json.dump(daten, datei, indent=2)
        return True
    except OSError:
        return False


def detect_language():
    """Sprache des Betriebssystems, falls dafuer eine Tabelle vorliegt."""
    try:
        locale.setlocale(locale.LC_CTYPE, "")
        code = (locale.getlocale()[0] or "").lower()
    except (locale.Error, ValueError):
        code = ""
    bekannt = {SOURCE_LANGUAGE, *TRANSLATIONS}
    kurz = code.split("_")[0]
    if kurz in bekannt:
        return kurz
    for name, sprache in (("german", "de"), ("deutsch", "de"), ("english", "en")):
        if kurz.startswith(name) and sprache in bekannt:
            return sprache
    return SOURCE_LANGUAGE


def startup_language():
    """Gespeicherte Sprache, sonst die des Betriebssystems."""
    gespeichert = load_config().get("language")
    if gespeichert and (gespeichert == SOURCE_LANGUAGE or gespeichert in TRANSLATIONS):
        return gespeichert
    return detect_language()


def startup_theme():
    """Gespeichertes Farbschema, sonst das helle."""
    gespeichert = load_config().get("theme")
    return gespeichert if gespeichert in THEMES else DEFAULT_THEME


# --------------------------------------------------------------------------
# Format- und Optionstabellen
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Format:
    """Beschreibt ein Ausgabeformat und seine Faehigkeiten."""

    name: str
    endung: str
    beschreibung: str
    vektor: bool = False          # aufloesungsunabhaengig, Groesse = Grundmass
    alpha: bool = False           # echte Transparenz moeglich
    max_kante: int | None = None  # harte Groessengrenze des Formats
    pillow_name: str = ""         # Formatkuerzel fuer Image.save()


FORMATE: dict[str, Format] = {
    "PNG":  Format("PNG",  ".png",  "Verlustfrei mit Transparenz - Standard für Web und Druck",
                   alpha=True, pillow_name="PNG"),
    "SVG":  Format("SVG",  ".svg",  "Vektor, beliebig skalierbar - ideal für Druck und Layout",
                   vektor=True, alpha=True),
    "JPEG": Format("JPEG", ".jpg",  "Komprimiert, keine Transparenz - für Fotoworkflows",
                   pillow_name="JPEG"),
    "WEBP": Format("WEBP", ".webp", "Kompakt mit Transparenz - für moderne Webseiten",
                   alpha=True, pillow_name="WEBP"),
    "TIFF": Format("TIFF", ".tif",  "Verlustfrei mit DPI-Angabe - für die Druckvorstufe",
                   alpha=True, pillow_name="TIFF"),
    "BMP":  Format("BMP",  ".bmp",  "Unkomprimiert und sehr einfach - für ältere Software",
                   pillow_name="BMP"),
    "GIF":  Format("GIF",  ".gif",  "Indizierte Farben - Hintergrund wird immer gefüllt",
                   pillow_name="GIF"),
    "ICO":  Format("ICO",  ".ico",  "Windows-Symboldatei - maximal 256 Pixel",
                   alpha=True, max_kante=256, pillow_name="ICO"),
    "PDF":  Format("PDF",  ".pdf",  "Druckfertige Seite mit DPI-Angabe",
                   pillow_name="PDF"),
    "EPS":  Format("EPS",  ".eps",  "PostScript für klassische Druckereien",
                   pillow_name="EPS"),
}

# Reihenfolge fuer Auswahlfelder und Hilfetexte
FORMAT_REIHENFOLGE = list(FORMATE)

# Endung -> Format, damit "ziel.svg" das Format automatisch bestimmt
ENDUNG_ZU_FORMAT = {f.endung: name for name, f in FORMATE.items()}
ENDUNG_ZU_FORMAT[".jpeg"] = "JPEG"
ENDUNG_ZU_FORMAT[".tiff"] = "TIFF"

FEHLERKORREKTUR = {
    "L": (ERROR_CORRECT_L, "L - niedrig (ca. 7 % wiederherstellbar)"),
    "M": (ERROR_CORRECT_M, "M - mittel (ca. 15 %)"),
    "Q": (ERROR_CORRECT_Q, "Q - hoch (ca. 25 %)"),
    "H": (ERROR_CORRECT_H, "H - sehr hoch (ca. 30 %, für Logos und Aufkleber)"),
}

GROESSEN_VORGABEN = [128, 256, 512, 1024, 2048, 4096]

MIN_KANTE = 32
MAX_KANTE = 10000


# --------------------------------------------------------------------------
# Optionen
# --------------------------------------------------------------------------

@dataclass
class QROptionen:
    """Alle Einstellungen, die einen QR-Code und seine Bilddatei bestimmen."""

    format: str = "PNG"
    groesse: int = 512                  # Kantenlaenge in Pixel (bei SVG: Grundmass)
    fehlerkorrektur: str = "M"
    rand: int = 4                       # Ruhezone in Modulen (Norm: mindestens 4)
    vordergrund: str = "#000000"
    hintergrund: str = "#FFFFFF"
    transparent: bool = False
    version: int | None = None          # None = automatisch passende Version
    dpi: int = 300
    qualitaet: int = 95                 # nur JPEG und WEBP

    def format_info(self) -> Format:
        return FORMATE[self.format]


class QRFehler(Exception):
    """Fehler, der dem Anwender im Klartext gezeigt werden kann."""


# --------------------------------------------------------------------------
# Pruefung und Normalisierung
# --------------------------------------------------------------------------

def farbe_pruefen(farbe: str, bezeichnung: str) -> tuple[int, int, int]:
    """Wandelt eine Farbangabe in RGB um oder meldet einen verstaendlichen Fehler."""
    if HAS_PIL:
        try:
            rgb = ImageColor.getrgb(farbe)
        except ValueError as exc:
            raise QRFehler(_("{feld} nicht lesbar: {wert}").format(
                feld=_(bezeichnung), wert=farbe)) from exc
        return rgb[:3]

    treffer = re.fullmatch(r"#?([0-9a-fA-F]{6})", farbe.strip())
    if not treffer:
        raise QRFehler(_("{feld} nicht lesbar: {wert}").format(feld=_(bezeichnung), wert=farbe))
    wert = treffer.group(1)
    return (int(wert[0:2], 16), int(wert[2:4], 16), int(wert[4:6], 16))


def optionen_pruefen(opts: QROptionen) -> QROptionen:
    """Prueft die Optionen, begrenzt sie aufs Machbare und liefert sie normalisiert."""
    if opts.format not in FORMATE:
        raise QRFehler(_("Unbekanntes Format: {wert}").format(wert=opts.format))
    if opts.fehlerkorrektur not in FEHLERKORREKTUR:
        raise QRFehler(_("Unbekannte Fehlerkorrektur: {wert}").format(wert=opts.fehlerkorrektur))
    if not MIN_KANTE <= opts.groesse <= MAX_KANTE:
        raise QRFehler(_("Größe muss zwischen {min} und {max} Pixel liegen.").format(
            min=MIN_KANTE, max=MAX_KANTE))
    if not 0 <= opts.rand <= 32:
        raise QRFehler(_("Rand muss zwischen 0 und 32 Modulen liegen."))
    if opts.version is not None and not 1 <= opts.version <= 40:
        raise QRFehler(_("Version muss zwischen 1 und 40 liegen."))
    if not 1 <= opts.qualitaet <= 100:
        raise QRFehler(_("Qualität muss zwischen 1 und 100 liegen."))

    farbe_pruefen(opts.vordergrund, "Vordergrundfarbe")
    farbe_pruefen(opts.hintergrund, "Hintergrundfarbe")

    info = FORMATE[opts.format]
    groesse = opts.groesse
    if info.max_kante and groesse > info.max_kante:
        groesse = info.max_kante

    return replace(opts, groesse=groesse, transparent=opts.transparent and info.alpha)


def anpassungen_beschreiben(gewuenscht: QROptionen, geprueft: QROptionen) -> list[str]:
    """Nennt, was optionen_pruefen() am Wunsch des Anwenders anpassen musste.

    optionen_pruefen() begrenzt stillschweigend aufs Machbare - ein ICO wird
    nie groesser als 256 Pixel, ein GIF nie durchsichtig. Damit Oberflaeche und
    Kommandozeile das gleichlautend erklaeren koennen, steht die Beschreibung
    hier an einer einzigen Stelle.
    """
    hinweise = []
    if gewuenscht.groesse != geprueft.groesse:
        hinweise.append(_("{format} erlaubt höchstens {kante} px - Größe angepasst.").format(
            format=geprueft.format, kante=geprueft.groesse))
    if gewuenscht.transparent and not geprueft.transparent:
        hinweise.append(_("{format} kennt keine Transparenz - Hintergrund wird gefüllt.").format(
            format=geprueft.format))
    return hinweise


def kontrast_warnung(opts: QROptionen) -> str | None:
    """Warnt, wenn Vorder- und Hintergrund zu aehnlich zum Scannen sind."""
    vg = farbe_pruefen(opts.vordergrund, "Vordergrundfarbe")
    hg = farbe_pruefen(opts.hintergrund, "Hintergrundfarbe")

    def helligkeit(rgb: tuple[int, int, int]) -> float:
        return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255

    hell_vg, hell_hg = helligkeit(vg), helligkeit(hg)
    verhaeltnis = (max(hell_vg, hell_hg) + 0.05) / (min(hell_vg, hell_hg) + 0.05)

    if hell_vg > hell_hg:
        return _("Der Vordergrund ist heller als der Hintergrund - die meisten Lesegeräte "
                 "erwarten dunkle Module auf hellem Grund.")
    if verhaeltnis < 3.0:
        return _("Zu wenig Kontrast ({wert}:1) - der Code ist kaum lesbar.").format(
            wert=f"{verhaeltnis:.1f}")
    if verhaeltnis < 7.0:
        return _("Geringer Kontrast ({wert}:1) - bitte vor dem Druck testen.").format(
            wert=f"{verhaeltnis:.1f}")
    return None


# --------------------------------------------------------------------------
# QR-Matrix
# --------------------------------------------------------------------------

@dataclass
class QRErgebnis:
    """Das fertige Modulraster samt Kennzahlen fuer die Anzeige."""

    matrix: list[list[bool]] = field(repr=False)
    version: int = 1
    module: int = 21            # Kantenlaenge in Modulen einschliesslich Rand
    zeichen: int = 0


def matrix_erzeugen(text: str, opts: QROptionen) -> QRErgebnis:
    """Kodiert den Text und liefert das Modulraster einschliesslich Ruhezone."""
    if not HAS_QRCODE:
        raise QRFehler(_("Das Paket 'qrcode' fehlt. Installation:  pip install qrcode Pillow"))
    if not text:
        raise QRFehler(_("Es wurde kein Inhalt angegeben."))

    qr = qrcode.QRCode(
        version=opts.version,
        error_correction=FEHLERKORREKTUR[opts.fehlerkorrektur][0],
        box_size=1,
        border=opts.rand,
    )
    qr.add_data(text)
    try:
        qr.make(fit=opts.version is None)
    except (qrcode.exceptions.DataOverflowError, ValueError) as exc:
        # ValueError kommt aus der automatischen Versionssuche, wenn selbst
        # Version 40 den Inhalt nicht mehr fasst.
        if opts.version is not None:
            raise QRFehler(
                _("Der Inhalt passt nicht in Version {version} bei Fehlerkorrektur {stufe}. "
                  "Bitte eine höhere Version oder 'automatisch' wählen.").format(
                    version=opts.version, stufe=opts.fehlerkorrektur)) from exc
        raise QRFehler(
            _("Der Inhalt ist zu lang für einen QR-Code. Eine niedrigere Fehlerkorrektur "
              "(z. B. L) schafft etwas Platz, sonst bitte den Text kürzen.")) from exc

    matrix = [[bool(zelle) for zelle in zeile] for zeile in qr.get_matrix()]
    return QRErgebnis(matrix=matrix, version=qr.version, module=len(matrix), zeichen=len(text))


# --------------------------------------------------------------------------
# Rasterbild
# --------------------------------------------------------------------------

def modulgroesse_bestimmen(module: int, zielkante: int) -> int:
    """Groesstes ganzzahliges Modulmass, das noch in die Zielkante passt."""
    return max(1, zielkante // module)


def _module_laufweise(matrix: list[list[bool]]):
    """Liefert je Zeile die zusammenhaengenden Modulketten als (y, start, breite).

    Zusammenhaengende Module in einem Zug zu zeichnen ist deutlich schneller als
    Modul fuer Modul und ergibt exakt dasselbe Bild.
    """
    for y, zeile in enumerate(matrix):
        breite_gesamt = len(zeile)
        x = 0
        while x < breite_gesamt:
            if not zeile[x]:
                x += 1
                continue
            start = x
            while x < breite_gesamt and zeile[x]:
                x += 1
            yield y, start, x - start


def bild_erzeugen(ergebnis: QRErgebnis, opts: QROptionen) -> Image.Image:
    """Zeichnet das Modulraster als RGBA-Bild in der gewuenschten Kantenlaenge."""
    if not HAS_PIL:
        raise QRFehler(_("Das Paket 'Pillow' fehlt. Installation:  pip install Pillow"))

    module = ergebnis.module
    kasten = modulgroesse_bestimmen(module, opts.groesse)
    rohkante = kasten * module

    vg = farbe_pruefen(opts.vordergrund, "Vordergrundfarbe") + (255,)
    hg = farbe_pruefen(opts.hintergrund, "Hintergrundfarbe") + (0 if opts.transparent else 255,)

    bild = Image.new("RGBA", (rohkante, rohkante), hg)
    zeichner = ImageDraw.Draw(bild)
    for y, start, breite in _module_laufweise(ergebnis.matrix):
        zeichner.rectangle(
            [start * kasten, y * kasten, (start + breite) * kasten - 1, (y + 1) * kasten - 1],
            fill=vg,
        )

    if rohkante != opts.groesse:
        # Nearest-Neighbour haelt die Modulkanten hart; Weichzeichnen wuerde die
        # Lesbarkeit auf kleinen Displays verschlechtern.
        bild = bild.resize((opts.groesse, opts.groesse), Image.NEAREST)

    return bild


def bild_fuer_format(bild: Image.Image, opts: QROptionen) -> Image.Image:
    """Passt Farbmodus und Transparenz an das Zielformat an."""
    info = opts.format_info()

    if info.alpha and opts.transparent:
        return bild if bild.mode == "RGBA" else bild.convert("RGBA")

    grund = Image.new(
        "RGBA", bild.size, farbe_pruefen(opts.hintergrund, "Hintergrundfarbe") + (255,)
    )
    flach = Image.alpha_composite(grund, bild.convert("RGBA"))

    if info.name == "GIF":
        return flach.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=16)
    return flach if info.alpha else flach.convert("RGB")


def speicherargumente(opts: QROptionen) -> dict:
    """Formatabhaengige Zusatzangaben fuer Image.save()."""
    info = opts.format_info()
    args: dict = {"format": info.pillow_name}

    if info.name in ("JPEG", "WEBP"):
        args["quality"] = opts.qualitaet
    if info.name == "JPEG":
        args["subsampling"] = 0          # keine Farbunterabtastung -> scharfe Kanten
        args["optimize"] = True
    if info.name == "PNG":
        args["optimize"] = True
        args["dpi"] = (opts.dpi, opts.dpi)
    if info.name == "TIFF":
        args["dpi"] = (opts.dpi, opts.dpi)
        args["compression"] = "tiff_lzw"
    if info.name == "PDF":
        args["resolution"] = float(opts.dpi)
    if info.name == "ICO":
        args["sizes"] = [(opts.groesse, opts.groesse)]
    return args


# --------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------

def svg_erzeugen(ergebnis: QRErgebnis, opts: QROptionen) -> str:
    """Baut ein SVG mit einem einzigen Pfad - klein, sauber, beliebig skalierbar."""
    module = ergebnis.module
    pfad = "".join(
        f"M{start} {y}h{breite}v1h-{breite}z"
        for y, start, breite in _module_laufweise(ergebnis.matrix)
    )
    hintergrund = (
        ""
        if opts.transparent
        else f'<rect width="{module}" height="{module}" fill="{opts.hintergrund}"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{opts.groesse}" '
        f'height="{opts.groesse}" viewBox="0 0 {module} {module}" '
        f'shape-rendering="crispEdges" role="img" aria-label="QR-Code">\n'
        f'  <desc>{PROGRAMM} {VERSION}</desc>\n'
        f'  {hintergrund}\n'
        f'  <path d="{pfad}" fill="{opts.vordergrund}"/>\n'
        '</svg>\n'
    )


# --------------------------------------------------------------------------
# Speichern
# --------------------------------------------------------------------------

def format_aus_pfad(pfad: str) -> str | None:
    """Ermittelt das Format anhand der Dateiendung, falls sie bekannt ist."""
    return ENDUNG_ZU_FORMAT.get(os.path.splitext(pfad)[1].lower())


def endung_ergaenzen(pfad: str, info: Format) -> str:
    """Haengt die Formatendung an, sofern nicht bereits eine passende vorhanden ist.

    Geprueft wird gegen die bekannten Endungen und nicht nur auf 'irgendein Punkt' -
    sonst wuerde ein Name wie 'mailto_info_example.org' als bereits vollstaendig gelten.
    """
    return pfad if format_aus_pfad(pfad) == info.name else pfad + info.endung


def dateiname_vorschlagen(text: str, nummer: int | None = None) -> str:
    """Leitet aus dem Inhalt einen kurzen, dateisystemtauglichen Namen ab."""
    kern = text.strip().splitlines()[0] if text.strip() else "qr"
    kern = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", kern)      # Schema entfernen
    kern = re.sub(r"[^\w\s.-]", "_", kern, flags=re.UNICODE)
    kern = re.sub(r"[\s_]+", "_", kern).strip("._-")
    kern = kern[:48] or "qr"
    if kern.upper() in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"(COM|LPT)\d", kern.upper()):
        kern = f"qr_{kern}"                                       # unter Windows gesperrt
    return f"{kern}_{nummer:03d}" if nummer is not None else kern


def qr_speichern(text: str, ziel: str, opts: QROptionen) -> tuple[str, QRErgebnis]:
    """Erzeugt den QR-Code fuer 'text' und schreibt ihn nach 'ziel'.

    Fehlende Verzeichnisse werden angelegt. Rueckgabe ist der tatsaechlich
    geschriebene Pfad (mit korrekter Endung) samt Kennzahlen des Codes.
    """
    opts = optionen_pruefen(opts)
    info = opts.format_info()
    ziel = endung_ergaenzen(ziel, info)

    ordner = os.path.dirname(os.path.abspath(ziel))
    os.makedirs(ordner, exist_ok=True)

    ergebnis = matrix_erzeugen(text, opts)

    if info.vektor:
        with open(ziel, "w", encoding="utf-8") as datei:
            datei.write(svg_erzeugen(ergebnis, opts))
    else:
        bild = bild_fuer_format(bild_erzeugen(ergebnis, opts), opts)
        bild.save(ziel, **speicherargumente(opts))

    return ziel, ergebnis


# --------------------------------------------------------------------------
# Stapelverarbeitung
# --------------------------------------------------------------------------

def stapel_eintraege_lesen(pfad: str) -> list[tuple[str, str | None]]:
    """Liest eine Stapeldatei: je Zeile ein Inhalt, optional 'Inhalt | Dateiname'.

    Leerzeilen und Zeilen, die mit '#' beginnen, werden uebersprungen.
    """
    try:
        with open(pfad, encoding="utf-8-sig") as datei:
            zeilen = datei.read().splitlines()
    except OSError as exc:
        raise QRFehler(_("Stapeldatei nicht lesbar: {fehler}").format(fehler=exc)) from exc

    eintraege: list[tuple[str, str | None]] = []
    for zeile in zeilen:
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#"):
            continue
        if "|" in zeile:
            inhalt, _trenner, name = zeile.partition("|")
            eintraege.append((inhalt.strip(), name.strip() or None))
        else:
            eintraege.append((zeile, None))

    if not eintraege:
        raise QRFehler(
            _("Die Stapeldatei enthält keine verwertbaren Zeilen: {pfad}").format(pfad=pfad))
    return eintraege


# --------------------------------------------------------------------------
# Kommandozeile
# --------------------------------------------------------------------------

def argumente_parser() -> argparse.ArgumentParser:
    formate = ", ".join(FORMAT_REIHENFOLGE)
    parser = argparse.ArgumentParser(
        prog="qr_generator.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{PROGRAMM} {VERSION} - " + _("QR-Codes aus Text erzeugen und speichern."),
        epilog=_(
            "Beispiele:\n"
            '  qr_generator.py                                  Oberfläche starten\n'
            '  qr_generator.py "https://example.org"            PNG 512 px im aktuellen Ordner\n'
            '  qr_generator.py "Hallo Welt" -o hallo.svg        Format aus der Endung\n'
            '  qr_generator.py "Text" -f PNG -s 1024 -e H       Größe und Fehlerkorrektur\n'
            '  qr_generator.py "Text" -f PNG -s 256 --transparent\n'
            "  qr_generator.py --datei inhalt.txt -o code.png   Inhalt aus einer Textdatei\n"
            '  echo "Text" | qr_generator.py - -o code.png      Inhalt aus der Pipeline\n'
            "  qr_generator.py --stapel liste.txt -a ausgabe -f SVG\n"
        ),
    )
    parser.add_argument("text", nargs="?",
                        help=_('Inhalt des QR-Codes; "-" liest von der Standardeingabe'))
    parser.add_argument("--datei", metavar="PFAD",
                        help=_("Inhalt aus einer Textdatei lesen (UTF-8)"))
    parser.add_argument("--stapel", metavar="PFAD",
                        help=_("Stapeldatei: je Zeile ein Code, optional 'Inhalt | Dateiname'"))

    ausgabe = parser.add_argument_group(_("Ausgabe"))
    ausgabe.add_argument("-o", "--ausgabe", metavar="PFAD",
                         help=_("Zieldatei (ohne Endung wird die des Formats ergänzt)"))
    ausgabe.add_argument("-a", "--ausgabeordner", metavar="ORDNER", default=".",
                         help=_("Zielordner, wenn kein Dateiname angegeben ist (Vorgabe: .)"))
    ausgabe.add_argument("-f", "--format", default=None, metavar="FORMAT",
                         type=lambda w: w.strip().upper(),
                         choices=FORMAT_REIHENFOLGE,
                         help=_("Ausgabeformat: {formate} (Vorgabe: PNG bzw. aus der Endung)"
                                ).format(formate=formate))
    ausgabe.add_argument("-s", "--groesse", type=int, default=512, metavar="PIXEL",
                         help=_("Kantenlänge in Pixel, {min}-{max} (Vorgabe: 512)").format(
                             min=MIN_KANTE, max=MAX_KANTE))
    ausgabe.add_argument("--dpi", type=int, default=300,
                         help=_("Auflösungsangabe für PNG/TIFF/PDF (Vorgabe: 300)"))
    ausgabe.add_argument("--qualitaet", type=int, default=95, metavar="1-100",
                         help=_("Kompressionsqualität für JPEG und WEBP (Vorgabe: 95)"))
    ausgabe.add_argument("--ueberschreiben", action="store_true",
                         help=_("vorhandene Dateien ersetzen statt zu nummerieren"))

    gestaltung = parser.add_argument_group(_("Gestaltung"))
    gestaltung.add_argument("-e", "--fehlerkorrektur", default="M", choices=list(FEHLERKORREKTUR),
                            type=lambda w: w.strip().upper(),
                            help=_("Fehlerkorrektur L/M/Q/H (Vorgabe: M)"))
    gestaltung.add_argument("-r", "--rand", type=int, default=4, metavar="MODULE",
                            help=_("Ruhezone in Modulen, Norm ist 4 (Vorgabe: 4)"))
    gestaltung.add_argument("--vordergrund", default="#000000", metavar="FARBE",
                            help=_('Modulfarbe, z. B. "#000000" oder "black"'))
    gestaltung.add_argument("--hintergrund", default="#FFFFFF", metavar="FARBE",
                            help=_('Hintergrundfarbe (Vorgabe: "#FFFFFF")'))
    gestaltung.add_argument("--transparent", action="store_true",
                            help=_("transparenter Hintergrund (PNG, SVG, WEBP, TIFF, ICO)"))
    gestaltung.add_argument("--qr-version", type=int, default=None, metavar="1-40",
                            help=_("feste QR-Version erzwingen (Vorgabe: automatisch)"))

    sonstiges = parser.add_argument_group(_("Sonstiges"))
    sonstiges.add_argument("--formate", action="store_true",
                           help=_("unterstützte Formate auflisten und beenden"))
    sonstiges.add_argument("--gui", action="store_true",
                           help=_("Oberfläche starten, auch wenn Argumente angegeben sind"))
    sonstiges.add_argument("--sprache", metavar="KÜRZEL", default=None,
                           help=_("Sprache der Ausgabe, z. B. de oder en"))
    sonstiges.add_argument("-q", "--still", action="store_true",
                           help=_("keine Statusmeldungen ausgeben"))
    sonstiges.add_argument("--version", action="version", version=f"{PROGRAMM} {VERSION}")
    return parser


def formate_auflisten() -> None:
    print(f"{PROGRAMM} {VERSION} - " + _("unterstützte Formate") + "\n")
    print(f"{_('Format'):<7} {_('Endung'):<7} {_('Transparenz'):<12} {_('Beschreibung')}")
    print("-" * 78)
    for name in FORMAT_REIHENFOLGE:
        info = FORMATE[name]
        alpha = _("ja") if info.alpha else _("nein")
        grenze = ""
        if info.max_kante:
            grenze = " " + _("(max. {kante} px)").format(kante=info.max_kante)
        print(f"{info.name:<7} {info.endung:<7} {alpha:<12} {_(info.beschreibung)}{grenze}")
    print("\n" + _("Fehlerkorrektur:"))
    for kuerzel, (_stufe, text) in FEHLERKORREKTUR.items():
        print(f"  {kuerzel}  {_(text)}")


def text_einlesen(args: argparse.Namespace) -> str:
    """Ermittelt den Inhalt aus Argument, Datei oder Standardeingabe."""
    if args.datei:
        try:
            with open(args.datei, encoding="utf-8-sig") as datei:
                return datei.read().strip()
        except OSError as exc:
            raise QRFehler(_("Datei nicht lesbar: {fehler}").format(fehler=exc)) from exc
    if args.text == "-":
        return sys.stdin.read().strip()
    return (args.text or "").strip()


def freier_pfad(pfad: str) -> str:
    """Haengt bei Bedarf eine Nummer an, damit nichts ueberschrieben wird."""
    if not os.path.exists(pfad):
        return pfad
    stamm, endung = os.path.splitext(pfad)
    nummer = 2
    while os.path.exists(f"{stamm}_{nummer}{endung}"):
        nummer += 1
    return f"{stamm}_{nummer}{endung}"


def cli_main(args: argparse.Namespace) -> int:
    if args.formate:
        formate_auflisten()
        return 0

    endungsformat = format_aus_pfad(args.ausgabe) if args.ausgabe else None
    formatname = args.format or endungsformat or "PNG"
    gewuenscht = QROptionen(
        format=formatname,
        groesse=args.groesse,
        fehlerkorrektur=args.fehlerkorrektur,
        rand=args.rand,
        vordergrund=args.vordergrund,
        hintergrund=args.hintergrund,
        transparent=args.transparent,
        version=args.qr_version,
        dpi=args.dpi,
        qualitaet=args.qualitaet,
    )
    opts = optionen_pruefen(gewuenscht)

    def melden(zeile: str) -> None:
        if not args.still:
            print(zeile)

    for hinweis in anpassungen_beschreiben(gewuenscht, opts):
        melden(_("Hinweis: {text}").format(text=hinweis))
    if endungsformat and args.format and endungsformat != args.format:
        melden(_("Hinweis: --format {format} hat Vorrang vor der Endung der Zieldatei "
                 "({endung}).").format(format=args.format, endung=endungsformat))
    warnung = kontrast_warnung(opts)
    if warnung:
        melden(_("Hinweis: {text}").format(text=warnung))

    if args.stapel:
        eintraege = stapel_eintraege_lesen(args.stapel)
        breite = len(str(len(eintraege)))
        fehler = 0
        for nummer, (inhalt, name) in enumerate(eintraege, start=1):
            name = name or dateiname_vorschlagen(inhalt, nummer)
            ziel = endung_ergaenzen(os.path.join(args.ausgabeordner, name), opts.format_info())
            if not args.ueberschreiben:
                ziel = freier_pfad(ziel)
            try:
                pfad, ergebnis = qr_speichern(inhalt, ziel, opts)
            except QRFehler as exc:
                fehler += 1
                print(f"[{nummer:>{breite}}/{len(eintraege)}] " +
                      _("Fehler: {text}").format(text=exc), file=sys.stderr)
                continue
            melden(f"[{nummer:>{breite}}/{len(eintraege)}] {pfad}  " +
                   _("(Version {version}, {module} Module)").format(
                       version=ergebnis.version, module=ergebnis.module))
        melden("\n" + _("Fertig: {gut} von {gesamt} Dateien geschrieben.").format(
            gut=len(eintraege) - fehler, gesamt=len(eintraege)))
        return 1 if fehler else 0

    text = text_einlesen(args)
    if not text:
        raise QRFehler(_("Kein Inhalt angegeben. Hilfe mit --help, Oberfläche mit --gui."))

    ziel = endung_ergaenzen(
        args.ausgabe or os.path.join(args.ausgabeordner, dateiname_vorschlagen(text)),
        opts.format_info(),
    )
    if not args.ueberschreiben:
        ziel = freier_pfad(ziel)

    pfad, ergebnis = qr_speichern(text, ziel, opts)
    melden(
        _("Gespeichert: {pfad}").format(pfad=os.path.abspath(pfad)) + "\n  " +
        _("Format {format}, {kante} px, Version {version} ({module} Module), "
          "Fehlerkorrektur {stufe}, {zeichen} Zeichen").format(
            format=opts.format, kante=opts.groesse, version=ergebnis.version,
            module=ergebnis.module, stufe=opts.fehlerkorrektur, zeichen=ergebnis.zeichen)
    )
    return 0


# --------------------------------------------------------------------------
# Wiederverwendbare Widgets
#
# Aufbau und Benennung entsprechen der Bild-Toolbox. Zusaetzlich merkt sich
# faerben() zu jedem Widget, welche Rolle seine Farben haben ("CARD", "TEXT",
# ...). Ein Wechsel des Farbschemas faerbt die vorhandenen Widgets dadurch nur
# um, statt die Oberflaeche neu aufzubauen - nichts blinkt, nichts springt.
# --------------------------------------------------------------------------

# Wird von widgets_bereitstellen() belegt, sobald Tkinter geladen ist.
FlatButton = None

# (Widget, Rollen) - Rollen ist None bei Widgets, die sich selbst umfaerben.
GEFAERBTE_WIDGETS: list = []


def faerben(widget, **rollen):
    """Widget einfaerben und die Farbrollen fuer spaeteres Umfaerben merken.

    Beispiel:  faerben(label, bg="CARD", fg="TEXT")
    """
    GEFAERBTE_WIDGETS.append((widget, rollen))
    widget.configure(**{option: THEMES[CURRENT_THEME][name] for option, name in rollen.items()})
    return widget


def farben_auffrischen():
    """Alle gemerkten Widgets auf die aktuelle Palette umstellen.

    Zerstoerte Widgets fallen dabei aus der Liste heraus; Tk meldet sie mit
    einem TclError, was hier das Aufraeumkriterium ist.
    """
    palette = THEMES[CURRENT_THEME]
    uebrig = []
    for widget, rollen in GEFAERBTE_WIDGETS:
        try:
            if rollen is None:
                widget.neu_faerben()
            else:
                widget.configure(**{opt: palette[name] for opt, name in rollen.items()})
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((widget, rollen))
    GEFAERBTE_WIDGETS[:] = uebrig


def widgets_bereitstellen():
    """Definiert die Widget-Klassen, sobald Tkinter geladen ist."""
    global FlatButton

    class _FlatButton(_tk.Button):
        """Flacher Button mit Hover-Effekt in vier Farbvarianten."""

        @staticmethod
        def styles():
            """Farbvarianten - erst beim Aufruf gelesen, damit das Schema stimmt."""
            return {
                "primary":   (ACCENT, ACCENT_DARK, ON_ACCENT),
                "secondary": (BTN_BG, BTN_HOVER, BTN_TEXT),
                "success":   (OK, OK_DARK, ON_ACCENT),
                "warn":      (WARN, WARN_DARK, ON_ACCENT),
                "danger":    (DANGER, DANGER_DARK, ON_ACCENT),
            }

        def __init__(self, parent, text, command=None, kind="secondary", **kw):
            kw.setdefault("padx", 14)
            kw.setdefault("pady", 6)
            super().__init__(parent, text=text, command=command, relief="flat", bd=0,
                             highlightthickness=0, cursor="hand2", font=FONT_SMALL, **kw)
            self._kind = kind
            self.neu_faerben()
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            GEFAERBTE_WIDGETS.append((self, None))       # faerbt sich selbst

        def neu_faerben(self):
            """Farben der eigenen Variante aus der aktuellen Palette holen."""
            styles = self.styles()
            bg, hover, fg = styles.get(self._kind, styles["secondary"])
            self._bg, self._hover = bg, hover
            self.configure(bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                           disabledforeground=BTN_DISABLED)

        def _enabled(self):
            return str(self["state"]) != "disabled"

        def _on_enter(self, _e):
            if self._enabled():
                self.configure(bg=self._hover)

        def _on_leave(self, _e):
            self.configure(bg=self._bg)

    FlatButton = _FlatButton


def make_card(parent, **pack_kw):
    """Karte mit dünnem Rahmen."""
    card = faerben(_tk.Frame(parent, highlightthickness=1),
                   bg="CARD", highlightbackground="BORDER", highlightcolor="BORDER")
    if pack_kw:
        card.pack(**pack_kw)
    return card


def card_title(parent, text):
    etikett = faerben(_tk.Label(parent, text=text, font=FONT_BOLD, anchor="w"),
                      bg="CARD", fg="TEXT")
    etikett.pack(fill="x", padx=14, pady=(12, 6))
    return etikett


def card_text(parent, text, rolle="MUTED", font=None):
    """Fliesstext in einer Karte."""
    etikett = faerben(
        _tk.Label(parent, text=text, font=font or FONT_SMALL, justify="left",
                  anchor="w", wraplength=760),
        bg="CARD", fg=rolle)
    etikett.pack(fill="x", padx=14, pady=(0, 10))
    return etikett


class ScrollBereich:
    """Senkrecht scrollbarer Bereich - der Inhalt kommt in .innen."""

    def __init__(self, eltern, hoehe):
        tk, ttk = _tk, _ttk
        self.aussen = faerben(tk.Frame(eltern), bg="BG")
        self.leinwand = faerben(
            tk.Canvas(self.aussen, highlightthickness=0, bd=0, height=hoehe), bg="BG")
        self.rolle = ttk.Scrollbar(self.aussen, orient="vertical", command=self.leinwand.yview)
        self.innen = faerben(tk.Frame(self.leinwand), bg="BG")

        self._fenster = self.leinwand.create_window((0, 0), window=self.innen, anchor="nw")
        self.leinwand.configure(yscrollcommand=self.rolle.set)
        self.leinwand.pack(side="left", fill="both", expand=True)
        self.rolle.pack(side="right", fill="y")

        self.innen.bind("<Configure>", self._inhalt_geaendert)
        self.leinwand.bind("<Configure>", self._flaeche_geaendert)
        # Mausrad nur, solange der Zeiger ueber diesem Bereich steht
        self.leinwand.bind("<Enter>", lambda _e: self.leinwand.bind_all("<MouseWheel>", self._rad))
        self.leinwand.bind("<Leave>", lambda _e: self.leinwand.unbind_all("<MouseWheel>"))

    def pack(self, **kw):
        self.aussen.pack(**kw)
        return self.aussen

    def _inhalt_geaendert(self, _e=None):
        self.leinwand.configure(scrollregion=self.leinwand.bbox("all"))

    def _flaeche_geaendert(self, ereignis):
        self.leinwand.itemconfigure(self._fenster, width=ereignis.width)

    def _rad(self, ereignis):
        oben, unten = self.leinwand.yview()
        if oben <= 0.0 and unten >= 1.0:            # nichts zu scrollen
            return
        self.leinwand.yview_scroll(int(-ereignis.delta / 120), "units")


# --------------------------------------------------------------------------
# Grafische Oberflaeche
# --------------------------------------------------------------------------

VORSCHAU_KANTE = 300


class QRApp:
    """Hauptfenster mit den Reitern QR-Code, Erklärungen und Info."""

    def __init__(self, master, start: QROptionen | None = None, starttext: str = "") -> None:
        self.master = master
        self.opts = start or QROptionen()
        self.gewuenscht = self.opts          # ungeprueft, fuer den Vergleich
        self.ergebnis: QRErgebnis | None = None
        self.vorschau_bild = None            # Referenz halten, sonst verschwindet sie
        self.nachlauf = None                 # laufender after()-Auftrag
        self.starttext = starttext
        self.aktiver_reiter = 0

        # Beim Doppelklick kann das Arbeitsverzeichnis C:\Windows\system32 sein
        # und als EXE der Temp-Ordner der Entpackung - als Startordner fuer den
        # Speicherdialog taugt beides nicht.
        self.letzter_ordner = programm_ordner()

        # Auf skalierten Bildschirmen muss die Vorschau in Pixeln mitwachsen,
        # sonst schrumpft sie gegenueber den Bedienelementen. Der Arbeitsbereich
        # des Monitors begrenzt sie nach oben.
        self.skalierung = max(1.0, master.winfo_fpixels("1i") / 96.0)
        self.arbeitsflaeche = self._arbeitsflaeche_ermitteln()
        _rand_x, _rand_y, platz_breite, platz_hoehe = self.arbeitsflaeche
        self.vorschau_kante = max(
            180,
            min(round(VORSCHAU_KANTE * self.skalierung), platz_hoehe // 3, platz_breite // 4),
        )

        master.title(f"{PROGRAMM} {VERSION}")
        master.configure(bg=BG)

        self._variablen_anlegen()
        self._stil_setzen()
        self._aufbauen()
        self._fenster_einpassen()

    # -- Bildschirm und Fenstergroesse -------------------------------------

    def _arbeitsflaeche_ermitteln(self) -> tuple[int, int, int, int]:
        """Arbeitsbereich (x, y, Breite, Höhe) des Monitors, auf dem das Fenster liegt.

        Bei mehreren Bildschirmen umfasst winfo_screenwidth() die gesamte
        virtuelle Flaeche. Wuerde man danach zentrieren, landete das Fenster auf
        der Naht zwischen zwei Monitoren. Unter Windows liefert GetMonitorInfo
        deshalb den tatsaechlichen Arbeitsbereich ohne Taskleiste.
        """
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

                benutzer = ctypes.windll.user32
                fenster = benutzer.GetParent(self.master.winfo_id()) or self.master.winfo_id()
                monitor = benutzer.MonitorFromWindow(fenster, 2)     # naechstgelegener Monitor
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                if benutzer.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    bereich = info.rcWork
                    return (bereich.left, bereich.top,
                            bereich.right - bereich.left, bereich.bottom - bereich.top)
            except (AttributeError, OSError, ValueError):
                pass
        return (0, 0, self.master.winfo_screenwidth(), self.master.winfo_screenheight())

    def _fenster_einpassen(self) -> None:
        """Fenster auf feste Größe setzen und vollständig auf den Monitor legen.

        Die noetige Groesse haengt von der Schriftgroesse und damit von der
        Windows-Skalierung ab, deshalb wird sie berechnet statt fest eingetragen.
        Passt der Inhalt ausnahmsweise nicht auf den Bildschirm, bleibt das
        Fenster veraenderbar - sonst waere es nicht mehr zu bedienen.
        """
        self.master.update_idletasks()
        rand_x, rand_y, platz_breite, platz_hoehe = self.arbeitsflaeche
        breite, hoehe = self.master.winfo_reqwidth(), self.master.winfo_reqheight()

        passt = breite <= platz_breite and hoehe <= platz_hoehe
        breite, hoehe = min(breite, platz_breite), min(hoehe, platz_hoehe)
        x = rand_x + max(0, (platz_breite - breite) // 2)
        y = rand_y + max(0, (platz_hoehe - hoehe) // 3)

        self.master.geometry(f"{breite}x{hoehe}+{x}+{y}")
        self.master.resizable(not passt, not passt)
        if not passt:
            self.master.minsize(round(480 * self.skalierung), round(360 * self.skalierung))

    # -- Zustand -----------------------------------------------------------

    def _variablen_anlegen(self) -> None:
        tk = _tk
        self.var_format = tk.StringVar(value=self.opts.format)
        self.var_groesse = tk.StringVar(value=str(self.opts.groesse))
        self.var_korrektur = tk.StringVar(value=self.opts.fehlerkorrektur)
        self.var_rand = tk.IntVar(value=self.opts.rand)
        self.var_dpi = tk.IntVar(value=self.opts.dpi)
        self.var_vordergrund = tk.StringVar(value=self.opts.vordergrund)
        self.var_hintergrund = tk.StringVar(value=self.opts.hintergrund)
        self.var_transparent = tk.BooleanVar(value=self.opts.transparent)
        self.var_stapel = tk.BooleanVar(value=False)
        self.var_status = tk.StringVar(value=_("Bereit."))
        self.var_info = tk.StringVar(value="")
        self.var_dunkel = tk.BooleanVar(value=CURRENT_THEME == "dark")

        for var in (self.var_format, self.var_groesse, self.var_korrektur, self.var_rand,
                    self.var_dpi, self.var_vordergrund, self.var_hintergrund,
                    self.var_transparent, self.var_stapel):
            var.trace_add("write", lambda *_a: self._spaeter_zeichnen())

    def _stil_setzen(self) -> None:
        """ttk-Bedienelemente an das gewählte Farbschema anpassen.

        Beim Schemawechsel genuegt es, diese Methode erneut aufzurufen: ttk
        zeichnet alle betroffenen Bedienelemente selbst neu.
        """
        tk, ttk = _tk, _ttk
        stil = ttk.Style()
        try:
            stil.theme_use("clam")
        except tk.TclError:
            pass

        for widget in ("TEntry", "TCombobox", "TSpinbox"):
            # lightcolor/darkcolor sind die 3D-Kanten des clam-Themes - ohne
            # sie zeichnet Tk im dunklen Schema weisse Raender um die Felder
            stil.configure(widget, fieldbackground=FIELD_BG, foreground=TEXT,
                           background=BTN_BG, bordercolor=BORDER,
                           lightcolor=BORDER, darkcolor=BORDER,
                           arrowcolor=TEXT, insertcolor=TEXT, padding=3)
            stil.map(widget,
                     fieldbackground=[("readonly", FIELD_BG), ("disabled", BG)],
                     background=[("readonly", BTN_BG), ("active", BTN_HOVER)],
                     foreground=[("readonly", TEXT), ("disabled", BTN_DISABLED)],
                     bordercolor=[("focus", ACCENT)],
                     lightcolor=[("focus", ACCENT)],
                     darkcolor=[("focus", ACCENT)])

        # Klappliste der Auswahlfelder ist ein klassisches Listenfeld
        self.master.option_add("*TCombobox*Listbox.background", FIELD_BG)
        self.master.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.master.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.master.option_add("*TCombobox*Listbox.selectForeground", ON_ACCENT)

        stil.configure("TScrollbar", background=BTN_BG, troughcolor=TROUGH,
                       bordercolor=BORDER, arrowcolor=MUTED)
        stil.map("TScrollbar", background=[("active", BTN_HOVER)])

        stil.configure("TNotebook", background=BG, bordercolor=BORDER, borderwidth=0)
        stil.configure("TNotebook.Tab", background=TAB_BG, foreground=MUTED,
                       bordercolor=BORDER, lightcolor=TAB_BG, darkcolor=TAB_BG,
                       padding=(16, 8), font=FONT_SMALL)
        stil.map("TNotebook.Tab",
                 background=[("selected", CARD), ("active", BTN_HOVER)],
                 foreground=[("selected", TEXT)],
                 lightcolor=[("selected", CARD)],
                 darkcolor=[("selected", CARD)])

    # -- Aufbau ------------------------------------------------------------

    def _aufbauen(self) -> None:
        tk, ttk = _tk, _ttk
        GEFAERBTE_WIDGETS.clear()
        self.aussen = faerben(tk.Frame(self.master), bg="BG")
        self.aussen.pack(fill="both", expand=True)

        self._kopfzeile_bauen(self.aussen)

        self.reiter = ttk.Notebook(self.aussen)
        self.reiter.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        seite_qr = faerben(tk.Frame(self.reiter), bg="BG")
        self.reiter.add(seite_qr, text="  " + _("QR-Code") + "  ")
        self._seite_qr_bauen(seite_qr)

        # Die Höhe der ersten Seite gibt das Maß vor; die beiden Textseiten
        # bekommen denselben Platz und scrollen darin.
        self.master.update_idletasks()
        hoehe = max(seite_qr.winfo_reqheight(), round(320 * self.skalierung))

        seite_hilfe = faerben(tk.Frame(self.reiter), bg="BG")
        self.reiter.add(seite_hilfe, text="  " + _("Erklärungen") + "  ")
        self._seite_hilfe_bauen(seite_hilfe, hoehe)

        seite_info = faerben(tk.Frame(self.reiter), bg="BG")
        self.reiter.add(seite_info, text="  " + _("Info & Copyright") + "  ")
        self._seite_info_bauen(seite_info, hoehe)

        self._statusleiste_bauen(self.aussen)

        self.reiter.select(self.aktiver_reiter)
        self.reiter.bind("<<NotebookTabChanged>>",
                         lambda _e: setattr(self, "aktiver_reiter", self.reiter.index("current")))

        if self.starttext:
            self.eingabe.insert("1.0", self.starttext)
        self._neu_zeichnen()

        self.master.bind("<Control-s>", lambda _e: self.speichern())

    def _kopfzeile_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        kopf = faerben(tk.Frame(eltern), bg="HEADER")
        kopf.pack(fill="x")

        marke = faerben(tk.Frame(kopf), bg="HEADER")
        marke.pack(side="left", padx=18, pady=12)
        faerben(tk.Label(marke, text=PROGRAMM, font=("Segoe UI", 15, "bold"), anchor="w"),
                bg="HEADER", fg="HEADER_TITLE").pack(fill="x")
        faerben(tk.Label(marke, text=_("Version {version}").format(version=VERSION),
                         font=FONT_TINY, anchor="w"),
                bg="HEADER", fg="HEADER_GROUP").pack(fill="x")

        umschalter = faerben(tk.Frame(kopf), bg="HEADER")
        umschalter.pack(side="right", padx=18)
        faerben(tk.Label(umschalter, text=_("Sprache & Darstellung"),
                         font=("Segoe UI", 8, "bold"), anchor="e"),
                bg="HEADER", fg="HEADER_GROUP").pack(fill="x", pady=(10, 2))

        zeile = faerben(tk.Frame(umschalter), bg="HEADER")
        zeile.pack(fill="x", pady=(0, 10))
        self.sprachnamen = _.available()
        self.sprachfeld = ttk.Combobox(zeile, state="readonly", font=FONT_SMALL, width=12,
                                       values=list(self.sprachnamen.values()))
        self.sprachfeld.set(self.sprachnamen[_.language])
        self.sprachfeld.pack(side="left")
        self.sprachfeld.bind("<<ComboboxSelected>>", self._sprache_gewaehlt)

        faerben(tk.Checkbutton(zeile, text=_("Dunkel"), variable=self.var_dunkel,
                               command=self._schema_umgeschaltet, font=FONT_SMALL,
                               highlightthickness=0, bd=0, cursor="hand2"),
                bg="HEADER", fg="HEADER_TEXT", activebackground="HEADER",
                activeforeground="HEADER_TITLE", selectcolor="HEADER_HOVER").pack(
            side="left", padx=(8, 0))

    def _statusleiste_bauen(self, eltern) -> None:
        tk = _tk
        leiste = faerben(tk.Frame(eltern), bg="STATUS_BG")
        leiste.pack(side="bottom", fill="x")
        faerben(tk.Label(leiste, textvariable=self.var_status, font=FONT_SMALL, anchor="w"),
                bg="STATUS_BG", fg="MUTED").pack(side="left", padx=14, pady=4)
        for name, vorhanden in (("qrcode", HAS_QRCODE), ("Pillow", HAS_PIL)):
            faerben(tk.Label(leiste, text=f"● {name}", font=FONT_TINY, anchor="e"),
                    bg="STATUS_BG", fg="OK" if vorhanden else "WARN").pack(
                side="right", padx=(0, 14))

    # -- Reiter 1: QR-Code -------------------------------------------------

    def _seite_qr_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        links = faerben(tk.Frame(raster), bg="BG")
        links.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # --- Inhalt ---
        karte_inhalt = make_card(links, fill="x")
        card_title(karte_inhalt, _("Inhalt des QR-Codes"))

        textbereich = faerben(tk.Frame(karte_inhalt), bg="CARD")
        textbereich.pack(fill="x", padx=14, pady=(0, 6))
        self.eingabe = faerben(
            tk.Text(textbereich, wrap="word", width=42, height=6, undo=True,
                    relief="flat", highlightthickness=1, font=FONT_MONO, padx=6, pady=6),
            bg="FIELD_BG", fg="TEXT", insertbackground="TEXT", selectbackground="ACCENT",
            selectforeground="ON_ACCENT", highlightbackground="BORDER", highlightcolor="ACCENT")
        self.eingabe.pack(side="left", fill="both", expand=True)
        rolle = ttk.Scrollbar(textbereich, orient="vertical", command=self.eingabe.yview)
        rolle.pack(side="right", fill="y")
        self.eingabe.configure(yscrollcommand=rolle.set)
        self.eingabe.bind("<<Modified>>", self._text_geaendert)

        faerben(tk.Checkbutton(karte_inhalt,
                               text=_("Jede Zeile als eigenen QR-Code speichern (Stapel)"),
                               variable=self.var_stapel, font=FONT_SMALL,
                               highlightthickness=0, bd=0, cursor="hand2", anchor="w"),
                bg="CARD", fg="TEXT", activebackground="CARD", activeforeground="TEXT",
                selectcolor="FIELD_BG").pack(fill="x", padx=12, pady=(0, 10))

        # --- Einstellungen ---
        karte_opt = make_card(links, fill="x", pady=(10, 0))
        card_title(karte_opt, _("Einstellungen"))
        self._einstellungen_bauen(karte_opt)

        # --- Vorschau ---
        rechts = faerben(tk.Frame(raster), bg="BG")
        rechts.pack(side="left", fill="y")
        karte_vor = make_card(rechts, fill="both", expand=True)
        card_title(karte_vor, _("Vorschau"))

        # Der Rahmen haelt die Vorschauflaeche auf fester Pixelgroesse. Ohne ihn
        # wuerden width/height des Labels als Zeichen und Zeilen gelten, solange
        # noch kein Bild gesetzt ist - das Fenster geriete dann riesig.
        flaeche = faerben(
            tk.Frame(karte_vor, width=self.vorschau_kante, height=self.vorschau_kante,
                     highlightthickness=1),
            bg="VIEWER_BG", highlightbackground="BORDER")
        flaeche.pack(padx=14, pady=(0, 8))
        flaeche.pack_propagate(False)
        self.vorschau = faerben(
            tk.Label(flaeche, anchor="center", font=FONT_SMALL, justify="center",
                     wraplength=self.vorschau_kante - 24),
            bg="VIEWER_BG", fg="VIEWER_TEXT")
        self.vorschau.pack(fill="both", expand=True)

        faerben(tk.Label(karte_vor, textvariable=self.var_info, font=FONT_TINY,
                         justify="center", wraplength=self.vorschau_kante),
                bg="CARD", fg="MUTED").pack(padx=14, pady=(0, 10))

        knoepfe = faerben(tk.Frame(karte_vor), bg="CARD")
        knoepfe.pack(fill="x", padx=14, pady=(0, 12))
        FlatButton(knoepfe, _("Speichern unter ..."), self.speichern, kind="primary").pack(
            side="right")
        FlatButton(knoepfe, _("Zurücksetzen"), self.zuruecksetzen).pack(side="right", padx=(0, 8))

    def _einstellungen_bauen(self, karte) -> None:
        tk, ttk = _tk, _ttk
        gitter = faerben(tk.Frame(karte), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 12))
        for spalte in (1, 3):
            gitter.columnconfigure(spalte, weight=1)

        def beschriftung(text, zeile, spalte):
            faerben(tk.Label(gitter, text=text, font=FONT_SMALL, anchor="w"),
                    bg="CARD", fg="MUTED").grid(row=zeile, column=spalte, sticky="w",
                                                padx=(0, 8), pady=4)

        beschriftung(_("Format"), 0, 0)
        ttk.Combobox(gitter, textvariable=self.var_format, values=FORMAT_REIHENFOLGE,
                     state="readonly", font=FONT_SMALL, width=10).grid(
            row=0, column=1, sticky="ew")

        beschriftung(_("Größe (px)"), 0, 2)
        ttk.Combobox(gitter, textvariable=self.var_groesse, font=FONT_SMALL, width=10,
                     values=[str(g) for g in GROESSEN_VORGABEN]).grid(row=0, column=3, sticky="ew")

        beschriftung(_("Fehlerkorrektur"), 1, 0)
        ttk.Combobox(gitter, textvariable=self.var_korrektur, values=list(FEHLERKORREKTUR),
                     state="readonly", font=FONT_SMALL, width=10).grid(
            row=1, column=1, sticky="ew")

        beschriftung(_("Rand (Module)"), 1, 2)
        ttk.Spinbox(gitter, from_=0, to=32, textvariable=self.var_rand, font=FONT_SMALL,
                    width=10).grid(row=1, column=3, sticky="ew")

        beschriftung(_("Auflösung (DPI)"), 2, 0)
        ttk.Spinbox(gitter, from_=72, to=1200, textvariable=self.var_dpi, font=FONT_SMALL,
                    width=10).grid(row=2, column=1, sticky="ew")

        faerben(tk.Checkbutton(gitter, text=_("Hintergrund transparent"),
                               variable=self.var_transparent, font=FONT_SMALL,
                               highlightthickness=0, bd=0, cursor="hand2", anchor="w"),
                bg="CARD", fg="TEXT", activebackground="CARD", activeforeground="TEXT",
                selectcolor="FIELD_BG").grid(row=2, column=2, columnspan=2, sticky="w", pady=4)

        beschriftung(_("Vordergrund"), 3, 0)
        self.knopf_vg = FlatButton(
            gitter, self.var_vordergrund.get(),
            lambda: self._farbe_waehlen(self.var_vordergrund, _("Vordergrundfarbe")))
        self.knopf_vg.grid(row=3, column=1, sticky="ew")

        beschriftung(_("Hintergrund"), 3, 2)
        self.knopf_hg = FlatButton(
            gitter, self.var_hintergrund.get(),
            lambda: self._farbe_waehlen(self.var_hintergrund, _("Hintergrundfarbe")))
        self.knopf_hg.grid(row=3, column=3, sticky="ew")

    # -- Reiter 2: Erklärungen ---------------------------------------------

    def _seite_hilfe_bauen(self, eltern, hoehe) -> None:
        tk = _tk
        bereich = ScrollBereich(eltern, hoehe)
        bereich.pack(fill="both", expand=True, padx=14, pady=14)
        innen = bereich.innen

        karte = make_card(innen, fill="x")
        card_title(karte, _("In drei Schritten zum QR-Code"))
        card_text(karte, _(
            "1.  Inhalt in das Textfeld schreiben - eine Adresse, einen Text, "
            "Kontaktdaten oder was sonst gescannt werden soll.\n"
            "2.  Format und Größe wählen. Die Vorschau zeigt sofort, wie der Code aussieht.\n"
            "3.  Auf 'Speichern unter ...' klicken (oder Strg+S drücken) und einen "
            "Ablageort wählen.\n\n"
            "Sind mehrere Zeilen eingetragen und der Stapelmodus eingeschaltet, entsteht "
            "aus jeder Zeile ein eigener Code; gefragt wird dann nach einem Zielordner."))

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Die Formate im Überblick"))
        for name in FORMAT_REIHENFOLGE:
            info = FORMATE[name]
            zeile = faerben(tk.Frame(karte), bg="CARD")
            zeile.pack(fill="x", padx=14, pady=2)
            faerben(tk.Label(zeile, text=info.name, font=FONT_BOLD, width=6, anchor="w"),
                    bg="CARD", fg="ACCENT").pack(side="left")
            faerben(tk.Label(zeile, text=info.endung, font=FONT_MONO, width=7, anchor="w"),
                    bg="CARD", fg="MUTED").pack(side="left")
            faerben(tk.Label(zeile, text=_("Transparenz") if info.alpha else "",
                             font=FONT_TINY, width=12, anchor="w"),
                    bg="CARD", fg="OK").pack(side="left")
            faerben(tk.Label(zeile, text=_(info.beschreibung), font=FONT_SMALL,
                             anchor="w", justify="left"),
                    bg="CARD", fg="TEXT").pack(side="left", fill="x", expand=True)
        card_text(karte, _(
            "Verlangt ein Format eine Einstellung, die es nicht beherrscht - etwa "
            "Transparenz bei JPEG oder mehr als 256 Pixel bei ICO -, wird die Einstellung "
            "angepasst und in der Statuszeile erklärt."), font=FONT_TINY)

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Fehlerkorrektur"))
        for kuerzel, (_stufe, text) in FEHLERKORREKTUR.items():
            zeile = faerben(tk.Frame(karte), bg="CARD")
            zeile.pack(fill="x", padx=14, pady=2)
            faerben(tk.Label(zeile, text=kuerzel, font=FONT_BOLD, width=6, anchor="w"),
                    bg="CARD", fg="ACCENT").pack(side="left")
            faerben(tk.Label(zeile, text=_(text), font=FONT_SMALL, anchor="w"),
                    bg="CARD", fg="TEXT").pack(side="left", fill="x", expand=True)
        card_text(karte, _(
            "Je höher die Stufe, desto mehr Schmutz, Knicke oder Überdeckung verträgt der "
            "Code - er braucht dafür aber mehr Module und wirkt feiner. Für Aufkleber und "
            "Aufdrucke lohnt sich Q oder H, für die Anzeige am Bildschirm genügt M."))

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Größe und Rand"))
        card_text(karte, _(
            "Die Größe ist die Kantenlänge des fertigen Bildes in Pixeln (32 bis 10000). "
            "Gezeichnet wird zuerst mit einer ganzzahligen Modulgröße und nur bei Bedarf "
            "ohne Weichzeichnen auf das Endmaß gebracht - so bleiben die Modulkanten hart "
            "und der Code gut lesbar. Bei SVG ist die Angabe nur das Grundmaß, die Datei "
            "bleibt beliebig skalierbar.\n\n"
            "Anhaltspunkte: 256 px für Bildschirm und E-Mail, 512 bis 1024 px für Web und "
            "Präsentationen, ab 2048 px oder SVG für den Druck.\n\n"
            "Der Rand (die Ruhezone) sollte laut Norm mindestens 4 Module betragen. "
            "Ohne diesen freien Rahmen erkennen viele Lesegeräte den Code nicht."))

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Gut lesbare Codes"))
        card_text(karte, _(
            "Dunkle Module auf hellem Grund funktionieren am zuverlässigsten. Ist der "
            "Kontrast zu gering oder die Darstellung umgekehrt, erscheint unten links ein "
            "Hinweis - der Code wird trotzdem erzeugt, sollte dann aber vor dem Druck "
            "getestet werden.\n\n"
            "Umlaute und andere Sonderzeichen werden als UTF-8 gespeichert. Sehr alte "
            "Lesegeräte deuten sie gelegentlich falsch; im Zweifel vorher ausprobieren."))

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Kommandozeile"))
        card_text(karte, _(
            "Mit Argumenten aufgerufen arbeitet das Programm ohne Oberfläche - praktisch "
            "für viele Codes auf einmal:"))
        beispiele = (
            'qr_generator.py "https://example.org"',
            'qr_generator.py "Hallo Welt" -o hallo.svg',
            'qr_generator.py "Text" -f PNG -s 1024 -e H',
            'qr_generator.py --stapel liste.txt -a ausgabe -f SVG',
            'qr_generator.py --help',
        )
        for befehl in beispiele:
            faerben(tk.Label(karte, text=befehl, font=FONT_MONO, anchor="w", padx=8, pady=3),
                    bg="CARD_ALT", fg="TEXT").pack(fill="x", padx=14, pady=1)
        faerben(tk.Frame(karte, height=12), bg="CARD").pack()

    # -- Reiter 3: Info & Copyright ----------------------------------------

    def _seite_info_bauen(self, eltern, hoehe) -> None:
        tk = _tk
        bereich = ScrollBereich(eltern, hoehe)
        bereich.pack(fill="both", expand=True, padx=14, pady=14)
        innen = bereich.innen

        karte = make_card(innen, fill="x")
        card_title(karte, _("Über dieses Programm"))
        card_text(karte, f"{PROGRAMM} {VERSION}", rolle="TEXT", font=FONT_H2)
        card_text(karte, _(
            "Erzeugt QR-Codes aus beliebigen textbasierten Inhalten und speichert sie als "
            "Bilddatei - in zehn Formaten und in jeder gewünschten Größe. Farbschema, "
            "Sprachumschaltung und Aufbau folgen der Bild-Toolbox.\n\n"
            "Das gesamte Programm steckt in einer einzigen Datei und läuft wahlweise mit "
            "dieser Oberfläche oder auf der Kommandozeile.\n\n"
            "Tastatur: Strg+S speichert den angezeigten Code."))

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Bibliotheken"))
        for name, vorhanden, zweck, stand in self.bibliotheken():
            zeile = faerben(tk.Frame(karte), bg="CARD")
            zeile.pack(fill="x", padx=14, pady=3)
            faerben(tk.Label(zeile, text="●", font=FONT_SMALL, width=3),
                    bg="CARD", fg="OK" if vorhanden else "WARN").pack(side="left")
            faerben(tk.Label(zeile, text=name, font=FONT_BOLD, width=12, anchor="w"),
                    bg="CARD", fg="TEXT").pack(side="left")
            faerben(tk.Label(zeile, text=zweck, font=FONT_SMALL, anchor="w"),
                    bg="CARD", fg="MUTED").pack(side="left", fill="x", expand=True)
            faerben(tk.Label(zeile, text=stand, font=FONT_SMALL),
                    bg="CARD", fg="OK" if vorhanden else "WARN").pack(side="right")
        if ist_eingefroren():
            card_text(karte, _(
                "Diese Fassung läuft als eigenständiges Programm - die Bibliotheken sind "
                "fest eingebettet, es muss nichts installiert werden."), font=FONT_TINY)
        else:
            faerben(tk.Frame(karte, height=10), bg="CARD").pack()

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Lizenz und Copyright"))
        card_text(karte, (
            "Licensed under MIT License\n"
            "Copyright 2026 Alexander Unverhau\n"
            "Created with assistance of Claude AI"), rolle="TEXT", font=FONT_BOLD)
        card_text(karte, _(
            "Hiermit wird unentgeltlich jeder Person, die eine Kopie dieser Software und "
            "der zugehörigen Dokumentation erhält, die Erlaubnis erteilt, sie "
            "uneingeschränkt zu nutzen, zu kopieren, zu verändern und weiterzugeben - "
            "unter der Bedingung, dass dieser Copyright-Vermerk und der Lizenztext in "
            "allen Kopien enthalten bleiben.\n\n"
            "Die Software wird ohne jede Gewähr bereitgestellt."))

        karte = make_card(innen, fill="x", pady=(10, 0))
        card_title(karte, _("Sprache und Darstellung"))
        card_text(karte, _(
            "Die Auswahl oben rechts stellt Sprache und Farbschema um; beides wird neben "
            "dem Programm in der Datei '{datei}' gespeichert und beim nächsten Start "
            "wieder verwendet. Ohne gespeicherte Einstellung richtet sich die Sprache nach "
            "dem Betriebssystem.\n\n"
            "Quellsprache ist Deutsch. Eine weitere Sprache entsteht durch einen Eintrag "
            "in den Tabellen LANGUAGE_NAMES und TRANSLATIONS am Ende der Programmdatei; "
            "nicht übersetzte Zeilen erscheinen weiterhin auf Deutsch.").format(
                datei=CONFIG_NAME))

    @staticmethod
    def bibliotheken():
        """(Name, vorhanden, Zweck, Stand) für die Info-Seite.

        'Stand' ist die Versionsnummer, wenn die Bibliothek geladen werden
        konnte - so ist auch in einer gebuendelten EXE nachvollziehbar, was
        tatsaechlich eingebettet wurde -, sonst der Installationsbefehl.
        """
        vorhanden_text = _("eingebettet") if ist_eingefroren() else _("installiert")

        def stand(vorhanden, modul, verteilung, befehl):
            if not vorhanden:
                return befehl
            return paket_version(modul, verteilung) or vorhanden_text

        return [
            ("qrcode", HAS_QRCODE, _("kodiert den Inhalt als QR-Matrix"),
             stand(HAS_QRCODE, qrcode, "qrcode", "pip install qrcode")),
            ("Pillow", HAS_PIL, _("zeichnet und speichert die Bilddateien"),
             stand(HAS_PIL, Image, "pillow", "pip install Pillow")),
            ("Tkinter", True, _("stellt diese Oberfläche dar"), f"Tk {_tk.TkVersion}"),
        ]

    # -- Sprache und Farbschema --------------------------------------------

    def _sprache_gewaehlt(self, _ereignis=None) -> None:
        gewaehlt = self.sprachfeld.get()
        for code, name in self.sprachnamen.items():
            if name == gewaehlt:
                self.sprache_setzen(code)
                return

    def sprache_setzen(self, code: str) -> None:
        """Sprache umstellen und die Oberfläche neu aufbauen.

        Anders als beim Farbschema aendert sich hier jeder Beschriftungstext und
        damit der Platzbedarf saemtlicher Elemente - ein Neuaufbau ist der
        ehrlichere Weg als hunderte Einzeltexte nachzuziehen.
        """
        if code == _.language:
            return
        _.language = code
        einstellungen = load_config()
        einstellungen["language"] = code
        save_config(einstellungen)
        self._neu_aufbauen()

    def _schema_umgeschaltet(self) -> None:
        self.schema_setzen("dark" if self.var_dunkel.get() else "light")

    def schema_setzen(self, name: str) -> None:
        """Zwischen hellem und dunklem Schema wechseln - ohne Neuaufbau.

        Die Widgets bleiben stehen und werden nur umgefaerbt; ttk-Elemente
        folgen dem neu gesetzten Stil von selbst. Dadurch flackert nichts und
        die Bildlaufposition bleibt erhalten.
        """
        if name == CURRENT_THEME:
            return
        apply_theme(name)
        einstellungen = load_config()
        einstellungen["theme"] = CURRENT_THEME
        save_config(einstellungen)

        self.master.configure(bg=BG)
        self._stil_setzen()
        farben_auffrischen()

    def _neu_aufbauen(self) -> None:
        """Oberfläche komplett neu aufbauen (nach einem Sprachwechsel).

        Der eingegebene Text und alle Einstellungen werden dabei uebernommen -
        ein Sprachwechsel mitten in der Arbeit darf nichts verwerfen.
        """
        if self.nachlauf is not None:
            self.master.after_cancel(self.nachlauf)
            self.nachlauf = None

        self.starttext = self.eingabe.get("1.0", "end-1c")
        gemerkt = {
            "format": self.var_format.get(),
            "groesse": self.var_groesse.get(),
            "korrektur": self.var_korrektur.get(),
            "rand": self.var_rand.get(),
            "dpi": self.var_dpi.get(),
            "vordergrund": self.var_vordergrund.get(),
            "hintergrund": self.var_hintergrund.get(),
            "transparent": self.var_transparent.get(),
            "stapel": self.var_stapel.get(),
        }

        self.vorschau_bild = None
        self.aussen.destroy()
        self.master.configure(bg=BG)

        self._variablen_anlegen()
        self.var_format.set(gemerkt["format"])
        self.var_groesse.set(gemerkt["groesse"])
        self.var_korrektur.set(gemerkt["korrektur"])
        self.var_rand.set(gemerkt["rand"])
        self.var_dpi.set(gemerkt["dpi"])
        self.var_vordergrund.set(gemerkt["vordergrund"])
        self.var_hintergrund.set(gemerkt["hintergrund"])
        self.var_transparent.set(gemerkt["transparent"])
        self.var_stapel.set(gemerkt["stapel"])

        self._stil_setzen()
        self._aufbauen()
        self.master.title(f"{PROGRAMM} {VERSION}")
        self._fenster_einpassen()

    # -- Eingaben ----------------------------------------------------------

    def _farbe_waehlen(self, variable, titel: str) -> None:
        from tkinter import colorchooser
        _rgb, hexwert = colorchooser.askcolor(color=variable.get(), title=titel,
                                              parent=self.master)
        if hexwert:
            variable.set(hexwert.upper())
            self._farbknoepfe_beschriften()

    def _farbknoepfe_beschriften(self) -> None:
        for knopf, var in ((self.knopf_vg, self.var_vordergrund),
                           (self.knopf_hg, self.var_hintergrund)):
            knopf.configure(text=var.get())

    def _text_geaendert(self, _ereignis=None) -> None:
        if self.eingabe.edit_modified():
            self.eingabe.edit_modified(False)
            self._spaeter_zeichnen()

    def _spaeter_zeichnen(self) -> None:
        """Vorschau erst nach kurzer Ruhe neu berechnen - das hält die Eingabe flüssig."""
        if self.nachlauf is not None:
            self.master.after_cancel(self.nachlauf)
        self.nachlauf = self.master.after(200, self._neu_zeichnen)

    def _text_holen(self) -> str:
        return self.eingabe.get("1.0", "end-1c").strip()

    def _zeilen_holen(self) -> list[str]:
        return [z.strip() for z in self.eingabe.get("1.0", "end-1c").splitlines() if z.strip()]

    def optionen_holen(self) -> QROptionen:
        """Liest die Eingabefelder und liefert geprüfte Optionen.

        Der ungepruefte Wunsch bleibt in self.gewuenscht stehen. Nur so kann
        _neu_zeichnen() erklaeren, was optionen_pruefen() anpassen musste -
        etwa die Groesse bei ICO oder die Transparenz bei GIF.
        """
        try:
            groesse = int(str(self.var_groesse.get()).strip())
        except ValueError as exc:
            raise QRFehler(_("Die Größe muss eine ganze Zahl sein.")) from exc
        try:
            rand, dpi = int(self.var_rand.get()), int(self.var_dpi.get())
        except (ValueError, _tk.TclError) as exc:
            raise QRFehler(_("Rand und DPI müssen ganze Zahlen sein.")) from exc

        self.gewuenscht = QROptionen(
            format=self.var_format.get(),
            groesse=groesse,
            fehlerkorrektur=self.var_korrektur.get(),
            rand=rand,
            vordergrund=self.var_vordergrund.get(),
            hintergrund=self.var_hintergrund.get(),
            transparent=self.var_transparent.get(),
            dpi=dpi,
        )
        return optionen_pruefen(self.gewuenscht)

    # -- Vorschau ----------------------------------------------------------

    def _vorschau_zeigen(self, bild) -> None:
        """Vorschaubild anzeigen, möglichst ohne die Fläche neu zu zeichnen.

        Ein frisches PhotoImage wuerde das Label kurz leeren - bei jeder
        Farbaenderung sichtbar als Blinken. Bei gleicher Groesse wird der Inhalt
        deshalb in das vorhandene Bild kopiert.
        """
        fertig = bild.convert("RGB")
        if (self.vorschau_bild is not None
                and (self.vorschau_bild.width(), self.vorschau_bild.height()) == fertig.size):
            self.vorschau_bild.paste(fertig)
            return
        self.vorschau_bild = _ImageTk.PhotoImage(fertig)
        self.vorschau.configure(image=self.vorschau_bild, text="")

    def _vorschau_leeren(self, hinweis: str = "") -> None:
        self.vorschau.configure(image="", text=hinweis)
        self.vorschau_bild = None
        self.var_info.set("")

    def _neu_zeichnen(self) -> None:
        self.nachlauf = None
        text = self._zeilen_holen()[0] if self.var_stapel.get() else self._text_holen()

        if not text:
            self._vorschau_leeren(_("Bitte einen Inhalt eingeben."))
            self.var_status.set(_("Bereit."))
            return

        try:
            opts = self.optionen_holen()
            self.opts = opts
            ergebnis = matrix_erzeugen(text, opts)
            bild = bild_erzeugen(ergebnis, replace(opts, groesse=self.vorschau_kante))
        except QRFehler as exc:
            self._vorschau_leeren()
            self.var_status.set(_("Fehler: {text}").format(text=exc))
            return

        self.ergebnis = ergebnis
        if opts.transparent:
            bild = self._auf_karo(bild)
        self._vorschau_zeigen(bild)

        anzahl = len(self._zeilen_holen()) if self.var_stapel.get() else 1
        stapelhinweis = (_("Stapel: {anzahl} Codes").format(anzahl=anzahl) + "  |  "
                         if self.var_stapel.get() else "")
        self.var_info.set(stapelhinweis + _(
            "Version {version}  |  {module} Module  |  {kante} px  |  {zeichen} Zeichen").format(
                version=ergebnis.version, module=ergebnis.module,
                kante=opts.groesse, zeichen=ergebnis.zeichen))

        # Angepasste Einstellungen zuerst - sie erklaeren, warum das Ergebnis
        # von der Eingabe abweicht; die Kontrastwarnung kommt danach.
        meldungen = anpassungen_beschreiben(self.gewuenscht, opts)
        warnung = kontrast_warnung(opts)
        if warnung:
            meldungen.append(warnung)
        self.var_status.set("   ".join(meldungen) if meldungen else _("Bereit."))

    def _auf_karo(self, bild):
        """Legt das Bild auf ein Schachbrett, damit Transparenz sichtbar wird."""
        karo = Image.new("RGBA", bild.size, (255, 255, 255, 255))
        zeichner = ImageDraw.Draw(karo)
        kante = round(10 * self.skalierung)
        for y in range(0, bild.size[1], kante):
            for x in range(0, bild.size[0], kante):
                if (x // kante + y // kante) % 2:
                    zeichner.rectangle([x, y, x + kante - 1, y + kante - 1],
                                       fill=(214, 214, 214, 255))
        return Image.alpha_composite(karo, bild)

    # -- Aktionen ----------------------------------------------------------

    def zuruecksetzen(self) -> None:
        vorgabe = QROptionen()
        self.var_format.set(vorgabe.format)
        self.var_groesse.set(str(vorgabe.groesse))
        self.var_korrektur.set(vorgabe.fehlerkorrektur)
        self.var_rand.set(vorgabe.rand)
        self.var_dpi.set(vorgabe.dpi)
        self.var_vordergrund.set(vorgabe.vordergrund)
        self.var_hintergrund.set(vorgabe.hintergrund)
        self.var_transparent.set(vorgabe.transparent)
        self._farbknoepfe_beschriften()
        self.var_status.set(_("Einstellungen zurückgesetzt."))

    def speichern(self) -> None:
        from tkinter import filedialog, messagebox

        try:
            opts = self.optionen_holen()
        except QRFehler as exc:
            messagebox.showerror(PROGRAMM, str(exc), parent=self.master)
            return

        if self.var_stapel.get():
            self._stapel_speichern(opts, filedialog, messagebox)
            return

        text = self._text_holen()
        if not text:
            messagebox.showinfo(PROGRAMM, _("Bitte zuerst einen Inhalt eingeben."),
                                parent=self.master)
            return

        info = opts.format_info()
        ziel = filedialog.asksaveasfilename(
            parent=self.master,
            title=_("QR-Code speichern"),
            initialdir=self.letzter_ordner,
            initialfile=dateiname_vorschlagen(text) + info.endung,
            defaultextension=info.endung,
            filetypes=[(f"{info.name} ({info.endung})", f"*{info.endung}"),
                       (_("Alle Dateien"), "*.*")],
        )
        if not ziel:
            return

        # Weicht die gewaehlte Endung vom Auswahlfeld ab, gewinnt die Endung.
        erkannt = format_aus_pfad(ziel)
        if erkannt and erkannt != opts.format:
            opts = optionen_pruefen(replace(opts, format=erkannt))
            self.var_format.set(erkannt)

        try:
            pfad, ergebnis = qr_speichern(text, ziel, opts)
        except (QRFehler, OSError) as exc:
            messagebox.showerror(PROGRAMM, _("Speichern fehlgeschlagen:\n{fehler}").format(
                fehler=exc), parent=self.master)
            return

        self.letzter_ordner = os.path.dirname(os.path.abspath(pfad))
        self.var_status.set(_("Gespeichert: {pfad}  (Version {version}, {kante} px)").format(
            pfad=pfad, version=ergebnis.version, kante=opts.groesse))

    def _stapel_speichern(self, opts: QROptionen, filedialog, messagebox) -> None:
        zeilen = self._zeilen_holen()
        if not zeilen:
            messagebox.showinfo(PROGRAMM, _("Bitte zuerst Inhalte eingeben - je Zeile einen."),
                                parent=self.master)
            return

        ordner = filedialog.askdirectory(
            parent=self.master, initialdir=self.letzter_ordner,
            title=_("Zielordner für {anzahl} QR-Codes").format(anzahl=len(zeilen)))
        if not ordner:
            return

        geschrieben, fehler = 0, []
        for nummer, inhalt in enumerate(zeilen, start=1):
            ziel = freier_pfad(endung_ergaenzen(
                os.path.join(ordner, dateiname_vorschlagen(inhalt, nummer)),
                opts.format_info()))
            try:
                qr_speichern(inhalt, ziel, opts)
                geschrieben += 1
            except (QRFehler, OSError) as exc:
                fehler.append(_("Zeile {nummer}: {fehler}").format(nummer=nummer, fehler=exc))

        self.letzter_ordner = ordner
        bilanz = _("{gut} von {gesamt} Codes gespeichert.").format(
            gut=geschrieben, gesamt=len(zeilen))
        self.var_status.set(bilanz)
        if fehler:
            messagebox.showwarning(
                PROGRAMM,
                bilanz + "\n\n" + _("Nicht gespeichert:") + "\n" + "\n".join(fehler[:10]),
                parent=self.master,
            )


def dpi_bewusstsein_aktivieren() -> float:
    """Meldet die Anwendung unter Windows als DPI-bewusst an.

    Ohne diese Anmeldung vergroessert Windows das Fenster nur als Bitmap - Schrift
    und QR-Vorschau wirken dann unscharf. Rueckgabe ist die Systemskalierung.
    """
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # System-DPI beachten
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except (AttributeError, OSError):                        # aeltere Windows-Fassungen
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError, NameError):
            pass
        return 1.0


def startfehler_melden(text: str) -> None:
    """Startfehler auf der Konsole und - wenn moeglich - in einem Fenster zeigen.

    Beim Doppelklick gibt es keine bleibende Konsole: die Meldung waere weg,
    bevor man sie lesen kann, und es saehe aus, als passiere ueberhaupt nichts.
    Unter pythonw.exe ist sys.stderr sogar None, ein print() wuerde scheitern.
    """
    if sys.stderr is not None:
        print(text, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        wurzel = tk.Tk()
        wurzel.withdraw()
        messagebox.showerror(f"{PROGRAMM} {VERSION}", text)
        wurzel.destroy()
    except Exception:                       # ohne Tkinter bleibt nur die Konsole
        pass


def gui_starten(args: argparse.Namespace | None = None) -> int:
    """Startet die Oberfläche; Kommandozeilenwerte dienen als Startbelegung."""
    global _tk, _ttk, _ImageTk
    try:
        import tkinter as _tk
        from tkinter import ttk as _ttk
    except ImportError:
        startfehler_melden(_("Fehler: Tkinter ist nicht verfügbar. Bitte die Kommandozeile "
                             "nutzen (Hilfe mit --help)."))
        return 2
    if not HAS_PIL or not HAS_QRCODE:
        fehlend = ", ".join(n for n, da in (("qrcode", HAS_QRCODE), ("Pillow", HAS_PIL)) if not da)
        meldung = _("Fehler: Es fehlen folgende Pakete: {pakete}").format(pakete=fehlend)
        if ist_eingefroren():
            # In einer EXE hilft kein pip - dort ist der Build unvollstaendig.
            meldung += "\n\n" + _("Dieses Programm wurde ohne die genannten Bibliotheken "
                                  "gebündelt und ist damit unvollständig.")
        else:
            # Den Pfad mitgeben: Auf Rechnern mit mehreren Python-Installationen
            # fehlt das Paket oft nur in derjenigen, die der Doppelklick startet.
            meldung += ("\n\n" + _("Installation:  pip install qrcode Pillow") + "\n\n" +
                        _("Verwendetes Python: {pfad}").format(pfad=sys.executable))
        startfehler_melden(meldung)
        return 2
    from PIL import ImageTk as _ImageTk

    widgets_bereitstellen()
    apply_theme(startup_theme())

    start, text = QROptionen(), ""
    if args is not None:
        try:
            start = optionen_pruefen(QROptionen(
                format=args.format or "PNG",
                groesse=args.groesse,
                fehlerkorrektur=args.fehlerkorrektur,
                rand=args.rand,
                vordergrund=args.vordergrund,
                hintergrund=args.hintergrund,
                transparent=args.transparent,
                dpi=args.dpi,
                qualitaet=args.qualitaet,
            ))
            text = text_einlesen(args)
        except QRFehler:
            start, text = QROptionen(), ""

    skalierung = dpi_bewusstsein_aktivieren()
    wurzel = _tk.Tk()
    if skalierung > 1.0:
        # Schriftgroessen sind in Punkt angegeben und muessen mitwachsen.
        wurzel.tk.call("tk", "scaling", skalierung * 96.0 / 72.0)
    QRApp(wurzel, start, text)
    wurzel.mainloop()
    return 0


# --------------------------------------------------------------------------
# SPRACHTABELLE / LANGUAGE TABLE
#
# Quellsprache ist Deutsch - der deutsche Text im Code ist zugleich der
# Schluessel. Eine weitere Sprache kommt in drei Schritten dazu:
#   1. Kuerzel und Anzeigename in LANGUAGE_NAMES eintragen,
#      z. B.  "fr": "Francais"
#   2. In TRANSLATIONS einen Eintrag "fr": { ... } anlegen und die
#      gewuenschten Zeilen uebersetzen.
#   3. Fertig - die Auswahl oben rechts zeigt die Sprache sofort an.
#
# Nicht uebersetzte Zeilen erscheinen automatisch auf Deutsch, eine
# unvollstaendige Tabelle ist also unproblematisch. Platzhalter in
# geschweiften Klammern - {pfad}, {format}, {fehler} ... - muessen in der
# Uebersetzung unveraendert vorkommen; ihre Reihenfolge im Satz ist frei.
# --------------------------------------------------------------------------

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "en": "English",
}

TRANSLATIONS = {
    "en": {
        # --- Rahmen, Reiter, allgemeine Begriffe --------------------------
        "QR-Code": "QR code",
        "Erklärungen": "Guide",
        "Info & Copyright": "About & copyright",
        "Sprache & Darstellung": "Language & appearance",
        "Dunkel": "Dark",
        "Version {version}": "Version {version}",
        "Bereit.": "Ready.",
        "Fehler: {text}": "Error: {text}",
        "Hinweis: {text}": "Note: {text}",
        "installiert": "installed",
        "Alle Dateien": "All files",
        "ja": "yes",
        "nein": "no",
        "Format": "Format",
        "Endung": "Extension",
        "Transparenz": "Transparency",
        "Beschreibung": "Description",
        "Fehlerkorrektur": "Error correction",
        "Fehlerkorrektur:": "Error correction:",

        # --- Reiter 1: Eingabe, Einstellungen, Vorschau -------------------
        "Inhalt des QR-Codes": "QR code content",
        "Jede Zeile als eigenen QR-Code speichern (Stapel)":
            "Save every line as its own QR code (batch)",
        "Einstellungen": "Settings",
        "Größe (px)": "Size (px)",
        "Rand (Module)": "Quiet zone (modules)",
        "Auflösung (DPI)": "Resolution (DPI)",
        "Hintergrund transparent": "Transparent background",
        "Vordergrund": "Foreground",
        "Hintergrund": "Background",
        "Vordergrundfarbe": "Foreground colour",
        "Hintergrundfarbe": "Background colour",
        "Vorschau": "Preview",
        "Bitte einen Inhalt eingeben.": "Please enter some content.",
        "Version {version}  |  {module} Module  |  {kante} px  |  {zeichen} Zeichen":
            "Version {version}  |  {module} modules  |  {kante} px  |  {zeichen} characters",
        "Stapel: {anzahl} Codes": "Batch: {anzahl} codes",
        "Speichern unter ...": "Save as ...",
        "Zurücksetzen": "Reset",
        "Einstellungen zurückgesetzt.": "Settings reset.",

        # --- Speichern ----------------------------------------------------
        "QR-Code speichern": "Save QR code",
        "Bitte zuerst einen Inhalt eingeben.": "Please enter some content first.",
        "Bitte zuerst Inhalte eingeben - je Zeile einen.":
            "Please enter the contents first - one per line.",
        "Zielordner für {anzahl} QR-Codes": "Target folder for {anzahl} QR codes",
        "Gespeichert: {pfad}  (Version {version}, {kante} px)":
            "Saved: {pfad}  (version {version}, {kante} px)",
        "Speichern fehlgeschlagen:\n{fehler}": "Saving failed:\n{fehler}",
        "{gut} von {gesamt} Codes gespeichert.": "Saved {gut} of {gesamt} codes.",
        "Nicht gespeichert:": "Not saved:",
        "Zeile {nummer}: {fehler}": "Line {nummer}: {fehler}",

        # --- Fehler und Hinweise ------------------------------------------
        "{feld} nicht lesbar: {wert}": "{feld} not readable: {wert}",
        "Unbekanntes Format: {wert}": "Unknown format: {wert}",
        "Unbekannte Fehlerkorrektur: {wert}": "Unknown error correction level: {wert}",
        "Größe muss zwischen {min} und {max} Pixel liegen.":
            "Size must be between {min} and {max} pixels.",
        "Rand muss zwischen 0 und 32 Modulen liegen.":
            "The quiet zone must be between 0 and 32 modules.",
        "Version muss zwischen 1 und 40 liegen.": "Version must be between 1 and 40.",
        "Qualität muss zwischen 1 und 100 liegen.": "Quality must be between 1 and 100.",
        "Die Größe muss eine ganze Zahl sein.": "The size must be a whole number.",
        "Rand und DPI müssen ganze Zahlen sein.":
            "Quiet zone and DPI must be whole numbers.",
        "Es wurde kein Inhalt angegeben.": "No content was given.",
        "Kein Inhalt angegeben. Hilfe mit --help, Oberfläche mit --gui.":
            "No content given. Use --help for help, --gui for the window.",
        "Der Inhalt ist zu lang für einen QR-Code. Eine niedrigere Fehlerkorrektur "
        "(z. B. L) schafft etwas Platz, sonst bitte den Text kürzen.":
            "The content is too long for a QR code. A lower error correction level "
            "(L, for instance) frees up some room; otherwise please shorten the text.",
        "Der Inhalt passt nicht in Version {version} bei Fehlerkorrektur {stufe}. "
        "Bitte eine höhere Version oder 'automatisch' wählen.":
            "The content does not fit into version {version} at error correction {stufe}. "
            "Please choose a higher version or 'automatic'.",
        "Der Vordergrund ist heller als der Hintergrund - die meisten Lesegeräte "
        "erwarten dunkle Module auf hellem Grund.":
            "The foreground is lighter than the background - most readers expect dark "
            "modules on a light ground.",
        "Zu wenig Kontrast ({wert}:1) - der Code ist kaum lesbar.":
            "Too little contrast ({wert}:1) - the code is hard to read.",
        "Geringer Kontrast ({wert}:1) - bitte vor dem Druck testen.":
            "Low contrast ({wert}:1) - please test before printing.",
        "Stapeldatei nicht lesbar: {fehler}": "Batch file not readable: {fehler}",
        "Die Stapeldatei enthält keine verwertbaren Zeilen: {pfad}":
            "The batch file contains no usable lines: {pfad}",
        "Datei nicht lesbar: {fehler}": "File not readable: {fehler}",
        "Das Paket 'qrcode' fehlt. Installation:  pip install qrcode Pillow":
            "The 'qrcode' package is missing. Install it with:  pip install qrcode Pillow",
        "Das Paket 'Pillow' fehlt. Installation:  pip install Pillow":
            "The 'Pillow' package is missing. Install it with:  pip install Pillow",
        "Fehler: Tkinter ist nicht verfügbar. Bitte die Kommandozeile "
        "nutzen (Hilfe mit --help).":
            "Error: Tkinter is not available. Please use the command line "
            "(--help for help).",
        "Verwendetes Python: {pfad}": "Python in use: {pfad}",
        "Dieses Programm wurde ohne die genannten Bibliotheken gebündelt und ist damit "
        "unvollständig.":
            "This program was bundled without the libraries named above and is therefore "
            "incomplete.",
        "eingebettet": "bundled",
        "Diese Fassung läuft als eigenständiges Programm - die Bibliotheken sind "
        "fest eingebettet, es muss nichts installiert werden.":
            "This build runs as a self-contained program - the libraries are bundled into "
            "it, nothing needs to be installed.",
        "Fehler: Es fehlen folgende Pakete: {pakete}":
            "Error: the following packages are missing: {pakete}",
        "Installation:  pip install qrcode Pillow":
            "Install them with:  pip install qrcode Pillow",

        # --- Formatbeschreibungen -----------------------------------------
        "Verlustfrei mit Transparenz - Standard für Web und Druck":
            "Lossless with transparency - the standard for web and print",
        "Vektor, beliebig skalierbar - ideal für Druck und Layout":
            "Vector, scales to any size - ideal for print and layout",
        "Komprimiert, keine Transparenz - für Fotoworkflows":
            "Compressed, no transparency - for photo workflows",
        "Kompakt mit Transparenz - für moderne Webseiten":
            "Compact with transparency - for modern websites",
        "Verlustfrei mit DPI-Angabe - für die Druckvorstufe":
            "Lossless with a DPI value - for prepress",
        "Unkomprimiert und sehr einfach - für ältere Software":
            "Uncompressed and very simple - for older software",
        "Indizierte Farben - Hintergrund wird immer gefüllt":
            "Indexed colours - the background is always filled",
        "Windows-Symboldatei - maximal 256 Pixel":
            "Windows icon file - 256 pixels at most",
        "Druckfertige Seite mit DPI-Angabe": "Print-ready page with a DPI value",
        "PostScript für klassische Druckereien": "PostScript for traditional print shops",

        # --- Fehlerkorrekturstufen ----------------------------------------
        "L - niedrig (ca. 7 % wiederherstellbar)": "L - low (about 7 % recoverable)",
        "M - mittel (ca. 15 %)": "M - medium (about 15 %)",
        "Q - hoch (ca. 25 %)": "Q - high (about 25 %)",
        "H - sehr hoch (ca. 30 %, für Logos und Aufkleber)":
            "H - very high (about 30 %, for logos and stickers)",

        # --- Reiter 2: Erklärungen ----------------------------------------
        "In drei Schritten zum QR-Code": "Three steps to a QR code",
        "1.  Inhalt in das Textfeld schreiben - eine Adresse, einen Text, "
        "Kontaktdaten oder was sonst gescannt werden soll.\n"
        "2.  Format und Größe wählen. Die Vorschau zeigt sofort, wie der Code aussieht.\n"
        "3.  Auf 'Speichern unter ...' klicken (oder Strg+S drücken) und einen "
        "Ablageort wählen.\n\n"
        "Sind mehrere Zeilen eingetragen und der Stapelmodus eingeschaltet, entsteht "
        "aus jeder Zeile ein eigener Code; gefragt wird dann nach einem Zielordner.":
            "1.  Type the content into the text box - an address, some text, contact "
            "details or whatever should be scanned.\n"
            "2.  Pick a format and a size. The preview shows the result straight away.\n"
            "3.  Click 'Save as ...' (or press Ctrl+S) and choose where to put the file."
            "\n\n"
            "With several lines entered and batch mode switched on, every line becomes "
            "its own code and you are asked for a target folder instead.",
        "Die Formate im Überblick": "The formats at a glance",
        "Verlangt ein Format eine Einstellung, die es nicht beherrscht - etwa "
        "Transparenz bei JPEG oder mehr als 256 Pixel bei ICO -, wird die Einstellung "
        "angepasst und in der Statuszeile erklärt.":
            "Whenever a format is asked for something it cannot do - transparency in "
            "JPEG, say, or more than 256 pixels in ICO - the setting is adjusted and "
            "the status line explains why.",
        "Je höher die Stufe, desto mehr Schmutz, Knicke oder Überdeckung verträgt der "
        "Code - er braucht dafür aber mehr Module und wirkt feiner. Für Aufkleber und "
        "Aufdrucke lohnt sich Q oder H, für die Anzeige am Bildschirm genügt M.":
            "The higher the level, the more dirt, creases or coverage the code "
            "tolerates - but it needs more modules and its pattern gets finer. Q or H "
            "pay off for stickers and printing; M is plenty for on-screen use.",
        "Größe und Rand": "Size and quiet zone",
        "Die Größe ist die Kantenlänge des fertigen Bildes in Pixeln (32 bis 10000). "
        "Gezeichnet wird zuerst mit einer ganzzahligen Modulgröße und nur bei Bedarf "
        "ohne Weichzeichnen auf das Endmaß gebracht - so bleiben die Modulkanten hart "
        "und der Code gut lesbar. Bei SVG ist die Angabe nur das Grundmaß, die Datei "
        "bleibt beliebig skalierbar.\n\n"
        "Anhaltspunkte: 256 px für Bildschirm und E-Mail, 512 bis 1024 px für Web und "
        "Präsentationen, ab 2048 px oder SVG für den Druck.\n\n"
        "Der Rand (die Ruhezone) sollte laut Norm mindestens 4 Module betragen. "
        "Ohne diesen freien Rahmen erkennen viele Lesegeräte den Code nicht.":
            "The size is the edge length of the finished image in pixels (32 to 10000). "
            "The code is first drawn at a whole-number module size and only scaled to "
            "the final measurement if needed, without smoothing - that keeps the module "
            "edges crisp and the code easy to read. For SVG the value is merely a base "
            "measurement; the file scales to any size.\n\n"
            "Rules of thumb: 256 px for screen and e-mail, 512 to 1024 px for web and "
            "presentations, 2048 px or SVG for print.\n\n"
            "The quiet zone should be at least 4 modules wide according to the "
            "standard. Without that empty frame many readers fail to see the code.",
        "Gut lesbare Codes": "Codes that scan well",
        "Dunkle Module auf hellem Grund funktionieren am zuverlässigsten. Ist der "
        "Kontrast zu gering oder die Darstellung umgekehrt, erscheint unten links ein "
        "Hinweis - der Code wird trotzdem erzeugt, sollte dann aber vor dem Druck "
        "getestet werden.\n\n"
        "Umlaute und andere Sonderzeichen werden als UTF-8 gespeichert. Sehr alte "
        "Lesegeräte deuten sie gelegentlich falsch; im Zweifel vorher ausprobieren.":
            "Dark modules on a light ground work most reliably. If the contrast is too "
            "low or the rendering inverted, a note appears at the bottom left - the "
            "code is still produced, but should be tested before printing.\n\n"
            "Accented and other special characters are stored as UTF-8. Very old "
            "readers occasionally misinterpret them; when in doubt, try it first.",
        "Kommandozeile": "Command line",
        "Mit Argumenten aufgerufen arbeitet das Programm ohne Oberfläche - praktisch "
        "für viele Codes auf einmal:":
            "Called with arguments the program works without a window - handy for many "
            "codes at once:",

        # --- Reiter 3: Info & Copyright -----------------------------------
        "Über dieses Programm": "About this program",
        "Erzeugt QR-Codes aus beliebigen textbasierten Inhalten und speichert sie als "
        "Bilddatei - in zehn Formaten und in jeder gewünschten Größe. Farbschema, "
        "Sprachumschaltung und Aufbau folgen der Bild-Toolbox.\n\n"
        "Das gesamte Programm steckt in einer einzigen Datei und läuft wahlweise mit "
        "dieser Oberfläche oder auf der Kommandozeile.\n\n"
        "Tastatur: Strg+S speichert den angezeigten Code.":
            "Creates QR codes from any text-based content and saves them as an image "
            "file - in ten formats and at any size you like. Colour scheme, language "
            "switching and layout follow the Bild-Toolbox.\n\n"
            "The whole program lives in a single file and runs either with this window "
            "or on the command line.\n\n"
            "Keyboard: Ctrl+S saves the code on display.",
        "Bibliotheken": "Libraries",
        "kodiert den Inhalt als QR-Matrix": "encodes the content as a QR matrix",
        "zeichnet und speichert die Bilddateien": "draws and saves the image files",
        "stellt diese Oberfläche dar": "renders this window",
        "Lizenz und Copyright": "Licence and copyright",
        "Hiermit wird unentgeltlich jeder Person, die eine Kopie dieser Software und "
        "der zugehörigen Dokumentation erhält, die Erlaubnis erteilt, sie "
        "uneingeschränkt zu nutzen, zu kopieren, zu verändern und weiterzugeben - "
        "unter der Bedingung, dass dieser Copyright-Vermerk und der Lizenztext in "
        "allen Kopien enthalten bleiben.\n\n"
        "Die Software wird ohne jede Gewähr bereitgestellt.":
            "Permission is hereby granted, free of charge, to any person obtaining a "
            "copy of this software and its associated documentation, to use, copy, "
            "modify and distribute it without restriction - provided that this "
            "copyright notice and the licence text remain in all copies.\n\n"
            "The software is provided without any warranty.",
        "Sprache und Darstellung": "Language and appearance",
        "Die Auswahl oben rechts stellt Sprache und Farbschema um; beides wird neben "
        "dem Programm in der Datei '{datei}' gespeichert und beim nächsten Start "
        "wieder verwendet. Ohne gespeicherte Einstellung richtet sich die Sprache nach "
        "dem Betriebssystem.\n\n"
        "Quellsprache ist Deutsch. Eine weitere Sprache entsteht durch einen Eintrag "
        "in den Tabellen LANGUAGE_NAMES und TRANSLATIONS am Ende der Programmdatei; "
        "nicht übersetzte Zeilen erscheinen weiterhin auf Deutsch.":
            "The controls in the top right switch language and colour scheme; both are "
            "stored next to the program in the file '{datei}' and reused on the next "
            "start. Without a stored setting the language follows the operating "
            "system.\n\n"
            "German is the source language. A further language is added by an entry in "
            "the LANGUAGE_NAMES and TRANSLATIONS tables at the end of the program file; "
            "untranslated lines keep appearing in German.",

        # --- Kommandozeile ------------------------------------------------
        "QR-Codes aus Text erzeugen und speichern.":
            "Create QR codes from text and save them.",
        "Beispiele:\n"
        '  qr_generator.py                                  Oberfläche starten\n'
        '  qr_generator.py "https://example.org"            PNG 512 px im aktuellen Ordner\n'
        '  qr_generator.py "Hallo Welt" -o hallo.svg        Format aus der Endung\n'
        '  qr_generator.py "Text" -f PNG -s 1024 -e H       Größe und Fehlerkorrektur\n'
        '  qr_generator.py "Text" -f PNG -s 256 --transparent\n'
        "  qr_generator.py --datei inhalt.txt -o code.png   Inhalt aus einer Textdatei\n"
        '  echo "Text" | qr_generator.py - -o code.png      Inhalt aus der Pipeline\n'
        "  qr_generator.py --stapel liste.txt -a ausgabe -f SVG\n":
            "Examples:\n"
            "  qr_generator.py                                  open the window\n"
            '  qr_generator.py "https://example.org"            PNG 512 px in this folder\n'
            '  qr_generator.py "Hello world" -o hello.svg       format from the extension\n'
            '  qr_generator.py "Text" -f PNG -s 1024 -e H       size and error correction\n'
            '  qr_generator.py "Text" -f PNG -s 256 --transparent\n'
            "  qr_generator.py --datei content.txt -o code.png  content from a text file\n"
            '  echo "Text" | qr_generator.py - -o code.png      content from the pipeline\n'
            "  qr_generator.py --stapel list.txt -a output -f SVG\n",
        "Ausgabe": "Output",
        "Gestaltung": "Appearance",
        "Sonstiges": "Other",
        'Inhalt des QR-Codes; "-" liest von der Standardeingabe':
            'content of the QR code; "-" reads from standard input',
        "Inhalt aus einer Textdatei lesen (UTF-8)":
            "read the content from a text file (UTF-8)",
        "Stapeldatei: je Zeile ein Code, optional 'Inhalt | Dateiname'":
            "batch file: one code per line, optionally 'content | file name'",
        "Zieldatei (ohne Endung wird die des Formats ergänzt)":
            "target file (without an extension the format's own is appended)",
        "Zielordner, wenn kein Dateiname angegeben ist (Vorgabe: .)":
            "target folder when no file name is given (default: .)",
        "Ausgabeformat: {formate} (Vorgabe: PNG bzw. aus der Endung)":
            "output format: {formate} (default: PNG, or taken from the extension)",
        "Kantenlänge in Pixel, {min}-{max} (Vorgabe: 512)":
            "edge length in pixels, {min}-{max} (default: 512)",
        "Auflösungsangabe für PNG/TIFF/PDF (Vorgabe: 300)":
            "resolution value for PNG/TIFF/PDF (default: 300)",
        "Kompressionsqualität für JPEG und WEBP (Vorgabe: 95)":
            "compression quality for JPEG and WEBP (default: 95)",
        "vorhandene Dateien ersetzen statt zu nummerieren":
            "replace existing files instead of numbering them",
        "Fehlerkorrektur L/M/Q/H (Vorgabe: M)":
            "error correction L/M/Q/H (default: M)",
        "Ruhezone in Modulen, Norm ist 4 (Vorgabe: 4)":
            "quiet zone in modules, the standard is 4 (default: 4)",
        'Modulfarbe, z. B. "#000000" oder "black"':
            'module colour, e.g. "#000000" or "black"',
        'Hintergrundfarbe (Vorgabe: "#FFFFFF")': 'background colour (default: "#FFFFFF")',
        "transparenter Hintergrund (PNG, SVG, WEBP, TIFF, ICO)":
            "transparent background (PNG, SVG, WEBP, TIFF, ICO)",
        "feste QR-Version erzwingen (Vorgabe: automatisch)":
            "force a fixed QR version (default: automatic)",
        "unterstützte Formate auflisten und beenden":
            "list the supported formats and exit",
        "Oberfläche starten, auch wenn Argumente angegeben sind":
            "open the window even when arguments are given",
        "Sprache der Ausgabe, z. B. de oder en":
            "language of the output, e.g. de or en",
        "keine Statusmeldungen ausgeben": "print no status messages",
        "unterstützte Formate": "supported formats",
        "(max. {kante} px)": "({kante} px max.)",
        "{format} erlaubt höchstens {kante} px - Größe angepasst.":
            "{format} allows {kante} px at most - size adjusted.",
        "Hinweis: --format {format} hat Vorrang vor der Endung der Zieldatei ({endung}).":
            "Note: --format {format} takes precedence over the target file's extension "
            "({endung}).",
        "{format} kennt keine Transparenz - Hintergrund wird gefüllt.":
            "{format} has no transparency - the background is filled in.",
        "(Version {version}, {module} Module)": "(version {version}, {module} modules)",
        "Fertig: {gut} von {gesamt} Dateien geschrieben.":
            "Done: wrote {gut} of {gesamt} files.",
        "Gespeichert: {pfad}": "Saved: {pfad}",
        "Abgebrochen.": "Cancelled.",
        "Format {format}, {kante} px, Version {version} ({module} Module), "
        "Fehlerkorrektur {stufe}, {zeichen} Zeichen":
            "format {format}, {kante} px, version {version} ({module} modules), "
            "error correction {stufe}, {zeichen} characters",
    },
}


# --------------------------------------------------------------------------
# Einstieg
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser_sprache = startup_language()

    # Die Sprache muss stehen, bevor argparse seine Hilfetexte zusammenbaut.
    if "--sprache" in argv:
        stelle = argv.index("--sprache")
        if stelle + 1 < len(argv):
            gewuenscht = argv[stelle + 1].strip().lower()
            if gewuenscht == SOURCE_LANGUAGE or gewuenscht in TRANSLATIONS:
                parser_sprache = gewuenscht
    _.language = parser_sprache

    parser = argumente_parser()
    args = parser.parse_args(argv)

    if args.gui or not argv:
        return gui_starten(args if argv else None)

    try:
        return cli_main(args)
    except QRFehler as exc:
        print(_("Fehler: {text}").format(text=exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n" + _("Abgebrochen."), file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
