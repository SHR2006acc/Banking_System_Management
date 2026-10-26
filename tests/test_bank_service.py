"""Tests unitaires Rôle 2 — règles métier du BankService.

Scénarios clés : validation des entrées, unicité du CIN, ordre de
clôture, client suspendu, insuffisance de solde, délétions bloquées
et — surtout — l'ATOMICITÉ du virement (2 jambes / 1 transaction).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.conftest import creer_base_ephemere, detruire_base

from app.services.bank_service import BankService
from app.services.exceptions import (
    CINDupliqueError, ClientAComptesError, ClientIntrouvableError,
    ClientSuspenduError, CompteClotureError, CompteIntrouvableError,
    CompteNonVideError, EntreeInvalideError, SoldeInsuffisantError,
)
from app.models.models import STATUT_CLIENT_SUSPENDU


class BanqueBase(unittest.TestCase):
    """Banc d'essai : base éphémère + service neuf par test."""

    def setUp(self) -> None:
        self.db = creer_base_ephemere()
        self.svc = BankService(self.db)

    def tearDown(self) -> None:
        detruire_base(self.db)

    # -- aides ------------------------------------------------------------
    def _client(self, cin: str = "AB111111"):
        return self.svc.ajouter_client("Test", "Jan", cin)

    def _compte(self, solde: float = 0.0, cin: str = "AB111111"):
        client = self._client(cin=cin)
        return self.svc.ouvrir_compte(client.id_client, solde_initial=solde)


class TestClients(BanqueBase):
    def test_lecture_cree_objets_complets(self) -> None:
        self.svc.ajouter_client("Dupont", "Alice", "AB123456",
                                telephone="0601020304", email="a@ex.fr")
        relue = self.svc.read_clients()[0]
        self.assertEqual(relue.nom_complet, "Dupont Alice")
        self.assertEqual(relue.email, "a@ex.fr")

    def test_cin_doublon_refuse(self) -> None:
        self.svc.ajouter_client("Bernard", "Karim", "CD54321")
        with self.assertRaises(CINDupliqueError):
            self.svc.ajouter_client("Bernard", "Karine", "CD54321")

    def test_champ_manquant_refuse(self) -> None:
        with self.assertRaises(EntreeInvalideError):
            self.svc.ajouter_client("   ", "Alice", "AB99999")
        with self.assertRaises(EntreeInvalideError):
            self.svc.ajouter_client("Nom", "Prenom", "  ")

    def test_email_invalide_refuse(self) -> None:
        with self.assertRaises(EntreeInvalideError):
            self.svc.ajouter_client("Bern", "Karim", "EF67890",
                                    email="pas-un-email")

    def test_email_valide_accepte(self) -> None:
        client = self.svc.ajouter_client("Ok", "Mail", "GH00001",
                                         email="ok.mail@domain.fr")
        self.assertEqual(client.email, "ok.mail@domain.fr")

    def test_client_inconnu(self) -> None:
        with self.assertRaises(ClientIntrouvableError):
            self.svc.obtenir_client(999)

    def test_suppression_bloquee_si_comptes(self) -> None:
        client = self._client()
        self.svc.ouvrir_compte(client.id_client)
        with self.assertRaises(ClientAComptesError):
            self.svc.supprimer_client(client.id_client)
        # le client a été conservé
        self.assertEqual(self.svc.read_clients()[0].id_client,
                         client.id_client)

    def test_suppression_possible_si_sans_compte(self) -> None:
        client = self._client("ZZ00001")
        self.svc.supprimer_client(client.id_client)
        self.assertEqual(self.svc.read_clients(), [])

    def test_statut_suspendu_par_le_service(self) -> None:
        client = self._client()
        suspendu = self.svc.changer_statut_client(
            client.id_client, STATUT_CLIENT_SUSPENDU)
        self.assertEqual(suspendu.statut, STATUT_CLIENT_SUSPENDU)


