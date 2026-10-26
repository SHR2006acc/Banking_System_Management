"""Mini-graphiques dessinés sur ``tk.Canvas`` (100 % bibliothèque standard).

Aucune dépendance (pas de matplotlib) : des rectangles pleins, un filet
d'axe, zéro décoration — cohérent avec la charte « flat institutionnel ».
"""
from __future__ import annotations

import tkinter as tk

from app.ui import theme as T
from app.ui.format import fmt_entier


class GraphiqueBarres(tk.Frame):
    """Histogramme vertical : ``(etiquette, valeur)`` par barre.

    Utilisation ::

        graphe = GraphiqueBarres(carte.corps, hauteur=150)
        graphe.pack(fill="both", expand=True)
        graphe.definir([("11/10", 1250.0), ("12/10", 980.0), ...])
    """

    def __init__(self, parent, hauteur: int = 150,
                 couleur: str = T.NAVY, **kwargs) -> None:
        super().__init__(parent, bg=T.SURFACE, **kwargs)
        self._couleur = couleur
        self._donnees: list[tuple[str, float]] = []
        self.canvas = tk.Canvas(self, height=hauteur, bg=T.SURFACE,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        # Redessin automatique à chaque changement de taille de la zone.
        self.canvas.bind("<Configure>", lambda _e: self._tracer())

    def definir(self, donnees) -> None:
        """Remplace les données : séquence de ``(etiquette, valeur)``."""
        self._donnees = [(str(etiquette), float(valeur))
                         for etiquette, valeur in donnees]
        self._tracer()

    def _tracer(self) -> None:
        """(Re)dessine le graphique dans le canvas."""
        canvas = self.canvas
        canvas.delete("all")
        largeur, hauteur = canvas.winfo_width(), canvas.winfo_height()
        if largeur <= 1 or hauteur <= 1 or not self._donnees:
            return

        marge_bas, marge_haut = 26, 20          # place pour les légendes
        zone = hauteur - marge_bas - marge_haut
        maximum = max((valeur for _, valeur in self._donnees), default=0) or 1
        nombre = len(self._donnees)
        interstice = 10
        largeur_barre = max(6, (largeur - interstice * (nombre + 1)) / nombre)
        base = hauteur - marge_bas

        # Axe horizontal : un simple filet de 1 px.
        canvas.create_line(0, base, largeur, base, fill=T.LINE)

        for index, (etiquette, valeur) in enumerate(self._donnees):
            x = interstice + index * (largeur_barre + interstice)
            hauteur_barre = (valeur / maximum) * zone
            canvas.create_rectangle(
                x, base - hauteur_barre, x + largeur_barre, base,
                fill=self._couleur, outline="")
            centre = x + largeur_barre / 2
            if nombre <= 8:                    # valeur au-dessus de la barre
                canvas.create_text(centre, base - hauteur_barre - 9,
                                   text=fmt_entier(valeur), fill=T.INK_SOFT,
                                   font=T.police(9))
            canvas.create_text(centre, base + 13, text=etiquette,
                               fill=T.MUTED, font=T.police(9))
