"""Fabriques de tests : base SQLite éphémère, isolée pour chaque test."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.db.db_manager import DatabaseManager


def creer_base_ephemere() -> DatabaseManager:
    """Base neuve (schéma appliqué) dans un fichier temporaire unique."""
    descripteur, chemin = tempfile.mkstemp(prefix="banque_test_", suffix=".db")
    os.close(descripteur)
    db = DatabaseManager(chemin)
    db.init_schema()
    return db


def detruire_base(db: DatabaseManager) -> None:
    """Ferme proprement puis supprime le fichier (Windows : close requis)."""
    db.close()
    Path(db.chemin_base).unlink(missing_ok=True)
