"""
QR-Code-Generator - Starter fuer den Doppelklick

Diese Datei startet nur die Oberflaeche von qr_generator.py. Sie traegt die
Endung .pyw, damit Windows sie mit pythonw.exe oeffnet: kein Konsolenfenster,
nur das Programmfenster - genau wie bei der Bild-Toolbox.

Fuer die Kommandozeile weiterhin qr_generator.py verwenden, dort steht auch
das eigentliche Programm.

Licensed under MIT License
Copyright 2026 Alexander Unverhau
Created with assistance of Claude AI
"""

import os
import sys

# Ohne Konsole gibt es kein Ziel fuer Fehlermeldungen. Ohne diese Zeilen
# beendet sich pythonw.exe beim ersten print() mit einem Fehler, und der
# Doppelklick sieht aus, als waere nichts passiert.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def melde_fehler(titel, text):
    """Fehler im Fenster zeigen - ohne Konsole sieht man sonst gar nichts."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        wurzel = tk.Tk()
        wurzel.withdraw()
        messagebox.showerror(titel, text)
        wurzel.destroy()
    except Exception:
        pass


def main():
    try:
        import qr_generator
    except ImportError as exc:
        melde_fehler(
            "QR-Code-Generator",
            f"Das Programm konnte nicht geladen werden:\n\n{exc}\n\n"
            "Bitte sicherstellen, dass qr_generator.py im selben Ordner liegt.")
        return 2

    try:
        qr_generator._.language = qr_generator.startup_language()
        return qr_generator.gui_starten()
    except Exception as exc:                       # nichts darf lautlos scheitern
        import traceback
        melde_fehler("QR-Code-Generator",
                     f"Unerwarteter Fehler:\n\n{exc}\n\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
