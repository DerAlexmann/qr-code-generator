"""Sammelt die vollständigen Lizenztexte der mitgelieferten Komponenten.

`DRITTANBIETER-LIZENZEN.md` nennt die Komponenten und verlinkt sie. MIT, BSD,
die zlib-Lizenz und die FreeType-Lizenz verlangen aber mehr als einen Verweis:
Bei der Weitergabe eines Binärbündels muss der Lizenztext selbst beiliegen.

Die Texte werden hier nicht ins Repository gelegt, sondern beim Bauen aus den
Paketen geholt, die tatsächlich installiert sind. Das hat zwei Vorteile: Sie
passen immer zu der Fassung, die in der EXE steckt, und es gibt keine Kopie,
die beim nächsten Versionssprung still veraltet.

Pillows Lizenzdatei ist dabei die wichtigste: Pillow bindet seine Bilddecoder
fest in die eigenen Erweiterungsmodule ein und sammelt deren Lizenztexte –
libjpeg-turbo, libpng, libtiff, libwebp, FreeType, HarfBuzz, Little CMS,
OpenJPEG, libavif, brotli und zlib – vollständig in dieser einen Datei.

Aufruf:  python lizenztexte_sammeln.py [Zielordner]
"""

from __future__ import annotations

import importlib.metadata as metadata
import shutil
import sys
from pathlib import Path

# Die Pakete, die im Bündel landen. colorama zieht pip als Abhängigkeit von
# qrcode mit, PyInstaller nimmt es aber nicht auf - geprüft an der fertigen
# EXE von 1.1.7, in der weder colorama noch pypng vorkommt.
PAKETE = ("qrcode", "Pillow", "pyinstaller")

# Dateinamen, unter denen Pakete ihre Lizenz ablegen. Die Schreibweise und der
# Ort sind nicht einheitlich: qrcode legt LICENSE direkt in die .dist-info,
# Pillow und PyInstaller in deren Unterordner licenses/.
LIZENZNAMEN = ("license", "licence", "copying", "notice")

UEBERSICHT = "00-UEBERSICHT.txt"

# Unter dieser Groesse ist eine Lizenzdatei kein Lizenztext, sondern ein
# Platzhalter. Der kuerzeste echte Text hier (qrcode, BSD 3-Clause) hat rund
# 2 KB; die MIT-Lizenz kommt auf etwa 1 KB.
MINDESTGROESSE = 500

KOPF = """Lizenztexte der Komponenten im QR-Code-Generator
================================================

Diese Sammlung entsteht beim Bauen der Windows-EXE aus den Paketen, die dafür
installiert wurden - die Texte passen deshalb genau zu der EXE, die daneben
liegt. Welche Komponente was tut und unter welcher Lizenz steht, steht in
DRITTANBIETER-LIZENZEN.md.

Enthalten:

"""

FUSS = """
Nicht als Text enthalten, sondern verlinkt
------------------------------------------

Der Windows-Build von Python bringt weitere Bestandteile mit, die nicht als
eigene Lizenzdatei in der Installation liegen - darunter Tcl/Tk (die
Oberfläche), OpenSSL, zlib und liblzma. Ihre Lizenztexte stehen vollständig
auf der Lizenzseite von Python, Abschnitt "Licenses and Acknowledgements for
Incorporated Software":

    https://docs.python.org/3/license.html

Die Lizenz von Tcl/Tk zusätzlich hier:

    https://www.tcl-lang.org/software/tcltk/license.html

Systembibliotheken von Windows (VCRUNTIME140.dll, api-ms-win-*) gehören zum
Betriebssystem und sind nicht aufgeführt.
"""


def lizenzdateien(paket: str) -> list[Path]:
    """Die Lizenzdateien eines installierten Pakets, aus dessen .dist-info."""
    verteilung = metadata.distribution(paket)
    gefunden = []
    for eintrag in verteilung.files or ():
        if ".dist-info" not in str(eintrag):
            continue
        if not Path(eintrag.name).stem.lower().startswith(LIZENZNAMEN):
            continue
        pfad = Path(verteilung.locate_file(eintrag))
        if pfad.is_file():
            gefunden.append(pfad)
    return gefunden


def python_lizenz() -> Path:
    """Die Lizenzdatei der Python-Installation, mit der gebaut wird."""
    pfad = Path(sys.base_prefix) / "LICENSE.txt"
    if not pfad.is_file():
        raise SystemExit(f"Die Python-Installation hat keine LICENSE.txt ({pfad}). "
                         "Ohne sie wäre die Sammlung unvollständig.")
    return pfad


def ablegen(quelle: Path, ziel: Path, name: str, schon_da: set[str]) -> str:
    """Einen Lizenztext ablegen - und dabei nichts stillschweigend verlieren."""
    if name in schon_da:
        # Zwei Dateien gleichen Namens aus verschiedenen Ordnern einer
        # .dist-info wuerden sich sonst gegenseitig ueberschreiben, und die
        # Uebersicht fuehrte den Namen zweimal auf.
        raise SystemExit(f"Zwei Lizenzdateien wollen als {name} abgelegt werden.")
    if quelle.stat().st_size < MINDESTGROESSE:
        raise SystemExit(f"{quelle} ist nur {quelle.stat().st_size} Bytes gross - "
                         "das ist kein Lizenztext.")
    shutil.copyfile(quelle, ziel / name)
    schon_da.add(name)
    return name


def main(ziel: Path) -> None:
    # Ein Ordner mit Resten eines frueheren Laufs waere tueckisch: Die
    # Dateinamen tragen die Versionsnummer, alte Texte blieben also liegen,
    # kaemen mit ins ZIP und stuenden nicht in der Uebersicht. Auf einem
    # frischen Runner ist der Ordner leer; lokal wird abgebrochen.
    if ziel.exists() and any(ziel.iterdir()):
        raise SystemExit(f"{ziel} ist nicht leer. Bitte den Ordner wegraeumen - "
                         "Reste eines frueheren Laufs kaemen sonst mit ins ZIP.")
    ziel.mkdir(parents=True, exist_ok=True)

    zeilen: list[str] = []
    abgelegt: set[str] = set()

    for paket in PAKETE:
        dateien = lizenzdateien(paket)
        if not dateien:
            # Lieber laut abbrechen: Eine stillschweigend fehlende Lizenz ist
            # genau der Mangel, den diese Sammlung verhindern soll.
            raise SystemExit(f"Im Paket {paket} war keine Lizenzdatei zu finden.")
        version = metadata.version(paket)
        for datei in dateien:
            name = f"{paket}-{version}-{datei.name}"
            if not name.lower().endswith(".txt"):
                name += ".txt"
            zeilen.append(f"  {ablegen(datei, ziel, name, abgelegt)}")

    quelle = python_lizenz()
    name = f"Python-{'.'.join(map(str, sys.version_info[:3]))}-{quelle.name}"
    zeilen.append(f"  {ablegen(quelle, ziel, name, abgelegt)}")

    (ziel / UEBERSICHT).write_text(KOPF + "\n".join(zeilen) + "\n" + FUSS,
                                   encoding="utf-8", newline="\n")
    print(f"{len(zeilen)} Lizenztexte in {ziel}")
    for zeile in zeilen:
        print(zeile)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "lizenztexte"))
