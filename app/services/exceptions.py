"""Exceptions métier (Rôle 2 — sous-système « traitements »).

Toutes héritent de ``ErreurMetier`` : la couche UI attrape la classe
mère et affiche le message. Chaque classe == une règle de gestion
explicite du SI bancaire, nommée et documentée.
"""
from __future__ import annotations


class ErreurMetier(Exception):
    """Classe mère de toutes les erreurs fonctionnelles."""


class EntreeInvalideError(ErreurMetier):
    """Saisie invalide : champ vide, montant <= 0, email malformé…"""


class CINDupliqueError(ErreurMetier):
    """Le CIN appartient déjà à un autre client (règle d'unicité)."""


class ClientIntrouvableError(ErreurMetier):
    """Aucun client pour la référence demandée."""


class ClientSuspenduError(ErreurMetier):
    """Client SUSPENDU : ouverture de compte / opérations refusées."""


class CompteIntrouvableError(ErreurMetier):
    """Aucun compte pour la référence demandée."""


class CompteClotureError(ErreurMetier):
    """Compte CLOTURE : aucune opération acceptée."""


class SoldeInsuffisantError(ErreurMetier):
    """Retrait ou virement dépassant le solde disponible."""


class CompteNonVideError(ErreurMetier):
    """Clôture refusée : le solde n'est pas nul."""


class ClientAComptesError(ErreurMetier):
    """Suppression refusée : le client possède encore des comptes."""
