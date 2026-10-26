"""Écran client « Mes opérations » (Rôle 3) : le relevé du client.

Sélection du compte dans une liste déroulante, puis relevé détaillé :
chaque ligne reçoit son signe (+ / −) et sa couleur, y compris les
DEUX jambes des virements — débit chez l'émetteur, crédit chez le
bénéficiaire — reconnaissables au ``id_virement`` partagé
(« double écriture », voir ``docs/interface.md``).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.models.models import (
    TYPE_DEPOT, TYPE_RETRAIT, TYPE_VIREMENT,
)
from app.ui import theme as T
from app.ui.base_view import VueBase
from app.ui.components import Carte, Tableau
from app.ui.format import fmt_date, fmt_montant


class MesOperationsView(VueBase):
    titre_onglet = "Mes opérations"
    titre_page = "Mes opérations"
    sous_titre = "Le relevé du compte sélectionné, du plus récent au plus ancien."

    # ------------------------------------------------------------------ #
    #  Construction                                                        #
    # ------------------------------------------------------------------ #
    def _construire(self) -> None:
        self._comptes: list = []

        carte = Carte(self, titre="Compte à consulter")
        carte.pack(fill="x", pady=(0, 14))
        ligne = tk.Frame(carte.corps, bg=T.SURFACE)
        ligne.pack(fill="x")
        self._combo = ttk.Combobox(ligne, state="readonly", width=36)
        self._combo.pack(side="left")
        self._combo.bind("<<ComboboxSelected>>",
                         lambda _e: self._recharger_releve())
        self._solde = tk.Label(ligne, text="", bg=T.SURFACE, fg=T.INK_SOFT,
                               font=T.police(11), anchor="w")
        self._solde.pack(side="left", padx=(14, 0))

        carte_releve = Carte(self, titre="Relevé des opérations")
        carte_releve.pack(fill="both", expand=True)
        self._tableau = Tableau(
            carte_releve.corps,
            colonnes=(("date", "Date", 140, "w"),
                      ("type", "Type", 110, "w"),
                      ("detail", "Détail", 200, "w"),
                      ("montant", "Montant", 150, "e"),
                      ("commentaire", "Commentaire", 220, "w")),
            hauteur=10)
        self._tableau.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    #  Rafraîchissement                                                    #
    # ------------------------------------------------------------------ #
    def rafraichir(self) -> None:
        """Recharge la liste des comptes en conservant la sélection."""
        if self.session is None or self.session.client is None:
            return
        choisi = None
        index = self._combo.current()
        if 0 <= index < len(self._comptes):
            choisi = self._comptes[index].numero

        self._comptes = self.service.read_comptes_par_client(
            self.session.client.id_client)
        self._combo["values"] = [f"{c.numero} — {c.type}"
                                 for c in self._comptes]
        index = next((i for i, c in enumerate(self._comptes)
                      if c.numero == choisi), 0)
        if self._comptes:
            self._combo.current(index)
        else:
            self._combo.set("")
        self._recharger_releve()

    def _compte_selectionne(self):
        index = self._combo.current()
        if 0 <= index < len(self._comptes):
            return self._comptes[index]
        return None

    def _recharger_releve(self) -> None:
        """Remplit le tableau pour le compte sélectionné."""
        compte = self._compte_selectionne()
        if compte is None:
            self._tableau.vider()
            self._solde.config(text="")
            return
        self._solde.config(
            text=f"Solde actuel : {fmt_montant(compte.solde)}")

        lignes = []
        for operation in self.service.releve(compte.id_compte):
            detail, signe = self._sens_et_detail(operation)
            lignes.append({
                "date": fmt_date(operation.date_op),
                "type": operation.type,
                "detail": detail,
                "montant": ("+" if signe > 0 else "") + fmt_montant(signe),
                "commentaire": operation.commentaire or "",
                "_signe": signe,
            })
        self._tableau.remplir(
            lignes,
            tags_fn=lambda ligne: (["credit"] if ligne["_signe"] > 0
                                   else ["debit"] if ligne["_signe"] < 0
                                   else []))

    # ------------------------------------------------------------------ #
    #  Sens des opérations                                                 #
    # ------------------------------------------------------------------ #
    def _sens_et_detail(self, operation) -> tuple[str, float]:
        """Rend une ligne : (détail, montant SIGNÉ vu du compte consulté).

        Pour un virement, la jambe écrite en premier est la source
        (débit) ; l'autre jambe porte le crédit. On résout le numéro du
        compte d'en face via le service — jamais de SQL dans la vue.
        """
        if operation.type == TYPE_VIREMENT and operation.id_virement:
            jambes = self.service.jambes_virement(operation.id_virement)
            if len(jambes) >= 2:
                source = min(jambes, key=lambda o: o.id_operation or 0)
                autre = next((j for j in jambes
                              if j.id_compte != operation.id_compte), None)
                if autre is not None:
                    numero_autre = self.service.obtenir_compte(
                        autre.id_compte).numero
                    if source.id_operation == operation.id_operation:
                        return f"Vers {numero_autre}", -operation.montant
                    return f"Depuis {numero_autre}", operation.montant
        if operation.type == TYPE_DEPOT:
            return "Dépôt", operation.montant
        if operation.type == TYPE_RETRAIT:
            return "Retrait", -operation.montant
        return "", operation.montant
