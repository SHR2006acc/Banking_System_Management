"""Capture chaque écran de l'application pour le rapport.

Outil de développement (hors application) : lance la vraie Application,
met sa fenêtre au premier plan, puis pour chaque écran :
  spectacle -f (plein écran) -> recadrage au cadre exact de la fenêtre
  (winfo_rootx/rooty/width/height) -> captures/<nom>.png.

Lancement :  cd "bank system" && /usr/bin/python3 \
             outils/capture_ecrans.py   (spectacle requis, KDE)
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.getcwd())

from PIL import Image                       # noqa: E402

from main import Application                # noqa: E402
from app.ui.comptes_view import _DialogueOuverture   # noqa: E402
from app.ui.session import Session          # noqa: E402

DOSSIER = os.path.join(os.getcwd(), "captures")
app = None                                  # l'Application, créée dans principal()


def stabiliser(duree: float = 0.7) -> None:
    """Laisse Tk traiter ses événements ET X peindre : image fidèle.

    ``time.sleep`` seul gèle l'application (pas de boucle événementielle
    pendant le script) : on alterne update() et petites pauses pour que
    les exposer-events et les timers « after » (toasts…) se déroulent.
    """
    fin = time.time() + duree
    while time.time() < fin:
        app.root.update()
        time.sleep(0.03)


def capturer(nom: str) -> None:
    """Plein écran spectacle, recadré sur la fenêtre, -> captures/nom.png."""
    stabiliser(0.6)
    plein = tempfile.mktemp(suffix=".png")
    subprocess.run(["spectacle", "-f", "-b", "-n", "-o", plein],
                   check=True, capture_output=True)
    stabiliser(0.1)
    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
    l, h = app.root.winfo_width(), app.root.winfo_height()
    image = Image.open(plein)
    image.crop((x, y, x + l, y + h)).save(
        os.path.join(DOSSIER, nom + ".png"))
    os.remove(plein)
    print(f"  capturé : {nom}.png")


def principal() -> None:
    global app
    os.makedirs(DOSSIER, exist_ok=True)
    app = Application()
    app.root.attributes("-topmost", True)
    app.root.deiconify()
    app.root.lift()
    app.root.update()
    time.sleep(0.5)

    for cle, nom in (
        ("dashboard", "dashboard"),
        ("clients", "clients"),
        ("comptes", "comptes"),
        ("operations", "operations"),
        ("galerie", "galerie"),
    ):
        app.shell.afficher(cle)
        capturer(nom)

    # Modale « Ouvrir un compte » par-dessus l'onglet Comptes.
    app.shell.afficher("comptes")
    vue_comptes = app.shell._vues["comptes"]
    titulaire = next(c for c in app.service.read_clients()
                     if c.statut == "ACTIF")
    vue_comptes._var_client.set(
        f"{titulaire.nom_complet} — CIN {titulaire.cin}")
    vue_comptes._rafraichir_tableau()
    boite = _DialogueOuverture(vue_comptes, app.service, titulaire)
    boite.afficher()
    capturer("comptes-ouverture")
    boite.fermer()

    # Espace client : bascule puis les trois écrans.
    client = next(c for c in app.service.read_clients()
                  if len(app.service.read_comptes_par_client(c.id_client))
                  >= 2)
    app.shell.changer_session(Session("client", client))
    capturer("client-comptes")          # le toast « Vue : … » est visible
    app.shell.afficher("mes_operations")
    capturer("client-operations")
    app.shell.afficher("nouvelle_operation")
    capturer("client-nouvelle-operation")

    app.db.close()
    app.root.destroy()
    print("Terminé.")


if __name__ == "__main__":
    principal()
