"""Rôle 1 — données de démonstration (appelé UNIQUEMENT sur base vierge).

Scénario : 3 clients, 4 comptes (1 clôturé), une dizaine d'opérations
couvrant les 3 types, dont un virement complet à DEUX jambes
(Alice -> Karim) pour illustrer la double écriture.
"""
from __future__ import annotations

import uuid

from app.dao.client_dao import ClientDAO
from app.dao.compte_dao import CompteDAO
from app.dao.operation_dao import OperationDAO
from app.db.db_manager import DatabaseManager
from app.models.models import (
    Client, Compte, Operation,
    STATUT_CLIENT_SUSPENDU, STATUT_COMPTE_CLOTURE,
    TYPE_DEPOT, TYPE_EPARGNE, TYPE_COURANT, TYPE_RETRAIT, TYPE_VIREMENT,
)


def peupler(db: DatabaseManager) -> None:
    """Insère le scénario de démonstration (base vierge attendue)."""
    clients = ClientDAO(db)
    comptes = CompteDAO(db)
    operations = OperationDAO(db)

    # ---------------------------------------------------------------- #
    # 1. Clients                                                        #
    # ---------------------------------------------------------------- #
    alice = Client(nom="Dupont", prenom="Alice", cin="AB123456",
                   telephone="06 11 22 33 44", email="alice.dupont@example.fr")
    karim = Client(nom="Bernard", prenom="Karim", cin="CD234567",
                   telephone="06 55 66 77 88", email="karim.bernard@example.fr")
    fatou = Client(nom="Chemin", prenom="Fatou", cin="EF345678",
                   statut=STATUT_CLIENT_SUSPENDU)
    alice.id_client = clients.create(alice)
    karim.id_client = clients.create(karim)
    fatou.id_client = clients.create(fatou)

    # ---------------------------------------------------------------- #
    # 2. Comptes (numéro généré par le DAO dans la transaction)         #
    # ---------------------------------------------------------------- #
    courant_a = Compte(id_client=alice.id_client, type=TYPE_COURANT)
    epargne_a = Compte(id_client=alice.id_client, type=TYPE_EPARGNE)
    courant_k = Compte(id_client=karim.id_client, type=TYPE_COURANT)
    cloture_f = Compte(id_client=fatou.id_client, type=TYPE_COURANT)
    for compte in (courant_a, epargne_a, courant_k, cloture_f):
        comptes.create(compte)

    # ---------------------------------------------------------------- #
    # 3. Opérations                                                     #
    # ---------------------------------------------------------------- #
    def ecrire(id_compte: int, type_op: str, montant: float,
               contrepartie: int | None = None, ref: str | None = None,
               commentaire: str | None = None) -> None:
        operations.create(Operation(
            id_compte=id_compte, type=type_op, montant=montant,
            id_contrepartie=contrepartie, id_virement=ref,
            commentaire=commentaire))

    ecrire(courant_a.id_compte, TYPE_DEPOT, 1000.0, commentaire="Versement initial")
    ecrire(courant_a.id_compte, TYPE_DEPOT, 800.0, commentaire="Salaire octobre")
    ecrire(courant_a.id_compte, TYPE_RETRAIT, 300.0, commentaire="Retrait DAB")
    ecrire(epargne_a.id_compte, TYPE_DEPOT, 500.0, commentaire="Livret A")
    ecrire(courant_k.id_compte, TYPE_DEPOT, 400.0, commentaire="Versement initial")
    ecrire(cloture_f.id_compte, TYPE_DEPOT, 250.0, commentaire="Solde d'ouverture")
    ecrire(cloture_f.id_compte, TYPE_RETRAIT, 250.0,
           commentaire="Vidage avant clôture")

    # Virement Alice -> Karim : DEUX jambes, UN seul identifiant (uuid)
    ref = str(uuid.uuid4())
    ecrire(courant_a.id_compte, TYPE_VIREMENT, 500.0,
           contrepartie=courant_k.id_compte, ref=ref, commentaire="Part du loyer")
    ecrire(courant_k.id_compte, TYPE_VIREMENT, 500.0,
           contrepartie=courant_a.id_compte, ref=ref, commentaire="Part du loyer")

    # Clôture du compte de Fatou : tracée, après vidage du solde.
    comptes.update_solde(cloture_f.id_compte, 0.0)
    cloture_f.statut = STATUT_COMPTE_CLOTURE
    comptes.update(cloture_f)

    # ---------------------------------------------------------------- #
    # 4. Soldes cohérents avec l'historique ci-dessus                   #
    # ---------------------------------------------------------------- #
    comptes.update_solde(courant_a.id_compte, 1000.0)   # 1000+800-300-500
    comptes.update_solde(epargne_a.id_compte, 500.0)
    comptes.update_solde(courant_k.id_compte, 900.0)    # 400+500
    comptes.update_solde(cloture_f.id_compte, 0.0)
