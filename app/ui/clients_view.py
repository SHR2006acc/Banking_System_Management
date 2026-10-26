"""Onglet « Clients » (Rôle 3) : CRUD complet fiche + tableau.

Flux : saisie -> service (règles métier) -> DAO -> bus.publier() ->
re-synchronisation de tous les onglets. La vue ne parle jamais à la
base directement.
"""
from __future__ import annotations

from tkinter import messagebox, ttk
import tkinter as tk

from app.models.models import STATUT_CLIENT_ACTIF, STATUTS_CLIENT, Client
from app.services.exceptions import ErreurMetier, EntreeInvalideError
from app.ui.base_view import VueBase


class ClientsView(VueBase):
    titre_onglet = "Clients"

    def _construire(self) -> None:
        self._client_courant: Client | None = None

        # ---------------- fiche de saisie (carte gauche) ----------------
        fiche = ttk.LabelFrame(self, text="Fiche client",
                               style="Carte.TLabelframe", padding=14)
        fiche.pack(side="left", fill="y", padx=(0, 12))
        self._var = {cle: tk.StringVar()
                     for cle in ("nom", "prenom", "cin", "telephone",
                                 "email", "statut")}
        self._var["statut"].set(STATUT_CLIENT_ACTIF)
        for rang, (cle, libelle) in enumerate((
            ("nom", "Nom *"),
            ("prenom", "Prénom *"),
            ("cin", "CIN *"),
            ("telephone", "Téléphone"),
            ("email", "Email"),
        )):
            ttk.Label(fiche, text=libelle,
                      style="Formulaire.TLabel").grid(
                row=rang, column=0, sticky="w", pady=4, padx=(0, 8))
            ttk.Entry(fiche, textvariable=self._var[cle],
                      width=28).grid(row=rang, column=1, sticky="we", pady=4)
        ttk.Label(fiche, text="Statut").grid(
            row=5, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Combobox(fiche, textvariable=self._var["statut"],
                     values=list(STATUTS_CLIENT), state="readonly",
                     width=26).grid(row=5, column=1, sticky="we", pady=4)
        fiche.columnconfigure(1, weight=1)

        boutons = ttk.Frame(fiche, style="Carte.TFrame")
        boutons.grid(row=6, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(boutons, text="Ajouter", style="Succes.TButton",
                   command=self._sur_ajouter).pack(side="left", padx=(0, 6))
        ttk.Button(boutons, text="Modifier", style="Action.TButton",
                   command=self._sur_modifier).pack(side="left", padx=(0, 6))
        ttk.Button(boutons, text="Supprimer", style="Danger.TButton",
                   command=self._sur_supprimer).pack(side="left")

        # ---------------- tableau (card droite) ---------------- ----------
        tableau = ttk.LabelFrame(self, text="Clientèle",
                                 style="Carte.TLabelframe", padding=(10, 10))
        tableau.pack(side="left", fill="both", expand=True)
        self._etiquette_nombre = ttk.Label(tableau, text="",
                                           style="CarteTitre.TLabel")
        self._etiquette_nombre.pack(anchor="w", pady=(0, 6))
        barre = ttk.Scrollbar(tableau, orient="vertical")
        self.arbre = ttk.Treeview(
            tableau,
            columns=("id", "cin", "nom", "prenom", "tel", "email", "statut"),
            show="headings", yscrollcommand=barre.set)
        for colonne, texte, largeur, ancre in (
            ("id", "ID", 45, "w"),
            ("cin", "CIN", 100, "w"),
            ("nom", "Nom", 130, "w"),
            ("prenom", "Prénom", 120, "w"),
            ("tel", "Téléphone", 120, "w"),
            ("email", "Email", 170, "w"),
            ("statut", "Statut", 90, "w"),
        ):
            self.arbre.heading(colonne, text=texte)
            self.arbre.column(colonne, width=largeur, anchor=ancre)
        barre.configure(command=self.arbre.yview)
        barre.pack(side="right", fill="y")
        self.arbre.pack(side="left", fill="both", expand=True)
        self.arbre.bind("<<TreeviewSelect>>", self._sur_selection)

    def _sur_selection(self, _event=None) -> None:
        """Clic sur une ligne : charge le client dans la fiche."""
        self.rafraichir_client_courant()
        self.remplir_fiche()

    # ----------------- lecture / sélection ------------------------
    def rafraichir_client_courant(self) -> None:
        """Met la fiche en phase avec la sélection du tableau."""
        selection = self.arbre.selection()
        if not selection:
            self._client_courant = None
            return
        identifiant = int(selection[0])
        self._client_courant = self.service.obtenir_client(identifiant)

    def remplir_fiche(self) -> None:
        client = self._client_courant
        valeurs = {"nom": "", "prenom": "", "cin": "",
                   "telephone": "", "email": ""}
        if client is not None:
            valeurs = {"nom": client.nom, "prenom": client.prenom,
                       "cin": client.cin,
                       "telephone": client.telephone or "",
                       "email": client.email or "",
                       "statut": client.statut}
        for cle, v in valeurs.items():
            self._var[cle].set(v)
        if client is None:
            self._var["statut"].set(STATUT_CLIENT_ACTIF)

    def lire_fiche(self) -> dict:
        """Extrait + valide légèrement : les champs * sont requis."""
        donnees = {cle: var.get().strip() for cle, var in self._var.items()}
        manquants = [lib for cle, lib in (
            ("nom", "nom"), ("prenom", "prénom"), ("cin", "CIN"))
            if not donnees[cle]]
        if manquants:
            raise EntreeInvalideError(
                "Champ(s) obligatoire(s) manquant(s) : " + ", ".join(manquants))
        return donnees

    # ----------------- actions formulaire --------------------------
    def _sur_ajouter(self) -> None:
        try:
            self.service.ajouter_client(**self.lire_fiche())
        except ErreurMetier as exc:
            self.signaler_erreur(exc)
            return
        self._sur_vider()
        self.bus.publier()
        messagebox.showinfo("Client", "Client ajouté.", parent=self)

    def _sur_modifier(self) -> None:
        if self._client_courant is None:
            messagebox.showinfo(
                "Modifier",
                "Sélectionnez d'abord un client dans le tableau.", parent=self)
            return
        try:
            self.service.modifier_client(
                self._client_courant.id_client, **self.lire_fiche())
        except ErreurMetier as exc:
            self.signaler_erreur(exc)
            return
        self.bus.publier()
        messagebox.showinfo("Client", "Client mis à jour.", parent=self)

    def _sur_supprimer(self) -> None:
        if self._client_courant is None:
            messagebox.showinfo(
                "Supprimer",
                "Sélectionnez d'abord un client dans le tableau.", parent=self)
            return
        client = self._client_courant
        if not messagebox.askyesno(
                "Confirmation",
                f"Supprimer définitivement {client.nom_complet} ?",
                parent=self):
            return
        try:
            self.service.supprimer_client(client.id_client)
        except ErreurMetier as exc:
            self.signaler_erreur(exc)  # ex. : possède encore des comptes
            return
        self._sur_vider()
        self.bus.publier()

    def _sur_vider(self) -> None:
        self.arbre.selection_remove(self.arbre.selection())
        self._client_courant = None
        self.remplir_fiche()

    # ----------------- bus / rafraîchissement ----------------------
    def rafraichir(self) -> None:
        clients = self.service.read_clients()
        self.vider(self.arbre)
        for client in clients:
            self.arbre.insert(
                "", "end", iid=str(client.id_client), values=(
                    client.id_client, client.cin, client.nom,
                    client.prenom, client.telephone or "",
                    client.email or "", client.statut))
        self._etiquette_nombre.config(
            text=f"{len(clients)} client(s) enregistré(s)")
