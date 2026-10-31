"""Waechter fuer die Auslieferung: Lizenzen, Versionsangaben, fester Bau.

Diese Vorkehrungen verfallen still, wenn niemand darueber wacht: Eine geloeschte
Tabellenzeile, ein vergessenes --version-file, eine Untergrenze statt einer
festen Fassung - nichts davon faellt beim Programmieren auf, und im Release ist
es zu spaet. Deshalb prueft jeder Test hier genau eine dieser Zusagen.

Jeder dieser Waechter wurde einmal absichtlich rot gesetzt (Zeile geloescht,
Bedingung verdreht, Fassung gelockert) und danach wiederhergestellt. Was nicht
rot wird, ist kein Waechter.

Zwei Fallen aus der Uebergabenotiz sind hier eingebaut:

- Vor dem Pruefen einer Workflow-Datei fallen die Kommentarzeilen weg. Sonst
  genuegte ein Kommentar, der die Zusage nur erwaehnt.
- Die Jobs werden erst ab "jobs:" zerlegt. Unter "on:" stehen "push" und
  "workflow_dispatch" genauso eingerueckt und sind keine Jobs.

Ohne Oberflaeche und ohne PyYAML - die Tests laufen auch auf einem nackten
Runner.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
LIZENZDATEI = WURZEL / "DRITTANBIETER-LIZENZEN.md"
RELEASE_YML = WURZEL / ".github" / "workflows" / "release.yml"
CI_YML = WURZEL / ".github" / "workflows" / "ci.yml"
DEPENDABOT = WURZEL / ".github" / "dependabot.yml"
QUELLTEXT = WURZEL / "qr_generator.py"

# Die englische Haelfte der Lizenzdatei beginnt mit dieser Ueberschrift.
ENGLISCHE_UEBERSCHRIFT = "# Licenses of third-party components"


# --------------------------------------------------------------------------
# Hilfen
# --------------------------------------------------------------------------

def ohne_kommentare(text: str) -> str:
    """Kommentarzeilen weg - ein Kommentar ist kein Beweis."""
    return "\n".join(z for z in text.splitlines() if not z.lstrip().startswith("#"))


def jobs_zerlegen(text: str) -> dict[str, str]:
    """Die Jobs eines Workflows als Name -> Block, gelesen erst ab "jobs:"."""
    zeilen = ohne_kommentare(text).splitlines()
    for nummer, zeile in enumerate(zeilen):
        if zeile.rstrip() == "jobs:":
            zeilen = zeilen[nummer + 1:]
            break
    else:
        raise AssertionError("Der Workflow hat keinen Abschnitt 'jobs:'.")

    jobs: dict[str, list[str]] = {}
    aktuell = None
    for zeile in zeilen:
        kopf = re.fullmatch(r"  ([A-Za-z][\w-]*):\s*", zeile)
        if kopf:
            aktuell = kopf.group(1)
            jobs[aktuell] = []
        elif aktuell is not None:
            jobs[aktuell].append(zeile)
    return {name: "\n".join(block) for name, block in jobs.items()}


def pakete(datei: Path) -> set[str]:
    """Die Paketnamen aus einer requirements-Datei."""
    namen = set()
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#")[0].strip()
        if zeile:
            namen.add(re.split(r"[=<>!~;\[ ]", zeile)[0])
    return namen


@pytest.fixture(scope="module")
def lizenztext() -> str:
    return LIZENZDATEI.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def haelften(lizenztext: str) -> tuple[str, str]:
    """Deutscher und englischer Teil der Lizenzdatei."""
    assert ENGLISCHE_UEBERSCHRIFT in lizenztext, (
        "Die Lizenzdatei hat keinen englischen Teil mehr."
    )
    deutsch, englisch = lizenztext.split(ENGLISCHE_UEBERSCHRIFT, 1)
    return deutsch, englisch


@pytest.fixture(scope="module")
def release() -> str:
    return ohne_kommentare(RELEASE_YML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def release_jobs() -> dict[str, str]:
    return jobs_zerlegen(RELEASE_YML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def versionsinfo():
    """Das Modul versionsinfo_erzeugen.py, geladen ohne Import des Programms."""
    import importlib.util

    pfad = WURZEL / "versionsinfo_erzeugen.py"
    spec = importlib.util.spec_from_file_location("versionsinfo_erzeugen", pfad)
    assert spec is not None and spec.loader is not None
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# --------------------------------------------------------------------------
# Lizenzen der Fremdkomponenten
# --------------------------------------------------------------------------

def tabellenzeile(text: str, bestandteil: str) -> list[str]:
    """Die Tabellenzeile eines Bestandteils, aufgeteilt in ihre Spalten.

    Gesucht wird der Zeilenanfang, nicht der Name irgendwo in der Zeile: "Python"
    steht auch in fuenf anderen Zeilen ("Teil der Python-Laufzeit"), das Loeschen
    der Python-Zeile blieb damit unbemerkt.
    """
    anfang = f"| **{bestandteil}".lower()
    zeilen = [z for z in text.splitlines() if z.lower().startswith(anfang)]
    assert len(zeilen) == 1, (
        f"{bestandteil} steht nicht genau einmal als Tabellenzeile da "
        f"({len(zeilen)} Treffer)."
    )
    return [spalte.strip() for spalte in zeilen[0].split("|")]


@pytest.mark.parametrize("paket", sorted(
    pakete(WURZEL / "requirements.txt") | pakete(WURZEL / "requirements-build.txt")
))
def test_lizenzhinweise_nennen_jede_abhaengigkeit(paket, haelften):
    """Jede Abhaengigkeit braucht eine Tabellenzeile - in beiden Sprachen.

    Eine Suche nach Teilzeichenketten im ganzen Text waere kein Waechter: Das
    Loeschen einer ganzen Tabellenzeile liess einen solchen Test gruen, weil
    der Name noch irgendwo im Fliesstext stand.
    """
    for sprache, text in zip(("deutschen", "englischen"), haelften):
        spalten = tabellenzeile(text, paket)
        assert spalten[2], f"Im {sprache} Teil fehlt bei {paket} die Lizenzangabe."


# Bestandteil und ein Stueck seiner Lizenzangabe, in beiden Sprachen gleich
# geschrieben. Ohne die Lizenzspalte waere der Test blind dafuer, dass aus
# "BSD 3-Clause" eines Tages "GPL" wird.
MITGELIEFERT = [
    ("Python", "PSF"),
    ("Tcl/Tk", "BSD"),
    ("qrcode", "BSD 3-Clause"),
    ("Pillow", "MIT-CMU"),
    ("zlib", "zlib"),
    ("OpenSSL", "Apache"),
    ("libffi", "MIT"),
    ("bzip2", "BSD"),
    ("XZ", "0BSD"),
    ("Expat", "MIT"),
    ("PyInstaller", "GPLv2"),
]


@pytest.mark.parametrize("bestandteil, lizenz", MITGELIEFERT)
def test_lizenzhinweise_nennen_die_mitgelieferten_teile(bestandteil, lizenz, haelften):
    """Die EXE enthaelt mehr als die Pakete aus requirements.txt."""
    for sprache, text in zip(("deutschen", "englischen"), haelften):
        spalten = tabellenzeile(text, bestandteil)
        assert lizenz.lower() in spalten[2].lower(), (
            f"Im {sprache} Teil steht bei {bestandteil} nicht {lizenz}, "
            f"sondern {spalten[2]!r}."
        )
        assert "http" in spalten[3], (
            f"Im {sprache} Teil fehlt bei {bestandteil} der Verweis auf den Lizenztext."
        )


def test_lizenzhinweise_nennen_freetype_als_doppelt_lizenziert(haelften):
    """FreeType ist FTL oder GPLv2 - die Wahl muss dastehen, samt Textpflicht.

    Steht das nicht da, sieht ein Leser nur "alles freizuegig" und uebersieht,
    dass dieser Teil eine Namensnennung verlangt. Geprueft wird je Sprache und
    in einer Zeile: FreeType und GPLv2 stehen auch anderswo im Text, der
    deutsche Absatz liess sich deshalb loeschen, ohne dass es auffiel.
    """
    for sprache, text in zip(("deutschen", "englischen"), haelften):
        zeilen = [z for z in text.splitlines()
                  if "**FreeType**" in z and "FTL" in z and "GPLv2" in z]
        assert zeilen, (
            f"Im {sprache} Teil fehlt der Hinweis, dass FreeType doppelt "
            "lizenziert ist (FTL oder GPLv2)."
        )


def test_lizenzhinweise_nennen_die_gebaute_python_fassung(haelften, release_jobs):
    """Die Fassung in der Tabelle muss die sein, mit der gebaut wird.

    An Python 3.12 haengen Tcl/Tk 8.6, libssl-3 und libffi-8. Wird die Fassung
    im Workflow angehoben, veraltet die Tabelle still.
    """
    gebaut = re.search(r'python-version:\s*"([\d.]+)"', release_jobs["windows-exe"])
    assert gebaut, "Im Bau-Job steht keine Python-Fassung."
    for sprache, text in zip(("deutschen", "englischen"), haelften):
        spalten = tabellenzeile(text, "Python")
        assert gebaut.group(1) in spalten[1], (
            f"Im {sprache} Teil nennt die Tabelle nicht Python {gebaut.group(1)}, "
            f"sondern {spalten[1]!r}."
        )


def test_lizenzhinweise_liegen_dem_release_bei(release_jobs, release):
    """Die Datei muss den Anwender erreichen, nicht nur das Repository.

    Drei Wege, und jeder einzeln geprueft: im Quellpaket, neben der EXE und als
    Anhang am Release. Die Fortsetzungszeilen des cp-Befehls werden
    zusammengezogen, sonst traegt die Pruefung nur fuer die erste Zeile.
    """
    quellpaket = " ".join(release_jobs["quellpaket"].replace("\\\n", " ").split())
    assert re.search(r"cp .*DRITTANBIETER-LIZENZEN\.md.* out/QR-Code-Generator/",
                     quellpaket), "Das Quellpaket enthaelt die Lizenzhinweise nicht."
    assert "Copy-Item DRITTANBIETER-LIZENZEN.md dist\\" in release_jobs["windows-exe"]
    assert "artefakte/windows-exe/DRITTANBIETER-LIZENZEN.md" in release


def test_quellpaket_enthaelt_die_genannten_dateien(release_jobs):
    """Worauf die mitgelieferten Dateien verweisen, muss auch mitkommen.

    DRITTANBIETER-LIZENZEN.md nennt lizenztexte_sammeln.py, und wer die EXE
    selbst bauen will, braucht die festen Fassungen. Ein Verweis auf eine
    Datei, die im Paket fehlt, ist kein Verweis.
    """
    quellpaket = " ".join(release_jobs["quellpaket"].replace("\\\n", " ").split())
    for datei in ("qr_generator.py", "QR-Code-Generator.pyw", "LICENSE", "NOTICE",
                  "DRITTANBIETER-LIZENZEN.md", "CHANGELOG.md", "requirements.txt",
                  "requirements-build.txt", "versionsinfo_erzeugen.py",
                  "lizenztexte_sammeln.py", "qr_code_generator.ico"):
        assert re.search(rf"cp .*\b{re.escape(datei)}\b.* out/QR-Code-Generator/",
                         quellpaket), f"{datei} fehlt im Quellpaket."


def test_volltexte_liegen_dem_release_bei(release):
    """MIT, BSD, zlib und die FTL verlangen den Lizenztext selbst."""
    assert "python lizenztexte_sammeln.py dist\\lizenztexte" in release
    assert "QR-Code-Generator-lizenztexte.zip" in release
    assert "artefakte/windows-exe/QR-Code-Generator-lizenztexte.zip" in release


def _lade(name: str, datei: str):
    """Ein Skript neben dem Programm als Modul laden, ohne es zu importieren."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, WURZEL / datei)
    assert spec is not None and spec.loader is not None
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _bauumgebung_fehlt() -> str | None:
    """Der Grund, warum das Einsammeln hier nicht laufen kann - oder None.

    Das Sammeln braucht die Umgebung, in der auch die EXE entsteht: PyInstaller
    installiert und eine Python-Installation nach Windows-Art, die ihre
    LICENSE.txt mitbringt. In der Testmatrix (Linux, macOS, ohne PyInstaller)
    ist beides nicht gegeben.
    """
    import importlib.metadata

    try:
        importlib.metadata.version("pyinstaller")
    except importlib.metadata.PackageNotFoundError:
        return "PyInstaller ist nicht installiert"
    if not (Path(sys.base_prefix) / "LICENSE.txt").is_file():
        return "die Python-Installation hat keine LICENSE.txt"
    return None


