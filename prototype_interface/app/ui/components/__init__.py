"""Composants réutilisables de l'interface (Rôle 3).

Chaque module apporte une famille de briques de la charte :

  * ``cartes``      : Carte, CarteKPI — les panneaux blancs ;
  * ``tableaux``    : Tableau — Treeview zébré avec état vide ;
  * ``champs``      : Champ, ChampMontant, Badge — saisie et états ;
  * ``retours``     : Modale, ConfirmationModale, afficher_toast ;
  * ``graphiques``  : GraphiqueBarres — mini-graphique Canvas ;
  * ``defilement``  : ZoneDefilante — conteneur scrollable.
"""
from app.ui.components.cartes import Carte, CarteKPI
from app.ui.components.champs import Badge, Champ, ChampMontant, ton_pour_statut
from app.ui.components.defilement import ZoneDefilante
from app.ui.components.graphiques import GraphiqueBarres
from app.ui.components.retours import ConfirmationModale, Modale, afficher_toast
from app.ui.components.tableaux import Tableau

__all__ = [
    "Carte", "CarteKPI", "Tableau", "Champ", "ChampMontant", "Badge",
    "ton_pour_statut", "Modale", "ConfirmationModale", "afficher_toast",
    "GraphiqueBarres", "ZoneDefilante",
]
