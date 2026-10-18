"""Sous-système « traitements » (Rôle 2) : TOUTES les règles de gestion.

La façade unique utilisée par l'UI. Position : entre les DAO (Rôle 1,
persistance brute) et les vues (Rôle 3, interface). Cette classe ne
fait JAMAIS d'IO écran, ne touche jamais à sqlite directement, et
n'importe jamais tkinter.

Règles portées :
  1. Montants strictement positifs (dépôt, retrait, virement).
  2. Solde >= 0 : vérifié AVANT écriture -> SoldeInsuffisantError ;
     le CHECK SQL reste le dernier rempart.
  3. Compte CLOTURE -> aucune opération (CompteClotureError).
  4. Client SUSPENDU -> ouverture de compte refusée et opérations
     bloquées sur ses comptes (ClientSuspenduError).
  5. Client supprimable UNIQUEMENT sans comptes (ClientAComptesError) :
     on ne détruit jamais l'historique.
  6. Virement = DEUX jambes écrites dans UNE transaction (voir
     ``virement``) : atomique, cohérent, traçable (uuid commun).
"""
from __future__ import annotations

import re
import uuid

from app.dao.client_dao import ClientDAO
from app.dao.compte_dao import CompteDAO
from app.dao.operation_dao import OperationDAO
from app.db.db_manager import DatabaseManager
from app.models.models import (
    Client, Compte, Operation,
    STATUT_CLIENT_ACTIF, STATUT_CLIENT_SUSPENDU, STATUTS_CLIENT,
    STATUT_COMPTE_ACTIF, STATUT_COMPTE_CLOTURE,
    TYPE_COURANT, TYPE_EPARGNE, TYPE_DEPOT, TYPE_RETRAIT, TYPE_VIREMENT,
)
from app.services.exceptions import (
    CINDupliqueError, ClientAComptesError, ClientIntrouvableError,
    ClientSuspenduError, CompteClotureError, CompteIntrouvableError,
    CompteNonVideError, EntreeInvalideError, SoldeInsuffisantError,
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


class BankService:
    """Métier bancaire : clients, comptes, opérations, dashboard."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._clients = ClientDAO(db)
        self._comptes = CompteDAO(db)
        self._operations = OperationDAO(db)

    # ================================================================== #
    #  CLIENTS                                                           #
    # ================================================================== #
    def ajouter_client(self, nom: str, prenom: str, cin: str,
                       telephone: str | None = None,
                       email: str | None = None,
                       statut: str | None = None) -> Client:
        """R1 : champs requis, CIN unique -> crée le client."""
        self._verifier_etat_civil(nom, prenom, cin, email)
        if self._clients.read_by_cin(cin.strip()) is not None:
            raise CINDupliqueError(
                f"Le CIN {cin.strip()!r} appartient déjà à un autre client.")
        statut_effectif = statut if statut in STATUTS_CLIENT else STATUT_CLIENT_ACTIF
        client = Client(nom=nom, prenom=prenom, cin=cin,
                        telephone=telephone, email=email,
                        statut=statut_effectif)
        client.normaliser()
        self._clients.create(client)
        return client

    def modifier_client(self, id_client: int, nom: str, prenom: str, cin: str,
                        telephone: str | None = None,
                        email: str | None = None,
                        statut: str | None = None) -> Client:
        """R1 : mêmes contrôles, sans heurter le CIN du client lui-même."""
        self._verifier_etat_civil(nom, prenom, cin, email)
        doublon = self._clients.read_by_cin(cin.strip())
        if doublon is not None and doublon.id_client != id_client:
            raise CINDupliqueError(
                f"Le CIN {cin.strip()!r} appartient déjà à un autre client.")
        if statut is None or statut not in STATUTS_CLIENT:
            statut = self.obtenir_client(id_client).statut
        client = Client(id_client=id_client, nom=nom, prenom=prenom, cin=cin,
                        telephone=telephone, email=email, statut=statut)
        client.normaliser()
        self._clients.update(client)
        return client

    def supprimer_client(self, id_client: int) -> None:
        """R5 : refus si le client possède encore des comptes ( même
        clôturés) : aucun historique ne doit perdre son titulaire."""
        client = self.obtenir_client(id_client)
        if self._comptes.read_by_client(client.id_client):
            raise ClientAComptesError(
                f"Suppression impossible : {client.nom_complet} possède "
                "encore des comptes. Clôturez et supprimez-les d'abord.")
        self._clients.delete(client.id_client)

    def changer_statut_client(self, id_client: int, statut: str) -> Client:
        """R4a : suspend / réactive un client (domaine CONTRÔLÉ)."""
        client = self.obtenir_client(id_client)
        if statut not in STATUTS_CLIENT:
            raise EntreeInvalideError(
                f"Statut inconnu : {statut!r} (attendu ACTIF ou SUSPENDU).")
        client.statut = statut
        self._clients.update(client)
        return client

    # -- lecture -------------------------------------------------------
    def read_clients(self) -> list[Client]:
        return self._clients.read_all()

    def obtenir_client(self, id_client: int) -> Client:
        client = self._clients.read_by_id(id_client)
        if client is None:
            raise ClientIntrouvableError(
                f"Aucun client #{id_client} dans la base.")
        return client

    # ================================================================== #
    #  COMPTES                                                           #
    # ================================================================== #
    def ouvrir_compte(self, id_client: int,
                      type_compte: str = TYPE_COURANT,
                      solde_initial: float = 0.0) -> Compte:
        """R4b (client actif) + type contrôlé -> numéro généré par DAO."""
        client = self.obtenir_client(id_client)
        if client.statut == STATUT_CLIENT_SUSPENDU:
            raise ClientSuspenduError(
                f"Ouverture refusée : {client.nom_complet} est SUSPENDU.")
        if type_compte not in (TYPE_COURANT, TYPE_EPARGNE):
            raise EntreeInvalideError(
                f"Type de compte inconnu : {type_compte!r}.")
        solde = float(solde_initial or 0.0)
        if solde < 0:
            raise EntreeInvalideError("Le solde initial doit être positif ou nul.")
        compte = Compte(id_client=client.id_client, type=type_compte, solde=solde)
        self._comptes.create(compte)   # attribue numero CPT-000x
        return compte

    def cloturer_compte(self, id_compte: int) -> Compte:
        """Clôture : OBLIGATOIREMENT à solde nul (règle de non-perte)."""
        compte = self.obtenir_compte(id_compte)
        if compte.statut == STATUT_COMPTE_CLOTURE:
            raise CompteClotureError(
                f"Le compte {compte.numero} est déjà clôturé.")
        if compte.solde != 0:
            raise CompteNonVideError(
                f"Clôture refusée : {compte.numero} contient "
                f"{compte.solde:.2f}. Videz le solde d'abord (retrait/virement).")
        compte.statut = STATUT_COMPTE_CLOTURE
        self._comptes.update(compte)
        return compte

    # -- lecture -------------------------------------------------------
    def read_comptes(self) -> list[Compte]:
        return self._comptes.read_all()

    def read_comptes_par_client(self, id_client: int) -> list[Compte]:
        return self._comptes.read_by_client(id_client)

    def obtenir_compte(self, id_compte: int) -> Compte:
        compte = self._comptes.read_by_id(id_compte)
        if compte is None:
            raise CompteIntrouvableError(
                f"Aucun compte #{id_compte} dans la base.")
        return compte

    # ================================================================== #
    #  OPÉRATIONS (le cœur transactionnel)                               #
    # ================================================================== #
    def depot(self, id_compte: int, montant: float,
              commentaire: str | None = None) -> Operation:
        """R2 + R3 + R4c : alimente le solde et historise, ENSEMBLE."""
        montant = self._verifier_montant(montant)
        with self._db.transaction():
            compte = self._compte_operable(id_compte)
            self._comptes.update_solde(compte.id_compte,
                                       compte.solde + montant)
            operation = Operation(
                id_compte=compte.id_compte, type=TYPE_DEPOT,
                montant=montant, commentaire=commentaire)
            self._operations.create(operation)
        return operation

    def retrait(self, id_compte: int, montant: float,
                commentaire: str | None = None) -> Operation:
        """R2 : refuse si insufficient ; rien n'est écrit en cas d'échec."""
        montant = self._verifier_montant(montant)
        with self._db.transaction():
            compte = self._compte_operable(id_compte)
            if compte.solde < montant:
                raise SoldeInsuffisantError(
                    f"Retrait refusé sur {compte.numero} : solde "
                    f"{compte.solde:.2f} < demande {montant:.2f}.")
            self._comptes.update_solde(compte.id_compte,
                                       compte.solde - montant)
            operation = Operation(
                id_compte=compte.id_compte, type=TYPE_RETRAIT,
                montant=montant, commentaire=commentaire)
            self._operations.create(operation)
        return operation

    def virement(self, id_source: int, id_cible: int, montant: float,
                 commentaire: str | None = None) -> list[Operation]:
        """**Écriture double atomique.**

        Dans UNE SEULE transaction :
          * contrôle des 2 comptes (activité, solde, distincts) ;
          * débit source / crédit cible ;
          * 2 lignes ``VIREMENT`` partageant le même ``id_virement``.
        Si QUOI que ce soit échoue -> ROLLBACK intégral : le couple
        (soldes, écritures) reste toujours cohérent.
        """
        montant = self._verifier_montant(montant)
        if id_source == id_cible:
            raise EntreeInvalideError(
                "Un virement requiert DEUX comptes distincts.")
        with self._db.transaction():
            source = self._compte_operable(id_source)
            cible = self._compte_operable(id_cible)
            if source.solde < montant:
                raise SoldeInsuffisantError(
                    f"Virement refusé : {source.numero} dispose de "
                    f"{source.solde:.2f}, demande {montant:.2f}.")
            ref = str(uuid.uuid4())
            self._comptes.update_solde(source.id_compte, source.solde - montant)
            self._comptes.update_solde(cible.id_compte, cible.solde + montant)
            texte = commentaire or f"Virement {source.numero} -> {cible.numero}"
            couple = (
                Operation(id_compte=source.id_compte,
                          id_contrepartie=cible.id_compte,
                          type=TYPE_VIREMENT, montant=montant,
                          id_virement=ref, commentaire=texte),
                Operation(id_compte=cible.id_compte,
                          id_contrepartie=source.id_compte,
                          type=TYPE_VIREMENT, montant=montant,
                          id_virement=ref, commentaire=texte),
            )
            legs = []
            for jambe in couple:
                self._operations.create(jambe)
                legs.append(jambe)
        return legs

    # -- lecture -------------------------------------------------------
    def releve(self, id_compte: int) -> list[Operation]:
        """Relevé d'un compte : du plus récent au plus ancien."""
        compte = self.obtenir_compte(id_compte)
        return self._operations.history(compte.id_compte)

    def jambes_virement(self, id_virement: str) -> list[Operation]:
        if not id_virement:
            raise EntreeInvalideError("Référence de virement absente.")
        return self._operations.legs_of_virement(id_virement)

    # ================================================================== #
    #  TABLEAU DE BORD                                                   #
    # ================================================================== #
    def operations_recentes(self, limite: int = 10) -> list[dict]:
        """Derniers mouvements tous comptes (lignes « riches »)."""
        return self._operations.derniers_mouvements(limite)

    def statistiques(self) -> dict:
        """Agrégats du SI : population, encours, activité."""
        nb_operations = self._operations.count()
        volume = self._operations.volume_total()
        comptes = self.read_comptes()
        return {
            "nb_clients": len(self.read_clients()),
            "nb_comptes": len(comptes),
            "nb_comptes_actifs": sum(
                1 for c in comptes if c.statut == STATUT_COMPTE_ACTIF),
            "encours_total": sum(c.solde for c in comptes),
            "nb_operations": nb_operations,
            "volume_operations": volume,
        }

    # ================================================================== #
    #  Aides internes (règles réutilisables)                             #
    # ================================================================== #
    def _verifier_etat_civil(self, nom: str, prenom: str, cin: str,
                             email: str | None) -> None:
        """R1 : champs requis + email grossièrement bien formé."""
        if not nom.strip():
            raise EntreeInvalideError("Le nom est obligatoire.")
        if not prenom.strip():
            raise EntreeInvalideError("Le prénom est obligatoire.")
        if not cin.strip():
            raise EntreeInvalideError("Le CIN est obligatoire.")
        if email is not None and email.strip() and not _EMAIL_RE.match(email.strip()):
            raise EntreeInvalideError(f"Email malformé : {email!r}.")

    @staticmethod
    def _verifier_montant(montant: float) -> float:
        """R : montant > 0 (à l'exclusion implicite du NaN/inf)."""
        try:
            valeur = float(montant)
        except (TypeError, ValueError):
            raise EntreeInvalideError("Montant non numérique.") from None
        if valeur <= 0:
            raise EntreeInvalideError("Le montant doit être STRICTEMENT positif.")
        return valeur

    def _compte_operable(self, id_compte: int) -> Compte:
        """R3 + R4c + CompteIntrouvable : « un compte doit pouvoir opérer »."""
        compte = self.obtenir_compte(id_compte)
        if compte.statut == STATUT_COMPTE_CLOTURE:
            raise CompteClotureError(
                f"Compte {compte.numero} clôturé : opération refusée.")
        client = self.obtenir_client(compte.id_client)
        if client.statut == STATUT_CLIENT_SUSPENDU:
            raise ClientSuspenduError(
                f"Client {client.nom_complet} SUSPENDU : opérations "
                f"bloquées sur {compte.numero}.")
        return compte
