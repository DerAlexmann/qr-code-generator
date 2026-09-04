"""Sprachtabelle: Vollstaendigkeit, Platzhalter und Abrufbarkeit."""

import ast
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "qr_generator.py"
PLATZHALTER = re.compile(r"\{(\w+)\}")


def schluessel_im_quelltext():
    """Alle _("...")-Aufrufe mit fester Zeichenkette einsammeln."""
    baum = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    gefunden = []
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name)
                and knoten.func.id == "_" and knoten.args):
            arg = knoten.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                gefunden.append(arg.value)
    return gefunden


def alle_schluessel(qr):
    """Feste Schluessel plus die, die erst zur Laufzeit nachgeschlagen werden."""
    dynamisch = (["Vordergrundfarbe", "Hintergrundfarbe"]
                 + [f.beschreibung for f in qr.FORMATE.values()]
                 + [text for _stufe, text in qr.FEHLERKORREKTUR.values()])
    return list(dict.fromkeys(schluessel_im_quelltext() + dynamisch))


def test_es_gibt_ueberhaupt_texte(qr):
    assert len(alle_schluessel(qr)) > 100


@pytest.mark.parametrize("sprache", ["en"])
def test_jeder_schluessel_ist_uebersetzt(qr, sprache):
    tabelle = qr.TRANSLATIONS[sprache]
    fehlend = [k for k in alle_schluessel(qr) if k not in tabelle]
    assert not fehlend, f"ohne Uebersetzung in '{sprache}': {fehlend[:5]}"


@pytest.mark.parametrize("sprache", ["en"])
def test_keine_verwaisten_eintraege(qr, sprache):
    """Ein Eintrag ohne passenden Schluessel ist fast immer ein Tippfehler."""
    bekannt = set(alle_schluessel(qr))
    ueberzaehlig = [k for k in qr.TRANSLATIONS[sprache] if k not in bekannt]
    assert not ueberzaehlig, f"ohne Entsprechung im Code: {ueberzaehlig[:5]}"


@pytest.mark.parametrize("sprache", ["en"])
def test_platzhalter_bleiben_gleich(qr, sprache):
    """{pfad}, {format} ... muessen in der Uebersetzung unveraendert vorkommen."""
    for deutsch, fremd in qr.TRANSLATIONS[sprache].items():
        assert set(PLATZHALTER.findall(deutsch)) == set(PLATZHALTER.findall(fremd)), deutsch


def test_uebersetzungen_sind_nicht_leer(qr):
    for sprache, tabelle in qr.TRANSLATIONS.items():
        for deutsch, fremd in tabelle.items():
            assert fremd.strip(), f"{sprache}: leere Uebersetzung fuer {deutsch!r}"


def test_jede_sprache_hat_einen_anzeigenamen(qr):
    assert qr.SOURCE_LANGUAGE in qr.LANGUAGE_NAMES
    for sprache in qr.TRANSLATIONS:
        assert sprache in qr.LANGUAGE_NAMES


def test_translator_liefert_in_jeder_sprache_text(qr):
    vorher = qr._.language
    try:
        for sprache in [qr.SOURCE_LANGUAGE, *qr.TRANSLATIONS]:
            qr._.language = sprache
            for schluessel in alle_schluessel(qr):
                assert qr._(schluessel).strip()
    finally:
        qr._.language = vorher


def test_quellsprache_gibt_den_text_unveraendert_zurueck(qr, deutsch):
    assert qr._("Bereit.") == "Bereit."


def test_unbekannte_sprache_faellt_auf_deutsch_zurueck(qr):
    uebersetzer = qr.Translator("xx")
    assert uebersetzer("Bereit.") == "Bereit."


def test_verfuegbare_sprachen_beginnen_mit_der_quellsprache(qr):
    namen = list(qr._.available())
    assert namen[0] == qr.SOURCE_LANGUAGE
