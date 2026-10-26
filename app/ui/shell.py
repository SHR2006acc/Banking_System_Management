"""Coquille de l'application (Rôle 3) : barre latérale, en-tête, routeur.

``AppShell`` remplace le ``ttk.Notebook`` d'origine : navigation
latérale professionnelle, en-tête avec utilisateur, barre d'état, et
routage entre les écrans.

Concepts clés :
  * **Registre** — ``EntreeNav`` décrit chaque écran (clé, libellé,
    classe, rôles autorisés). La barre latérale ET le routeur sont
    construits à partir de cette source unique : ajouter un écran =
    ajouter une ligne dans ``NAVIGATION`` (``main.py``).
  * **Rôles** — le registre complet est filtré selon le rôle de la
    session courante : le client ne voit que ses trois écrans, jamais
    ceux de l'administration.
  * **Instanciation paresseuse** — un écran n'est construit qu'à sa
    première visite, puis conservé (son état interne survit à la
    navigation).
  * **Bus d'événements** — le shell s'y abonne : la barre d'état se
    remet à jour après chaque modification de la base.
  * **Bascule de session** — ``changer_session()`` détruit les écrans
    en cache, purge le bus de ses abonnés morts et reconstruit la
    navigation. Admin et client partagent la même base : une opération
    saisie d'un côté apparaît de l'autre.
"""
from __future__ import annotations

from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk

from app.services.bank_service import BankService
from app.ui import theme as T
from app.ui.base_view import BusRafraichissement, VueBase
from app.ui.components.retours import afficher_toast
from app.ui.session import SelecteurSession, Session
from app.ui.utilitaires import lier_recursif


@dataclass(frozen=True)
class EntreeNav:
    """Description d'un écran dans la navigation du shell.

    ``roles`` porte le cloisonnement Client / Administrateur : le shell
    ne construit que les entrées dont un des rôles autorisés est celui
    de la session courante.
    """

    cle: str
    libelle: str
    classe: type
    roles: tuple[str, ...] = ("admin",)


