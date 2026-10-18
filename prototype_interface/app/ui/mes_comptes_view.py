"""Écran client « Mes comptes » (Rôle 3).

Pendant de ``comptes_view`` côté administrateur — même service, même
base — mais le périmètre est dicté par la session : le client ne voit
que ``read_comptes_par_client``. L'écran n'est construit que dans
l'espace client (``roles=("client",)`` dans ``NAVIGATION``).
"""
from __future__ import annotations

import tkinter as tk

from app.models.models import STATUT_COMPTE_ACTIF, STATUT_COMPTE_CLOTURE
from app.ui import theme as T
from app.ui.base_view import VueBase
from app.ui.components import Carte, CarteKPI, Tableau
from app.ui.format import fmt_date, fmt_montant


class MesComptesView(VueBase):
    titre_onglet = "Mes comptes"
    titre_page = "Mes comptes"
    sous_titre = "Vos comptes et leurs soldes, en temps réel."

    # ------------------------------------------------------------------ #
    #  Construction                                                        #
    # ------------------------------------------------------------------ #
    def _construire(self) -> None:
        indicateurs = tk.Frame(self, bg=T.BG)
        indicateurs.pack(fill="x", pady=(0, 14))
        self._kpi_actifs = CarteKPI(indicateurs, "Comptes actifs")
        self._kpi_actifs.grid(row=0, column=0, sticky="nsew")
        self._kpi_encours = CarteKPI(indicateurs, "Encours total")
        self._kpi_encours.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        indicateurs.columnconfigure(0, weight=1)
        indicateurs.columnconfigure(1, weight=1)

        carte = Carte(self, titre="Vos comptes")
        carte.pack(fill="both", expand=True)
        self._tableau = Tableau(
            carte.corps,
            colonnes=(("numero", "N° compte", 150, "w"),
                      ("type", "Type", 120, "w"),
                      ("ouverture", "Ouverture", 130, "w"),
                      ("solde", "Solde", 170, "e"),
                      ("statut", "Statut", 120, "w")),
            hauteur=8)
        self._tableau.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    #  Rafraîchissement                                                    #
    # ------------------------------------------------------------------ #
    def rafraichir(self) -> None:
        """Recharge les comptes du client connecté depuis le service."""
        if self.session is None or self.session.client is None:
            return
        comptes = self.service.read_comptes_par_client(
            self.session.client.id_client)

        lignes = []
        for compte in comptes:
            lignes.append({
                "numero": compte.numero,
                "type": compte.type,
                "ouverture": fmt_date(compte.date_ouverture),
                "solde": fmt_montant(compte.solde),
                "statut": compte.statut,
            })
        self._tableau.remplir(
            lignes, id_cle="numero",
            tags_fn=lambda ligne: (["desactive"]
                                   if ligne["statut"] == STATUT_COMPTE_CLOTURE
                                   else []))

        actifs = [c for c in comptes if c.statut == STATUT_COMPTE_ACTIF]
        accord = "s" if len(comptes) > 1 else ""
        self._kpi_actifs.definir(str(len(actifs)),
                                 f"sur {len(comptes)} compte{accord}")
        self._kpi_encours.definir(
            fmt_montant(sum(c.solde for c in actifs)),
            "soldes cumulés de vos comptes actifs")
