# QR Code Generator

**Create QR codes from text and save them as an image file** – a desktop program for Windows,
macOS and Linux that turns any text-based content into QR codes, in ten formats and at any size
you like. A single Python file, no installation, no cloud, no telemetry – everything runs
locally.

[![CI](https://github.com/DerAlexmann/qr-code-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/DerAlexmann/qr-code-generator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

*[Deutsche Fassung: **[README.md](README.md)**]*

---

## Screenshots

![The QR code tab with input, settings and live preview](docs/screenshots/qr-code-hell.png)

<details>
<summary><b>More views</b> – dark scheme, guide, about &amp; copyright</summary>

### Dark colour scheme

Switchable at runtime, top right. Switching recolours the existing controls
instead of rebuilding the window.

![The QR code tab in the dark colour scheme](docs/screenshots/qr-code-dunkel.png)

### Guide

A short walkthrough, all formats with their properties, the error correction
levels and notes on size, quiet zone and readability.

![The guide tab](docs/screenshots/erklaerungen.png)

### About & copyright

Details about the program, the libraries actually loaded together with their
versions, and the licence and copyright notice.

![The about and copyright tab](docs/screenshots/info.png)

</details>

---

## Installation

```bash
git clone https://github.com/DerAlexmann/qr-code-generator.git
cd qr-code-generator
pip install -r requirements.txt
```

If you would rather not set up Python, take the ready-made `QR-Code-Generator.exe`
from the [latest release](https://github.com/DerAlexmann/qr-code-generator/releases/latest).

Requires Python 3.9 or newer. Tkinter for the window already ships with the
Windows installers of Python.

For double-clicking there is [`QR-Code-Generator.pyw`](QR-Code-Generator.pyw)
next to it: Windows opens `.pyw` files with `pythonw.exe`, so only the program
window appears and no console window.

## The window

```bash
python qr_generator.py
```

The window has three tabs:

**QR code** – text box, settings and a live preview. Format, size, error
correction, quiet zone, resolution, colours and transparency can all be set;
the preview updates itself after every change. If the colour contrast is too
low for scanning, a note appears at the bottom left. `Ctrl`+`S` saves. With
"Save every line as its own QR code" each line becomes a separate code in a
folder of your choosing.

**Guide** – a short walkthrough, the ten formats and what they can do, the four
error correction levels, notes on size and quiet zone, tips for codes that scan
well, and command line examples.

**About & copyright** – details about the program, the status of the required
libraries, the licence and copyright notice, and an explanation of the language
and appearance settings.

### Language and colour scheme

The language selector and the "Dark" switch sit in the top right. Both take
effect immediately and are stored in `qr-code-generator.json` next to the
script. Without a stored setting the language follows the operating system.
Switching rebuilds the window without losing the entered text or the settings.

German is the source language; English ships with the program. A further
language is added by one entry each in `LANGUAGE_NAMES` and `TRANSLATIONS` at
the end of the program file – untranslated lines keep appearing in German.

## Command line

```bash
python qr_generator.py "https://example.org"                 # PNG, 512 px
python qr_generator.py "Hello world" -o hello.svg            # format from the extension
python qr_generator.py "Text" -f PNG -s 1024 -e H            # size and error correction
python qr_generator.py "Text" -f PNG -s 256 --transparent    # no background
python qr_generator.py --datei content.txt -o code.png       # content from a text file
echo "Text" | python qr_generator.py - -o code.png           # content from the pipeline
python qr_generator.py --stapel list.txt -a output -f SVG    # many codes at once
python qr_generator.py --formate                             # list the formats
python qr_generator.py --sprache en --help                   # help in English
```

The option names stay German so that they match the program file. Without `-o`
the file name is derived from the content. Existing files are never
overwritten but numbered instead – `--ueberschreiben` turns that off. The exit
code is `0` on success and `2` on an error. Messages appear in the same
language as the window; `--sprache` switches them for a single call.

### Batch file

One line per QR code, optionally with its own file name after a `|`. Blank
lines and lines starting with `#` are skipped.

```
# Notice for the entrance hall
https://example.org        | website
mailto:info@example.org    | contact
WIFI:T:WPA;S:GuestNet;P:secret;;
```

## Bundling as an EXE

```bash
pyinstaller --onefile --windowed --name QR-Code-Generator --copy-metadata qrcode qr_generator.py
```

PyInstaller finds `qrcode`, `Pillow` and Tkinter on its own – no extra
`--hidden-import` entries are needed. The other two switches are still worth it:

* `--windowed` suppresses the console window behind the program window. The
  command line still works in that build and still writes files, you just do
  not see its messages. Leave the switch out if you mainly use the EXE from a
  terminal.
* `--copy-metadata qrcode` includes the package metadata that the
  "About & copyright" tab reads the version number from. Without it the tab
  shows "bundled" instead of `8.2`; nothing else changes. Pillow does not need
  it because it carries its version itself.

The EXE stores `qr-code-generator.json` next to itself rather than in its
temporary extraction folder, which is deleted on exit. For the same reason the
save dialog starts in the folder holding the EXE.

## Formats

| Format | Extension | Transparency | Intended for |
| ------ | --------- | ------------ | ------------ |
| PNG  | `.png`  | yes | the standard for web and print |
| SVG  | `.svg`  | yes | vector, scales to any size – ideal for layout |
| JPEG | `.jpg`  | no  | photo workflows |
| WEBP | `.webp` | yes | modern websites |
| TIFF | `.tif`  | yes | prepress, with a DPI value |
| BMP  | `.bmp`  | no  | older software |
| GIF  | `.gif`  | no  | indexed colours |
| ICO  | `.ico`  | yes | Windows icon file, 256 px at most |
| PDF  | `.pdf`  | no  | print-ready page |
| EPS  | `.eps`  | no  | traditional print shops |

If a format is asked for a size or transparency it cannot provide, the program
adjusts the setting and says so.

## Sizes

`--groesse` sets the edge length of the finished image in pixels (32 to 10000).
The code is first drawn at a whole-number module size and only scaled to the
final measurement if needed, without smoothing – that keeps the module edges
crisp and the code easy to read. For SVG the value is merely a base
measurement; the file scales to any size.

Rules of thumb: 256 px for screen and e-mail, 512 to 1024 px for web and
presentations, 2048 px or SVG for print. For stickers and printed material that
may get dirty or partly covered, error correction `Q` or `H` pays off.

## Notes on readability

* The quiet zone should be at least 4 modules wide according to the standard; that is the default.
* Dark modules on a light ground work most reliably. Inverted colours and weak
  contrast are reported.
* Accented and other special characters are stored as UTF-8. Very old readers
  occasionally misinterpret them – when in doubt, test first.
* A single QR code holds a few thousand characters depending on the error
  correction level. If the content is too long, the program says so in plain words.

---

## Contributing

Bug reports, translations, new output formats and improvements are all
welcome – see [CONTRIBUTING.md](CONTRIBUTING.md). The
[code of conduct](CODE_OF_CONDUCT.md) applies to this project.

Please do **not** report security findings as a public issue; use the private
route described in [SECURITY.md](SECURITY.md) instead.

All changes are recorded in the [changelog](CHANGELOG.md).

## Licence and authorship

Published under the [MIT License](LICENSE).

Copyright © 2026 Alexander Unverhau · **Created with assistance of Claude AI
(Anthropic)**, see [NOTICE](NOTICE). For transparency, the note on AI assistance
appears everywhere the copyright notice does: in the header of the program file,
in the application's *About & copyright* tab, in the `NOTICE` and in both
READMEs.

Libraries used: [qrcode](https://github.com/lincolnloop/python-qrcode)
(BSD 3-Clause) and [Pillow](https://python-pillow.org/) (MIT-CMU).