class AppShell(ttk.Frame):
    """Assemblage : barre latérale + en-tête + zone d'écrans + état."""

    def __init__(self, parent, service: BankService, bus: BusRafraichissement,
                 registre: tuple[EntreeNav, ...],
                 session: Session | None = None,
                 info_base: str = "") -> None:
        super().__init__(parent)
        self._service = service
        self._bus = bus
        self._session = session or Session("admin")
        self._registre_complet = tuple(registre)
        self._info_base = info_base
        self._vues: dict[str, VueBase] = {}
        self._actif: str | None = None
        self._items_nav: dict[str, tuple[tk.Frame, tk.Frame, tk.Label]] = {}

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._construire_barre_laterale()
        self._construire_zone_droite()
        self._construire_raccourcis()
        self._maj_identite()
        self.rafraichir()   # compteurs de la barre d'état dès le départ

    # ================================================================== #
    #  Session                                                            #
    # ================================================================== #
    @property
    def session(self) -> Session:
        return self._session

    @property
    def _registre(self) -> dict[str, EntreeNav]:
        """Écrans visibles pour le rôle de la session courante."""
        return {entree.cle: entree for entree in self._registre_complet
                if self._session.role in entree.roles}

    def changer_session(self, session: Session) -> None:
        """Bascule Administrateur <-> Client, à chaud.

        Les écrans en cache sont détruits (leur périmètre de données
        était celui de l'ancienne session), le bus est purgé de ces
        abonnés morts puis le shell s'y ré-abonne, la navigation et
        l'identité de l'en-tête sont reconstruites. Les deux espaces
        partageant la même base, une opération faite côté client est
        visible côté admin dès la bascule.
        """
        self._session = session
        for vue in self._vues.values():
            vue.destroy()
        self._vues.clear()
        self._actif = None
        self._bus.reinitialiser()
        self._bus.abonner(self)
        self._reconstruire_nav()
        self._maj_identite()
        premier = next(iter(self._registre), None)
        if premier is not None:
            self.afficher(premier)
        self.rafraichir()
        afficher_toast(self, f"Vue : {session.libelle}", ton="info")

    def _choisir_session(self) -> None:
        """Ouvre le sélecteur et bascule si le choix a changé."""
        boite = SelecteurSession(self, self._service, self._session)
        boite.afficher()
        boite.attendre()
        if boite.resultat is not None and boite.resultat != self._session:
            self.changer_session(boite.resultat)

    def _maj_identite(self) -> None:
        """Synchro de l'en-tête (pastille, nom, rôle) sur la session."""
        self._puce_initiales.config(text=self._session.initiales)
        self._etiquette_nom.config(text=self._session.libelle)
        self._etiquette_role.config(text=self._session.sous_libelle)

    # ================================================================== #
    #  Barre latérale                                                     #
    # ================================================================== #
    def _construire_barre_laterale(self) -> None:
        barre = tk.Frame(self, bg=T.NAVY_DEEP, width=238)
        barre.grid(row=0, column=0, sticky="ns")
        barre.grid_propagate(False)     # largeur figée malgré les enfants

        # Marque : monogramme carré + nom.
        marque = tk.Frame(barre, bg=T.NAVY_DEEP)
        marque.pack(fill="x", padx=18, pady=(20, 16))
        tk.Label(marque, text="B", bg=T.SURFACE, fg=T.NAVY,
                 font=T.police(15, True), width=2, height=1).pack(side="left")
        tk.Label(marque, text="BANQUE MVP", bg=T.NAVY_DEEP, fg=T.SURFACE,
                 font=T.police(13, True)).pack(side="left", padx=(10, 0))

        tk.Label(barre, text="NAVIGATION", bg=T.NAVY_DEEP,
                 fg=T.TITRE_SIDEBAR, font=T.police(10, True),
                 anchor="w").pack(fill="x", padx=20, pady=(4, 6))
        # Conteneur des items : vidé/rempli à chaque bascule de session.
        self._liste_nav = tk.Frame(barre, bg=T.NAVY_DEEP)
        self._liste_nav.pack(fill="x")
        self._reconstruire_nav()

        # Pied : déconnexion (reliée à l'authentification plus tard).
        pied = tk.Frame(barre, bg=T.NAVY_DEEP)
        pied.pack(side="bottom", fill="x", pady=(0, 12))
        tk.Frame(pied, bg=T.NAVY_ITEM, height=1).pack(fill="x", padx=16,
                                                      pady=(0, 8))
        self._creer_item_deconnexion(pied)

    def _reconstruire_nav(self) -> None:
        """Recrée les items de navigation depuis le registre filtré."""
        for enfant in self._liste_nav.winfo_children():
            enfant.destroy()
        self._items_nav.clear()
        for entree in self._registre.values():
            self._creer_item_nav(self._liste_nav, entree)
        self._maj_nav()

    def _creer_item_nav(self, parent, entree: EntreeNav) -> None:
        """Un item = cadre + barre d'accent (3 px) + étiquette."""
        conteneur = tk.Frame(parent, bg=T.NAVY_DEEP, height=42,
                             cursor="hand2")
        conteneur.pack(fill="x", pady=1)
        conteneur.pack_propagate(False)
        accent = tk.Frame(conteneur, bg=T.NAVY_DEEP, width=3)
        accent.pack(side="left", fill="y")
        etiquette = tk.Label(conteneur, text=entree.libelle, bg=T.NAVY_DEEP,
                             fg=T.TEXTE_SIDEBAR, font=T.police(11),
                             anchor="w", cursor="hand2")
        etiquette.pack(side="left", fill="both", expand=True, padx=(13, 0))

        self._items_nav[entree.cle] = (conteneur, accent, etiquette)
        # Liaison récursive : le survol ne « saute » pas d'un enfant à
        # l'autre (cadre / barre / étiquette).
        lier_recursif(conteneur, "<Enter>",
                      lambda _e, c=entree.cle: self._maj_nav(c))
        lier_recursif(conteneur, "<Leave>",
                      lambda _e: self._maj_nav(None))
        lier_recursif(conteneur, "<Button-1>",
                      lambda _e, c=entree.cle: self.afficher(c))

    def _creer_item_deconnexion(self, parent) -> None:
        conteneur = tk.Frame(parent, bg=T.NAVY_DEEP, height=40,
                             cursor="hand2")
        conteneur.pack(fill="x")
        etiquette = tk.Label(conteneur, text="Déconnexion", bg=T.NAVY_DEEP,
                             fg=T.TEXTE_SIDEBAR, font=T.police(11),
                             anchor="w", cursor="hand2")
        etiquette.pack(fill="both", expand=True, padx=(16, 0))

        def survoler(_event=None):
            etiquette.config(fg=T.SURFACE)

        def quitter(_event=None):
            etiquette.config(fg=T.TEXTE_SIDEBAR)

        lier_recursif(conteneur, "<Enter>", survoler)
        lier_recursif(conteneur, "<Leave>", quitter)
        lier_recursif(conteneur, "<Button-1>",
                      lambda _e: self._sur_deconnexion())

    def _sur_deconnexion(self) -> None:
        afficher_toast(
            self,
            "Déconnexion : elle sera reliée au module d'authentification "
            "(évolution prévue).", ton="info")

    def _maj_nav(self, survol_cle: str | None = None) -> None:
        """Recolore tous les items selon l'état actif / survolé / normal."""
        for cle, (conteneur, accent, etiquette) in self._items_nav.items():
            if cle == self._actif:
                conteneur.config(bg=T.NAVY_ITEM)
                accent.config(bg=T.SURFACE)          # barre d'accent blanche
                etiquette.config(bg=T.NAVY_ITEM, fg=T.SURFACE,
                                 font=T.police(11, True))
            elif cle == survol_cle:
                conteneur.config(bg=T.NAVY_ITEM)
                accent.config(bg=T.NAVY_ITEM)
                etiquette.config(bg=T.NAVY_ITEM, fg=T.SURFACE,
                                 font=T.police(11))
            else:
                conteneur.config(bg=T.NAVY_DEEP)
                accent.config(bg=T.NAVY_DEEP)
                etiquette.config(bg=T.NAVY_DEEP, fg=T.TEXTE_SIDEBAR,
                                 font=T.police(11))

    # ================================================================== #
    #  Zone droite : en-tête + écrans + barre d'état                      #
    # ================================================================== #
    def _construire_zone_droite(self) -> None:
        droite = tk.Frame(self, bg=T.BG)
        droite.grid(row=0, column=1, sticky="nsew")
        droite.columnconfigure(0, weight=1)
        droite.rowconfigure(1, weight=1)
        self._construire_entete(droite)
        self.zone = tk.Frame(droite, bg=T.BG)
        self.zone.grid(row=1, column=0, sticky="nsew")
        self._construire_barre_etat(droite)

    def _construire_entete(self, parent) -> None:
        entete = tk.Frame(parent, bg=T.SURFACE)
        entete.grid(row=0, column=0, sticky="ew")

        textes = tk.Frame(entete, bg=T.SURFACE)
        textes.pack(side="left", padx=24, pady=(12, 10))
        self._titre_page = tk.Label(textes, text="", bg=T.SURFACE, fg=T.INK,
                                    font=T.police(15, True), anchor="w")
        self._titre_page.pack(fill="x")
        self._sous_page = tk.Label(textes, text="", bg=T.SURFACE, fg=T.MUTED,
                                   font=T.police(10), anchor="w")
        self._sous_page.pack(fill="x")

        droite = tk.Frame(entete, bg=T.SURFACE)
        droite.pack(side="right", padx=24, pady=8)
        ttk.Button(droite, text="Déconnexion", style="Lien.TButton",
                   command=self._sur_deconnexion).pack(side="right")
        tk.Frame(droite, bg=T.LINE, width=1).pack(side="right", fill="y",
                                                  padx=12, pady=3)
        ttk.Button(droite, text="Changer de vue",
                   style="Secondaire.TButton",
                   command=self._choisir_session).pack(side="right")
        tk.Frame(droite, bg=T.LINE, width=1).pack(side="right", fill="y",
                                                  padx=12, pady=3)
        puce = tk.Frame(droite, bg=T.SURFACE)
        puce.pack(side="right")
        self._puce_initiales = tk.Label(puce, text="AD", bg=T.NAVY,
                                        fg=T.SURFACE,
                                        font=T.police(11, True),
                                        padx=9, pady=5)
        self._puce_initiales.pack(side="left")
        identite = tk.Frame(puce, bg=T.SURFACE)
        identite.pack(side="left", padx=(9, 0))
        self._etiquette_nom = tk.Label(identite, text="Administrateur",
                                       bg=T.SURFACE, fg=T.INK,
                                       font=T.police(11, True), anchor="w")
        self._etiquette_nom.pack(fill="x")
        self._etiquette_role = tk.Label(identite, text="Rôle : admin · MVP",
                                        bg=T.SURFACE, fg=T.MUTED,
                                        font=T.police(10), anchor="w")
        self._etiquette_role.pack(fill="x")

        tk.Frame(entete, bg=T.LINE, height=1).pack(side="bottom", fill="x")

    def _construire_barre_etat(self, parent) -> None:
        etat = tk.Frame(parent, bg=T.SURFACE)
        etat.grid(row=2, column=0, sticky="ew")
        tk.Frame(etat, bg=T.LINE, height=1).pack(fill="x")
        contenu = tk.Frame(etat, bg=T.SURFACE)
        contenu.pack(fill="x", padx=18, pady=6)
        texte_base = (f"● Base : {self._info_base}" if self._info_base
                      else "● Base connectée")
        tk.Label(contenu, text=texte_base, bg=T.SURFACE, fg=T.INK_SOFT,
                 font=T.police(10)).pack(side="left")
        self._etat_donnees = tk.Label(contenu, text="", bg=T.SURFACE,
                                      fg=T.INK_SOFT, font=T.police(10))
        self._etat_donnees.pack(side="right")

    # ================================================================== #
    #  Routage                                                            #
    # ================================================================== #
    def afficher(self, cle: str) -> None:
        """Affiche l'écran ``cle`` (créé à la première visite)."""
        if cle not in self._registre:
            return
        vue = self._vues.get(cle)
        if vue is None:
            vue = self._registre[cle].classe(self.zone, self._service,
                                             self._bus,
                                             session=self._session)
            self._bus.abonner(vue)
            self._vues[cle] = vue
        if self._actif and self._actif != cle:
            self._vues[self._actif].pack_forget()
        vue.pack(fill="both", expand=True)
        vue.rafraichir()
        self._actif = cle
        self._titre_page.config(
            text=getattr(vue, "titre_page", "") or self._registre[cle].libelle)
        self._sous_page.config(text=getattr(vue, "sous_titre", "") or "")
        self._maj_nav()

    def rafraichir(self) -> None:
        """Abonné au bus : actualise la barre d'état (compteurs)."""
        stats = self._service.statistiques()
        self._etat_donnees.config(
            text=f"{stats['nb_clients']} clients · "
                 f"{stats['nb_comptes']} comptes · "
                 f"{stats['nb_operations']} opérations")

    # ================================================================== #
    #  Raccourcis clavier                                                 #
    # ================================================================== #
    def _construire_raccourcis(self) -> None:
        racine = self.winfo_toplevel()
        # Posés une fois pour toutes : ils résolvent l'écran à l'index
        # AU MOMENT de l'appui, donc suivent les bascules de session
        # sans re-binding.
        for index in range(1, 10):
            racine.bind(f"<Control-Key-{index}>",
                        lambda _e, i=index - 1: self._ouvrir_par_index(i))
        racine.bind("<F5>", lambda _e: self._rafraichir_actif())

    def _ouvrir_par_index(self, index: int) -> None:
        """Ctrl+1..9 : ouvre le n-ième écran du registre FILTRÉ."""
        cles = list(self._registre)
        if 0 <= index < len(cles):
            self.afficher(cles[index])

    def _rafraichir_actif(self) -> None:
        if self._actif and self._actif in self._vues:
            self._vues[self._actif].rafraichir()
        self.rafraichir()
