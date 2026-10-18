"""Onglet « Comptes » (Rôle 3) : filtre client, ouverture, clôture."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.models.models import TYPE_COURANT, TYPE_EPARGNE, Client
from app.services.exceptions import ErreurMetier
from app.ui import theme as T
from app.ui.base_view import VueBase, fmt_montant
from app.ui.components import (
    ChampMontant, ConfirmationModale, Modale, afficher_toast,
)
from app.ui.format import extraire_montant, fmt_date


class ComptesView(VueBase):
    titre_onglet = "Comptes"

    def _construire(self) -> None:
        # ---------------- filtre par client --------------------------
        filtre = ttk.LabelFrame(self, text="Titulaire",
                                style="Carte.TLabelframe", padding=(12, 8))
        filtre.pack(fill="x", pady=(0, 10))
        ttk.Label(filtre, text="Client :", style="Formulaire.TLabel").pack(
            side="left", padx=(0, 8))
        self._var_client = tk.StringVar()
        self._combo_clients = ttk.Combobox(
            filtre, textvariable=self._var_client, state="readonly", width=44)
        self._combo_clients.pack(side="left")
        self._combo_clients.bind(
            "<<ComboboxSelected>>", lambda _e: self._rafraichir_tableau())
        ttk.Button(filtre, text="Tous", style="Lien.TButton",
                   command=self._reinitialiser_filtre).pack(side="left", padx=8)

        # ---------------- actions de gestion --------------------------
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Ouvrir un compte…",
                   style="Succes.TButton", command=self._sur_ouvrir).pack(
            side="left")
        ttk.Button(actions, text="Clôturer le compte sélectionné",
                   style="Danger.TButton", command=self._sur_cloturer).pack(
            side="left", padx=8)

        # ---------------- tableau ------------------------------------
        tableau = ttk.LabelFrame(self, text="Comptes",
                                 style="Carte.TLabelframe", padding=(10, 10))
        tableau.pack(fill="both", expand=True)
        self._etiquette_nombre = ttk.Label(tableau, text="",
                                           style="CarteTitre.TLabel")
        self._etiquette_nombre.pack(anchor="w", pady=(0, 6))
        barre = ttk.Scrollbar(tableau, orient="vertical")
        self.arbre = ttk.Treeview(
            tableau,
            columns=("numero", "titulaire", "type", "solde", "statut", "date"),
            show="headings", yscrollcommand=barre.set)
        for colonne, texte, largeur, ancre in (
            ("numero", "N° compte", 110, "w"),
            ("titulaire", "Titulaire", 190, "w"),
            ("type", "Type", 100, "w"),
            ("solde", "Solde", 120, "e"),
            ("statut", "Statut", 90, "w"),
            ("date", "Ouverture", 160, "w"),
        ):
            self.arbre.heading(colonne, text=texte)
            self.arbre.column(colonne, width=largeur, anchor=ancre)
        barre.configure(command=self.arbre.yview)
        barre.pack(side="right", fill="y")
        self.arbre.pack(side="left", fill="both", expand=True)

    # ---------------- lecture clients + tableau --------------------------
    def _rafraichir_combo(self) -> None:
        self._clients: list[Client] = self.service.read_clients()
        valeurs = [""] + [f"{c.nom_complet} — CIN {c.cin}" for c in self._clients]
        courant = self._var_client.get()
        self._combo_clients.configure(values=valeurs)
        if courant not in valeurs:
            self._var_client.set("")

    def _client_selectionne(self) -> Client | None:
        cle = self._var_client.get()
        for client in self._clients:
            if f"{client.nom_complet} — CIN {client.cin}" == cle:
                return client
        return None

    def _reinitialiser_filtre(self) -> None:
        self._var_client.set("")
        self._rafraichir_tableau()

    def _rafraichir_tableau(self) -> None:
        self.vider(self.arbre)
        client = self._client_selectionne()
        comptes = (self.service.read_comptes_par_client(client.id_client)
                   if client else self.service.read_comptes())
        self._etiquette_nombre.config(
            text=f"{len(comptes)} compte(s) — "
                 f"titulaire : {client.nom_complet if client else 'tous les clients'}")
        for compte in comptes:
            titulaire = self.service.obtenir_client(compte.id_client)
            self.arbre.insert(
                "", "end", iid=str(compte.id_compte), values=(
                    compte.numero, titulaire.nom_complet, compte.type,
                    fmt_montant(compte.solde), compte.statut,
                    fmt_date(compte.date_ouverture)))

    def rafraichir(self) -> None:
        self._rafraichir_combo()
        self._rafraichir_tableau()

    # ---------------- ouverture d'un compte ------------------------------
    def _sur_ouvrir(self) -> None:
        client = self._client_selectionne()
        if client is None:
            afficher_toast(
                self, "Choisissez d'abord le client titulaire dans le "
                      "filtre ci-dessus.", ton="avertissement")
            return
        boite = _DialogueOuverture(self, self.service, client)
        boite.afficher()
        boite.attendre()
        if boite.resultat is not None:
            afficher_toast(
                self, f"Compte {boite.resultat.numero} ouvert pour "
                      f"{client.nom_complet} — solde initial "
                      f"{fmt_montant(boite.resultat.solde)}.", ton="succes")
            self.bus.publier()

    # ---------------- clôture -------------------------------------------
    def _sur_cloturer(self) -> None:
        selection = self.arbre.selection()
        if not selection:
            afficher_toast(self, "Sélectionnez un compte dans le tableau.",
                           ton="avertissement")
            return
        compte = self.service.obtenir_compte(int(selection[0]))
        if not ConfirmationModale.demander(
                self, "Clôture",
                f"Clôturer définitivement {compte.numero} "
                f"(solde {fmt_montant(compte.solde)}) ?\n"
                "Un compte clôturé n'accepte plus aucune opération.",
                texte_confirmer="Clôturer"):
            return
        try:
            self.service.cloturer_compte(compte.id_compte)
        except ErreurMetier as exc:
            afficher_toast(self, str(exc), ton="erreur")  # ex. solde non nul
            return
        afficher_toast(self, f"Compte {compte.numero} clôturé.",
                       ton="succes")
        self.bus.publier()


class _DialogueOuverture(Modale):
    """Boîte modale « Ouvrir un compte » : type + solde initial.

    Bâtie sur ``Modale`` (charte, ✕, Échap, focus différé) : le
    constructeur ne bloque pas. L'appelant fait ``afficher()`` puis
    ``attendre()``, et lit ``resultat`` : le ``Compte`` créé, ou None.
    """

    def __init__(self, parent, service, client: Client) -> None:
        super().__init__(parent, "Ouvrir un compte")
        self._service = service
        self._client = client

        tk.Label(self.corps, text=f"Titulaire : {client.nom_complet}",
                 bg=T.SURFACE, fg=T.INK, font=T.police(11, True),
                 anchor="w").pack(fill="x", pady=(0, 10))

        tk.Label(self.corps, text="Type de compte", bg=T.SURFACE,
                 fg=T.INK_SOFT, font=T.police(11),
                 anchor="w").pack(fill="x")
        self._var_type = tk.StringVar(value=TYPE_COURANT)
        ttk.Combobox(self.corps, textvariable=self._var_type,
                     values=[TYPE_COURANT, TYPE_EPARGNE],
                     state="readonly", width=20).pack(anchor="w",
                                                      pady=(3, 12))

        self._solde = ChampMontant(self.corps, "Solde initial")
        self._solde.pack(fill="x")
        self._solde.definir("0")
        tk.Label(self.corps,
                 text="Le solde initial peut rester à 0 ; il est crédité "
                      "dès l'ouverture.",
                 bg=T.SURFACE, fg=T.MUTED, font=T.police(10),
                 wraplength=380, justify="left",
                 anchor="w").pack(fill="x", pady=(6, 0))

        ttk.Button(self.pied, text="Annuler", style="Secondaire.TButton",
                   command=self.fermer).pack(side="right", padx=(8, 0))
        ttk.Button(self.pied, text="Ouvrir le compte",
                   style="Succes.TButton",
                   command=self._sur_valider).pack(side="right")

    def _sur_valider(self) -> None:
        self._solde.effacer_erreur()
        try:
            solde = extraire_montant(self._solde.lire() or "0",
                                     zero_autorise=True)
        except ErreurMetier as erreur:
            self._solde.afficher_erreur(str(erreur))
            return
        try:
            self.resultat = self._service.ouvrir_compte(
                self._client.id_client, self._var_type.get(), solde)
        except ErreurMetier as erreur:
            self._solde.afficher_erreur(str(erreur))
            return
        self.fermer()
