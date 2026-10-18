#!/usr/bin/env bash
# Lance l'application bancaire.
#
# Choix de l'interpréteur : on préfère celui dont Tk voit le plus de
# polices via fontconfig (Xft = texte lissé). Sur cette machine, le
# Python système en voit ~750 ; le Tk livré avec micromamba (sans Xft)
# n'en voit que 4 et rend un texte bitmap peu lisible. Si le test
# échoue, repli automatique sur l'environnement du projet.
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

for python in /usr/bin/python3 ~/micromamba/envs/ai_env/bin/python; do
    if [ -x "$python" ] && lisible "$python"; then
        exec "$python" main.py
    fi
done

# Derniers recours : le python3 du PATH, puis l'environnement du projet.
if command -v python3 >/dev/null 2>&1; then
    exec python3 main.py
fi
exec ~/micromamba/envs/ai_env/bin/python main.py
