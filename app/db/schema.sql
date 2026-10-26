-- =====================================================================
--  Schéma relationnel — Système bancaire MVP
--  SQLite 3  |  Contraintes d'intégrité déclaratives
-- =====================================================================

CREATE TABLE IF NOT EXISTS client (
    id_client     INTEGER PRIMARY KEY AUTOINCREMENT,
    nom           TEXT NOT NULL,
    prenom        TEXT NOT NULL,
    cin           TEXT NOT NULL UNIQUE,          -- identité unique : doublon impossible
    telephone     TEXT,
    email         TEXT,
    statut        TEXT NOT NULL DEFAULT 'ACTIF'
                  CHECK (statut IN ('ACTIF','SUSPENDU')),  -- domaine restreint
    date_creation TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS compte (
    id_compte      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client      INTEGER NOT NULL REFERENCES client(id_client),  -- intégrité référentielle
    numero         TEXT NOT NULL UNIQUE,        -- identifiant fonctionnel unique
    type           TEXT NOT NULL DEFAULT 'COURANT'
                   CHECK (type IN ('COURANT','EPARGNE')),   -- domaine restreint
    solde          REAL NOT NULL DEFAULT 0
                   CHECK (solde >= 0),          -- invariant bancaire dernier rempart
    statut         TEXT NOT NULL DEFAULT 'ACTIF'
                   CHECK (statut IN ('ACTIF','CLOTURE')),
    date_ouverture TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS operation (
    id_operation    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_compte       INTEGER NOT NULL REFERENCES compte(id_compte),       -- compte concerné
    id_contrepartie INTEGER REFERENCES compte(id_compte),                -- autre jambe d'un virement
    type            TEXT NOT NULL CHECK (type IN ('DEPOT','RETRAIT','VIREMENT')),
    montant         REAL NOT NULL CHECK (montant > 0),                   -- jamais nul ni négatif
    id_virement     TEXT,       -- uuid : groupe les DEUX jambes d'un même virement
    date_op         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    commentaire     TEXT
);

CREATE INDEX IF NOT EXISTS idx_op_compte ON operation(id_compte);   -- perf : historique par compte
-- Fin du schéma. Le jeu de démonstration est géré par app/db/seed.py.
