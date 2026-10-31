# Lizenzen der Fremdkomponenten

Der Quellcode des QR-Code-Generators steht unter der MIT-Lizenz – siehe
[LICENSE](LICENSE). Diese Datei listet die Bestandteile anderer Projekte auf, die in der
fertigen **Windows-EXE** mitgeliefert werden, und sagt, was daraus folgt.

*English version below – [Licenses of third-party components](#licenses-of-third-party-components).*

## Das Wichtigste in vier Sätzen

- **Der Quellcode bleibt MIT.** Daran ändert diese Datei nichts.
- **Das Skript** `qr_generator.py` liefert nichts mit. `qrcode` und Pillow installieren
  Sie selbst; es gilt jeweils deren eigene Lizenz.
- **Die Windows-EXE** enthält zusätzlich die Python-Laufzeit, Tcl/Tk und die
  Bibliotheken von Pillow – **alle mit freizügigen Lizenzen**. Die EXE darf deshalb
  auch als Gesamtwerk unter der MIT-Lizenz weitergegeben werden.
- Es ist **kein Bestandteil unter GPL oder LGPL** enthalten, der auf das Gesamtwerk
  durchschlägt. Die einzige GPL-Komponente ist der Bootloader von PyInstaller, und
  dessen Lizenz nimmt damit erzeugte Programme ausdrücklich aus.

### Warum bleibt alles MIT?

Nachgesehen statt angenommen: Die Namen der mitgelieferten Bibliotheken lassen sich aus
der fertigen EXE auslesen (`grep -a -o -E '[A-Za-z0-9_.+-]+\.(dll|pyd)'`). Darin steckt
keine Bibliothek mit ansteckender Lizenz – anders als bei Bildformaten wie HEIC, die
unter Windows üblicherweise GPL-Teile mitbringen. Der QR-Code-Generator braucht nichts
davon: Er zeichnet seine Ausgabe selbst und schreibt nur Formate, die Pillow von Haus
aus kann.

Zwei Komponenten verlangen aber mehr als bloßes Dulden:

- **FreeType** ist doppelt lizenziert – FreeType-Lizenz (FTL) **oder** GPLv2. Hier gilt
  die FTL, und die verlangt, dass ihr Text und ihr Urhebervermerk beiliegen.
- **MIT, BSD und die zlib-Lizenz** verlangen bei der Weitergabe eines Binärbündels
  ebenfalls den Lizenztext selbst, nicht nur einen Verweis.

Deshalb liegt jedem Release die Datei `QR-Code-Generator-lizenztexte.zip` mit den
vollständigen Texten bei – siehe [Vollständige Lizenztexte](#vollständige-lizenztexte).

## Was in der Windows-EXE steckt

| Bestandteil | Lizenz | Lizenztext und Quellcode |
|---|---|---|
| **Python 3.12** – Laufzeit und Standardbibliothek | PSF License 2.0 | [docs.python.org](https://docs.python.org/3/license.html) |
| **Tcl/Tk 8.6** – die Oberfläche (`tcl86t.dll`, `tk86t.dll`) | Tcl/Tk-Lizenz (BSD-artig) | [tcl-lang.org](https://www.tcl-lang.org/software/tcltk/license.html) |
| **qrcode** – kodiert den Inhalt als QR-Matrix | BSD 3-Clause | [LICENSE](https://github.com/lincolnloop/python-qrcode/blob/main/LICENSE) |
| **Pillow** – zeichnet und speichert die Bilddateien | MIT-CMU | [LICENSE](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| **zlib** (`zlib1.dll`) – Packen in PNG und ZIP | zlib-Lizenz | [zlib.net](https://zlib.net/zlib_license.html) |
| **OpenSSL** (`libssl-3.dll`, `libcrypto-3.dll`) – Teil der Python-Laufzeit | Apache License 2.0 | [openssl-library.org](https://openssl-library.org/source/license/) |
| **libffi** (`libffi-8.dll`) – Teil der Python-Laufzeit | MIT | [LICENSE](https://github.com/libffi/libffi/blob/master/LICENSE) |
| **bzip2** (`_bz2.pyd`) – Teil der Python-Laufzeit | BSD-artig | [sourceware.org](https://sourceware.org/bzip2/) |
| **XZ Utils / liblzma** (`_lzma.pyd`) – Teil der Python-Laufzeit | 0BSD (Kernteil gemeinfrei) | [tukaani.org](https://tukaani.org/xz/) |
| **Expat** (`pyexpat.pyd`) – XML-Leser der Standardbibliothek | MIT | [COPYING](https://github.com/libexpat/libexpat/blob/master/expat/COPYING) |
| **PyInstaller** – dessen Bootloader startet die gepackte Anwendung | GPLv2 **mit** Ausnahme für damit erzeugte Programme | [Lizenzhinweis](https://pyinstaller.org/en/stable/license.html) |

OpenSSL, libffi, bzip2 und liblzma benutzt das Programm nicht – es geht nicht ins Netz
und liest keine Archive. Sie stecken in der EXE, weil PyInstaller die
Standardbibliothek von Python mitnimmt, und sind deshalb hier aufgeführt.

### Vollständige Lizenztexte

An jedem Release hängt `QR-Code-Generator-lizenztexte.zip`. Darin liegen die Texte von
`qrcode`, Pillow, PyInstaller und Python, jeweils mit der Versionsnummer im Dateinamen.

Die Sammlung entsteht beim Bauen durch `lizenztexte_sammeln.py` aus den Paketen, die
dafür installiert wurden. Sie passt damit immer zu genau der EXE, die daneben liegt –
eine Kopie im Repository würde beim nächsten Versionssprung still veralten.

Nicht als Text enthalten, sondern verlinkt: Tcl/Tk, OpenSSL, zlib, bzip2, liblzma und
Expat. Diese Bestandteile liegen im Windows-Build von Python, der ihre Lizenztexte nicht
als eigene Dateien mitbringt. Sie stehen vollständig auf der
[Lizenzseite von Python](https://docs.python.org/3/license.html) im Abschnitt *Licenses
and Acknowledgements for Incorporated Software*.

Der Quellcode des QR-Code-Generators selbst liegt zu jeder Version als ZIP am
[Release](../../releases) und im Verlauf dieses Repositorys.

### Weitere Bibliotheken innerhalb von Pillow

Pillow bindet seine Bilddecoder fest in die eigenen Erweiterungsmodule ein (`_imaging`,
`_imagingcms`, `_imagingft`, `_webp`, `_avif`). Sie erscheinen deshalb nicht als eigene
Dateien, sind aber mit in der EXE: **libjpeg-turbo, libpng, libtiff, libwebp, FreeType,
HarfBuzz, Little CMS, OpenJPEG, libavif** (mit **aom** und **dav1d**), **brotli, XZ
Utils** und **zlib**. Ihre vollständigen Lizenztexte stehen gesammelt in der
[LICENSE-Datei von Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE),
die in jedem Pillow-Paket mitgeliefert wird und über `lizenztexte_sammeln.py` im Release
landet.

### Der Bootloader von PyInstaller

PyInstaller steht unter GPLv2, macht für den Bootloader aber eine ausdrückliche
Ausnahme: Programme, die damit gepackt werden, dürfen unter beliebiger Lizenz
weitergegeben werden – auch unter MIT, auch ohne Offenlegung. Nur Änderungen am
Bootloader selbst fielen unter die GPL. Daran ändert dieses Projekt nichts; es benutzt
den unveränderten Bootloader aus dem Paket.

### Nicht aufgeführt: Systembibliotheken von Windows

Dateien wie `VCRUNTIME140.dll`, `ucrtbase.dll` oder die `api-ms-win-*`-Bibliotheken
gehören zum Betriebssystem beziehungsweise zu dessen Laufzeitumgebung und werden hier
nicht einzeln aufgeführt.

## Pflege dieser Datei

Kommt eine Abhängigkeit hinzu oder fällt eine weg, gehört das hier hinein. Der Test
`tests/test_verpackung.py` prüft, dass jedes Paket aus `requirements.txt` und
`requirements-build.txt` in **beiden** Sprachabschnitten dieser Datei vorkommt und dass
sie dem Release beiliegt – er schlägt fehl, wenn das vergessen wird.

---

# Licenses of third-party components

The QR-Code-Generator source code is licensed under the MIT License – see
[LICENSE](LICENSE). This file lists the components from other projects that ship inside
the finished **Windows executable**, and what follows from that.

## The short version

- **The source code stays MIT.** This file changes nothing about that.
- **The script** `qr_generator.py` bundles nothing. You install `qrcode` and Pillow
  yourself, and their own licenses apply.
- **The Windows executable** additionally contains the Python runtime, Tcl/Tk and
  Pillow's libraries – **all of them permissively licensed**. The executable may
  therefore be distributed as a whole under the MIT License as well.
- **No component under the GPL or LGPL** affects the work as a whole. The only GPL
  component is PyInstaller's bootloader, and its license explicitly exempts the programs
  it builds.

### Why does everything stay MIT?

Checked rather than assumed: the names of the bundled libraries can be read out of the
finished executable (`grep -a -o -E '[A-Za-z0-9_.+-]+\.(dll|pyd)'`). None of them carries
a copyleft license – unlike image formats such as HEIC, which on Windows usually bring
GPL parts along. The QR-Code-Generator needs none of that: it draws its output itself and
only writes formats Pillow supports out of the box.

Two components ask for more than mere tolerance, though:

- **FreeType** is dual-licensed – the FreeType License (FTL) **or** GPLv2. The FTL
  applies here, and it requires its text and copyright notice to be included.
- **MIT, BSD and the zlib license** likewise require the license text itself to
  accompany a binary distribution, not just a link.

That is why every release ships `QR-Code-Generator-lizenztexte.zip` with the full texts –
see [Full license texts](#full-license-texts).

## What is inside the Windows executable

| Component | License | License text and source |
|---|---|---|
| **Python 3.12** – runtime and standard library | PSF License 2.0 | [docs.python.org](https://docs.python.org/3/license.html) |
| **Tcl/Tk 8.6** – the user interface (`tcl86t.dll`, `tk86t.dll`) | Tcl/Tk license (BSD-style) | [tcl-lang.org](https://www.tcl-lang.org/software/tcltk/license.html) |
| **qrcode** – encodes the content as a QR matrix | BSD 3-Clause | [LICENSE](https://github.com/lincolnloop/python-qrcode/blob/main/LICENSE) |
| **Pillow** – draws and saves the image files | MIT-CMU | [LICENSE](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| **zlib** (`zlib1.dll`) – compression for PNG and ZIP | zlib license | [zlib.net](https://zlib.net/zlib_license.html) |
| **OpenSSL** (`libssl-3.dll`, `libcrypto-3.dll`) – part of the Python runtime | Apache License 2.0 | [openssl-library.org](https://openssl-library.org/source/license/) |
| **libffi** (`libffi-8.dll`) – part of the Python runtime | MIT | [LICENSE](https://github.com/libffi/libffi/blob/master/LICENSE) |
| **bzip2** (`_bz2.pyd`) – part of the Python runtime | BSD-style | [sourceware.org](https://sourceware.org/bzip2/) |
| **XZ Utils / liblzma** (`_lzma.pyd`) – part of the Python runtime | 0BSD (core in the public domain) | [tukaani.org](https://tukaani.org/xz/) |
| **Expat** (`pyexpat.pyd`) – the standard library's XML parser | MIT | [COPYING](https://github.com/libexpat/libexpat/blob/master/expat/COPYING) |
| **PyInstaller** – its bootloader starts the packaged application | GPLv2 **with** an exception for the programs it builds | [license notice](https://pyinstaller.org/en/stable/license.html) |

The program uses neither OpenSSL, libffi, bzip2 nor liblzma – it does not access the
network and does not read archives. They are in the executable because PyInstaller
bundles Python's standard library, and they are listed here for that reason.

### Full license texts

Every release has `QR-Code-Generator-lizenztexte.zip` attached. It contains the texts for
`qrcode`, Pillow, PyInstaller and Python, each with its version number in the file name.

The collection is assembled at build time by `lizenztexte_sammeln.py` from the packages
that were installed for it. It therefore always matches the exact executable next to it –
a copy kept in the repository would quietly go stale at the next version bump.

Not included as text but linked: Tcl/Tk, OpenSSL, zlib, bzip2, liblzma and Expat. These
parts live inside the Windows build of Python, which does not ship their license texts as
separate files. They are printed in full on
[Python's license page](https://docs.python.org/3/license.html) in the section *Licenses
and Acknowledgements for Incorporated Software*.

The source code of the QR-Code-Generator itself is attached to every
[release](../../releases) as a ZIP file and is part of this repository's history.

### Further libraries inside Pillow

Pillow links its image decoders into its own extension modules (`_imaging`,
`_imagingcms`, `_imagingft`, `_webp`, `_avif`). They therefore do not appear as separate
files, but they are in the executable: **libjpeg-turbo, libpng, libtiff, libwebp,
FreeType, HarfBuzz, Little CMS, OpenJPEG, libavif** (with **aom** and **dav1d**),
**brotli, XZ Utils** and **zlib**. Their full license texts are collected in
[Pillow's LICENSE file](https://github.com/python-pillow/Pillow/blob/main/LICENSE), which
ships inside every Pillow package and reaches the release through
`lizenztexte_sammeln.py`.

### PyInstaller's bootloader

PyInstaller is licensed under GPLv2 but makes an explicit exception for its bootloader:
programs packaged with it may be distributed under any license – including MIT, including
without disclosing source. Only changes to the bootloader itself would fall under the
GPL. This project changes nothing there; it uses the unmodified bootloader from the
package.

### Not listed: Windows system libraries

Files such as `VCRUNTIME140.dll`, `ucrtbase.dll` or the `api-ms-win-*` libraries belong to
the operating system and its runtime environment and are not listed individually here.

## Keeping this file current

When a dependency is added or dropped, it belongs in here. The test
`tests/test_verpackung.py` checks that every package from `requirements.txt` and
`requirements-build.txt` appears in **both** language sections of this file and that the
file ships with the release – it fails if that is forgotten.
