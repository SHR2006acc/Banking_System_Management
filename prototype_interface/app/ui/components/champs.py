"""Composants de saisie : ``Champ``, ``ChampMontant``, ``Badge``.

Principe : le champ affiche son erreur LUI-MÊME (ligne rouge sous la
saisie) au lieu d'ouvrir une boîte de dialogue. L'utilisateur corrige
sans perdre le contexte.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui import theme as T
from app.ui.format import extraire_montant


class Champ(ttk.Frame):
    """Libellé + zone de saisie + ligne d'erreur inline (masquée).

    Utilisation ::

        champ = Champ(carte.corps, "Nom", obligatoire=True)
        champ.pack(fill="x")
        ...
        if champ.est_vide():
            champ.afficher_erreur("Le nom est obligatoire.")
    """

    def __init__(self, parent, libelle: str, obligatoire: bool = False,
                 valeur: str = "", largeur: int = 28,
                 fond: str = T.SURFACE, style: str = "Carte.TFrame") -> None:
        super().__init__(parent, style=style)
        self._fond = fond
        texte = libelle + (" *" if obligatoire else "")
        tk.Label(self, text=texte, bg=fond, fg=T.INK_SOFT,
                 font=T.police(11), anchor="w").grid(row=0, column=0, sticky="w")
        self.var = tk.StringVar(value=valeur)
        self.entree = ttk.Entry(self, textvariable=self.var, width=largeur)
        self.entree.grid(row=1, column=0, sticky="we", pady=(3, 0))
        self._erreur = tk.Label(self, text="", bg=fond, fg=T.NEG,
                                font=T.police(10), anchor="w", justify="left")
        self._erreur.grid(row=2, column=0, sticky="w", pady=(3, 0))
        self._erreur.grid_remove()          # masquée tant que tout va bien
        self.columnconfigure(0, weight=1)

    # -- lecture / écriture ------------------------------------------------
    def lire(self) -> str:
        """Texte saisi, espaces retirés aux extrémités."""
        return self.var.get().strip()

    def definir(self, valeur) -> None:
        self.var.set("" if valeur is None else str(valeur))

    def vider(self) -> None:
        self.definir("")

    def est_vide(self) -> bool:
        return not self.lire()

    # -- retour visuel -------------------------------------------------------
    def afficher_erreur(self, message: str) -> None:
        self._erreur.config(text=message)
        self._erreur.grid()

    def effacer_erreur(self) -> None:
        self._erreur.config(text="")
        self._erreur.grid_remove()

    def donner_focus(self) -> None:
        self.entree.focus_set()


class ChampMontant(Champ):
    """Saisie d'un montant : aligné à droite, filtre de frappe, suffixe €.

    ``valeur()`` relit la saisie à la française (« 1 250,50 ») et lève
    une ``EntreeInvalideError`` au message prêt à afficher si besoin.
    """

    def __init__(self, parent, libelle: str, largeur: int = 14,
                 fond: str = T.SURFACE, style: str = "Carte.TFrame") -> None:
        super().__init__(parent, libelle, largeur=largeur,
                         fond=fond, style=style)
        self.entree.configure(justify="right")
        tk.Label(self, text="€", bg=fond, fg=T.INK_SOFT,
                 font=T.police(11)).grid(row=1, column=1, sticky="w",
                                         padx=(6, 0))
        # Filtre de frappe : seuls chiffres, espaces et séparateurs passent.
        self.entree.bind("<KeyRelease>", self._filtrer_frappe)

    def _filtrer_frappe(self, _event=None) -> None:
        brut = self.var.get()
        propre = "".join(c for c in brut if c.isdigit() or c in " .,")
        if propre != brut:
            self.var.set(propre)

    def valeur(self) -> float:
        """Montant validé (> 0) ; lève ``EntreeInvalideError`` sinon."""
        return extraire_montant(self.var.get())


class Badge(tk.Label):
    """Étiquette d'état : majuscules, coins francs, fond teinté.

    Tons disponibles : ``actif`` (vert), ``suspendu`` (ambre),
    ``cloture`` (gris), ``neutre`` (bleu), ``danger`` (rouge).
    """

    _TONS = {
        "actif": (T.POS, T.POS_TINT),
        "suspendu": (T.WARN, T.WARN_TINT),
        "cloture": (T.INK_SOFT, T.BADGE_NEUTRE_TINT),
        "neutre": (T.NAVY, T.NAVY_TINT),
        "danger": (T.NEG, T.NEG_TINT),
    }

    def __init__(self, parent, texte: str = "", ton: str = "neutre") -> None:
        avant, arriere = self._TONS.get(ton, self._TONS["neutre"])
        super().__init__(parent, text=str(texte).upper(), bg=arriere,
                         fg=avant, font=T.police(10, True), padx=9, pady=3)

    def definir(self, texte: str, ton: str = "neutre") -> None:
        avant, arriere = self._TONS.get(ton, self._TONS["neutre"])
        self.config(text=str(texte).upper(), fg=avant, bg=arriere)


def ton_pour_statut(statut: str) -> str:
    """Statut métier -> ton de badge (source unique de correspondance)."""
    correspondance = {
        "ACTIF": "actif",
        "SUSPENDU": "suspendu",
        "CLOTURE": "cloture",
        "COURANT": "neutre",
        "EPARGNE": "neutre",
    }
    return correspondance.get((statut or "").upper(), "neutre")
