"""Écran « Galerie » (développement) : vitrine du système de design.

Rassemble tous les composants de la charte dans tous leurs états. Il
sert de harnais de test visuel pendant la construction de l'interface :
tout composant ajouté au projet est d'abord validé ici, sur un écran
jetable, avant d'entrer dans un vrai écran métier.

À retirer (ou réserver au rôle développeur) une fois les écrans réels
terminés.
"""
from __future__ import annotations

from datetime import date, timedelta

import tkinter as tk
from tkinter import ttk

from app.services.exceptions import ErreurMetier
from app.ui import theme as T
from app.ui.base_view import VueBase
from app.ui.components import (
    Badge, Carte, CarteKPI, Champ, ChampMontant, ConfirmationModale,
    GraphiqueBarres, Tableau, ZoneDefilante, afficher_toast,
)
from app.ui.format import fmt_montant

# Volume quotidien simulé pour la démonstration du graphique.
_VOLUMES_DEMO = (1200, 980, 1540, 760, 2100, 1680, 890,
                 1320, 1750, 640, 1980, 1120, 1450, 1870)


class GalerieView(VueBase):
    titre_onglet = "Galerie (dév)"
    titre_page = "Galerie de style"
    sous_titre = "Tous les composants de la charte, dans tous leurs états."

    # ------------------------------------------------------------------ #
    #  Construction                                                        #
    # ------------------------------------------------------------------ #
    def _construire(self) -> None:
        zone = ZoneDefilante(self)
        zone.pack(fill="both", expand=True)
        conteneur = zone.contenu

        self._section_boutons(conteneur)
        self._section_badges(conteneur)
        self._section_indicateurs(conteneur)
        self._section_tableau(conteneur)
        self._section_saisie(conteneur)
        self._section_retours(conteneur)
        self._section_graphique(conteneur)

    def rafraichir(self) -> None:
        """Écran de démonstration : rien à recharger depuis la base."""

    # ------------------------------------------------------------------ #
    #  Sections                                                            #
    # ------------------------------------------------------------------ #
    def _section_boutons(self, parent) -> None:
        carte = Carte(parent, titre="Boutons — chaque style porte une intention")
        carte.pack(fill="x", pady=(0, 14))
        ligne = tk.Frame(carte.corps, bg=T.SURFACE)
        ligne.pack(fill="x")
        for texte, style in (
            ("Action primaire", "Primaire.TButton"),
            ("Valider", "Succes.TButton"),
            ("Action dangereuse", "Danger.TButton"),
            ("Secondaire", "Secondaire.TButton"),
            ("Lien discret", "Lien.TButton"),
        ):
            ttk.Button(ligne, text=texte, style=style).pack(
                side="left", padx=(0, 8))
        ligne_etats = tk.Frame(carte.corps, bg=T.SURFACE)
        ligne_etats.pack(fill="x", pady=(10, 0))
        for texte, style in (
            ("Désactivé", "Primaire.TButton"),
            ("Désactivé", "Danger.TButton"),
            ("Désactivé", "Secondaire.TButton"),
        ):
            ttk.Button(ligne_etats, text=texte, style=style,
                       state="disabled").pack(side="left", padx=(0, 8))
        tk.Label(carte.corps,
                 text="Bleu = action neutre · vert = validation · "
                      "rouge = destructif · gris = secondaire.",
                 bg=T.SURFACE, fg=T.MUTED,
                 font=T.police(10)).pack(anchor="w", pady=(10, 0))

    def _section_badges(self, parent) -> None:
        carte = Carte(parent, titre="Badges d'état")
        carte.pack(fill="x", pady=(0, 14))
        ligne = tk.Frame(carte.corps, bg=T.SURFACE)
        ligne.pack(fill="x")
        for texte, ton in (("Actif", "actif"), ("Suspendu", "suspendu"),
                           ("Clôturé", "cloture"), ("Nouveau", "neutre"),
                           ("Incident", "danger")):
            Badge(ligne, texte, ton).pack(side="left", padx=(0, 8))

    def _section_indicateurs(self, parent) -> None:
        carte = Carte(parent, titre="Indicateurs (cartes KPI)")
        carte.pack(fill="x", pady=(0, 14))
        rangee = tk.Frame(carte.corps, bg=T.SURFACE)
        rangee.pack(fill="x")
        for index, (libelle, valeur, sous) in enumerate((
            ("Clients", "128", "dont 4 suspendus"),
            ("Comptes actifs", "141", "sur 145 comptes"),
            ("Encours total", fmt_montant(1_234_567.89), "tous comptes confondus"),
            ("Volume des opérations", fmt_montant(340_250.0), "double écriture incluse"),
        )):
            indicateur = CarteKPI(rangee, libelle, valeur)
            indicateur.definir(valeur, sous)
            indicateur.grid(row=0, column=index, sticky="nsew",
                            padx=(0 if index == 0 else 12, 0))
            rangee.columnconfigure(index, weight=1)

    def _section_tableau(self, parent) -> None:
        carte = Carte(parent, titre="Tableau — zébrures, survol, état vide")
        carte.pack(fill="x", pady=(0, 14))
        ttk.Button(carte.actions, text="Remplir la démo",
                   style="Primaire.TButton",
                   command=self._remplir_tableau).pack(side="right")
        ttk.Button(carte.actions, text="Vider (état vide)",
                   style="Secondaire.TButton",
                   command=self._vider_tableau).pack(side="right", padx=(0, 8))

        self._tableau = Tableau(
            carte.corps,
            colonnes=(("numero", "N° compte", 130, "w"),
                      ("titulaire", "Titulaire", 230, "w"),
                      ("type", "Type", 110, "w"),
                      ("solde", "Solde", 140, "e"),
                      ("statut", "Statut", 110, "w")),
            hauteur=5)
        self._tableau.pack(fill="both", expand=True)
        self._tableau.sur_double_clic(
            lambda ligne: afficher_toast(
                self, f"Double-clic : {ligne['titulaire']} "
                      f"({ligne['numero']})", ton="info"))
        tk.Label(carte.corps,
                 text="Survolez une ligne, sélectionnez-la (bleu clair), "
                      "double-cliquez pour l'action.",
                 bg=T.SURFACE, fg=T.MUTED,
                 font=T.police(10)).pack(anchor="w", pady=(8, 0))

    def _remplir_tableau(self) -> None:
        lignes = (
            {"numero": "CPT-0001", "titulaire": "Dupont Alice",
             "type": "COURANT", "solde": fmt_montant(1000.0),
             "statut": "ACTIF"},
            {"numero": "CPT-0002", "titulaire": "Dupont Alice",
             "type": "EPARGNE", "solde": fmt_montant(500.0),
             "statut": "ACTIF"},
            {"numero": "CPT-0003", "titulaire": "Bernard Karim",
             "type": "COURANT", "solde": fmt_montant(900.0),
             "statut": "ACTIF"},
            {"numero": "CPT-0004", "titulaire": "Chemin Fatou",
             "type": "COURANT", "solde": fmt_montant(0.0),
             "statut": "CLOTURE"},
        )
        self._tableau.remplir(
            lignes, id_cle="numero",
            tags_fn=lambda ligne: (["desactive"]
                                   if ligne["statut"] == "CLOTURE" else []))
        afficher_toast(self, f"{self._tableau.nombre()} lignes affichées.",
                       ton="succes")

    def _vider_tableau(self) -> None:
        self._tableau.vider()

    def _section_saisie(self, parent) -> None:
        carte = Carte(parent, titre="Saisie — erreurs affichées sous le champ")
        carte.pack(fill="x", pady=(0, 14))
        grille = tk.Frame(carte.corps, bg=T.SURFACE)
        grille.pack(fill="x")
        self._champ_nom = Champ(grille, "Nom du client", obligatoire=True)
        self._champ_nom.grid(row=0, column=0, sticky="we", padx=(0, 16))
        self._champ_email = Champ(grille, "Email")
        self._champ_email.grid(row=0, column=1, sticky="we", padx=(0, 16))
        self._champ_montant = ChampMontant(grille, "Montant")
        self._champ_montant.grid(row=0, column=2, sticky="we")
        for colonne in range(3):
            grille.columnconfigure(colonne, weight=1)

        actions = tk.Frame(carte.corps, bg=T.SURFACE)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Valider la saisie",
                   style="Primaire.TButton",
                   command=self._valider_saisie).pack(side="left")
        ttk.Button(actions, text="Réinitialiser", style="Secondaire.TButton",
                   command=self._reinitialiser_saisie).pack(side="left",
                                                           padx=(8, 0))

    def _valider_saisie(self) -> None:
        """Démo de validation : erreurs inline, aucun dialogue bloquant."""
        for champ in (self._champ_nom, self._champ_email,
                      self._champ_montant):
            champ.effacer_erreur()
        valide = True
        if self._champ_nom.est_vide():
            self._champ_nom.afficher_erreur("Le nom est obligatoire.")
            valide = False
        email = self._champ_email.lire()
        if email and "@" not in email:
            self._champ_email.afficher_erreur(
                "Email invalide — exemple : nom@domaine.fr")
            valide = False
        montant = None
        try:
            montant = self._champ_montant.valeur()
        except ErreurMetier as erreur:
            self._champ_montant.afficher_erreur(str(erreur))
            valide = False
        if valide:
            afficher_toast(
                self, f"Saisie valide : {self._champ_nom.lire()} · "
                      f"montant {fmt_montant(montant)}", ton="succes")

    def _reinitialiser_saisie(self) -> None:
        for champ in (self._champ_nom, self._champ_email,
                      self._champ_montant):
            champ.vider()
            champ.effacer_erreur()

    def _section_retours(self, parent) -> None:
        carte = Carte(parent, titre="Retours — notifications et confirmation")
        carte.pack(fill="x", pady=(0, 14))
        ligne = tk.Frame(carte.corps, bg=T.SURFACE)
        ligne.pack(fill="x")
        for texte, ton in (("Toast succès", "succes"),
                           ("Toast erreur", "erreur"),
                           ("Toast info", "info"),
                           ("Toast avertissement", "avertissement")):
            ttk.Button(ligne, text=texte, style="Secondaire.TButton",
                       command=lambda t=ton, x=texte: afficher_toast(
                           self, f"{x} — voici une notification "
                                 f"non bloquante.", ton=t)).pack(
                side="left", padx=(0, 8))
        ttk.Button(ligne, text="Ouvrir une confirmation…",
                   style="Primaire.TButton",
                   command=self._demander_confirmation).pack(side="left",
                                                             padx=(16, 0))
        tk.Label(carte.corps,
                 text="Remplace avantageusement les boîtes messagebox : "
                      "ton de la charte, disparition automatique.",
                 bg=T.SURFACE, fg=T.MUTED,
                 font=T.police(10)).pack(anchor="w", pady=(10, 0))

    def _demander_confirmation(self) -> None:
        confirme = ConfirmationModale.demander(
            self, "Confirmation",
            "Cette action est une démonstration. Confirmer l'opération ?",
            texte_confirmer="Confirmer")
        afficher_toast(
            self,
            "Action confirmée." if confirme else "Action annulée.",
            ton="succes" if confirme else "info")

    def _section_graphique(self, parent) -> None:
        carte = Carte(parent, titre="Graphique — volume des opérations "
                                     "(14 derniers jours, données de démo)")
        carte.pack(fill="x", pady=(0, 14))
        graphe = GraphiqueBarres(carte.corps, hauteur=160)
        graphe.pack(fill="both", expand=True)
        aujourd_hui = date.today()
        donnees = []
        for index, volume in enumerate(_VOLUMES_DEMO):
            jour = aujourd_hui - timedelta(days=13 - index)
            donnees.append((jour.strftime("%d/%m"), float(volume)))
        graphe.definir(donnees)