class TestComptes(BanqueBase):
    def test_ouverture_numero_sequence(self) -> None:
        c1 = self._compte()
        c2 = self._compte(cin="BB00002")
        self.assertEqual(c1.numero, "CPT-0001")
        self.assertEqual(c2.numero, "CPT-0002")

    def test_ouverture_client_inconnu(self) -> None:
        with self.assertRaises(ClientIntrouvableError):
            self.svc.ouvrir_compte(123)

    def test_ouverture_client_suspendu_refusee(self) -> None:
        client = self._client()
        self.svc.changer_statut_client(client.id_client, STATUT_CLIENT_SUSPENDU)
        with self.assertRaises(ClientSuspenduError):
            self.svc.ouvrir_compte(client.id_client)

    def test_solde_initial_negatif_refuse(self) -> None:
        with self.assertRaises(EntreeInvalideError):
            self.svc.ouvrir_compte(self._client().id_client, solde_initial=-5)

    def test_cloture_refusee_si_solde_non_nul(self) -> None:
        compte = self._compte(solde=100.0)
        with self.assertRaises(CompteNonVideError):
            self.svc.cloturer_compte(compte.id_compte)
        # le compte reste actif
        self.assertEqual(self.svc.obtenir_compte(compte.id_compte).statut,
                         "ACTIF")

    def test_cloture_possible_si_solde_nul(self) -> None:
        compte = self._compte()
        compte_ferme = self.svc.cloturer_compte(compte.id_compte)
        self.assertEqual(compte_ferme.statut, "CLOTURE")
        # ensuite : plus AUCUNE opération
        with self.assertRaises(CompteClotureError):
            self.svc.depot(compte.id_compte, 50.0)

    def test_double_cloture_refusee(self) -> None:
        compte = self._compte()
        self.svc.cloturer_compte(compte.id_compte)
        with self.assertRaises(CompteClotureError):
            self.svc.cloturer_compte(compte.id_compte)

    def test_compte_inconnu(self) -> None:
        with self.assertRaises(CompteIntrouvableError):
            self.svc.obtenir_compte(987)


class TestOperations(BanqueBase):
    def test_depot_solde_et_historique(self) -> None:
        compte = self._compte()
        self.svc.depot(compte.id_compte, 250.5)
        self.assertEqual(
            self.svc.obtenir_compte(compte.id_compte).solde, 250.5)
        historique = self.svc.releve(compte.id_compte)
        self.assertEqual(len(historique), 1)
        self.assertEqual(historique[0].type, "DEPOT")

    def test_retrait_ok(self) -> None:
        compte = self._compte(solde=100.0)
        self.svc.retrait(compte.id_compte, 40.0)
        self.assertEqual(
            self.svc.obtenir_compte(compte.id_compte).solde, 60.0)

    def test_solde_insuffisant_et_rien_n_ecrit(self) -> None:
        compte = self._compte(solde=100.0)
        with self.assertRaises(SoldeInsuffisantError):
            self.svc.retrait(compte.id_compte, 100.01)
        self.assertEqual(
            self.svc.obtenir_compte(compte.id_compte).solde, 100.0)
        self.assertEqual(self.svc.releve(compte.id_compte), [])

    def test_montants_invalides(self) -> None:
        compte = self._compte()
        for montant in (0, -10, "abc"):
            with self.assertRaises(EntreeInvalideError):
                self.svc.depot(compte.id_compte, montant)
        self.assertEqual(
            self.svc.obtenir_compte(compte.id_compte).solde, 0.0)

    def test_client_suspendu_bloque_operations(self) -> None:
        compte = self._compte()
        self.svc.changer_statut_client(
            compte.id_client, STATUT_CLIENT_SUSPENDU)
        with self.assertRaises(ClientSuspenduError):
            self.svc.depot(compte.id_compte, 10.0)

    def test_statistiques(self) -> None:
        self._compte(solde=100.0)
        stats = self.svc.statistiques()
        self.assertEqual(stats["nb_clients"], 1)
        self.assertEqual(stats["nb_comptes"], 1)
        self.assertEqual(stats["nb_comptes_actifs"], 1)
        self.assertEqual(stats["encours_total"], 100.0)


