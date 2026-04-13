"""
helpers.py — All business logic and DB query functions for VoteWave
"""
import re
import uuid
import io
import sqlite3
import pandas as pd
from database import get_conn, hash_pw

# ─────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────
COLORS = ["#f5c842","#4dabf7","#2ec27e","#ff6b35","#cc5de8",
          "#e63946","#74c0fc","#a9e34b","#ffa94d","#da77f2"]

EMOJIS = ["🦁","🦅","🌿","🏛️","🌍","⭐","🔥","💡",
          "🎯","🕊️","🌊","🏆","🦋","🌟","🎖️"]


# ─────────────────────────────────────────────────────────
#  ORGANIZATIONS
# ─────────────────────────────────────────────────────────
def slugify(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def get_all_orgs() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM organizations ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_org(org_id: int) -> dict | None:
    conn = get_conn()
    row  = conn.execute("SELECT * FROM organizations WHERE id=?", (org_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_org(name: str, desc: str = "") -> tuple[bool, any]:
    slug = slugify(name)
    conn = get_conn()
    try:
        conn.execute("INSERT INTO organizations(name,slug,description) VALUES(?,?,?)",
                     (name, slug, desc))
        conn.commit()
        oid = conn.execute("SELECT id FROM organizations WHERE slug=?", (slug,)).fetchone()[0]
        conn.close()
        return True, oid
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Organization name already exists."


def update_org(org_id: int, name: str, desc: str):
    conn = get_conn()
    conn.execute("UPDATE organizations SET name=?,description=? WHERE id=?", (name, desc, org_id))
    conn.commit(); conn.close()


def delete_org(org_id: int):
    """Delete org and ALL child data in correct order (manual cascade)."""
    conn = get_conn()
    eids = [r[0] for r in conn.execute(
        "SELECT id FROM elections WHERE org_id=?", (org_id,)
    ).fetchall()]
    for eid in eids:
        vids = [r[0] for r in conn.execute(
            "SELECT id FROM voters WHERE election_id=?", (eid,)
        ).fetchall()]
        for vid in vids:
            conn.execute("DELETE FROM votes WHERE voter_id=?", (vid,))
        conn.execute("DELETE FROM voters     WHERE election_id=?", (eid,))
        conn.execute("DELETE FROM candidates WHERE election_id=?", (eid,))
    conn.execute("DELETE FROM elections      WHERE org_id=?", (org_id,))
    conn.execute("DELETE FROM admin_requests WHERE org_id=?", (org_id,))
    conn.execute("DELETE FROM org_admins     WHERE org_id=?", (org_id,))
    conn.execute("DELETE FROM organizations  WHERE id=?",     (org_id,))
    conn.commit(); conn.close()


# ─────────────────────────────────────────────────────────
#  ADMIN REGISTRATION REQUESTS
# ─────────────────────────────────────────────────────────
def submit_admin_request(org_id, name, username, email, password, reason="") -> tuple[bool, str]:
    """Submit a pending admin request — super admin must approve before login."""
    conn = get_conn()
    dup_req = conn.execute(
        "SELECT id FROM admin_requests WHERE (username=? OR email=?) AND status='pending'",
        (username, email)
    ).fetchone()
    dup_adm = conn.execute(
        "SELECT id FROM org_admins WHERE username=? OR email=?", (username, email)
    ).fetchone()
    if dup_req or dup_adm:
        conn.close()
        return False, "Username or email already exists or has a pending request."
    conn.execute(
        "INSERT INTO admin_requests(org_id,name,username,email,password,reason) VALUES(?,?,?,?,?,?)",
        (org_id, name, username, email, hash_pw(password), reason)
    )
    conn.commit(); conn.close()
    return True, "Request submitted."


def get_admin_requests(status: str = None) -> list[dict]:
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT r.*, o.name AS org_name FROM admin_requests r "
            "JOIN organizations o ON o.id=r.org_id "
            "WHERE r.status=? ORDER BY r.created_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT r.*, o.name AS org_name FROM admin_requests r "
            "JOIN organizations o ON o.id=r.org_id ORDER BY r.created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve_admin_request(request_id: int, reviewer: str, note: str = "") -> tuple[bool, str]:
    from datetime import datetime
    conn = get_conn()
    req  = conn.execute("SELECT * FROM admin_requests WHERE id=?", (request_id,)).fetchone()
    if not req:
        conn.close(); return False, "Request not found."
    if req["status"] != "pending":
        conn.close(); return False, "Request already reviewed."
    now = datetime.now().isoformat()
    try:
        conn.execute(
            "INSERT INTO org_admins(org_id,name,username,email,password,role) VALUES(?,?,?,?,?,?)",
            (req["org_id"], req["name"], req["username"], req["email"], req["password"], "admin")
        )
        conn.execute(
            "UPDATE admin_requests SET status='approved',reviewed_by=?,review_note=?,reviewed_at=? WHERE id=?",
            (reviewer, note, now, request_id)
        )
        conn.commit(); conn.close()
        return True, f"Admin '{req['name']}' approved."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username or email conflict — account may already exist."


def reject_admin_request(request_id: int, reviewer: str, note: str = ""):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "UPDATE admin_requests SET status='rejected',reviewed_by=?,review_note=?,reviewed_at=? WHERE id=?",
        (reviewer, note, datetime.now().isoformat(), request_id)
    )
    conn.commit(); conn.close()


def delete_admin_request(request_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM admin_requests WHERE id=?", (request_id,))
    conn.commit(); conn.close()


def pending_request_count() -> int:
    conn = get_conn()
    n    = conn.execute("SELECT COUNT(*) FROM admin_requests WHERE status='pending'").fetchone()[0]
    conn.close()
    return n


# ─────────────────────────────────────────────────────────
#  ORG ADMINS
# ─────────────────────────────────────────────────────────
def get_org_admins(org_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM org_admins WHERE org_id=? ORDER BY name", (org_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def register_org_admin(org_id, name, username, email, password, role="admin") -> tuple[bool, str]:
    """Direct admin creation — used by super admin or existing admin."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO org_admins(org_id,name,username,email,password,role) VALUES(?,?,?,?,?,?)",
            (org_id, name, username, email, hash_pw(password), role)
        )
        conn.commit(); conn.close()
        return True, "Admin created."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username or email already exists."


def login_org_admin(username: str, password: str) -> dict | None:
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM org_admins WHERE username=? AND password=?",
        (username, hash_pw(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def login_super_admin(username: str, password: str) -> bool:
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM super_admins WHERE username=? AND password=?",
        (username, hash_pw(password))
    ).fetchone()
    conn.close()
    return row is not None


def update_org_admin(aid: int, name: str, email: str, role: str, new_pw: str = None):
    conn = get_conn()
    if new_pw:
        conn.execute(
            "UPDATE org_admins SET name=?,email=?,role=?,password=? WHERE id=?",
            (name, email, role, hash_pw(new_pw), aid)
        )
    else:
        conn.execute(
            "UPDATE org_admins SET name=?,email=?,role=? WHERE id=?",
            (name, email, role, aid)
        )
    conn.commit(); conn.close()


def delete_org_admin(aid: int):
    conn = get_conn()
    conn.execute("DELETE FROM org_admins WHERE id=?", (aid,))
    conn.commit(); conn.close()


# ─────────────────────────────────────────────────────────
#  ELECTIONS
# ─────────────────────────────────────────────────────────
def get_elections(org_id: int, status: str = None) -> list[dict]:
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM elections WHERE org_id=? AND status=? ORDER BY created_at DESC",
            (org_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM elections WHERE org_id=? ORDER BY created_at DESC", (org_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_election(eid: int) -> dict | None:
    conn = get_conn()
    row  = conn.execute("SELECT * FROM elections WHERE id=?", (eid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_election(org_id, name, desc, status, start, end):
    conn = get_conn()
    conn.execute(
        "INSERT INTO elections(org_id,name,description,status,start_date,end_date) VALUES(?,?,?,?,?,?)",
        (org_id, name, desc, status, start or None, end or None)
    )
    conn.commit(); conn.close()


def update_election(eid, name, desc, status, start, end):
    conn = get_conn()
    conn.execute(
        "UPDATE elections SET name=?,description=?,status=?,start_date=?,end_date=? WHERE id=?",
        (name, desc, status, start or None, end or None, eid)
    )
    conn.commit(); conn.close()


def delete_election(eid: int):
    """Delete election and all child data in correct order (manual cascade)."""
    conn = get_conn()
    vids = [r[0] for r in conn.execute(
        "SELECT id FROM voters WHERE election_id=?", (eid,)
    ).fetchall()]
    for vid in vids:
        conn.execute("DELETE FROM votes WHERE voter_id=?", (vid,))
    conn.execute("DELETE FROM votes      WHERE election_id=?", (eid,))
    conn.execute("DELETE FROM voters     WHERE election_id=?", (eid,))
    conn.execute("DELETE FROM candidates WHERE election_id=?", (eid,))
    conn.execute("DELETE FROM elections  WHERE id=?",          (eid,))
    conn.commit(); conn.close()


def set_election_status(eid: int, status: str):
    conn = get_conn()
    conn.execute("UPDATE elections SET status=? WHERE id=?", (status, eid))
    conn.commit(); conn.close()


# ─────────────────────────────────────────────────────────
#  CANDIDATES
# ─────────────────────────────────────────────────────────
def get_candidates(eid: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM candidates WHERE election_id=? ORDER BY id", (eid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_candidate(eid, name, party, bio, emoji, color):
    conn = get_conn()
    conn.execute(
        "INSERT INTO candidates(election_id,name,party,bio,emoji,color) VALUES(?,?,?,?,?,?)",
        (eid, name, party, bio, emoji, color)
    )
    conn.commit(); conn.close()


def update_candidate(cid, name, party, bio, emoji, color):
    conn = get_conn()
    conn.execute(
        "UPDATE candidates SET name=?,party=?,bio=?,emoji=?,color=? WHERE id=?",
        (name, party, bio, emoji, color, cid)
    )
    conn.commit(); conn.close()


def delete_candidate(cid: int):
    conn = get_conn()
    conn.execute("DELETE FROM candidates WHERE id=?", (cid,))
    conn.commit(); conn.close()


# ─────────────────────────────────────────────────────────
#  VOTERS  (per-election, simple register/login — no OTP)
# ─────────────────────────────────────────────────────────
def gen_voter_id() -> str:
    return f"VW-{uuid.uuid4().hex[:8].upper()}"


def register_voter(election_id, name, email, password) -> tuple[bool, str]:
    """Register a voter for an election. Returns (True, voter_id) or (False, error)."""
    conn = get_conn()
    try:
        vid = gen_voter_id()
        conn.execute(
            "INSERT INTO voters(election_id,voter_id,name,email,password) VALUES(?,?,?,?,?)",
            (election_id, vid, name, email, hash_pw(password))
        )
        conn.commit(); conn.close()
        return True, vid
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email already registered for this election."


def login_voter(email: str, password: str, election_id: int) -> dict | None:
    """Returns voter dict on success, None on failure."""
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM voters WHERE email=? AND password=? AND election_id=?",
        (email, hash_pw(password), election_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_voter_elections(email: str) -> list[dict]:
    """All elections this voter email is registered for (across all orgs)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT v.*, e.name AS election_name, e.status AS election_status,
               e.org_id, o.name AS org_name
        FROM voters v
        JOIN elections e ON e.id = v.election_id
        JOIN organizations o ON o.id = e.org_id
        WHERE v.email = ?
        ORDER BY v.created_at DESC
    """, (email,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_voter_vote(voter_db_id: int, election_id: int) -> dict | None:
    conn = get_conn()
    row  = conn.execute("""
        SELECT v.*, c.name AS cand_name, c.party, c.emoji, c.color
        FROM votes v JOIN candidates c ON c.id = v.candidate_id
        WHERE v.voter_id = ? AND v.election_id = ?
    """, (voter_db_id, election_id)).fetchone()
    conn.close()
    return dict(row) if row else None


def cast_vote(voter_db_id: int, election_id: int, candidate_id: int) -> tuple[bool, str]:
    if get_voter_vote(voter_db_id, election_id):
        return False, "You have already voted in this election."
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO votes(voter_id,election_id,candidate_id) VALUES(?,?,?)",
            (voter_db_id, election_id, candidate_id)
        )
        conn.commit(); conn.close()
        return True, "Vote cast successfully!"
    except Exception as e:
        return False, str(e)


def get_voters_for_election(election_id: int) -> pd.DataFrame:
    conn = get_conn()
    rows = conn.execute("""
        SELECT v.voter_id, v.name, v.email, v.created_at,
               CASE WHEN vt.id IS NOT NULL THEN '✅ Voted' ELSE '⏳ Pending' END AS status,
               COALESCE(c.name, '—') AS voted_for
        FROM voters v
        LEFT JOIN votes vt ON vt.voter_id = v.id AND vt.election_id = v.election_id
        LEFT JOIN candidates c ON c.id = vt.candidate_id
        WHERE v.election_id = ?
        ORDER BY v.created_at DESC
    """, (election_id,)).fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def delete_voter(voter_db_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM voters WHERE id=?", (voter_db_id,))
    conn.commit(); conn.close()


def reset_election_voters(election_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM voters WHERE election_id=?", (election_id,))
    conn.commit(); conn.close()


def reset_election_votes(election_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM votes WHERE election_id=?", (election_id,))
    conn.commit(); conn.close()


# ─────────────────────────────────────────────────────────
#  RESULTS & STATS
# ─────────────────────────────────────────────────────────
def get_results(election_id: int) -> pd.DataFrame:
    conn = get_conn()
    df   = pd.read_sql_query("""
        SELECT c.id, c.name, c.party, c.color, c.emoji, COUNT(v.id) AS votes
        FROM candidates c
        LEFT JOIN votes v ON v.candidate_id = c.id AND v.election_id = c.election_id
        WHERE c.election_id = ?
        GROUP BY c.id ORDER BY votes DESC
    """, conn, params=(election_id,))
    conn.close()
    return df


def get_stats(election_id: int) -> dict:
    conn         = get_conn()
    total_voters = conn.execute("SELECT COUNT(*) FROM voters     WHERE election_id=?", (election_id,)).fetchone()[0]
    total_voted  = conn.execute("SELECT COUNT(*) FROM votes      WHERE election_id=?", (election_id,)).fetchone()[0]
    total_cands  = conn.execute("SELECT COUNT(*) FROM candidates WHERE election_id=?", (election_id,)).fetchone()[0]
    conn.close()
    pct = round(total_voted / total_voters * 100, 1) if total_voters else 0
    return {"total_voters": total_voters, "total_voted": total_voted,
            "total_cands": total_cands, "turnout_pct": pct}


def results_to_csv(election_id: int, election_name: str) -> bytes:
    df    = get_results(election_id)
    total = int(df["votes"].sum())
    df["percentage"] = df["votes"].apply(lambda v: round(v / total * 100, 1) if total else 0)
    df["election"]   = election_name
    buf = io.StringIO()
    df[["election", "name", "party", "votes", "percentage"]].to_csv(buf, index=False)
    return buf.getvalue().encode()