def _bauumgebung_verlangen() -> None:
    """Ueberspringen, wo das Sammeln nicht laufen kann - aber nicht im Bau-Job.

    Uebersprungen ist nicht gruen: Im Job mit den festgenagelten Bauversionen
    ist PYINSTALLER_PFLICHT gesetzt, dort waere ein Skip ein verdeckter Fehler.
    """
    grund = _bauumgebung_fehlt()
    if not grund:
        return
    if os.environ.get("PYINSTALLER_PFLICHT") == "1":
        pytest.fail(f"Pflichttest nicht lauffaehig: {grund}")
    pytest.skip(f"keine Bauumgebung: {grund}")


def test_lizenztexte_werden_vollstaendig_eingesammelt(tmp_path):
    """Das Sammelskript liefert fuer jedes Paket einen Text und eine Uebersicht."""
    _bauumgebung_verlangen()
    modul = _lade("lizenztexte_sammeln", "lizenztexte_sammeln.py")

    ziel = tmp_path / "lizenztexte"
    modul.main(ziel)

    import importlib.metadata

    gesammelt = sorted(p.name for p in ziel.iterdir())
    assert modul.UEBERSICHT in gesammelt
    for paket in modul.PAKETE:
        # Mit Versionsnummer im Namen - das versprechen die Lizenzdatei und
        # das Aenderungsprotokoll, und nur so sieht man, welche Fassung gilt.
        erwartet = f"{paket}-{importlib.metadata.version(paket)}-"
        assert any(name.startswith(erwartet) for name in gesammelt), (
            f"Fuer {paket} fehlt ein Lizenztext namens {erwartet}*."
        )
    assert any(name.startswith("Python-") for name in gesammelt), (
        "Die Lizenz der Python-Installation fehlt in der Sammlung."
    )
    # Die Texte sind keine leeren Huellen.
    for datei in ziel.iterdir():
        assert datei.stat().st_size > 500, f"{datei.name} ist auffaellig kurz."

    # Pillows Datei ist die wichtigste: In ihr stehen die Texte der fest
    # eingebundenen Decoder. Eine Datei mit 600 beliebigen Bytes bestuende die
    # Groessenpruefung, waere aber nutzlos.
    pillow = next(ziel / name for name in gesammelt if name.startswith("Pillow-"))
    text = pillow.read_text(encoding="utf-8", errors="replace")
    for teil in ("FreeType", "libjpeg", "zlib"):
        assert teil in text, f"In Pillows Lizenzdatei fehlt {teil}."

    # Jede abgelegte Datei steht in der Uebersicht - sonst findet sie niemand.
    uebersicht = (ziel / modul.UEBERSICHT).read_text(encoding="utf-8")
    for name in gesammelt:
        if name != modul.UEBERSICHT:
            assert name in uebersicht, f"{name} fehlt in {modul.UEBERSICHT}."


