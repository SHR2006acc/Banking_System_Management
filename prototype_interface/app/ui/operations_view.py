"""Onglet « Opérations » (Rôle 3) : dépôt / retrait / virement + relevé."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.models.models import (
    Compte, Operation,
    STATUT_COMPTE_ACTIF,
    TYPE_DEPOT, TYPE_RETRAIT, TYPE_VIREMENT,
)
from app.services.exceptions import ErreurMetier
from app.ui.base_view import VueBase, fmt_montant
from app.ui.format import extraire_montant, fmt_date


class OperationsView(VueBase):
    titre_onglet = "Opérations"

    def _construire(self) -> None:
        haut = ttk.Frame(self)
        haut.pack(fill="x", pady=(0, 10))
        self._construire_simple(haut, "Dépôt", TYPE_DEPOT)          # 3 champs
        self._construire_simple(haut, "Retrait", TYPE_RETRAIT)      # 3 champs
        self._construire_virement(haut)
        self._construire_releve()

    # ------------------------------------------------------------------ #
    #  Cartes formulaire : dépôt et retrait                              #
    # ------------------------------------------------------------------ #
    def _construire_simple(self, parent, titre: str, type_op: str) -> None:
        texte_bouton = "Encaisser" if type_op == TYPE_DEPOT else "Décaisser"
        style_bouton = ("Succes.TButton" if type_op == TYPE_DEPOT
                        else "Danger.TButton")
        cadre = ttk.LabelFrame(parent, text=titre, style="Carte.TLabelframe",
                               padding=(12, 10))
        corps = tk.Frame(cadre, bg="#ffffff")
        corps.pack()
        var_compte = tk.StringVar()
        var_montant = tk.StringVar()
        var_commentaire = tk.StringVar()
        champ_compte = ttk.Combobox(corps, textvariable=var_compte,
                                    state="readonly", width=32)
        champ_compte.grid(row=0, column=0, columnspan=2, sticky="we", pady=2)
        tk.Label(corps, text="Montant :", bg="#ffffff").grid(
            row=1, column=0, sticky="w")
        ttk.Entry(corps, textvariable=var_montant, width=12).grid(
            row=1, column=1, sticky="we", pady=2)
        tk.Label(corps, text="Commentaire :", bg="#ffffff").grid(
            row=2, column=0, sticky="w")
        ttk.Entry(corps, textvariable=var_commentaire, width=12).grid(
            row=2, column=1, sticky="we", pady=2)
        ttk.Button(cadre, text=texte_bouton, style=style_bouton,
                   command=lambda: self._sur_mouvement_simple(
                       type_op, var_compte, var_montant, var_commentaire)
                   ).pack(anchor="e", pady=(8, 0))
        corps.columnconfigure(1, weight=1)
        attrs = {
            TYPE_DEPOT: ("_combo_depot", "_var_depot", "_var_depot_cmt"),
            TYPE_RETRAIT: ("_combo_retrait", "_var_retrait", "_var_retrait_cmt"),
        }
        combo_attr, montant_attr, cmt_attr = attrs[type_op]
        setattr(self, combo_attr, champ_compte)
        setattr(self, montant_attr, var_montant)
        setattr(self, cmt_attr, var_commentaire)

    # ------------------------------------------------------------------ #
    #  Carte virement (2 comptes + montant)                              #
    # ------------------------------------------------------------------ #
    def _construire_virement(self, parent) -> None:
        cadre = ttk.LabelFrame(parent, text="Virement",
                               style="Carte.TLabelframe", padding=(12, 10))
        corps = tk.Frame(cadre, bg="#ffffff")
        corps.pack()
        self._var_vir_source = tk.StringVar()
        self._var_vir_cible = tk.StringVar()
        self._var_vir_montant = tk.StringVar()
        self._var_vir_cmt = tk.StringVar()
        self._combo_vir_source = ttk.Combobox(
            corps, textvariable=self._var_vir_source, state="readonly", width=32)
        self._combo_vir_cible = ttk.Combobox(
            corps, textvariable=self._var_vir_cible, state="readonly", width=32)
        tk.Label(corps, text="Compte à débiter :", bg="#ffffff").grid(
            row=0, column=0, sticky="w")
        self._combo_vir_source.grid(row=0, column=1, sticky="we", pady=2)
        tk.Label(corps, text="Compte à créditer :", bg="#ffffff").grid(
            row=1, column=0, sticky="w")
        self._combo_vir_cible.grid(row=1, column=1, sticky="we", pady=2)
        tk.Label(corps, text="Montant :", bg="#ffffff").grid(
            row=2, column=0, sticky="w")
        ttk.Entry(corps, textvariable=self._var_vir_montant, width=12).grid(
            row=2, column=1, sticky="we", pady=2)
        ttk.Entry(corps, textvariable=self._var_vir_cmt, width=12).grid(
            row=3, column=1, sticky="we", pady=2)
        tk.Label(corps, text="Commentaire :", bg="#ffffff").grid(
            row=3, column=0, sticky="w")
        ttk.Button(cadre, text="Transférer", style="Action.TButton",
                   command=self._sur_virement).pack(anchor="e", pady=(8, 0))
        corps.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------ #
    #  Relevé (compte ou tout)                                           #
    # ------------------------------------------------------------------ #
    def _construire_releve(self) -> None:
        cadre = ttk.LabelFrame(self, text="Relevé",
                               style="Carte.TLabelframe", padding=(10, 10))
        cadre.pack(fill="both", expand=True)
        barre_filtre = ttk.Frame(cadre)
        barre_filtre.pack(fill="x", pady=(0, 8))
        ttk.Label(barre_filtre, text="Compte :", style="Formulaire.TLabel"
                  ).pack(side="left", padx=(0, 6))
        self._var_releve = tk.StringVar()
        self._combo_releve = ttk.Combobox(
            barre_filtre, textvariable=self._var_releve,
            state="readonly", width=46)
        self._combo_releve.pack(side="left")
        self._combo_releve.bind(
            "<<ComboboxSelected>>", lambda _e: self._rafraichir_releve())
        ttk.Button(barre_filtre, text="Tout", command=self._sur_tout_releve
                   ).pack(side="left", padx=8)

        barre = ttk.Scrollbar(cadre, orient="vertical")
        self.arbre = ttk.Treeview(
            cadre, columns=("date", "type", "detail", "montant", "cmt"),
            show="headings", height=10, yscrollcommand=barre.set)
        self.arbre.tag_configure("credit", foreground="#1b6b2a")
        self.arbre.tag_configure("debit", foreground="#b02020")
        for colonne, texte, largeur, ancre in (
            ("date", "Date", 165, "w"),
            ("type", "Type", 100, "w"),
            ("detail", "Contrepartie / détail", 210, "w"),
            ("montant", "Montant", 110, "e"),
            ("cmt", "Commentaire", 170, "w"),
        ):
            self.arbre.heading(colonne, text=texte)
            self.arbre.column(colonne, width=largeur, anchor=ancre)
        barre.configure(command=self.arbre.yview)
        barre.pack(side="right", fill="y")
        self.arbre.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------ #
    #  Plan de comptes partagé entre les formulaires                     #
    # ------------------------------------------------------------------ #
    def _libelle_compte(self, compte: Compte) -> str:
        titulaire = self.service.obtenir_client(compte.id_client)
        noms = titulaire.nom_complet if titulaire else "—"
        return (f"{compte.numero} — {noms} ({compte.type})")

    def _rafraichir_combos(self) -> None:
        comptes = self.service.read_comptes()
        self._comptes_actifs = [c for c in comptes
                                if c.statut == STATUT_COMPTE_ACTIF]
        self._comptes_tous = comptes
        valeurs_formulaires = [self._libelle_compte(c)
                               for c in self._comptes_actifs]
        for combo in (self._combo_depot, self._combo_retrait,
                      self._combo_vir_source, self._combo_vir_cible):
            combo.configure(values=valeurs_formulaires)
        # relevé : TOUS les comptes, y compris clôturés (historique figé)
        self._combo_releve.configure(
            values=["Tous les comptes"]
                   + [self._libelle_compte(c) for c in comptes])

    def _compte_provenant_libelle(self, libelle: str) -> Compte | None:
        for compte in self._comptes_actifs:
            if self._libelle_compte(compte) == libelle:
                return compte
        return None

    def _compte_releve_selectionne(self) -> Compte | None:
        libelle = self._var_releve.get()
        if not libelle or libelle == "Tous les comptes":
            return None
        for compte in self._comptes_tous:
            if self._libelle_compte(compte) == libelle:
                return compte
        return None

    # ------------------------------------------------------------------ #
    #  Actions                                                           #
    # ------------------------------------------------------------------ #
    def _sur_mouvement_simple(
            self, type_op: str, var_compte, var_montant, var_cmt) -> None:
        compte = self._compte_provenant_libelle(var_compte.get())
        if compte is None:
            messagebox.showinfo(
                type_op.title(), "Sélectionnez un compte dans la liste.",
                parent=self)
            return
        try:
            montant = extraire_montant(var_montant.get())
        except ErreurMetier as exc:
            messagebox.showerror(
                "Montant invalide", str(exc), parent=self)
            return
        try:
            if type_op == TYPE_DEPOT:
                self.service.depot(compte.id_compte, montant,
                                   var_cmt.get().strip() or None)
            else:
                self.service.retrait(compte.id_compte, montant,
                                     var_cmt.get().strip() or None)
        except ErreurMetier as exc:
            self.signaler_erreur(exc)
            return
        var_montant.set("")
        var_cmt.set("")
        self.bus.publier()

    def _sur_virement(self) -> None:
        source = self._compte_provenant_libelle(self._var_vir_source.get())
        cible = self._compte_provenant_libelle(self._var_vir_cible.get())
        if source is None or cible is None:
            messagebox.showinfo(
                "Virement",
                "Sélectionnez le compte à débiter ET le compte à créditer.",
                parent=self)
            return
        try:
            montant = extraire_montant(self._var_vir_montant.get())
        except ErreurMetier as exc:
            messagebox.showerror(
                "Montant invalide", str(exc), parent=self)
            return
        try:
            self.service.virement(
                source.id_compte, cible.id_compte, montant,
                self._var_vir_cmt.get().strip() or None)
        except ErreurMetier as exc:
            self.signaler_erreur(exc)
            return
        self._var_vir_montant.set("")
        self._var_vir_cmt.set("")
        self.bus.publier()

    # ------------------------------------------------------------------ #
    #  Relevé                                                            #
    # ------------------------------------------------------------------ #
    def _sur_tout_releve(self) -> None:
        self._var_releve.set("Tous les comptes")
        self._rafraichir_releve()

    def _sens_operation(self, operation: Operation) -> tuple[str, str]:
        """Rendu d'une ligne : (détail, montant signé)."""
        if operation.type == TYPE_VIREMENT and operation.id_virement:
            jambes = self.service.jambes_virement(operation.id_virement)
            if len(jambes) >= 2:
                source = min(jambes, key=lambda o: o.id_operation or 0)
                autre = next(j for j in jambes
                             if j.id_compte != operation.id_compte)
                numero_autre = (self.service.obtenir_compte(
                    autre.id_compte).numero)
                if source.id_operation == operation.id_operation:
                    return f"vers {numero_autre}", -operation.montant
                return f"depuis {numero_autre}", operation.montant
        if operation.type == TYPE_DEPOT:
            return "", operation.montant
        return "", -operation.montant   # retrait

    def _rafraichir_releve(self) -> None:
        self.vider(self.arbre)
        compte = self._compte_releve_selectionne()
        if compte is not None:
            lignes = self.service.releve(compte.id_compte)
        else:
            # Tout : on affiche les 50 derniers mouvements (montant brut)
            for ligne in self.service.operations_recentes(limite=50):
                self.arbre.insert(
                    "", "end", values=(
                        fmt_date(ligne["date_op"]), ligne["type"],
                        (ligne["numero_contrepartie"]
                         or "") if ligne["type"] == TYPE_VIREMENT else "",
                        fmt_montant(float(ligne["montant"])),
                        ligne["commentaire"] or ""))
            return
        for operation in lignes:
            detail, montant_signe = self._sens_operation(operation)
            signe = "+" if montant_signe >= 0 else "−"
            affichage = signe + " " + fmt_montant(abs(montant_signe))
            self.arbre.insert(
                "", "end", tags=("credit" if montant_signe >= 0 else "debit",),
                values=(fmt_date(operation.date_op), operation.type, detail,
                        affichage, operation.commentaire or ""))

    # ------------------------------------------------------------------ #
    #  Bus                                                               #
    # ------------------------------------------------------------------ #
    def rafraichir(self) -> None:
        self._rafraichir_combos()
        self._rafraichir_releve()
