"""
database.py — SQLite setup & connection for VoteWave
"""
import sqlite3
import hashlib

DB = "votewave.db"


def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ── Super-admin (platform owner) ──────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS super_admins(
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    c.execute("INSERT OR IGNORE INTO super_admins(username,password) VALUES(?,?)",
              ("superadmin", hash_pw("super123")))

    # ── Organizations (tenants) ───────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS organizations(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT UNIQUE NOT NULL,
        slug        TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Org admins (approved accounts only) ──────────────
    c.execute("""CREATE TABLE IF NOT EXISTS org_admins(
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id     INTEGER NOT NULL,
        username   TEXT UNIQUE NOT NULL,
        email      TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        name       TEXT NOT NULL,
        role       TEXT DEFAULT 'admin',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
    )""")

    # ── Admin registration requests (pending super-admin approval) ──
    c.execute("""CREATE TABLE IF NOT EXISTS admin_requests(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id      INTEGER NOT NULL,
        name        TEXT NOT NULL,
        username    TEXT NOT NULL,
        email       TEXT NOT NULL,
        password    TEXT NOT NULL,
        reason      TEXT,
        status      TEXT DEFAULT 'pending',
        reviewed_by TEXT,
        review_note TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TEXT,
        FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
    )""")

    # ── Elections (belong to an org) ─────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS elections(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id      INTEGER NOT NULL,
        name        TEXT NOT NULL,
        description TEXT,
        status      TEXT DEFAULT 'draft',
        start_date  TEXT,
        end_date    TEXT,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
    )""")

    # ── Candidates (belong to an election) ───────────────
    c.execute("""CREATE TABLE IF NOT EXISTS candidates(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        election_id INTEGER NOT NULL,
        name        TEXT NOT NULL,
        party       TEXT NOT NULL,
        bio         TEXT,
        emoji       TEXT DEFAULT '🧑',
        color       TEXT DEFAULT '#f5c842',
        FOREIGN KEY(election_id) REFERENCES elections(id) ON DELETE CASCADE
    )""")

    # ── Voters (registered per election) ─────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS voters(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        election_id INTEGER NOT NULL,
        voter_id    TEXT NOT NULL,
        name        TEXT NOT NULL,
        email       TEXT NOT NULL,
        password    TEXT NOT NULL,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(election_id, email),
        UNIQUE(voter_id),
        FOREIGN KEY(election_id) REFERENCES elections(id) ON DELETE CASCADE
    )""")

    # ── Votes (one per voter per election) ────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS votes(
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        voter_id     INTEGER NOT NULL,
        election_id  INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        voted_at     TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(voter_id, election_id),
        FOREIGN KEY(voter_id)     REFERENCES voters(id)     ON DELETE CASCADE,
        FOREIGN KEY(election_id)  REFERENCES elections(id)  ON DELETE CASCADE,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    )""")

    conn.commit()
    conn.close()