def test_lizenztexte_brechen_ohne_python_lizenz_ab(tmp_path, monkeypatch):
    """Fehlt die LICENSE.txt der Python-Installation, ist die Sammlung unvollstaendig.

    Sie darf dann nicht stillschweigend ohne diesen Teil entstehen: Die Lizenz
    von Python deckt auch libffi und bzip2 mit ab.
    """
    modul = _lade("lizenztexte_ohne_python", "lizenztexte_sammeln.py")
    monkeypatch.setattr(sys, "base_prefix", str(tmp_path))

    with pytest.raises(SystemExit) as fehler:
        modul.python_lizenz()
    assert "LICENSE.txt" in str(fehler.value)


def test_lizenztexte_brechen_bei_fehlender_lizenzdatei(tmp_path, monkeypatch):
    """Ein Paket ohne Lizenzdatei muss laut abbrechen, nicht stillschweigend fehlen.

    Geprueft wird der eigene Abbruch, nicht der von importlib: Ein erfundener
    Paketname loest schon in metadata.distribution() einen Fehler aus, und der
    Test waere dann aus dem falschen Grund gruen.
    """
    modul = _lade("lizenztexte_sammeln_leer", "lizenztexte_sammeln.py")
    monkeypatch.setattr(modul, "lizenzdateien", lambda paket: [])

    with pytest.raises(SystemExit) as fehler:
        modul.main(tmp_path / "unvollstaendig")
    assert "Lizenzdatei" in str(fehler.value)


def test_lizenztexte_brechen_bei_unbekanntem_paket_ab(tmp_path, monkeypatch):
    """Steht ein Paket in PAKETE, das nicht installiert ist, bricht der Bau ab."""
    import importlib.metadata

    modul = _lade("lizenztexte_sammeln_fremd", "lizenztexte_sammeln.py")
    monkeypatch.setattr(modul, "PAKETE", ("ein-paket-das-es-nicht-gibt",))

    with pytest.raises(importlib.metadata.PackageNotFoundError):
        modul.main(tmp_path / "unvollstaendig")


def test_pakete_der_lizenztexte_passen_zum_festen_bau():
    """Die Liste im Sammelskript und die festen Bauversionen muessen deckungsgleich sein.

    Beide Listen stehen an verschiedenen Stellen. Kommt ein Paket in den Bau,
    aber nicht in die Sammlung, fehlt sein Lizenztext still - und genau das
    soll die Sammlung verhindern.
    """
    modul = _lade("lizenztexte_pakete", "lizenztexte_sammeln.py")
    gebaut = {name.lower() for name in pakete(WURZEL / "requirements-build.txt")}
    gesammelt = {name.lower() for name in modul.PAKETE}
    assert gebaut == gesammelt, (
        f"requirements-build.txt: {sorted(gebaut)}, PAKETE: {sorted(gesammelt)}"
    )


def test_lizenztexte_lehnen_eine_namenskollision_ab(tmp_path, monkeypatch):
    """Zwei Lizenzdateien gleichen Namens duerfen sich nicht gegenseitig ueberschreiben.

    Ein Paket kann LICENSE sowohl in der .dist-info als auch in deren
    Unterordner licenses/ fuehren. Beide landeten unter demselben Zielnamen,
    und die zweite ueberschriebe die erste - sichtbar nur daran, dass die
    Uebersicht den Namen zweimal nennt.
    """
    modul = _lade("lizenztexte_kollision", "lizenztexte_sammeln.py")
    erster, zweiter = tmp_path / "a", tmp_path / "b"
    for ordner in (erster, zweiter):
        ordner.mkdir()
        (ordner / "LICENSE").write_text("L" * 600, encoding="utf-8")
    monkeypatch.setattr(modul, "PAKETE", ("qrcode",))
    monkeypatch.setattr(modul, "lizenzdateien",
                        lambda paket: [erster / "LICENSE", zweiter / "LICENSE"])

    with pytest.raises(SystemExit) as fehler:
        modul.main(tmp_path / "ziel")
    assert "LICENSE" in str(fehler.value)


