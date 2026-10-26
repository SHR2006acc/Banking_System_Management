"""Tests unitaires Rôle 1 — persistance : CRUD des DAO + contraintes SQL.

Exécuter depuis le dossier « bank system » :
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.conftest import creer_base_ephemere, detruire_base

from app.dao.client_dao import ClientDAO
from app.dao.compte_dao import CompteDAO
from app.dao.operation_dao import OperationDAO
from app.models.models import Client, Compte, Operation, TYPE_VIREMENT


class TestClientDAO(unittest.TestCase):
    def setUp(self) -> None:
        self.db = creer_base_ephemere()
        self.dao = ClientDAO(self.db)

    def tearDown(self) -> None:
        detruire_base(self.db)

    def _client(self, cin: str = "AA111111", nom: str = "Test") -> Client:
        return Client(nom=nom, prenom="Jan", cin=cin)

    def test_create_read_by_id(self) -> None:
        client = self._client()
        identifiant = self.dao.create(client)
        self.assertEqual(client.id_client, identifiant)
        relu = self.dao.read_by_id(identifiant)
        self.assertEqual(relu.cin, "AA111111")
        self.assertEqual(relu.nom, "Test")
        self.assertEqual(relu.statut, "ACTIF")      # défaut SQL

    def test_read_all_trie_par_nom(self) -> None:
        self.dao.create(self._client(cin="C1", nom="Zoe"))
        self.dao.create(self._client(cin="C2", nom="Adam"))
        self.assertEqual([c.nom for c in self.dao.read_all()],
                         ["Adam", "Zoe"])

    def test_read_by_cin(self) -> None:
        cree = self.dao.create(self._client(cin="CIN77"))
        self.assertEqual(self.dao.read_by_cin("CIN77").id_client, cree)
        self.assertIsNone(self.dao.read_by_cin("INCONNU"))

    def test_update(self) -> None:
        client = self._client()
        self.dao.create(client)
        client.prenom = "Jane"
        client.email = "jane@test.fr"
        self.assertTrue(self.dao.update(client))
        self.assertEqual(self.dao.read_by_id(client.id_client).prenom, "Jane")

    def test_delete(self) -> None:
        client = self._client()
        self.dao.create(client)
        self.assertTrue(self.dao.delete(client.id_client))
        self.assertIsNone(self.dao.read_by_id(client.id_client))
        self.assertFalse(self.dao.delete(999))

    def test_cin_unique_contrainte(self) -> None:
        self.dao.create(self._client(cin="M777"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.dao.create(self._client(cin="M777", nom="Autre"))


class TestCompteDAO(unittest.TestCase):
    def setUp(self) -> None:
        self.db = creer_base_ephemere()
        self.dao = CompteDAO(self.db)
        self.id_client = ClientDAO(self.db).create(
            Client(nom="Test", prenom="Jan", cin="F99999"))

    def tearDown(self) -> None:
        detruire_base(self.db)

    def test_create_genere_numero(self) -> None:
        compte = Compte(id_client=self.id_client)
        self.dao.create(compte)
        self.assertEqual(compte.numero, "CPT-0001")
        autre = Compte(id_client=self.id_client)
        self.dao.create(autre)
        self.assertEqual(autre.numero, "CPT-0002")

    def test_read_by_client(self) -> None:
        self.dao.create(Compte(id_client=self.id_client))
        self.dao.create(Compte(id_client=self.id_client,
                               type="EPARGNE"))
        # quelques comptes d'un autre client
        autre_client = ClientDAO(self.db).create(
            Client(nom="Second", prenom="P", cin="Z99999"))
        self.dao.create(Compte(id_client=autre_client))
        comptes_test = self.dao.read_by_client(self.id_client)
        self.assertEqual(len(comptes_test), 2)
        self.assertEqual([c.numero for c in comptes_test],
                         ["CPT-0001", "CPT-0002"])

    def test_update_solde(self) -> None:
        compte = Compte(id_client=self.id_client)
        self.dao.create(compte)
        self.assertTrue(self.dao.update_solde(compte.id_compte, 150.25))
        self.assertEqual(self.dao.read_by_id(compte.id_compte).solde, 150.25)

    def test_solde_negatif_interdit(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.dao.create(
                Compte(id_client=self.id_client, solde=-1.0))

    def test_fk_client_requis(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.dao.create(Compte(id_client=999))


class TestOperationDAO(unittest.TestCase):
    def setUp(self) -> None:
        self.db = creer_base_ephemere()
        self.cdao = ClientDAO(self.db)
        self.dao = OperationDAO(self.db)
        self.id_client = self.cdao.create(
            Client(nom="Test", prenom="Jan", cin="H11111"))
        self.comptes_dao = CompteDAO(self.db)
        self.compte_a = self.comptes_dao.create(
            Compte(id_client=self.id_client))
        self.compte_b = self.comptes_dao.create(
            Compte(id_client=self.id_client))

    def tearDown(self) -> None:
        detruire_base(self.db)

    def test_create_histo(self) -> None:
        self.dao.create(Operation(
            id_compte=self.compte_a, type="DEPOT", montant=100.0))
        self.assertEqual(len(self.dao.history(self.compte_a)), 1)
        self.assertEqual(self.dao.history(self.compte_b), [])

    def test_history_ordre_desc(self) -> None:
        premier = self.dao.create(Operation(
            id_compte=self.compte_a, type="DEPOT", montant=10.0))
        second = self.dao.create(Operation(
            id_compte=self.compte_a, type="DEPOT", montant=20.0))
        historique = self.dao.history(self.compte_a)
        # id_operation DESC (dates identiques à la seconde près)
        self.assertEqual(historique[0].id_operation, second)
        self.assertIn(premier, [o.id_operation for o in historique])

    def test_jambes_virement(self) -> None:
        ref = "abcd1234"
        leg_1 = self.dao.create(Operation(
            id_compte=self.compte_a, id_contrepartie=self.compte_b,
            type=TYPE_VIREMENT, montant=50.0, id_virement=ref))
        leg_2 = self.dao.create(Operation(
            id_compte=self.compte_b, id_contrepartie=self.compte_a,
            type=TYPE_VIREMENT, montant=50.0, id_virement=ref))
        jambes = self.dao.legs_of_virement(ref)
        self.assertEqual(len(jambes), 2)
        self.assertEqual(jambes[0].id_operation, leg_1)  # débit d'abord
        self.assertEqual(jambes[1].id_operation, leg_2)

    def test_count_et_volume(self) -> None:
        self.dao.create(Operation(
            id_compte=self.compte_a, type="DEPOT", montant=100.0))
        self.dao.create(Operation(
            id_compte=self.compte_a, type="RETRAIT", montant=30.0))
        self.assertEqual(self.dao.count(), 2)
        self.assertEqual(self.dao.volume_total(), 130.0)

    def test_derniers_mouvements_joignable(self) -> None:
        self.dao.create(Operation(
            id_compte=self.compte_a, type="DEPOT", montant=10.0))
        lignes = self.dao.derniers_mouvements(5)
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0]["numero_compte"], "CPT-0001")
        self.assertIsNone(lignes[0]["numero_contrepartie"])


if __name__ == "__main__":
    unittest.main()
