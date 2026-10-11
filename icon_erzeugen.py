"""Erzeugt das Programmsymbol qr_code_generator.ico.

Gezeichnet wird ein stilisierter QR-Code in Weiss auf einer abgerundeten
Flaeche im Akzentblau des Farbschemas. Die .ico enthaelt alle ueblichen
Groessen, vom Reiter der Taskleiste bis zur grossen Kachel im Explorer.

Das Sinnbild bleibt grob: drei Eckmarken, eine Taktspur und eine Handvoll
Datenmodule. Ein echter QR-Code mit 21 Modulen je Kante waere bei 16 Pixeln
nur noch ein grauer Fleck - bei sieben Modulen ist die Form auch im kleinen
Reiter der Taskleiste noch zu erkennen.

Fuer 16 und 24 Pixel steht trotzdem eine zweite, groebere Zeichnung in der
Datei: dort hat eine Eckmarke rechnerisch keine zwei Pixel fuer ihren Ring,
die Aussparung fliesst zu und das Ganze wird ein Fleck. Die kleine Fassung
verzichtet deshalb auf Ring und Taktspur und setzt auf fuenf statt sieben
Module.

Aufruf:  python icon_erzeugen.py
Benoetigt:  pip install Pillow
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr_code_generator.ico")
KANTE = 1024                                  # Vorlage, wird heruntergerechnet
GROESSEN = [16, 24, 32, 48, 64, 128, 256]

BLAU = (47, 125, 225, 255)                    # ACCENT des hellen Schemas
WEISS = (255, 255, 255, 255)

INNENRAND = KANTE * 5 // 32                   # Abstand vom Bildrand zum Raster

# Taktspur und Datenmodule als (Spalte, Zeile), Zaehlung ab 0. Die drei
# Eckmarken belegen je 3x3 Module und stehen deshalb nicht in dieser Liste.
RASTER = 7                                    # Module je Kante des Sinnbilds
MODULE = [
    (3, 0), (3, 2), (0, 3), (2, 3), (3, 3), (4, 3), (6, 3), (3, 4), (3, 6),
    (4, 4), (6, 4), (5, 5), (4, 6), (6, 6),
]

# Die grobe Fassung fuer 16 und 24 Pixel: Eckmarken ohne Ring, zwei Module
# je Kante, dazu drei verstreute Datenmodule. Sie duerfen keine Figur
# bilden - vier symmetrisch gesetzte ergaben ein Pluszeichen zwischen den
# Ecken, und das sieht nach allem aus, nur nicht nach einem QR-Code.
RASTER_KLEIN = 5
MODULE_KLEIN = [(2, 2), (4, 3), (3, 4)]
KLEINE_GROESSEN = (16, 24)


def eckmarke(stift: ImageDraw.ImageDraw, x: float, y: float, einheit: float) -> None:
    """Eine Eckmarke: weisses Quadrat, blaue Aussparung, weisser Kern.

    Die Aussparung ist mit Bedacht breit gehalten. Bei 16 Pixeln fliesst sie
    ohnehin zu, und dann bleibt immer noch ein weisses Quadrat in der Ecke
    stehen - das ist genau das, woran man einen QR-Code erkennt.
    """
    seite = 3 * einheit
    rund = max(1, round(einheit * 0.18))
    stift.rounded_rectangle((x, y, x + seite, y + seite), radius=rund, fill=WEISS)

    loch = einheit * 0.62
    stift.rounded_rectangle((x + loch, y + loch, x + seite - loch, y + seite - loch),
                            radius=max(1, rund // 2), fill=BLAU)

    kern = einheit * 1.18
    stift.rounded_rectangle((x + kern, y + kern, x + seite - kern, y + seite - kern),
                            radius=max(1, rund // 2), fill=WEISS)


def zeichnen(grob: bool = False) -> Image.Image:
    bild = Image.new("RGBA", (KANTE, KANTE), (0, 0, 0, 0))
    stift = ImageDraw.Draw(bild)

    rand = KANTE // 16
    stift.rounded_rectangle((rand, rand, KANTE - rand, KANTE - rand),
                            radius=KANTE // 5, fill=BLAU)

    raster = RASTER_KLEIN if grob else RASTER
    module = MODULE_KLEIN if grob else MODULE
    marke = 2 if grob else 3
    einheit = (KANTE - 2 * INNENRAND) / raster

    for spalte, zeile in ((0, 0), (raster - marke, 0), (0, raster - marke)):
        x, y = INNENRAND + spalte * einheit, INNENRAND + zeile * einheit
        if grob:
            seite = marke * einheit
            stift.rounded_rectangle((x, y, x + seite, y + seite),
                                    radius=max(1, round(einheit * 0.18)), fill=WEISS)
        else:
            eckmarke(stift, x, y, einheit)

    # Einzelne Module etwas kleiner als ihre Zelle - der schmale Spalt laesst
    # das Raster erkennen, statt die Flaeche zuzuschmieren.
    luft = einheit * 0.07
    rund = max(1, round(einheit * 0.15))
    for spalte, zeile in module:
        x = INNENRAND + spalte * einheit + luft
        y = INNENRAND + zeile * einheit + luft
        stift.rounded_rectangle((x, y, x + einheit - 2 * luft, y + einheit - 2 * luft),
                                radius=rund, fill=WEISS)

    return bild


def main() -> None:
    fein = zeichnen()
    grob = zeichnen(grob=True)

    # Jede Groesse wird hier fertig gerechnet und vollstaendig uebergeben.
    # Pillow nimmt aus append_images nur die Bilder, deren Groesse genau
    # passt; fuer alle uebrigen greift es nicht etwa auf die Vorlage zurueck,
    # sondern auf das zuletzt durchlaufene Bild der Liste - und weil
    # thumbnail() nie vergroessert, blieben davon nur Krueppel uebrig.
    bilder = [(grob if n in KLEINE_GROESSEN else fein).resize((n, n), Image.LANCZOS)
              for n in GROESSEN]

    bilder[-1].save(ZIEL, sizes=[(n, n) for n in GROESSEN], append_images=bilder[:-1])
    print("geschrieben:", ZIEL)


if __name__ == "__main__":
    main()
