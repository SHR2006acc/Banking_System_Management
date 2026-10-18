"""Objets du domaine (dataclasses) et constantes de domaines de valeurs.

Rôle 2 — sous-système « traitements ». Ces structures circulent entre
les DAO (persistance), le service (règles métier) et l'UI (affichage).
Les constantes reprennent EXACTEMENT les domaines imposés par les
contraintes CHECK de ``schema.sql`` : source de vérité unique.
Tout écart serait rejeté par la base : ceinture + bretelles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------- #
# Domaines de valeurs (miroirs des CHECK du schéma)                      #
# ---------------------------------------------------------------------- #
TYPE_COURANT = "COURANT"
TYPE_EPARGNE = "EPARGNE"
TYPES_COMPTE = (TYPE_COURANT, TYPE_EPARGNE)

TYPE_DEPOT = "DEPOT"
TYPE_RETRAIT = "RETRAIT"
TYPE_VIREMENT = "VIREMENT"
TYPES_OPERATION = (TYPE_DEPOT, TYPE_RETRAIT, TYPE_VIREMENT)

STATUT_CLIENT_ACTIF = "ACTIF"
STATUT_CLIENT_SUSPENDU = "SUSPENDU"
STATUTS_CLIENT = (STATUT_CLIENT_ACTIF, STATUT_CLIENT_SUSPENDU)

STATUT_COMPTE_ACTIF = "ACTIF"
STATUT_COMPTE_CLOTURE = "CLOTURE"
STATUTS_COMPTE = (STATUT_COMPTE_ACTIF, STATUT_COMPTE_CLOTURE)


def _texte(valeur: object) -> Optional[str]:
    """'' -> None : évite les pseudo-valeurs vides dans la base."""
    texte = (valeur or "").strip()
    return texte or None


@dataclass
class Client:
    """Client de la banque : identité (CIN) + coordonnées."""

    id_client: Optional[int] = None
    nom: str = ""
    prenom: str = ""
    cin: str = ""
    telephone: Optional[str] = None
    email: Optional[str] = None
    statut: str = STATUT_CLIENT_ACTIF
    date_creation: Optional[str] = None

    @property
    def nom_complet(self) -> str:
        """« Nom Prénom » — libellé utilisé par l'interface."""
        return f"{self.nom} {self.prenom}".strip()

    def normaliser(self) -> None:
        """Nettoie la saisie : trim partout, champs vides -> None."""
        self.nom = self.nom.strip()
        self.prenom = self.prenom.strip()
        self.cin = self.cin.strip()
        self.telephone = _texte(self.telephone)
        self.email = _texte(self.email)


@dataclass
class Compte:
    """Compte bancaire rattaché à un client."""

    id_compte: Optional[int] = None
    id_client: int = 0
    numero: str = ""                      # généré : CPT-0001, CPT-0002…
    type: str = TYPE_COURANT
    solde: float = 0.0
    statut: str = STATUT_COMPTE_ACTIF
    date_ouverture: Optional[str] = None


@dataclass
class Operation:
    """Mouvement sur un compte : DEPOT / RETRAIT / VIREMENT.

    Virement : DEUX lignes partageant le même ``id_virement`` (uuid),
    chacune avec ``id_contrepartie`` = l'autre compte. Les deux jambes
    sont écrites (ou annulées) ensemble : « double écriture ».
    """

    id_operation: Optional[int] = None
    id_compte: int = 0
    id_contrepartie: Optional[int] = None
    type: str = TYPE_DEPOT
    montant: float = 0.0
    id_virement: Optional[str] = None
    date_op: Optional[str] = None
    commentaire: Optional[str] = None