def test_lizenztexte_lehnen_eine_leere_lizenzdatei_ab(tmp_path, monkeypatch):
    """Ein Platzhalter ist kein Lizenztext - und faellt sonst niemandem auf."""
    modul = _lade("lizenztexte_leer", "lizenztexte_sammeln.py")
    kurz = tmp_path / "LICENSE"
    kurz.write_text("siehe Website", encoding="utf-8")
    monkeypatch.setattr(modul, "PAKETE", ("qrcode",))
    monkeypatch.setattr(modul, "lizenzdateien", lambda paket: [kurz])

    with pytest.raises(SystemExit) as fehler:
        modul.main(tmp_path / "ziel")
    assert "Lizenztext" in str(fehler.value)


def test_lizenztexte_lehnen_einen_vollen_zielordner_ab(tmp_path):
    """Reste eines frueheren Laufs kaemen sonst mit ins ZIP.

    Die Dateinamen tragen die Versionsnummer: Nach einem Versionssprung bleibt
    der alte Text liegen, wird mitgepackt und steht nicht in der Uebersicht.
    """
    modul = _lade("lizenztexte_voll", "lizenztexte_sammeln.py")
    ziel = tmp_path / "ziel"
    ziel.mkdir()
    (ziel / "Pillow-1.0-LICENSE.txt").write_text("alt", encoding="utf-8")

    with pytest.raises(SystemExit) as fehler:
        modul.main(ziel)
    assert "nicht leer" in str(fehler.value)


# --------------------------------------------------------------------------
# Der Release-Workflow
# --------------------------------------------------------------------------

def test_release_laesst_sich_proben(release_jobs):
    """Nur der veroeffentlichende Job haengt am Tag, die Bau-Jobs nicht.

    Ohne Tag kennt die Action keinen Namen fuer den Release und bricht ab. Ein
    Probelauf per workflow_dispatch waere dadurch immer rot - und ein roter
    Lauf, der nichts bedeutet, wird irgendwann nicht mehr angesehen.

    Geprueft wird der genaue Ausdruck: "github.ref_type != 'tag'" stand in
    einem Nachbarprojekt einmal genau verkehrt in der Bedingung und kam durch
    einen Test, der nur nach "ref_type" suchte.
    """
    assert "if: github.ref_type == 'tag'" in release_jobs["release"]
    for name in ("quellpaket", "windows-exe"):
        assert "if:" not in release_jobs[name], (
            f"Der Bau-Job {name} hat eine Bedingung - dann prueft der "
            "Probelauf nichts mehr."
        )


def test_release_bleibt_ein_entwurf(release_jobs):
    """Der Release entsteht als Entwurf, nicht sofort oeffentlich.

    Der Entwurf ist die Stelle zum Pruefen: unsignierte EXE, Pruefsumme,
    Lizenzdatei, Notizen. Faellt draft weg, ist das Release in der Sekunde
    oeffentlich, in der der Tag ankommt.
    """
    assert "draft: true" in release_jobs["release"]


def test_release_haengt_an_den_richtigen_ausloesern(release):
    """Ein Tag baut, ein Probelauf ist moeglich - beides muss dastehen."""
    kopf = release.split("jobs:")[0]
    assert 'tags: ["v*"]' in kopf, "Ohne diesen Ausloeser baut kein Tag ein Release."
    assert "workflow_dispatch:" in kopf, "Ohne diesen Ausloeser ist kein Probelauf moeglich."


def test_release_wartet_auf_beide_bau_jobs(release_jobs):
    """Ohne needs liefe der Release los, bevor die Anhaenge fertig sind."""
    assert "needs: [quellpaket, windows-exe]" in release_jobs["release"]


def test_release_schreibt_notizen(release_jobs):
    """Die Notizen entstehen aus den Commits; von Hand kaeme sonst nichts dazu."""
    assert "generate_release_notes: true" in release_jobs["release"]


def test_upload_und_anhang_nennen_dieselben_dateien(release_jobs):
    """Was gebaut wird, muss auch hochgeladen und angehaengt werden.

    Drei Listen muessen zusammenpassen: die gepruefte Liste im Bau-Job, die
    Pfade von upload-artifact und die files: der Release-Action. Faellt ein
    Eintrag aus einer der beiden letzten heraus, liegt die Datei zwar im
    Bau-Ordner, haengt aber nicht am Release - und bei einem Probelauf ohne
    Tag faellt es nicht einmal auf, weil der Release-Job dann ausbleibt.
    """
    exe = release_jobs["windows-exe"]
    hochgeladen = re.search(r"path: \|(.*?)(?=\n\s*\w+:|\Z)", exe, re.DOTALL)
    assert hochgeladen, "Im Bau-Job gibt es keine Liste hochzuladender Dateien."
    namen = {Path(z.strip()).name for z in hochgeladen.group(1).splitlines() if z.strip()}

    angehaengt = re.search(r"files: \|(.*?)(?=\n\s*\w+:|\Z)", release_jobs["release"],
                           re.DOTALL)
    assert angehaengt, "Der Release-Job haengt keine Dateien an."
    anhaenge = {Path(z.strip()).name for z in angehaengt.group(1).splitlines() if z.strip()}

    assert namen <= anhaenge, (
        f"Diese Dateien werden gebaut, haengen aber nicht am Release: {sorted(namen - anhaenge)}"
    )
    assert "*.zip" in anhaenge, "Das Quellpaket haengt nicht am Release."
    for datei in ("QR-Code-Generator.exe", "SHA256SUMS.txt",
                  "DRITTANBIETER-LIZENZEN.md", "QR-Code-Generator-lizenztexte.zip"):
        assert datei in namen, f"{datei} wird nicht hochgeladen."


def test_release_ersetzt_schraegstriche_im_refnamen(release):
    """Ein Probelauf von einem Branch wie dependabot/pip/... darf nicht am Pfad scheitern."""
    assert "${GITHUB_REF_NAME//\\//-}" in release


def test_release_scheitert_wenn_eine_datei_fehlt(release):
    """Die laschen Vorgaben der Actions sind korrigiert.

    Vorgabe ist "warn" beziehungsweise false: Ein Release entstuende dann ohne
    Pruefsumme oder Lizenzdatei, ohne dass etwas rot wird.
    """
    assert release.count("if-no-files-found: error") == 2, (
        "Jeder der beiden upload-artifact-Schritte braucht if-no-files-found: error."
    )
    assert "fail_on_unmatched_files: true" in release


def test_release_baut_aus_den_festen_versionen(release_jobs):
    """Die EXE entsteht aus requirements-build.txt, nicht aus den Untergrenzen."""
    exe = release_jobs["windows-exe"]
    assert "pip install -r requirements-build.txt" in exe
    assert "pip install -r requirements.txt" not in exe, (
        "Die EXE wuerde aus den Untergrenzen gebaut - dann ergibt derselbe Tag "
        "nicht zweimal dieselbe Datei."
    )


