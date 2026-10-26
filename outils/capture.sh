#!/usr/bin/env bash
# Capture la fenêtre ACTIVE de l'application — pour les captures du rapport.
#
#   Usage :  outils/capture.sh captures/dashboard.png
#
# 1. Lancez ce script ;
# 2. pendant les 2 secondes d'attente, donnez le focus à la fenêtre
#    de l'application (clic dessus) ;
# 3. la capture est enregistrée et référencée dans le README.
set -e
sortie="${1:-captures/capture.png}"
cd "$(dirname "$0")/.."
mkdir -p "$(dirname "$sortie")"
sleep 2
spectacle -a -b -n -o "$sortie"
echo "Capture enregistrée : $sortie"
