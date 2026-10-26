#!/usr/bin/env bash
# Lance l'application bancaire.
#
# Préférence : un interpréteur dont Tk voit assez de polices via
# fontconfig (texte lissé). Si le test échoue, repli sur python3.
set -e
cd "$(dirname "$0")"

# Vrai si l'interpréteur donné expose assez de polices pour un rendu
# confortable (même logique que detecter_famille, côté application).
lisible() {
    "$1" -c 'import tkinter as tk, tkinter.font as fonts
import sys
try:
    racine = tk.Tk(); racine.withdraw()
    nombre = len(set(fonts.families(racine)))
    racine.destroy()
except Exception:
    nombre = 0
sys.exit(0 if nombre > 50 else 1)' >/dev/null 2>&1
}

if command -v python3 >/dev/null 2>&1 && lisible python3; then
    exec python3 main.py
fi

# Repli : le python3 du PATH même si le rendu est moins lissé.
if command -v python3 >/dev/null 2>&1; then
    exec python3 main.py
fi
exec python main.py