def test_release_erzeugt_und_benutzt_die_versionsangaben(release_jobs):
    """Ohne --version-file bleiben die Dateieigenschaften leer - wie bei 1.1.7."""
    exe = release_jobs["windows-exe"]
    assert "python versionsinfo_erzeugen.py" in exe
    assert "--version-file versionsinfo.txt" in exe
    # Erzeugen vor dem Bauen, sonst ist die Datei beim Packen noch nicht da.
    assert exe.index("versionsinfo_erzeugen.py") < exe.index("--version-file")


def test_release_sieht_sich_die_fertige_exe_an(release_jobs):
    """Der Build-Text beweist nichts - die fertige Datei muss angesehen werden."""
    exe = release_jobs["windows-exe"]
    assert "VersionInfo" in exe
    # Die ganzen Bedingungen, nicht ihre Bestandteile: Ein -ne, das zu einem
    # -eq verdreht wird, oder 'tag', das zu 'branch' wird, kehrt die Wirkung
    # um - und eine Suche nach "GITHUB_REF_TYPE" bemerkt davon nichts.
    assert "if (-not $info.ProductName -or -not $info.ProductVersion) {" in exe, (
        "Leere Versionsangaben werden nicht abgefangen."
    )
    assert ("if ($env:GITHUB_REF_TYPE -eq 'tag' -and "
            '"v$($info.ProductVersion)" -ne $env:GITHUB_REF_NAME) {') in exe, (
        "Der Abgleich zwischen Tag und Version steht nicht so da, dass er wirkt."
    )
    assert exe.count("throw") >= 3


def test_release_bildet_die_pruefsumme(release_jobs, release):
    """Die SHA-256 entsteht im Workflow, nicht von Hand nach dem Hochladen."""
    exe = release_jobs["windows-exe"]
    assert "Get-FileHash" in exe and "SHA256" in exe
    assert "SHA256SUMS.txt" in exe
    assert "artefakte/windows-exe/SHA256SUMS.txt" in release
    # Zwei Leerzeichen und ein Zeilenumbruch nach Unix-Art - genau das
    # erwartet "sha256sum -c". Out-File schrieb CRLF, und dann liest
    # sha256sum den Dateinamen mit einem Wagenruecklauf daran.
    assert '"$h  QR-Code-Generator.exe`n"' in exe, (
        "Das Format der Pruefsummendatei passt nicht zu sha256sum -c."
    )
    # .NET richtet sich nicht nach dem Arbeitsordner von PowerShell.
    assert "Join-Path $PWD" in exe


def test_release_baut_die_exe_mit_symbol(release_jobs):
    """Das Programmsymbol gehoert als Ressource in die EXE."""
    assert '--icon "qr_code_generator.ico"' in release_jobs["windows-exe"]


def test_release_nimmt_die_paketdaten_und_verbirgt_die_konsole(release_jobs):
    """Zwei Schalter, die man nicht vermisst, bis sie fehlen.

    Ohne --copy-metadata qrcode steht im Reiter "Info & Copyright" statt der
    Fassung nur "eingebettet"; qrcode fuehrt seit Fassung 8 kein __version__
    mehr. Ohne --windowed steht hinter der Oberflaeche ein Konsolenfenster.
    """
    exe = release_jobs["windows-exe"]
    assert "--copy-metadata qrcode" in exe
    assert "--windowed" in exe


def test_release_verlangt_jeden_anhang_einzeln(release_jobs):
    """if-no-files-found: error faengt keine einzelne fehlende Datei ab.

    Die Einstellung schlaegt erst an, wenn ueber alle Muster zusammen gar
    nichts gefunden wird. Fehlte nur die Pruefsumme, entstuende das Artefakt
    ohne sie. Deshalb muss jede Datei vor dem Hochladen einzeln verlangt
    werden.
    """
    exe = release_jobs["windows-exe"]
    assert "Test-Path $datei" in exe and "throw" in exe

    # Gelesen wird die Liste selbst, nicht der ganze Job: Der Dateiname steht
    # auch in dem Schritt, der die Datei erzeugt, und in den Pfaden fuer den
    # Anhang. Eine Suche im ganzen Text blieb deshalb gruen, als der Eintrag
    # aus der Liste geloescht wurde.
    liste = re.search(r"\$erwartet = @\((.*?)\n\s*\)", exe, re.DOTALL)
    assert liste, "Im Job gibt es keine Liste der erwarteten Anhaenge."
    for datei in ("QR-Code-Generator.exe", "SHA256SUMS.txt",
                  "DRITTANBIETER-LIZENZEN.md", "QR-Code-Generator-lizenztexte.zip"):
        assert datei in liste.group(1), (
            f"{datei} steht nicht in der Liste der verlangten Anhaenge."
        )


def test_release_prueft_den_rueckgabewert_der_skripte(release_jobs):
    """Ein gescheitertes Python-Skript muss durchschlagen.

    Bei einem mehrzeiligen run: zaehlt unter PowerShell nur der Rueckgabewert
    des letzten Befehls. Steht hinter dem Skript noch ein Cmdlet, waere der
    Schritt gruen, obwohl das Skript abgebrochen ist.
    """
    exe = release_jobs["windows-exe"]
    assert "if ($LASTEXITCODE -ne 0)" in exe
    # Die Pruefung muss vor dem Einpacken stehen, nicht danach.
    assert exe.index("$LASTEXITCODE") < exe.index("Compress-Archive")


def test_release_prueft_die_exe_gegen_die_erzeugten_angaben(release_jobs):
    """Die ganze Kette wird belegt: Quelltext, erzeugte Datei, fertige EXE.

    Nur "nicht leer" zu pruefen liesse eine EXE durch, die eine voellig andere
    Version meldet - und bei einem Probelauf ohne Tag faellt es sonst nie auf.
    """
    exe = release_jobs["windows-exe"]
    assert "versionsinfo.txt" in exe
    # Die Soll-Werte muessen aus der erzeugten Datei gelesen werden. Nur nach
    # den Variablennamen zu suchen war zu wenig: Sie stehen an mehreren
    # Stellen, und das Loeschen der lesenden Zeile blieb unbemerkt.
    assert "StringStruct\\('ProductName'" in exe
    assert "StringStruct\\('ProductVersion'" in exe
    assert "-ne $sollName" in exe and "-ne $sollVersion" in exe


