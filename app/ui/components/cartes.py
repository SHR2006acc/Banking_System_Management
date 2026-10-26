"""Composants « cartes » : le panneau blanc, brique de base de la page."""
from __future__ import annotations

import tkinter as tk

from app.ui import theme as T


class Carte(tk.Frame):
    """Panneau blanc à filet 1 px (coins francs, aucun arrondi).

    Structure ::

        ┌─ barre d'accent (2 px, optionnelle) ─────────┐
        │ Titre                        [zone actions]   │
        │ ──────────── filet 1 px ────────────          │
        │ corps : vos widgets                           │
        └──────────────────────────────────────────────┘

    Utilisation ::

        carte = Carte(parent, titre="Fiche client", accent=T.NAVY)
        ttk.Label(carte.corps, text="Nom").pack(fill="x")
        ttk.Button(carte.actions, text="Ajouter").pack(side="right")
    """

    def __init__(self, parent, titre: str | None = None,
                 accent: str | None = None, padding: int = 16,
                 **kwargs) -> None:
        super().__init__(parent, bg=T.SURFACE, bd=0,
                         highlightthickness=1,
                         highlightbackground=T.LINE,
                         highlightcolor=T.LINE, **kwargs)
        if accent:
            tk.Frame(self, bg=accent, height=2).pack(fill="x", side="top")

        self.actions: tk.Frame | None = None
        if titre is not None:
            entete = tk.Frame(self, bg=T.SURFACE)
            entete.pack(fill="x", padx=padding, pady=(12, 0))
            tk.Label(entete, text=titre, bg=T.SURFACE, fg=T.NAVY,
                     font=T.police(13, True), anchor="w").pack(side="left")
            self.actions = tk.Frame(entete, bg=T.SURFACE)
            self.actions.pack(side="right")
            tk.Frame(self, bg=T.LINE, height=1).pack(
                fill="x", padx=padding, pady=(10, 0))

        self.corps = tk.Frame(self, bg=T.SURFACE)
        haut = 12 if titre is not None else padding
        self.corps.pack(fill="both", expand=True,
                        padx=padding, pady=(haut, padding))


class CarteKPI(Carte):
    """Carte d'indicateur : légende, grande valeur, sous-texte.

    C'est la brique des tableaux de bord (clients, encours, volume…).
    """

    def __init__(self, parent, libelle: str, valeur: str = "—",
                 accent: str = T.NAVY, **kwargs) -> None:
        super().__init__(parent, accent=accent, padding=16, **kwargs)
        tk.Label(self.corps, text=libelle.upper(), bg=T.SURFACE, fg=T.MUTED,
                 font=T.police(10, True), anchor="w").pack(fill="x")
        self._valeur = tk.Label(self.corps, text=valeur, bg=T.SURFACE,
                                fg=T.INK, font=T.police(24, True), anchor="w")
        self._valeur.pack(fill="x", pady=(6, 0))
        self._sous = tk.Label(self.corps, text="", bg=T.SURFACE,
                              fg=T.INK_SOFT, font=T.police(10), anchor="w")
        self._sous.pack(fill="x", pady=(3, 0))

    def definir(self, valeur: str, sous: str | None = None) -> None:
        """Met à jour la valeur affichée (et le sous-texte optionnel)."""
        self._valeur.config(text=str(valeur))
        self._sous.config(text=sous or "")
