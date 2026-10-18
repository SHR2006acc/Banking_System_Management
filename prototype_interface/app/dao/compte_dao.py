"""DAO « compte » : accès paramétré à la table compte (Rôle 1).

Génère les numéros fonctionnels ``CPT-000x`` à l'intérieur de la
transaction d'insertion (pas de numéro attribué hors transaction).
"""
from __future__ import annotations

import sqlite3

from app.db.db_manager import DatabaseManager
from app.models.models import (
    STATUT_COMPTE_ACTIF, TYPE_COURANT, Compte,
)

_COLONNES = "id_compte, id_client, numero, type, solde, statut, date_ouverture"


def _vers_compte(ligne: sqlite3.Row) -> Compte:
    """Ligne SQL -> dataclass Compte."""
    return Compte(
        id_compte=ligne["id_compte"],
        id_client=ligne["id_client"],
        numero=ligne["numero"],
        type=ligne["type"],
        solde=float(ligne["solde"]),
        statut=ligne["statut"],
        date_ouverture=ligne["date_ouverture"],
    )


class CompteDAO:
    """CRUD complet sur ``compte`` — requêtes 100% paramétrées."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Lecture                                                            #
    # ------------------------------------------------------------------ #
    def read_all(self) -> list[Compte]:
        cur = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM compte ORDER BY numero"
        )
        return [_vers_compte(l) for l in cur.fetchall()]

    def read_by_id(self, id_compte: int) -> Compte | None:
        ligne = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM compte WHERE id_compte = ?", (id_compte,)
        ).fetchone()
        return _vers_compte(ligne) if ligne else None

    def read_by_numero(self, numero: str) -> Compte | None:
        ligne = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM compte WHERE numero = ?", (numero,)
        ).fetchone()
        return _vers_compte(ligne) if ligne else None

    def read_by_client(self, id_client: int) -> list[Compte]:
        cur = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM compte WHERE id_client = ? ORDER BY numero",
            (id_client,),
        )
        return [_vers_compte(l) for l in cur.fetchall()]

    def prochain_numero(self) -> str:
        """Numéro suivant (CPT-0001…) — à appeler DANS la transaction."""
        ligne = self._db.connexion().execute(
            "SELECT COALESCE(MAX(id_compte), 0) + 1 FROM compte"
        ).fetchone()
        return f"CPT-{ligne[0]:04d}"

    def nb_par_client(self, id_client: int) -> int:
        ligne = self._db.connexion().execute(
            "SELECT COUNT(*) FROM compte WHERE id_client = ?", (id_client,)
        ).fetchone()
        return int(ligne[0])

    # ------------------------------------------------------------------ #
    # Écriture                                                           #
    # ------------------------------------------------------------------ #
    def create(self, compte: Compte) -> int:
        with self._db.transaction() as conn:
            if not compte.numero:
                compte.numero = self.prochain_numero()
            cur = conn.execute(
                "INSERT INTO compte (id_client, numero, type, solde, statut)"
                " VALUES (?, ?, ?, ?, ?)",
                (compte.id_client, compte.numero,
                 compte.type or TYPE_COURANT, float(compte.solde),
                 compte.statut or STATUT_COMPTE_ACTIF),
            )
            compte.id_compte = cur.lastrowid
        return compte.id_compte

    def update(self, compte: Compte) -> bool:
        """Mise à jour d'EN-TÊTE (numero/type/statut) : pas du solde,
        qui ne bouge QUE par ``update_solde`` tracée par une opération."""
        with self._db.transaction() as conn:
            cur = conn.execute(
                "UPDATE compte SET numero = ?, type = ?, statut = ?"
                " WHERE id_compte = ?",
                (compte.numero, compte.type, compte.statut, compte.id_compte),
            )
            modifie = cur.rowcount == 1
        return modifie

    def update_solde(self, id_compte: int, solde: float) -> bool:
        """Écriture dédiée du solde : chemin unique, appelé par le service
        dans la même transaction que l'opération qui la justifie."""
        with self._db.transaction() as conn:
            cur = conn.execute(
                "UPDATE compte SET solde = ? WHERE id_compte = ?",
                (float(solde), id_compte),
            )
            modifie = cur.rowcount == 1
        return modifie

    def delete(self, id_compte: int) -> bool:
        with self._db.transaction() as conn:
            cur = conn.execute("DELETE FROM compte WHERE id_compte = ?", (id_compte,))
            supprime = cur.rowcount == 1
        return supprime
