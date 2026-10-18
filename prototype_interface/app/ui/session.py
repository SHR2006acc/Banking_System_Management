"""Session utilisateur (Rôle 3) : « qui est devant l'interface ? »

Deux espaces, comme le prévoit l'interface cible du projet d'équipe
(``docs/user-interface.md``) :

  * **Administrateur** — tous les écrans de gestion : tableau de bord,
    clients, comptes, opérations, galerie ;
  * **Client** — ses comptes, son relevé, ses opérations.

Le sélecteur (bouton « Changer de vue » de l'en-tête) bascule de l'un à
l'autre à chaud. Les deux espaces partagent le MÊME ``BankService`` et
la même base : une opération saisie côté client est immédiatement
visible côté administrateur — c'est le scénario de démonstration.

Quand le module d'authentification de l'équipe arrivera, il produira
simplement une ``Session`` (rôle + client) à la place du sélecteur :
ni le shell ni les écrans n'auront à changer.
"""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from app.models.models import Client
from app.services.bank_service import BankService
from app.ui import theme as T
from app.ui.components.champs import Badge
from app.ui.components.retours import Modale
from app.ui.utilitaires import lier_recursif


@dataclass(frozen=True)
class Session:
    """Identité courante : rôle + client éventuel (rôle « client »)."""

    role: str = "admin"                 # "admin" | "client"
    client: Client | None = None       # renseigné pour le rôle client

    @property
    def libelle(self) -> str:
        """Nom affiché dans l'en-tête."""
        if self.role == "client" and self.client is not None:
            return self.client.nom_complet
        return "Administrateur"

    @property
    def sous_libelle(self) -> str:
        """Ligne secondaire de l'en-tête (rôle + contexte)."""
        if self.role == "client" and self.client is not None:
            return f"Rôle : client · n° {self.client.id_client}"
        return "Rôle : admin · MVP"

    @property
    def initiales(self) -> str:
        """Monogramme de la pastille (deux lettres)."""
        if self.role == "client" and self.client is not None:
            return (self.client.nom[:1] + self.client.prenom[:1]).upper()
        return "AD"


class SelecteurSession(Modale):
    """Choix de l'espace : Administrateur ou un client enregistré.

    Cycle de vie habituel des modales : ``afficher()`` puis
    ``attendre()`` ; le choix se lit dans ``self.resultat`` (une
    ``Session``, ou ``None`` si l'utilisateur a annulé).
    """

    def __init__(self, parent, service: BankService,
                 courante: Session) -> None:
        super().__init__(parent, "Changer de vue")
        self.resultat: Session | None = None
        self._courante = courante

        tk.Label(self.corps, text="Espace de démonstration :",
                 bg=T.SURFACE, fg=T.INK_SOFT, font=T.police(11),
                 anchor="w").pack(fill="x", pady=(0, 8))

        self._ajouter_option(
            Session("admin"), "Administrateur",
            "Tableau de bord · clients · comptes · opérations")
        for client in service.read_clients():
            self._ajouter_option(
                Session("client", client),
                f"Espace client — {client.nom_complet}",
                f"Client n° {client.id_client} · CIN {client.cin} · "
                f"{client.statut.lower()}")

        ttk.Button(self.pied, text="Annuler", style="Secondaire.TButton",
                   command=self.fermer).pack(side="right")

    # ------------------------------------------------------------------ #
    def _ajouter_option(self, session: Session, titre: str,
                        detail: str) -> None:
        """Une ligne cliquable ; la ligne de la vue courante est teintée."""
        courant = session == self._courante
        base = T.NAVY_TINT if courant else T.SURFACE
        ligne = tk.Frame(self.corps, bg=base, cursor="hand2",
                         highlightthickness=1, highlightbackground=T.LINE,
                         highlightcolor=T.LINE)
        ligne.pack(fill="x", pady=(0, 6))
        textes = tk.Frame(ligne, bg=base)
        textes.pack(side="left", fill="x", expand=True, padx=12, pady=8)
        tk.Label(textes, text=titre, bg=base, fg=T.INK,
                 font=T.police(11, True), anchor="w").pack(fill="x")
        tk.Label(textes, text=detail, bg=base, fg=T.MUTED,
                 font=T.police(10), anchor="w").pack(fill="x")
        if courant:
            Badge(ligne, "actuelle", "neutre").pack(side="right", padx=12)

        # Teinte de survol : on ne recolore que nos propres étiquettes
        # (le badge garde ses couleurs sémantiques).
        teintes = [ligne, textes] + list(textes.winfo_children())

        def teindre(fond: str, _event=None) -> None:
            for widget in teintes:
                widget.config(bg=fond)

        lier_recursif(ligne, "<Enter>", lambda _e: teindre(T.SURFACE_ALT))
        lier_recursif(ligne, "<Leave>", lambda _e: teindre(base))
        lier_recursif(ligne, "<Button-1>",
                      lambda _e, s=session: self._choisir(s))

    def _choisir(self, session: Session) -> None:
        self.resultat = session
        self.fermer()