def test_release_verlangt_eine_ausgabe_von_der_exe(release_jobs):
    """Dass das Fenster stehen bleibt, beweist wenig.

    Eine --windowed-EXE mit einem Fehler beim Start zeigt einen
    Meldungsdialog und laeuft dabei weiter; der Rauchtest allein waere gruen.
    Erst eine geschriebene Datei belegt, dass qrcode, Pillow und die
    mitgenommenen Paketdaten im gepackten Zustand geladen werden.
    """
    exe = release_jobs["windows-exe"]
    assert "-Wait" in exe
    assert "if ($p.ExitCode -ne 0) {" in exe
    # Die Bedingungen selbst, nicht nur ihre Meldungstexte: Ein if, das auf
    # $false gesetzt wird, macht den Schritt wirkungslos, und der Meldungstext
    # stuende weiter da.
    assert "if (-not $datei) {" in exe, "Eine fehlende Datei wird nicht abgefangen."
    assert "if ($datei.Length -eq 0) {" in exe, "Eine leere Datei wird nicht abgefangen."
    # Die Argumente selbst, nicht nur den Ordnernamen: Ohne --ArgumentList
    # startet nur die Oberflaeche, und von der Kommandozeile ist nichts
    # geprueft. Der Ordnername allein stand auch in der Datei-Pruefung.
    assert "-ArgumentList" in exe
    for teil in ("'-f','PNG'", "'-a','rauchtest'"):
        assert teil in exe, f"Der Aufruf der EXE enthaelt {teil} nicht."


def test_schreibrechte_nur_beim_veroeffentlichen(release, release_jobs):
    """Die Bau-Jobs installieren Pakete und packen eine EXE - ohne Token.

    Schreibrechte fuer den ganzen Lauf hiessen: Jeder Schritt, der fremden
    Code ausfuehrt, koennte das Repository aendern.
    """
    kopf = release.split("jobs:")[0]
    assert "contents: read" in kopf, "Der Workflow raeumt sich mehr Rechte ein als noetig."
    assert "contents: write" in release_jobs["release"]
    for name in ("quellpaket", "windows-exe"):
        assert "contents: write" not in release_jobs[name]


# --------------------------------------------------------------------------
# Fester Bau
# --------------------------------------------------------------------------

def bauversionen() -> dict[str, str]:
    """Paketname -> feste Fassung aus requirements-build.txt."""
    gefunden = {}
    for zeile in (WURZEL / "requirements-build.txt").read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#")[0].strip()
        if zeile:
            name, _, version = zeile.partition("==")
            gefunden[name.strip().lower()] = version.strip()
    return gefunden


def test_bauversionen_sind_festgenagelt():
    """Jede Zeile in requirements-build.txt nennt genau eine Fassung.

    "==" allein genuegt nicht: "qrcode==8.*" hat es auch und ist doch ein
    Bereich. Verlangt wird deshalb die ganze Zeile in der Form Paket==1.2.3.
    """
    datei = WURZEL / "requirements-build.txt"
    zeilen = 0
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#")[0].strip()
        if not zeile:
            continue
        zeilen += 1
        assert re.fullmatch(r"[A-Za-z0-9._-]+==\d+(\.\d+)*", zeile), (
            f"{zeile!r} ist keine genaue Fassung."
        )
    assert zeilen >= 3, "Es sollten mindestens PyInstaller, qrcode und Pillow dastehen."


