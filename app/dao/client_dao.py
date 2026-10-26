"""DAO « client » : accès paramétré à la table client (Rôle 1).

Couche bête et disciplinée : elle lit/écrit et ne connaît QUE la table.
Les règles fonctionnelles (unicité métier du CIN, client possède des
comptes…) vivent dans ``services.bank_service`` ; les contraintes
dures (UNIQUE, CHECK, FK) restent dans ``schema.sql``.
"""
from __future__ import annotations

import sqlite3

from app.db.db_manager import DatabaseManager
from app.models.models import STATUT_CLIENT_ACTIF, Client

_COLONNES = "id_client, nom, prenom, cin, telephone, email, statut, date_creation"


def _vers_client(ligne: sqlite3.Row) -> Client:
    """Ligne SQL -> dataclass Client (unicité du mapping)."""
    return Client(
        id_client=ligne["id_client"],
        nom=ligne["nom"],
        prenom=ligne["prenom"],
        cin=ligne["cin"],
        telephone=ligne["telephone"],
        email=ligne["email"],
        statut=ligne["statut"],
        date_creation=ligne["date_creation"],
    )


class ClientDAO:
    """CRUD complet sur ``client`` — requêtes 100% paramétrées."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Lecture                                                            #
    # ------------------------------------------------------------------ #
    def read_all(self) -> list[Client]:
        cur = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM client ORDER BY nom, prenom"
        )
        return [_vers_client(l) for l in cur.fetchall()]

    def read_by_id(self, id_client: int) -> Client | None:
        ligne = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM client WHERE id_client = ?", (id_client,)
        ).fetchone()
        return _vers_client(ligne) if ligne else None

    def read_by_cin(self, cin: str) -> Client | None:
        ligne = self._db.connexion().execute(
            f"SELECT {_COLONNES} FROM client WHERE cin = ?", (cin,)
        ).fetchone()
        return _vers_client(ligne) if ligne else None

    # ------------------------------------------------------------------ #
    # Écriture (chaque méthode s'entoure d'une transaction)              #
    # ------------------------------------------------------------------ #
    def create(self, client: Client) -> int:
        with self._db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO client (nom, prenom, cin, telephone, email, statut)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (client.nom, client.prenom, client.cin,
                 client.telephone, client.email,
                 client.statut or STATUT_CLIENT_ACTIF),
            )
            client.id_client = cur.lastrowid
        return client.id_client

    def update(self, client: Client) -> bool:
        with self._db.transaction() as conn:
            cur = conn.execute(
                "UPDATE client SET nom = ?, prenom = ?, cin = ?,"
                " telephone = ?, email = ?, statut = ? WHERE id_client = ?",
                (client.nom, client.prenom, client.cin,
                 client.telephone, client.email, client.statut, client.id_client),
            )
            modifie = cur.rowcount == 1
        return modifie

    def delete(self, id_client: int) -> bool:
        with self._db.transaction() as conn:
            cur = conn.execute("DELETE FROM client WHERE id_client = ?", (id_client,))
            supprime = cur.rowcount == 1
        return supprime
