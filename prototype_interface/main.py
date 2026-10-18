"""Point d'entrée de l'application bancaire (Rôle 3 — assemblage).

Lancement :  ``python main.py``
Au premier démarrage, la base ``banque.db`` est créée puis peuplée par
les données de démonstration (``app/db/seed.py``).

Ordre d'assemblage — c'est le sens des dépendances, jamais l'inverse :
    données (DatabaseManager) -> métier (BankService) -> interface (AppShell)
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

from app.db.db_manager import DatabaseManager
from app.services.bank_service import BankService
from app.ui.base_view import BusRafraichissement
from app.ui.theme import appliquer_theme
from app.ui.shell import AppShell, EntreeNav
from app.ui.session import Session
from app.ui.dashboard_view import DashboardView
from app.ui.clients_view import ClientsView
from app.ui.comptes_view import ComptesView
from app.ui.operations_view import OperationsView
from app.ui.galerie_view import GalerieView
from app.ui.mes_comptes_view import MesComptesView
from app.ui.mes_operations_view import MesOperationsView
from app.ui.nouvelle_operation_view import NouvelleOperationView
from app.ui.utilitaires import centrer_fenetre

CHEMIN_BASE = Path(__file__).resolve().parent / "banque.db"
TITRE = "Banque MVP — système d'information bancaire"
LARGEUR_FENETRE, HAUTEUR_FENETRE = 1180, 760

# Registre de navigation : LA source unique de vérité des écrans du
# shell. Ajouter un écran = ajouter une ligne ici (et rien d'autre).
# ``roles`` cloisonne les espaces : l'administrateur voit les cinq
# écrans de gestion, le client uniquement ses trois écrans — le shell
# filtre le registre selon la session courante.
NAVIGATION = (
    # -- Espace administrateur -----------------------------------------
    EntreeNav("dashboard", "Tableau de bord", DashboardView),
    EntreeNav("clients", "Clients", ClientsView),
    EntreeNav("comptes", "Comptes", ComptesView),
    EntreeNav("operations", "Opérations", OperationsView),
    EntreeNav("galerie", "Galerie (dév)", GalerieView),
    # -- Espace client --------------------------------------------------
    EntreeNav("mes_comptes", "Mes comptes", MesComptesView,
              roles=("client",)),
    EntreeNav("mes_operations", "Mes opérations", MesOperationsView,
              roles=("client",)),
    EntreeNav("nouvelle_operation", "Nouvelle opération",
              NouvelleOperationView, roles=("client",)),
)


class Application:
    """Assemble les 3 sous-systèmes : données -> métier -> interface."""

    def __init__(self) -> None:
        # ------- sous-système données + métier --------------------------
        premier_lancement = not CHEMIN_BASE.exists()
        self.db = DatabaseManager(CHEMIN_BASE)
        self.db.init_schema()
        if premier_lancement:
            self.db.seed_demo_data()
        self.service = BankService(self.db)

        # ------- sous-système interface ---------------------------------
        self.root = tk.Tk()
        appliquer_theme(self.root)      # AVANT tout widget : styles + polices
        self.root.title(TITRE)
        centrer_fenetre(self.root, LARGEUR_FENETRE, HAUTEUR_FENETRE)
        self.root.minsize(1040, 660)

        # Bus d'événements : le shell (barre d'état) s'y abonne aussi.
        self.bus = BusRafraichissement()
        self.shell = AppShell(self.root, self.service, self.bus, NAVIGATION,
                              session=Session("admin"),
                              info_base=CHEMIN_BASE.name)
        self.shell.pack(fill="both", expand=True)
        self.bus.abonner(self.shell)
        self.shell.afficher("dashboard")

        self.root.protocol("WM_DELETE_WINDOW", self.fermer)
        self.root.bind("<Control-q>", lambda _e: self.fermer())

    def fermer(self) -> None:
        """Fermeture propre : base d'abord, puis fenêtre."""
        self.db.close()
        self.root.destroy()

    def demarrer(self) -> None:
        self.root.mainloop()


def main() -> None:
    Application().demarrer()


if __name__ == "__main__":
    main()
