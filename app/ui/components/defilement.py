"""Zone défilante verticale (recette Canvas : ttk n'en fournit pas).

Tk n'a pas de « frame scrollable » : on combine un ``tk.Canvas``, une
``ttk.Scrollbar`` et une frame interne, dont la largeur suit celle du
canvas. La molette est gérée globalement : elle n'agit que sur la zone
survolée (et sur Linux, la molette émet ``<Button-4>`` / ``<Button-5>``,
pas ``<MouseWheel>`` — piège classique).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui import theme as T

_molette_installee = False


def _installer_molette(racine: tk.Misc) -> None:
    """Un seul gestionnaire de molette pour tout le processus."""
    global _molette_installee
    if _molette_installee:
        return
    _molette_installee = True

    def sur_molette(event):
        # Remonter la hiérarchie depuis le widget survolé jusqu'à la
        # zone défilante qui le contient (marquée par attribut).
        widget = event.widget
        while widget is not None:
            zone = getattr(widget, "_zone_defilante", None)
            if zone is not None:
                zone.defiler(event)
                return
            widget = getattr(widget, "master", None)

    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        racine.bind_all(sequence, sur_molette, add="+")


class ZoneDefilante(ttk.Frame):
    """Conteneur défilant vertical.

    Rangez vos widgets dans ``zone.contenu`` (une frame ordinaire) ;
    tout ce qui dépasse devient accessible par la molette ou la barre.
    """

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._zone_defilante = self        # marqueur repéré par la molette
        _installer_molette(self.winfo_toplevel())

        self.canvas = tk.Canvas(self, bg=T.BG, highlightthickness=0, bd=0)
        self.barre = ttk.Scrollbar(self, orient="vertical",
                                   command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.barre.set)
        self.barre.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.contenu = tk.Frame(self.canvas, bg=T.BG)
        self._fenetre = self.canvas.create_window(
            (0, 0), window=self.contenu, anchor="nw")
        self.contenu.bind("<Configure>", self._quand_contenu_change)
        self.canvas.bind("<Configure>", self._quand_canvas_change)

    # ------------------------------------------------------------------ #
    #  Internes                                                           #
    # ------------------------------------------------------------------ #
    def _quand_contenu_change(self, _event=None) -> None:
        """La zone défilante épouse la hauteur réelle du contenu."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _quand_canvas_change(self, event) -> None:
        """La frame interne garde la même largeur que le canvas."""
        self.canvas.itemconfigure(self._fenetre, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def defiler(self, event) -> None:
        """Défile d'une unité selon l'événement molette (X11 ou Windows)."""
        if getattr(event, "num", 0) == 4:
            pas = -1
        elif getattr(event, "num", 0) == 5:
            pas = 1
        else:
            pas = -1 if getattr(event, "delta", 0) > 0 else 1
        self.canvas.yview_scroll(pas, "units")
