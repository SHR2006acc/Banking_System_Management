"""Petits utilitaires partagés par la couche interface (Rôle 3)."""
from __future__ import annotations

import tkinter as tk


def lier_recursif(fenetre: tk.Misc, sequence: str, rappel) -> None:
    """Lie ``sequence`` à ``fenetre`` ET à tous ses descendants présents.

    Indispensable pour les zones cliquables composites (un item de la
    barre latérale = un cadre + une barre + une étiquette) : sans cela,
    le survol et le clic s'interrompent dès que la souris passe d'un
    enfant à l'autre.
    """
    fenetre.bind(sequence, rappel)
    for enfant in fenetre.winfo_children():
        lier_recursif(enfant, sequence, rappel)


def centrer_fenetre(fenetre: tk.Misc, largeur: int, hauteur: int) -> None:
    """Centre une fenêtre sur l'écran (léger décalage vers le haut)."""
    fenetre.update_idletasks()
    x = (fenetre.winfo_screenwidth() - largeur) // 2
    y = (fenetre.winfo_screenheight() - hauteur) // 3
    fenetre.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")