def test_bauversionen_erfuellen_die_untergrenzen():
    """Die feste Fassung muss die Untergrenze aus requirements.txt einhalten.

    "Pillow==1.0" waere eine genaue Fassung und gleichzeitig unter der
    Untergrenze "Pillow>=9.1" - der Bau installierte dann etwas, mit dem das
    Programm nachweislich nicht laeuft.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    fest = bauversionen()
    for zeile in (WURZEL / "requirements.txt").read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#")[0].strip()
        if not zeile:
            continue
        bedingung = Requirement(zeile)
        name = bedingung.name.lower()
        assert name in fest, f"{bedingung.name} hat keine feste Bauversion."
        assert bedingung.specifier.contains(Version(fest[name])), (
            f"{bedingung.name}=={fest[name]} erfuellt {bedingung.specifier} nicht."
        )


def test_bauversionen_decken_alle_laufzeitpakete_ab():
    """Was zum Laufen gebraucht wird, muss auch fuer den Bau festgelegt sein."""
    fehlend = pakete(WURZEL / "requirements.txt") - pakete(WURZEL / "requirements-build.txt")
    assert not fehlend, f"In requirements-build.txt fehlen: {sorted(fehlend)}"


def test_bauversionen_enthalten_den_packer():
    """PyInstaller selbst gehoert dazu - eine neue Fassung soll kein Release kippen."""
    assert "pyinstaller" in {p.lower() for p in pakete(WURZEL / "requirements-build.txt")}


def test_ci_prueft_die_festgenagelten_versionen():
    """Die gepinnte Kombination laeuft in jedem Pull Request, nicht erst beim Tag."""
    jobs = jobs_zerlegen(CI_YML.read_text(encoding="utf-8"))
    passende = [block for block in jobs.values()
                if "pip install -r requirements-build.txt" in block]
    assert passende, (
        "Kein CI-Job installiert requirements-build.txt - eine unvertraegliche "
        "Anhebung fiele erst im Release auf."
    )
    block = passende[0]
    # Der Job muss dort laufen, wo auch die EXE entsteht - die beiden
    # Hilfsskripte des Baus sind auf Windows zugeschnitten.
    assert "runs-on: windows-latest" in block

    # Importieren allein beweist nichts: Es muss eine echte Datei entstehen,
    # und zwar auf beiden Wegen - PNG ueber Pillow, SVG ohne Pillow.
    assert "qr_generator.py" in block
    assert "-f PNG" in block and "-f SVG" in block
    assert "if ($datei.Length -eq 0)" in block or "Length -eq 0" in block
    assert "Count -ne 2" in block

    # Beide Hilfsskripte laufen hier mit, sonst erst beim Tag.
    assert "python versionsinfo_erzeugen.py" in block
    assert "python lizenztexte_sammeln.py" in block
    # Nach jedem nativen Aufruf: Unter PowerShell zaehlt sonst nur der letzte.
    assert block.count("if ($LASTEXITCODE -ne 0)") >= 4, (
        "Nicht jeder Python-Aufruf im Job wird auf seinen Rueckgabewert geprueft."
    )

    assert "test_verpackung.py" in block
    # Ohne diese Variable darf der Lizenztext-Test ueberspringen - und waere
    # gruen, ohne etwas geprueft zu haben. Genau hier ist er Pflicht.
    assert 'PYINSTALLER_PFLICHT: "1"' in block


def test_dependabot_laesst_die_untergrenzen_in_ruhe():
    """Die Untergrenze nennt die aelteste laufende Fassung, kein Upgrade-Ziel."""
    text = ohne_kommentare(DEPENDABOT.read_text(encoding="utf-8"))
    assert re.search(r'versioning-strategy:\s*"?increase-if-necessary"?', text), (
        "Ohne diese Einstellung hebt Dependabot auch die Untergrenzen an."
    )


def test_abgeleitete_dateien_sind_nicht_eingecheckt():
    """Was beim Bauen entsteht, gehoert nicht ins Repository.

    versionsinfo.txt kommt aus VERSION, der Ordner lizenztexte/ aus den
    installierten Paketen. Eingecheckt wuerden beide beim naechsten
    Versionssprung still veralten.
    """
    gitignore = (WURZEL / ".gitignore").read_text(encoding="utf-8")
    for eintrag in (r"versionsinfo\.txt", r"lizenztexte/"):
        assert re.search(rf"^{eintrag}$", gitignore, re.MULTILINE), (
            f"{eintrag} steht nicht in .gitignore."
        )
    for name in ("versionsinfo.txt", "lizenztexte"):
        if (WURZEL / name).exists():
            assert _ist_ignoriert(name), f"{name} liegt da und wird nicht ignoriert."


def _ist_ignoriert(name: str) -> bool:
    """Fragt git, ob eine Datei wirklich ignoriert wird.

    Ausserhalb eines Repositorys - etwa im entpackten Quellpaket - antwortet
    git mit 128. Dann ist die Frage nicht zu beantworten, und der Test soll
    nicht daran scheitern.
    """
    fertig = subprocess.run(["git", "check-ignore", name], cwd=WURZEL,
                            capture_output=True)
    if fertig.returncode >= 128:
        pytest.skip("kein Git-Repository - check-ignore nicht moeglich")
    return fertig.returncode == 0


# --------------------------------------------------------------------------
# Versionsangaben der EXE
# --------------------------------------------------------------------------

def test_versionsinfo_kommt_aus_dem_quelltext(versionsinfo, qr):
    """Eine Versionsquelle, nicht zwei: gelesen wird aus qr_generator.py.

    Verglichen wird gegen das geladene Programm, nicht gegen denselben
    Suchausdruck noch einmal: Sonst waere ein Fehler darin auf beiden Seiten
    gleich und faellt nie auf.
    """
    version, programm = qr.VERSION, qr.PROGRAMM

    assert versionsinfo.aus_quelltext("VERSION") == version
    assert versionsinfo.aus_quelltext("PROGRAMM") == programm

    text = versionsinfo.inhalt(programm, version)
    assert f"StringStruct('ProductVersion', '{version}')" in text
    assert f"StringStruct('ProductName', '{programm}')" in text
    # Auch der Dateiname steht in Anfuehrungszeichen, die aus repr() kommen -
    # ein Apostroph im Programmnamen wuerde die Datei sonst aufbrechen, und
    # PyInstaller liest sie als Python-Ausdruck ein.
    assert f"StringStruct('OriginalFilename', '{programm}.exe')" in text
    assert "Claude AI" in text, "Der Hinweis auf die KI-Mithilfe fehlt im Copyright."

    # Sprachkennung und Zeichensatz muessen an beiden Stellen dieselben sein.
    # Passen sie nicht zusammen, zeigt Windows leere oder falsche Felder -
    # also genau der Mangel, den 1.1.8 behebt, nur anders verursacht.
    assert versionsinfo.SPRACHE == 1031, "Die Quellsprache des Programms ist Deutsch."
    kennung = f"{versionsinfo.SPRACHE:04x}{versionsinfo.ZEICHENSATZ:04x}".upper()
    assert f"StringTable(\n        '{kennung}'," in text
    assert (f"VarStruct('Translation', "
            f"[{versionsinfo.SPRACHE}, {versionsinfo.ZEICHENSATZ}])") in text


def test_versionsinfo_bleibt_ein_gueltiger_ausdruck(versionsinfo):
    """PyInstaller liest die Datei als Python-Ausdruck - sie muss einer bleiben.

    Geprueft mit einem Apostroph im Programmnamen: Wird irgendein Feld ohne
    repr() eingesetzt, bricht die Zeichenkette mitten im Text auf, und
    PyInstaller scheitert erst beim Bauen mit einem Syntaxfehler.
    """
    text = versionsinfo.inhalt("Pat's Werkzeug", "1.0")
    ohne_kommentar = "\n".join(z for z in text.splitlines()
                               if not z.lstrip().startswith("#"))
    compile(ohne_kommentar, "<versionsinfo>", "eval")


def test_versionsinfo_liest_keinen_offenen_ausdruck(versionsinfo, tmp_path, monkeypatch):
    """Die Konstante muss die ganze Zeile sein, nicht deren Anfang.

    Bei "VERSION = "1.1.8" + SUFFIX" wuerde ein nicht verankerter Suchausdruck
    nur "1.1.8" lesen. Die Titelleiste zeigte dann eine andere Fassung als die
    Dateieigenschaften - und niemand wuesste, welche stimmt.
    """
    quelle = tmp_path / "offen.py"
    quelle.write_text('VERSION = "1.1.8" + SUFFIX\n', encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)

    with pytest.raises(SystemExit):
        versionsinfo.aus_quelltext("VERSION")


@pytest.mark.parametrize("version, erwartet", [
    ("1", (1, 0, 0, 0)),
    ("1.1", (1, 1, 0, 0)),
    ("1.1.8", (1, 1, 8, 0)),
    ("1.1.8.2", (1, 1, 8, 2)),
    ("65535", (65535, 0, 0, 0)),          # genau die Grenze ist noch erlaubt
])
def test_vierstellig_rechnet_richtig(versionsinfo, version, erwartet):
    assert versionsinfo.vierstellig(version) == erwartet


@pytest.mark.parametrize("version", [
    "1.2.3rc1", "1.1.8-beta", "", "x.y", "1.70000",
    "65536",                              # eine Stelle ueber der Grenze
    "1.2.3.4.5",                          # fuenf Stellen passen nicht in vier
])
def test_vierstellig_lehnt_unbrauchbares_mit_klartext_ab(versionsinfo, version):
    """Abbrechen statt raten - Windows will vier Zahlen."""
    with pytest.raises(SystemExit) as fehler:
        versionsinfo.vierstellig(version)
    assert str(fehler.value), "Der Abbruch muss einen Grund nennen."


def test_versionsinfo_lehnt_zeichen_ausserhalb_von_ascii_ab(versionsinfo, tmp_path,
                                                            monkeypatch):
    """In den Dateieigenschaften sollen keine verstuemmelten Umlaute stehen."""
    quelle = tmp_path / "umlaut.py"
    quelle.write_text('PROGRAMM = "QR-Code-Generator fuer Grueszen"\n'
                      .replace("Grueszen", "Grüße"), encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)

    with pytest.raises(SystemExit) as fehler:
        versionsinfo.aus_quelltext("PROGRAMM")
    assert "ASCII" in str(fehler.value)


def test_versionsinfo_bricht_ohne_konstante_ab(versionsinfo, tmp_path, monkeypatch):
    """Keine Konstante ist genauso wenig brauchbar wie zwei."""
    quelle = tmp_path / "leer.py"
    quelle.write_text("# hier steht keine Version\n", encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)

    with pytest.raises(SystemExit) as fehler:
        versionsinfo.aus_quelltext("VERSION")
    assert "0-mal" in str(fehler.value)


def test_versionsinfo_laesst_keine_alte_datei_stehen(versionsinfo, tmp_path, monkeypatch):
    """Bricht das Erzeugen ab, darf keine Datei von vorher liegen bleiben.

    Sonst nimmt ein spaeterer Bau mit --version-file stillschweigend die alte
    Fassung mit, und die EXE meldet eine Version, die es nicht mehr gibt.
    """
    ziel = tmp_path / "versionsinfo.txt"
    ziel.write_text("Reste von gestern", encoding="utf-8")
    quelle = tmp_path / "ohne.py"
    quelle.write_text("# hier steht keine Version\n", encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "ZIEL", ziel)
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)

    with pytest.raises(SystemExit):
        versionsinfo.main()
    assert not ziel.exists(), "Die alte versionsinfo.txt liegt noch da."


def test_versionsinfo_bricht_bei_mehrdeutiger_konstante_ab(versionsinfo, tmp_path,
                                                           monkeypatch):
    """Steht die Konstante nicht genau einmal am Zeilenanfang, ist Abbruch richtiger."""
    doppelt = tmp_path / "doppelt.py"
    doppelt.write_text('VERSION = "1.0"\nVERSION = "2.0"\n', encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", doppelt)
    with pytest.raises(SystemExit):
        versionsinfo.aus_quelltext("VERSION")


def test_versionsdatei_wird_von_pyinstaller_angenommen(versionsinfo, tmp_path,
                                                       monkeypatch):
    """Der eigentliche Beweis: PyInstaller liest die Datei als Ausdruck ein.

    Ohne PyInstaller wird uebersprungen - im Job "Festgenagelte Bauversionen"
    ist das Paket installiert, dort macht PYINSTALLER_PFLICHT den Test zur
    Pflicht. Uebersprungen ist nicht gruen.
    """
    if os.environ.get("PYINSTALLER_PFLICHT") == "1":
        import PyInstaller.utils.win32.versioninfo as vi
    else:
        vi = pytest.importorskip("PyInstaller.utils.win32.versioninfo")

    ziel = tmp_path / "versionsinfo.txt"
    monkeypatch.setattr(versionsinfo, "ZIEL", ziel)
    versionsinfo.main()

    gelesen = vi.load_version_info_from_text_file(str(ziel))

    # Nicht nur, dass die Feldnamen vorkommen - die stehen immer da, egal was
    # sie enthalten. Geprueft werden die Werte.
    version = versionsinfo.aus_quelltext("VERSION")
    haupt, neben, flick, bau = versionsinfo.vierstellig(version)
    # Windows fuehrt die vier Zahlen in zwei 32-Bit-Werten.
    assert gelesen.ffi.fileVersionMS == (haupt << 16) + neben
    assert gelesen.ffi.fileVersionLS == (flick << 16) + bau
    assert gelesen.ffi.productVersionMS == gelesen.ffi.fileVersionMS
    assert gelesen.ffi.productVersionLS == gelesen.ffi.fileVersionLS

    tabelle = gelesen.kids[0].kids[0]
    assert tabelle.name == f"{versionsinfo.SPRACHE:04x}{versionsinfo.ZEICHENSATZ:04x}".upper()
    felder = {feld.name: feld.val for feld in tabelle.kids}
    assert felder["ProductVersion"] == version
    assert felder["FileVersion"] == version
    assert felder["ProductName"] == versionsinfo.aus_quelltext("PROGRAMM")
    assert felder["CompanyName"], "Ohne Urheber bleibt das Feld in den Eigenschaften leer."
    assert "Claude AI" in felder["LegalCopyright"]
    assert felder["FileDescription"]


# --------------------------------------------------------------------------
# Kleinigkeiten, die dazugehoeren
# --------------------------------------------------------------------------

def test_security_md_nennt_die_aktuelle_reihe():
    """Die Tabelle in SECURITY.md soll die laufende Reihe nennen, nicht die von vorgestern."""
    version = re.search(r'^VERSION\s*=\s*"([^"]+)"',
                        QUELLTEXT.read_text(encoding="utf-8"), re.MULTILINE).group(1)
    reihe = ".".join(version.split(".")[:2]) + ".x"
    text = (WURZEL / "SECURITY.md").read_text(encoding="utf-8")
    # Und zwar als unterstuetzt: "| 1.1.x | nein |" waere auch ein Treffer.
    zeilen = [z for z in text.splitlines()
              if z.startswith("|") and reihe in z and "✅" in z]
    assert zeilen, f"SECURITY.md fuehrt {reihe} nicht als unterstuetzt."


@pytest.mark.parametrize("datei", ["README.md", "README.en.md"])
def test_erst_start_hinweis_steht_in_beiden_readmes(datei):
    """Jedes Release mit unsignierter EXE braucht diesen Hinweis - in beiden Sprachen."""
    text = (WURZEL / datei).read_text(encoding="utf-8")
    assert "SmartScreen" in text
    # Der Dateiname ausdruecklich: "SHA256" steht auch im Befehl darunter, und
    # ohne den Namen weiss niemand, wo der Wert zum Vergleichen liegt.
    assert "SHA256SUMS.txt" in text, (
        "Die README nennt nicht, wo die Pruefsumme zum Vergleichen liegt."
    )
    assert "Get-FileHash" in text


@pytest.mark.parametrize("datei", ["README.md", "README.en.md", "NOTICE"])
def test_verweis_auf_die_lizenzdatei(datei):
    """Die Lizenzhinweise muessen von den Stellen aus auffindbar sein, die man liest."""
    text = (WURZEL / datei).read_text(encoding="utf-8")
    assert "DRITTANBIETER-LIZENZEN.md" in text


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
