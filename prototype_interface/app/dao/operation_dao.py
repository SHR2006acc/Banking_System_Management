"""DAO « operation » : accès paramétré à la table operation (Rôle 1).

``history()`` et ``legs_of_virement()`` sont les deux lectures clés du
SI : le relevé d'un compte et les deux jambes d'un virement.
``derniers_mouvements()`` alimente le tableau de bord (join compte).
"""
from __future__ import annotations

import sqlite3

from app.db.db_manager import DatabaseManager
from app.models.models import Operation

_COLONNES = "id_operation, id_compte, id_contrepartie, type, montant, id_virement, date_op, commentaire"


def _vers_operation(ligne: sqlite3.Row) -> Operation:
    """Ligne SQL -> dataclass Operation."""
    return Operation(
        id_operation=ligne["id_operation"],
        id_compte=ligne["id_compte"],
        id_contrepartie=ligne["id_contrepartie"],
        type=ligne["type"],
        montant=float(ligne["montant"]),
        id_virement=ligne["id_virement"],
        date_op=ligne["date_op"],
        commentaire=ligne["commentaire"],
    )


class OperationDAO:
    """CRUD + lectures spécialisées sur ``operation`` — paramétré."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Lecture                                                            #
    # ------------------------------------------------------------------ #
    def read_all(self) -> list[Operation]:
        cur = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM operation ORDER BY id_operation"
        )
        return [_vers_operation(l) for l in cur.fetchall()]

    def history(self, id_compte: int) -> list[Operation]:
        """Relevé d'un compte, du plus récent au plus ancien."""
        cur = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM operation WHERE id_compte = ?"
            " ORDER BY date_op DESC, id_operation DESC",
            (id_compte,),
        )
        return [_vers_operation(l) for l in cur.fetchall()]

    def legs_of_virement(self, id_virement: str) -> list[Operation]:
        """Les DEUX jambes d'un virement, dans l'ordre d'insertion :
        leg[0] = compte DEBITEUR (source), leg[1] = compte CRÉDITÉ."""
        cur = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM operation WHERE id_virement = ?"
            " ORDER BY id_operation",
            (id_virement,),
        )
        return [_vers_operation(l) for l in cur.fetchall()]

    def read_by_id(self, id_operation: int) -> Operation | None:
        ligne = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM operation WHERE id_operation = ?",
            (id_operation,),
        ).fetchone()
        return _vers_operation(ligne) if ligne else None

    def count(self) -> int:
        ligne = self._db.connexion().execute(
            "SELECT COUNT(*) FROM operation"
        ).fetchone()
        return int(ligne[0])

    def volume_total(self) -> float:
        """Volume brut : somme des montants de toutes les opérations."""
        ligne = self._db.connexion().execute(
            "SELECT COALESCE(SUM(montant), 0) FROM operation"
        ).fetchone()
        return float(ligne[0])

    def derniers_mouvements(self, limite: int = 10) -> list[dict]:
        """Derniers mouvements TOUS comptes confondus (vue « dashboard »).
        Retourne des dicts riches : numero du compte + de la contrepartie."""
        cur = self._db.connexion().execute(
            "SELECT o.id_operation, o.id_compte, o.id_contrepartie, o.type,"
            " o.montant, o.id_virement, o.date_op, o.commentaire,"
            " c.numero  AS numero_compte,"
            " c2.numero AS numero_contrepartie"
            " FROM operation o"
            " JOIN compte c ON c.id_compte = o.id_compte"
            " LEFT JOIN compte c2 ON c2.id_compte = o.id_contrepartie"
            " ORDER BY o.id_operation DESC LIMIT ?",
            (limite,),
        )
        return [dict(l) for l in cur.fetchall()]

    # ------------------------------------------------------------------ #
    # Écriture                                                           #
    # ------------------------------------------------------------------ #
    def create(self, operation: Operation) -> int:
        with self._db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO operation"
                " (id_compte, id_contrepartie, type, montant, id_virement, commentaire)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (operation.id_compte, operation.id_contrepartie, operation.type,
                 float(operation.montant), operation.id_virement,
                 operation.commentaire),
            )
            operation.id_operation = cur.lastrowid
        return operation.id_operation
