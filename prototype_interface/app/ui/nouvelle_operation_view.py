"""Écran client « Nouvelle opération » (Rôle 3).

Le client alimente ou débite SES comptes, ou vire vers un autre compte
de la banque. Chaque action passe par ``BankService`` : les règles
(montant > 0, solde suffisant, comptes ACTIF et distincts, écriture
double atomique pour le virement) sont exactement celles testées dans
``tests/`` — l'interface ne contient aucune règle métier.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.models.models import STATUT_COMPTE_ACTIF
from app.services.exceptions import ErreurMetier
from app.ui import theme as T
from app.ui.base_view import VueBase
from app.ui.components import (
    Carte, Champ, ChampMontant, Modale, afficher_toast,
)
from app.ui.format import fmt_montant


class NouvelleOperationView(VueBase):
    titre_onglet = "Nouvelle opération"
    titre_page = "Nouvelle opération"
    sous_titre = "Déposez, retirez ou virez depuis vos comptes."

    # ------------------------------------------------------------------ #
    #  Construction                                                        #
    # ------------------------------------------------------------------ #
    def _construire(self) -> None:
        self._comptes: list = []

        carte_compte = Carte(self, titre="Depuis votre compte")
        carte_compte.pack(fill="x", pady=(0, 14))
        ligne = tk.Frame(carte_compte.corps, bg=T.SURFACE)
        ligne.pack(fill="x")
        self._combo = ttk.Combobox(ligne, state="readonly", width=36)
        self._combo.pack(side="left")
        self._combo.bind("<<ComboboxSelected>>",
                         lambda _e: self._maj_solde())
        self._solde = tk.Label(ligne, text="", bg=T.SURFACE, fg=T.INK_SOFT,
                               font=T.police(11), anchor="w")
        self._solde.pack(side="left", padx=(14, 0))

        carte_op = Carte(self, titre="Opération")
        carte_op.pack(fill="x")
        self._montant = ChampMontant(carte_op.corps,
                                     "Montant de l'opération")
        self._montant.pack(anchor="w")

        actions = tk.Frame(carte_op.corps, bg=T.SURFACE)
        actions.pack(fill="x", pady=(12, 0))
        self._bouton_depot = ttk.Button(actions, text="Déposer",
                                        style="Succes.TButton",
                                        command=lambda: self._simple("depot"))
        self._bouton_depot.pack(side="left")
        self._bouton_retrait = ttk.Button(actions, text="Retirer",
                                          style="Primaire.TButton",
                                          command=lambda: self._simple(
                                              "retrait"))
        self._bouton_retrait.pack(side="left", padx=(8, 0))
        self._bouton_virement = ttk.Button(
            actions, text="Virement vers un autre compte…",
            style="Secondaire.TButton", command=self._ouvrir_virement)
        self._bouton_virement.pack(side="left", padx=(8, 0))

        tk.Label(carte_op.corps, text=(
            "Le dépôt crédite le compte, le retrait le débite (solde "
            "suffisant exigé). Le virement écrit DEUX lignes liées dans "
            "la même transaction : un débit ici, un crédit chez le "
            "bénéficiaire. Tout apparaît aussitôt côté administrateur."),
            bg=T.SURFACE, fg=T.MUTED, font=T.police(10),
            wraplength=580, justify="left", anchor="w").pack(
            fill="x", pady=(12, 0))

    # ------------------------------------------------------------------ #
    #  Rafraîchissement                                                    #
    # ------------------------------------------------------------------ #
    def rafraichir(self) -> None:
        """Recharge les comptes ACTIFS du client, sélection conservée."""
        if self.session is None or self.session.client is None:
            return
        choisi = None
        index = self._combo.current()
        if 0 <= index < len(self._comptes):
            choisi = self._comptes[index].id_compte

        self._comptes = [c for c in self.service.read_comptes_par_client(
            self.session.client.id_client)
            if c.statut == STATUT_COMPTE_ACTIF]
        self._combo["values"] = [f"{c.numero} — {fmt_montant(c.solde)}"
                                 for c in self._comptes]
        index = next((i for i, c in enumerate(self._comptes)
                      if c.id_compte == choisi), 0)
        if self._comptes:
            self._combo.current(index)
        else:
            self._combo.set("")

        etat = "normal" if self._comptes else "disabled"
        for bouton in (self._bouton_depot, self._bouton_retrait,
                       self._bouton_virement):
            bouton.configure(state=etat)
        self._maj_solde()

    def _compte_selectionne(self):
        index = self._combo.current()
        if 0 <= index < len(self._comptes):
            return self._comptes[index]
        return None

    def _maj_solde(self) -> None:
        compte = self._compte_selectionne()
        self._solde.config(
            text=(f"Solde actuel : {fmt_montant(compte.solde)}"
                  if compte else ""))

    # ------------------------------------------------------------------ #
    #  Dépôt / retrait                                                     #
    # ------------------------------------------------------------------ #
    def _simple(self, genre: str) -> None:
        """Dépôt ou retrait sur le compte sélectionné.

        Les erreurs du service (solde insuffisant, compte clôturé,
        montant invalide) s'affichent SOUS le champ — jamais de trace
        technique. Le succès notifie par toast puis re-synchronise
        toutes les vues via le bus.
        """
        compte = self._compte_selectionne()
        if compte is None:
            afficher_toast(self, "Sélectionnez d'abord un compte.",
                           ton="avertissement")
            return
        self._montant.effacer_erreur()
        try:
            montant = self._montant.valeur()
        except ErreurMetier as erreur:
            self._montant.afficher_erreur(str(erreur))
            return
        try:
            if genre == "depot":
                self.service.depot(compte.id_compte, montant,
                                   commentaire="Dépôt guichet client")
                verbe = "Dépôt"
            else:
                self.service.retrait(compte.id_compte, montant,
                                     commentaire="Retrait guichet client")
                verbe = "Retrait"
        except ErreurMetier as erreur:
            self._montant.afficher_erreur(str(erreur))
            return
        self._montant.vider()
        afficher_toast(self, f"{verbe} de {fmt_montant(montant)} effectué "
                             f"sur {compte.numero}.", ton="succes")
        self.bus.publier()      # toutes les vues + barre d'état du shell

    # ------------------------------------------------------------------ #
    #  Virement                                                            #
    # ------------------------------------------------------------------ #
    def _ouvrir_virement(self) -> None:
        compte = self._compte_selectionne()
        if compte is None or self.session is None \
                or self.session.client is None:
            afficher_toast(self, "Sélectionnez d'abord un compte.",
                           ton="avertissement")
            return
        boite = _DialogueVirement(self, self.service,
                                  self.session.client, compte)
        boite.afficher()
        boite.attendre()
        if boite.resultat:
            afficher_toast(self, boite.resultat, ton="succes")
            self.bus.publier()


class _DialogueVirement(Modale):
    """Saisie d'un virement : compte bénéficiaire + montant.

    Le bénéficiaire est désigné par son NUMÉRO (pratique bancaire) ;
    la résolution numéro -> identifiant est faite ici, si bien qu'un
    numéro inconnu devient un simple message sous le champ. Le point
    d'entrée métier reste ``BankService.virement`` (écriture double).
    """

    def __init__(self, parent, service, client, source) -> None:
        super().__init__(parent, "Virement")
        self._service = service
        self._source = source

        tk.Label(self.corps,
                 text=f"Depuis {source.numero} — "
                      f"{fmt_montant(source.solde)}",
                 bg=T.SURFACE, fg=T.INK, font=T.police(11, True),
                 anchor="w").pack(fill="x", pady=(0, 10))

        self._beneficiaire = Champ(self.corps,
                                   "Compte bénéficiaire (n° CPT-…)",
                                   obligatoire=True, largeur=24)
        self._beneficiaire.pack(fill="x")

        propres = [c.numero for c in service.read_comptes_par_client(
            client.id_client) if c.id_compte != source.id_compte]
        if propres:
            self._beneficiaire.definir(propres[0])
            aide = ("L'un de vos autres comptes est prérempli ; saisissez "
                    "un autre numéro pour virer vers un tiers.")
        else:
            aide = "Saisissez le numéro du compte bénéficiaire."
        tk.Label(self.corps, text=aide, bg=T.SURFACE, fg=T.MUTED,
                 font=T.police(10), anchor="w", wraplength=360,
                 justify="left").pack(fill="x", pady=(4, 10))

        self._montant = ChampMontant(self.corps, "Montant du virement")
        self._montant.pack(fill="x")

        ttk.Button(self.pied, text="Annuler", style="Secondaire.TButton",
                   command=self.fermer).pack(side="right", padx=(8, 0))
        ttk.Button(self.pied, text="Valider le virement",
                   style="Primaire.TButton",
                   command=self._valider).pack(side="right")

    # ------------------------------------------------------------------ #
    def _valider(self) -> None:
        """Contrôles de surface, puis l'appel qui compte : le service."""
        self._beneficiaire.effacer_erreur()
        self._montant.effacer_erreur()

        numero = self._beneficiaire.lire()
        if not numero:
            self._beneficiaire.afficher_erreur(
                "Indiquez le compte bénéficiaire.")
            return
        cible = next((c for c in self._service.read_comptes()
                      if c.numero.upper() == numero.upper()), None)
        if cible is None:
            self._beneficiaire.afficher_erreur(
                f"Compte introuvable : « {numero} ».")
            return
        if cible.id_compte == self._source.id_compte:
            self._beneficiaire.afficher_erreur(
                "Le bénéficiaire ne peut pas être le compte source.")
            return

        try:
            montant = self._montant.valeur()
        except ErreurMetier as erreur:
            self._montant.afficher_erreur(str(erreur))
            return
        try:
            self._service.virement(self._source.id_compte, cible.id_compte,
                                   montant,
                                   commentaire="Virement initié par le client")
        except ErreurMetier as erreur:
            self._montant.afficher_erreur(str(erreur))
            return

        self.resultat = (f"Virement de {fmt_montant(montant)} vers "
                         f"{cible.numero} effectué.")
        self.fermer()
