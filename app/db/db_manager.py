"""Gestionnaire de base SQLite (Rôle 1 — données & persistance).

Responsabilités :
  * ouverture paresseuse d'une unique connexion (application bureau) ;
  * création du schéma depuis ``schema.sql`` ;
  * transactions IMBRICABLES via le gestionnaire de contexte
    ``transaction()`` : le premier niveau fait le COMMIT (ou ROLLBACK
    complet en cas d'exception), les niveaux imbriqués rejoignent la
    transaction SQL en cours. C'est ce qui permet au service de grouper
    PLUSIEURS appels DAO dans UNE transaction atomique (ex. : virement).
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3

CHEMIN_SCHEMA = Path(__file__).resolve().parent / "schema.sql"


class DatabaseManager:
    """Point d'entrée unique vers la base SQLite."""

    def __init__(self, chemin_base: str | Path = "banque.db") -> None:
        self.chemin_base = Path(chemin_base)
        self._connexion: sqlite3.Connection | None = None
        self._profondeur_transaction = 0

    # ------------------------------------------------------------------ #
    # Connexion / transactions                                           #
    # ------------------------------------------------------------------ #
    def connexion(self) -> sqlite3.Connection:
        """Connexion (créée à la première demande), lignes de type dict."""
        if self._connexion is None:
            self._connexion = sqlite3.connect(self.chemin_base)
            self._connexion.row_factory = sqlite3.Row
            # SQLite ignore les clés étrangères par défaut : indispensable.
            self._connexion.execute("PRAGMA foreign_keys = ON;")
        return self._connexion

    @contextmanager
    def transaction(self):
        """Contexte transactionnel : ``with db.transaction():``.

        * niveau 1 : COMMIT à la sortie, ROLLBACK si exception ;
        * niveaux > 1 : rejoint la transaction ouverte (pas de commit
          intermédiaire) -> une erreur récente annule TOUT.
        """
        conn = self.connexion()
        self._profondeur_transaction += 1
        try:
            yield conn
            if self._profondeur_transaction == 1:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._profondeur_transaction -= 1

    # ------------------------------------------------------------------ #
    # Schéma / jeu de démonstration                                      #
    # ------------------------------------------------------------------ #
    def init_schema(self) -> None:
        """Applique le DDL de ``schema.sql`` (idempotent : IF NOT EXISTS)."""
        self.connexion().executescript(
            CHEMIN_SCHEMA.read_text(encoding="utf-8"))

    def seed_demo_data(self) -> None:
        """Peuple la base (3 clients / 4 comptes / ~9 opérations) si vide."""
        effectif = self.connexion().execute("SELECT COUNT(*) FROM client").fetchone()[0]
        if effectif:
            return
        from app.db import seed  # import local : évite l'import circulaire
        seed.peupler(self)

    def close(self) -> None:
        if self._connexion is not None:
            self._connexion.close()
            self._connexion = None
