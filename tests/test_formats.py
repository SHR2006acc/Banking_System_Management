"""Tests des helpers de formatage (couche interface, Rôle 3).

Ces helpers décident de TOUT affichage de montant et de TOUTE relecture
de saisie numérique : les tester, c'est verrouiller l'expérience des
5 écrans. Aucun affichage graphique requis (pas besoin de display).
"""
from __future__ import annotations

import unittest

from app.services.exceptions import EntreeInvalideError
from app.ui.format import (
    extraire_montant, fmt_date, fmt_entier, fmt_montant,
)


class TestAffichage(unittest.TestCase):
    """fmt_montant / fmt_entier / fmt_date."""

    def test_montant_millier(self):
        self.assertEqual(fmt_montant(1500.0), "1 500,00 €")

    def test_montant_millions_sans_limite(self):
        self.assertEqual(fmt_montant(1_234_567.89), "1 234 567,89 €")

    def test_montant_milliard(self):
        self.assertEqual(fmt_montant(9_876_543_210.5), "9 876 543 210,50 €")

    def test_montant_zero_ou_none(self):
        self.assertEqual(fmt_montant(0), "0,00 €")
        self.assertEqual(fmt_montant(None), "0,00 €")

    def test_entier(self):
        self.assertEqual(fmt_entier(1_234_567), "1 234 567")

    def test_date_complete(self):
        self.assertEqual(fmt_date("2026-10-18 14:32:05"), "18/10/2026 14:32")

    def test_date_absente_ou_inconnue(self):
        self.assertEqual(fmt_date(None), "—")
        self.assertEqual(fmt_date(""), "—")
        self.assertEqual(fmt_date("bizarre"), "bizarre")


class TestSaisie(unittest.TestCase):
    """extraire_montant : grammaire de relecture."""

    def test_francais_standard(self):
        self.assertEqual(extraire_montant("1 250,50"), 1250.50)

    def test_espaces_de_toute_sorte(self):
        self.assertEqual(extraire_montant("1\u202f250,50"), 1250.50)
        self.assertEqual(extraire_montant(" 1 250,50 "), 1250.50)

    def test_suffixe_devise(self):
        self.assertEqual(extraire_montant("1 234 €"), 1234.0)

    def test_sans_separateur(self):
        self.assertEqual(extraire_montant("1000000"), 1_000_000.0)

    def test_point_decimal(self):
        self.assertEqual(extraire_montant("1250.5"), 1250.5)
        self.assertEqual(extraire_montant("0.5"), 0.5)

    def test_point_milliers(self):
        self.assertEqual(extraire_montant("1.000"), 1000.0)
        self.assertEqual(extraire_montant("12.500"), 12_500.0)

    def test_zero_point_trois_chiffres_reste_decimal(self):
        # « 0.500 » signifie 0,5 — le zéro de tête tranche.
        self.assertEqual(extraire_montant("0.500"), 0.5)

    def test_points_multiples_milliers(self):
        self.assertEqual(extraire_montant("1.000.000"), 1_000_000.0)

    def test_les_deux_separateurs(self):
        self.assertEqual(extraire_montant("1.000.000,50"), 1_000_000.50)
        self.assertEqual(extraire_montant("1,000,000.50"), 1_000_000.50)

    def test_virgule_seule_decimale(self):
        self.assertEqual(extraire_montant("0,5"), 0.5)

    def test_zero_refuse_par_defaut(self):
        with self.assertRaises(EntreeInvalideError):
            extraire_montant("0")
        with self.assertRaises(EntreeInvalideError):
            extraire_montant("0,00")

    def test_zero_autorise_pour_solde_initial(self):
        # Ouvrir un compte : le solde initial PEUT être nul.
        self.assertEqual(extraire_montant("0", zero_autorise=True), 0.0)
        self.assertEqual(extraire_montant("0,00", zero_autorise=True), 0.0)

    def test_refus_saisies_invalides(self):
        for mauvais in ("", "   ", "abc", "-5", "0", "12,34,56",
                        "1.23.45", "1e3", "+,5", "€"):
            with self.subTest(saisie=mauvais):
                with self.assertRaises(EntreeInvalideError):
                    extraire_montant(mauvais)

    def test_message_du_refus_en_francais(self):
        try:
            extraire_montant("abc")
        except EntreeInvalideError as erreur:
            self.assertIn("Montant invalide", str(erreur))
            self.assertIn("1 250,50", str(erreur))
        else:
            self.fail("EntreeInvalideError attendue")


if __name__ == "__main__":
    unittest.main()
