"""Composant ``Tableau`` : un ``ttk.Treeview`` habillé selon la charte.

Apports par rapport à un Treeview brut :
  * colonnes déclarées par une simple liste de tuples ;
  * lignes zébrées (lisibilité), survol teinté, sélection bleu clair ;
  * mémoïsation des données : ``ligne_selectionnee()`` renvoie le dict ;
  * état vide intégré (« Aucune donnée à afficher ») ;
  * tags sémantiques prêts : ``credit`` (vert), ``debit`` (rouge),
    ``desactive`` (gris).
"""
from __future__ import annotations

from typing import Callable, Iterable, Mapping, Sequence

import tkinter as tk
from tkinter import ttk

from app.ui import theme as T


class Tableau(tk.Frame):
    """Tableau de données de la charte.

    ``colonnes`` : séquence de tuples ``(cle, entete, largeur, ancre)``
    avec ``ancre`` ∈ ``{"w", "e", "center"}``. La dernière colonne
    s'étire quand la fenêtre s'élargit ; les autres gardent leur largeur.

    Le tableau ne formate RIEN : les valeurs fournies à ``remplir()``
    sont déjà du texte d'affichage (via ``app.ui.format``).
    """

    def __init__(self, parent, colonnes: Sequence[tuple],
                 hauteur: int = 10, texte_vide: str = "Aucune donnée à afficher",
                 **kwargs) -> None:
        super().__init__(parent, bg=T.SURFACE, bd=0, **kwargs)
        self._colonnes = tuple(colonnes)
        self._donnees: dict[str, dict] = {}
        self._survole: str | None = None
        self._rappel_double: Callable[[dict], None] | None = None

        defilement = ttk.Scrollbar(self, orient="vertical")
        self.arbre = ttk.Treeview(
            self,
            columns=[cle for cle, *_ in self._colonnes],
            show="headings", height=hauteur, selectmode="browse",
            yscrollcommand=defilement.set)
        for index, (cle, entete, largeur, ancre) in enumerate(self._colonnes):
            self.arbre.heading(cle, text=entete)
            self.arbre.column(
                cle, width=largeur, anchor=ancre,
                stretch=(index == len(self._colonnes) - 1))
        defilement.configure(command=self.arbre.yview)
        defilement.pack(side="right", fill="y")
        self.arbre.pack(side="left", fill="both", expand=True)

        # Tags (couleurs = jetons du thème, jamais de hex hors theme.py).
        self.arbre.tag_configure("paire", background=T.SURFACE_ALT)
        self.arbre.tag_configure("survol", background=T.SURVOL)
        self.arbre.tag_configure("credit", foreground=T.POS)
        self.arbre.tag_configure("debit", foreground=T.NEG)
        self.arbre.tag_configure("desactive", foreground=T.MUTED)

        # État vide : étiquette posée par-dessus le tableau, visible
        # uniquement quand le tableau n'a aucune ligne.
        self._vide = ttk.Label(self.arbre, text=texte_vide, style="Vide.TLabel")

        self.arbre.bind("<Motion>", self._sur_survol)
        self.arbre.bind("<Leave>", self._sur_sortie)
        self.arbre.bind("<Double-1>", self._sur_double_clic)
        self._maj_etat_vide()

    # ------------------------------------------------------------------ #
    #  API publique                                                       #
    # ------------------------------------------------------------------ #
    def remplir(self, lignes: Iterable[Mapping], id_cle: str | None = None,
                tags_fn: Callable[[Mapping], Iterable[str]] | None = None) -> None:
        """Remplace tout le contenu.

        ``id_cle`` : nom de la colonne servant d'identifiant de ligne
        (ex. ``"id_client"``) — l'iid du Treeview vaut alors cette valeur.
        ``tags_fn`` : fonction optionnelle ``ligne -> tags`` pour teinter
        des lignes (``"debit"``, ``"desactive"``…).
        """
        self.vider()
        for index, ligne in enumerate(lignes):
            iid = str(ligne[id_cle]) if id_cle else str(index)
            valeurs = tuple(str(ligne.get(cle, "")) for cle, *_ in self._colonnes)
            tags = [] if index % 2 == 0 else ["paire"]
            if tags_fn:
                tags = list(tags_fn(ligne)) + tags
            self._donnees[iid] = dict(ligne)
            self.arbre.insert("", "end", iid=iid, values=valeurs, tags=tags)
        self._maj_etat_vide()

    def vider(self) -> None:
        """Supprime toutes les lignes (et affiche l'état vide)."""
        self.arbre.delete(*self.arbre.get_children())
        self._donnees.clear()
        self._maj_etat_vide()

    def selection(self) -> str | None:
        """Iid de la ligne sélectionnée, ou ``None``."""
        selection = self.arbre.selection()
        return selection[0] if selection else None

    def ligne_selectionnee(self) -> dict | None:
        """Dict de données de la ligne sélectionnée, ou ``None``."""
        iid = self.selection()
        return self._donnees.get(iid) if iid else None

    def nombre(self) -> int:
        return len(self._donnees)

    def contenu(self) -> list[dict]:
        return list(self._donnees.values())

    def sur_selection(self, rappel: Callable[[dict | None], None]) -> None:
        """``rappel(ligne_ou_None)`` à chaque changement de sélection."""
        self.arbre.bind("<<TreeviewSelect>>",
                        lambda _e: rappel(self.ligne_selectionnee()))

    def sur_double_clic(self, rappel: Callable[[dict], None]) -> None:
        """``rappel(ligne)`` lors d'un double-clic sur une ligne."""
        self._rappel_double = rappel

    # ------------------------------------------------------------------ #
    #  Internes : zébrures, survol, état vide                             #
    # ------------------------------------------------------------------ #
    def _maj_etat_vide(self) -> None:
        if self.arbre.get_children():
            self._vide.place_forget()
        else:
            self._vide.place(relx=0.5, rely=0.5, anchor="center")

    def _retirer_survol(self) -> None:
        if self._survole and self.arbre.exists(self._survole):
            tags = [t for t in self.arbre.item(self._survole, "tags")
                    if t != "survol"]
            self.arbre.item(self._survole, tags=tags)

    def _sur_survol(self, event) -> None:
        iid = self.arbre.identify_row(event.y)
        if iid == self._survole:
            return
        self._retirer_survol()
        if iid:
            tags = list(self.arbre.item(iid, "tags"))
            # Le tag « survol » passe EN PREMIER : à options égales, le
            # premier tag de la liste l'emporte sur les suivants.
            self.arbre.item(iid, tags=["survol"] + [t for t in tags
                                                    if t != "survol"])
        self._survole = iid or None

    def _sur_sortie(self, _event=None) -> None:
        self._retirer_survol()
        self._survole = None

    def _sur_double_clic(self, event) -> None:
        iid = self.arbre.identify_row(event.y)
        if iid and self._rappel_double and iid in self._donnees:
            self._rappel_double(self._donnees[iid])