class TestVirement(BanqueBase):
    def test_virement_double_ecriture(self) -> None:
        source = self._compte(solde=500.0)
        cible = self._compte(cin="BB22222")
        jambes = self.svc.virement(source.id_compte, cible.id_compte, 150.0)
        # deux lignes, un seul identifiant de virement
        self.assertEqual(len(jambes), 2)
        refs = {j.id_virement for j in jambes}
        self.assertEqual(len(refs), 1)
        # soldes : 500-150 ; 0+150
        self.assertEqual(
            self.svc.obtenir_compte(source.id_compte).solde, 350.0)
        self.assertEqual(
            self.svc.obtenir_compte(cible.id_compte).solde, 150.0)
        # contreparties croisées
        debitee, creditee = jambes
        self.assertEqual(debitee.id_contrepartie, cible.id_compte)
        self.assertEqual(creditee.id_contrepartie, source.id_compte)

    def test_meme_compte_refuse(self) -> None:
        compte = self._compte(solde=100.0)
        with self.assertRaises(EntreeInvalideError):
            self.svc.virement(compte.id_compte, compte.id_compte, 10.0)

    def test_solde_insuffisant_tout_annule(self) -> None:
        source = self._compte(solde=500.0)
        cible = self._compte(cin="BB33333")
        with self.assertRaises(SoldeInsuffisantError):
            self.svc.virement(source.id_compte, cible.id_compte, 500.01)
        # RIEN n'a bougé : aucun débit, aucun crédit, aucune écriture
        self.assertEqual(
            self.svc.obtenir_compte(source.id_compte).solde, 500.0)
        self.assertEqual(
            self.svc.obtenir_compte(cible.id_compte).solde, 0.0)
        self.assertEqual(len(self.svc.releve(source.id_compte)), 0)
        self.assertEqual(len(self.svc.releve(cible.id_compte)), 0)

    def test_cible_cloturee_annule_tout(self) -> None:
        source = self._compte(solde=500.0)
        cible = self._compte(cin="BB44444")
        self.svc.cloturer_compte(cible.id_compte)
        with self.assertRaises(CompteClotureError):
            self.svc.virement(source.id_compte, cible.id_compte, 100.0)
        self.assertEqual(
            self.svc.obtenir_compte(source.id_compte).solde, 500.0)
        self.assertEqual(len(self.svc.releve(source.id_compte)), 0)

    def test_atomicite_une_jambe_fait_echouer_le_tout(self) -> None:
        """Simule une panne SQL au moment du CREDIT cible : le débit,
        déjà appliqué, doit être annulé par le ROLLBACK de la transaction."""
        source = self._compte(solde=500.0)
        cible = self._compte(cin="BB55555")

        original = self.svc._comptes.update_solde
        appels = []

        def mauvais_update_solde(id_compte, solde):
            appels.append(id_compte)
            if len(appels) == 2:      # 1er appel = débit source (réussi)…
                raise RuntimeError("panne simulée")  # …2e échoue
            return original(id_compte, solde)

        self.svc._comptes.update_solde = mauvais_update_solde
        with self.assertRaises(RuntimeError):
            self.svc.virement(source.id_compte, cible.id_compte, 100.0)

        # état cohérent : aucun solde n'a bougé, aucune écriture
        self.assertEqual(appels, [source.id_compte, cible.id_compte])
        self.assertEqual(
            self.svc.obtenir_compte(source.id_compte).solde, 500.0)
        self.assertEqual(
            self.svc.obtenir_compte(cible.id_compte).solde, 0.0)
        total = self.db.connexion().execute(
            "SELECT COUNT(*) FROM operation").fetchone()[0]
        self.assertEqual(total, 0)

    def test_jambes_lues_via_service(self) -> None:
        source = self._compte(solde=300.0)
        cible = self._compte(cin="BB66666")
        jambes = self.svc.virement(source.id_compte, cible.id_compte, 75.0)
        lues = self.svc.jambes_virement(jambes[0].id_virement)
        self.assertEqual(len(lues), 2)


if __name__ == "__main__":
    unittest.main()
