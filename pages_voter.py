"""
pages_voter.py — Voter-facing pages
Simple register & login — no OTP/email verification.
login_voter() returns dict|None (simple, no tuple).
"""
import streamlit as st
import time
import plotly.graph_objects as pgo
from datetime import datetime
from database import get_conn
from helpers import (
    get_election, get_candidates,
    get_results, get_stats, get_voter_elections, get_voter_vote,
    register_voter, login_voter, cast_vote, results_to_csv,
)
from ui import render_header, metric, sbadge, nav, render_countdown, election_timer


# ─────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────
def render_footer():
    st.markdown(
        '<div style="margin-top:3.5rem;padding:2rem 0 1rem;border-top:1px solid #2a2f42;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">'

        # Left — brand
        '<div>'
        '<div style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:900;'
        'background:linear-gradient(135deg,#f5c842,#ff6b35);-webkit-background-clip:text;'
        '-webkit-text-fill-color:transparent;">🗳️ VoteWave</div>'
        '<div style="font-size:.75rem;color:#6b7080;margin-top:.2rem;">Secure · Transparent · Democratic</div>'
        '</div>'

        # Center — links
        '<div style="display:flex;gap:1.5rem;flex-wrap:wrap;">'
        '<span style="font-size:.78rem;color:#6b7080;">🔒 End-to-end secure voting</span>'
        '<span style="font-size:.78rem;color:#6b7080;">📊 Real-time results</span>'
        '<span style="font-size:.78rem;color:#6b7080;">🏢 Multi-organization support</span>'
        '</div>'

        # Right — copyright
        '<div style="font-size:.72rem;color:#3a3f52;text-align:right;">'
        f'© {__import__("datetime").datetime.now().year} VoteWave. All rights reserved.<br>'
        '<span style="color:#2a2f42;">Built with Streamlit &amp; SQLite</span>'
        '</div>'

        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────────────────
def page_home():
    # ── Hero Section ──────────────────────────────────────
    st.markdown(
        '<div style="padding:2rem 0 1rem;">'

        # Badge
        '<div style="display:inline-flex;align-items:center;gap:.4rem;background:#1e1a2e;'
        'border:1px solid #cc5de840;border-radius:20px;padding:.25rem .9rem;margin-bottom:1rem;">'
        '<span class="activity-dot" style="background:#2ec27e;box-shadow:0 0 6px #2ec27e80;"></span>'
        '<span style="font-size:.72rem;color:#cc5de8;font-weight:600;letter-spacing:.1em;">LIVE PLATFORM</span>'
        '</div>'

        # Title
        '<div style="font-family:\'Playfair Display\',serif;font-size:clamp(2.4rem,5vw,4rem);'
        'font-weight:900;background:linear-gradient(135deg,#f5c842 0%,#ff6b35 60%,#e63946 100%);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
        'line-height:1.1;margin-bottom:.6rem;">VoteWave 🗳️</div>'

        # Tagline
        '<div style="font-size:1.15rem;color:#c8cdd8;font-weight:400;margin-bottom:.5rem;max-width:600px;">'
        'The modern platform for <strong style="color:#f5c842;">secure</strong>, '
        '<strong style="color:#ff6b35;">transparent</strong> and '
        '<strong style="color:#2ec27e;">real-time</strong> digital elections.'
        '</div>'

        # Sub-tagline
        '<div style="font-size:.88rem;color:#6b7080;margin-bottom:1.8rem;max-width:520px;">'
        'From student councils to corporate boards — run any election with full transparency, '
        'instant results and complete voter privacy.'
        '</div>'

        '</div>',
        unsafe_allow_html=True
    )

    # ── CTA Cards ─────────────────────────────────────────
    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        st.markdown(
            '<div class="card">'
            '<div class="section-label">New Voter</div>'
            '<div style="font-family:\'Playfair Display\',serif;font-size:1.4rem;font-weight:700;margin-bottom:.3rem;">Register &amp; Vote</div>'
            '<div class="cand-bio">Create your voter account in seconds and cast your vote for any active election.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("📝 Register Now →", key="home_reg"): nav("voter_register")
    with col_r:
        st.markdown(
            '<div class="card">'
            '<div class="section-label">Returning Voter</div>'
            '<div style="font-family:\'Playfair Display\',serif;font-size:1.4rem;font-weight:700;margin-bottom:.3rem;">Login &amp; Continue</div>'
            '<div class="cand-bio">Already registered? Log in to access your ballot and track your elections.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("🔓 Login →", key="home_login"): nav("voter_login")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Available Elections ───────────────────────────────
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.*, o.name AS org_name
        FROM elections e
        JOIN organizations o ON o.id=e.org_id
        WHERE e.status IN ('active','closed')
        ORDER BY e.status ASC, e.created_at DESC
    """).fetchall()
    conn.close()
    elections = [dict(r) for r in rows]

    now     = datetime.now()
    visible = []
    for e in elections:
        if e["status"] == "active":
            visible.append(e)
        elif e["status"] == "closed":
            end = e.get("end_date")
            try:
                ref = datetime.fromisoformat(end) if end else datetime.fromisoformat(e["created_at"])
                if (now - ref).days < 2:
                    visible.append(e)
            except Exception:
                pass

    if not visible:
        st.markdown(
            '<div class="card-flat" style="text-align:center;padding:2rem;">'
            '<div style="font-size:2rem;margin-bottom:.5rem;">📭</div>'
            '<div style="font-weight:600;color:#8a8fa8;margin-bottom:.3rem;">No Active Elections Right Now</div>'
            '<div class="cand-bio">New elections will appear here when published by an organization admin.</div>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="section-label">🗳️ Available Elections</div>', unsafe_allow_html=True)
        for e in visible:
            cands = get_candidates(e["id"])
            stats = get_stats(e["id"])
            timer = election_timer(e)
            dot_c = "#2ec27e" if e["status"] == "active" else "#e63946"
            st.markdown(
                f'<div class="election-card">'
                f'<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;">'
                f'<div style="flex:1;">'
                f'<div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem;">'
                f'<span class="activity-dot" style="background:{dot_c};box-shadow:0 0 5px {dot_c}80;"></span>'
                f'<span style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:700;">{e["name"]}</span>'
                f'&nbsp;{sbadge(e["status"])}</div>'
                f'<div style="font-size:.75rem;color:#cc5de8;margin-bottom:.3rem;">🏢 {e["org_name"]}</div>'
                + (f'<div class="cand-bio">{e["description"]}</div>' if e.get("description") else "")
                + f'<div style="font-size:.72rem;color:#6b7080;margin-top:.3rem;">👤 {stats["total_voters"]} voters · 🗳️ {stats["total_voted"]} votes · 📋 {len(cands)} candidates</div>'
                + '</div>'
                + f'<div style="text-align:right;min-width:100px;">'
                + (f'<div style="font-size:.72rem;color:#6b7080;">{timer["sub"]}</div>'
                   if e["status"] == "active"
                   else '<div style="font-size:.72rem;color:#e63946;">Election Closed</div>')
                + '</div></div></div>',
                unsafe_allow_html=True
            )
            bc1, bc2, bc3 = st.columns([1, 1, 3])
            with bc1:
                if st.button("🗳️ Vote / Login", key=f"vote_btn_{e['id']}"):
                    st.session_state["home_sel_election"] = e["id"]; nav("voter_login")
            with bc2:
                if st.button("📝 Register", key=f"reg_btn_{e['id']}"):
                    st.session_state["home_sel_election"] = e["id"]; nav("voter_register")
            with bc3:
                if st.button("📊 Results", key=f"res_btn_{e['id']}"):
                    st.session_state["viewing_election"] = e["id"]; nav("public_results")
            st.markdown("<hr>", unsafe_allow_html=True)

    # ── Admin access row ──────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:1rem;">Organization Admin?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔐 Admin Login",    key="home_admin_login"):    nav("admin_login")
    with c2:
        if st.button("📝 Admin Register", key="home_admin_register"): nav("admin_register")

    # ── Footer ────────────────────────────────────────────
    render_footer()


# ─────────────────────────────────────────────────────────
#  VOTER REGISTER  (simple — no OTP)
# ─────────────────────────────────────────────────────────
def page_voter_register():
    render_header("Voter Registration")
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.*, o.name AS org_name FROM elections e
        JOIN organizations o ON o.id=e.org_id
        WHERE e.status='active' ORDER BY e.name
    """).fetchall()
    conn.close()
    active_elections = [dict(r) for r in rows]

    if not active_elections:
        st.warning("No active elections available for registration right now.")
        if st.button("← Back"): nav("home")
        return

    col, _ = st.columns([1.3, 1])
    with col:
        st.markdown('<div class="card"><div class="section-label">Register to Vote</div>', unsafe_allow_html=True)

        pre         = st.session_state.get("home_sel_election")
        emap        = {e["id"]: f"{e['name']} ({e['org_name']})" for e in active_elections}
        default_idx = list(emap.keys()).index(pre) if pre and pre in emap else 0
        sel_eid     = st.selectbox("Select Election *", list(emap.keys()),
                                   format_func=lambda x: emap[x], index=default_idx, key="reg_eid")
        name        = st.text_input("Full Name *")
        email       = st.text_input("Email Address *")
        password    = st.text_input("Password *", type="password")
        confirm     = st.text_input("Confirm Password", type="password")
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1: submit = st.button("✅ Register")
        with c2:
            if st.button("← Back"): nav("home")

        if submit:
            if not all([name, email, password, sel_eid]):
                st.error("All fields are required.")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, result = register_voter(sel_eid, name, email, password)
                if ok:
                    st.balloons()
                    st.success("✅ Registered successfully! You can now log in.")
                    st.markdown(
                        f'<div style="margin-top:.7rem;">'
                        f'<div class="section-label">Your Voter ID</div>'
                        f'<div class="voter-id-box">{result}</div>'
                        f'<div class="cand-bio" style="margin-top:.3rem;">Save this — it is your unique identifier for this election.</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if st.button("🔓 Go to Login"): nav("voter_login")
                else:
                    st.error(result)


# ─────────────────────────────────────────────────────────
#  VOTER LOGIN  (simple — login_voter returns dict|None)
# ─────────────────────────────────────────────────────────
def page_voter_login():
    render_header("Voter Login")
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.*, o.name AS org_name FROM elections e
        JOIN organizations o ON o.id=e.org_id
        WHERE e.status='active' ORDER BY e.name
    """).fetchall()
    conn.close()
    active_elections = [dict(r) for r in rows]

    col, _ = st.columns([1.2, 1])
    with col:
        st.markdown('<div class="card"><div class="section-label">Voter Login</div>', unsafe_allow_html=True)

        if active_elections:
            pre         = st.session_state.get("home_sel_election")
            emap        = {e["id"]: f"{e['name']} ({e['org_name']})" for e in active_elections}
            default_idx = list(emap.keys()).index(pre) if pre and pre in emap else 0
            sel_eid     = st.selectbox("Select Election", list(emap.keys()),
                                       format_func=lambda x: emap[x], index=default_idx, key="login_eid")
        else:
            st.warning("No active elections at the moment.")
            sel_eid = None

        email    = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1: submit = st.button("🔓 Login")
        with c2:
            if st.button("← Back"): nav("home")

        if submit:
            if not sel_eid:
                st.error("No active election to log in to.")
            elif not email or not password:
                st.error("Please enter your email and password.")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
            else:
                # login_voter returns dict on success, None on failure
                voter = login_voter(email, password, sel_eid)
                if voter:
                    st.session_state.voter            = voter
                    st.session_state.active_election  = get_election(sel_eid)
                    st.session_state["session_start"] = datetime.now().isoformat()
                    nav("ballot")
                else:
                    st.error("Invalid email or password, or not registered for this election.")

        st.markdown("---")
        if st.button("📝 Register for an Election"): nav("voter_register")


# ─────────────────────────────────────────────────────────
#  MY ELECTIONS
# ─────────────────────────────────────────────────────────
def page_my_elections():
    voter = st.session_state.voter
    if not voter: nav("voter_login")
    render_header("My Elections")

    registrations = get_voter_elections(voter["email"])
    if not registrations:
        st.info("You are not registered for any elections.")
        if st.button("📝 Register for an Election"): nav("voter_register")
        return

    st.markdown(
        f'<div class="cand-bio" style="margin-bottom:1rem;">You are registered for {len(registrations)} election(s).</div>',
        unsafe_allow_html=True
    )

    for reg in registrations:
        e = get_election(reg["election_id"])
        if not e: continue
        conn  = get_conn()
        v_row = conn.execute(
            "SELECT id FROM voters WHERE election_id=? AND email=?",
            (e["id"], voter["email"])
        ).fetchone()
        conn.close()
        vote  = get_voter_vote(v_row[0], e["id"]) if v_row else None
        dot_c = "#2ec27e" if e["status"] == "active" else ("#e63946" if e["status"] == "closed" else "#f5c842")

        st.markdown(
            f'<div class="election-card">'
            f'<div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem;">'
            f'<span class="activity-dot" style="background:{dot_c};"></span>'
            f'<span style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;">{e["name"]}</span>'
            f'&nbsp;{sbadge(e["status"])}</div>'
            f'<div style="font-size:.75rem;color:#cc5de8;">🏢 {reg["org_name"]}</div>'
            + (f'<div class="cand-bio">{e["description"]}</div>' if e.get("description") else "")
            + (f'<div style="margin-top:.4rem;"><span class="voted-badge">✓ Voted for {vote["cand_name"]}</span></div>'
               if vote else
               '<div style="margin-top:.4rem;font-size:.8rem;color:#f5c842;">⏳ Not voted yet</div>')
            + '</div>',
            unsafe_allow_html=True
        )
        bc1, bc2, bc3 = st.columns([1, 1, 3])
        if e["status"] == "active":
            with bc1:
                if st.button("🗳️ Vote", key=f"myel_vote_{e['id']}"):
                    if v_row:
                        conn  = get_conn()
                        v_full= conn.execute("SELECT * FROM voters WHERE id=?", (v_row[0],)).fetchone()
                        conn.close()
                        st.session_state.voter = dict(v_full)
                    st.session_state.active_election = e
                    nav("ballot")
        with bc2:
            if st.button("📊 Results", key=f"myel_res_{e['id']}"):
                st.session_state["viewing_election"] = e["id"]; nav("public_results")
        st.markdown("<hr>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
#  BALLOT
# ─────────────────────────────────────────────────────────
def page_ballot():
    voter    = st.session_state.voter
    election = st.session_state.active_election
    if not voter:    nav("voter_login")
    if not election: nav("my_elections")

    election = get_election(election["id"])
    st.session_state.active_election = election

    col_t, col_u = st.columns([3, 1])
    with col_t: render_header("The Ballot")
    with col_u:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="text-align:right;">'
            f'<div style="font-size:.74rem;color:#6b7080;">Logged in as</div>'
            f'<div style="font-weight:600;color:#e8e8e8;">{voter["name"]}</div>'
            f'<div style="font-family:monospace;font-size:.71rem;color:#f5c842;">{voter["voter_id"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    if not election:
        st.error("Election not found."); return

    phase = render_countdown(election)
    if phase == "upcoming":
        st.warning("⏳ Voting hasn't started yet."); return
    if phase == "closed":
        st.error("🔒 This election is closed.")
        if st.button("📊 Results"):
            st.session_state["viewing_election"] = election["id"]; nav("public_results")
        return

    vote = get_voter_vote(voter["id"], election["id"])
    if vote:
        st.markdown(
            f'<div class="card" style="text-align:center;padding:2rem;">'
            f'<div style="font-size:2.5rem;margin-bottom:.4rem;">🎉</div>'
            f'<div style="font-family:\'Playfair Display\',serif;font-size:1.5rem;font-weight:700;margin-bottom:.3rem;">Vote Submitted!</div>'
            f'<div class="cand-bio" style="margin-bottom:.7rem;">You voted for <strong style="color:#f5c842;">{vote["cand_name"]}</strong> · {vote["party"]}</div>'
            f'<span class="voted-badge">✓ VOTE RECORDED</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 View Results"):
                st.session_state["viewing_election"] = election["id"]; nav("public_results")
        with c2:
            if st.button("🗳️ My Elections"): nav("my_elections")
        return

    st.markdown(f'<div class="section-label">Election: {election["name"]}</div>', unsafe_allow_html=True)
    if election.get("description"):
        st.markdown(f'<div class="cand-bio" style="margin-bottom:.8rem;">{election["description"]}</div>', unsafe_allow_html=True)

    candidates = get_candidates(election["id"])
    if not candidates:
        st.warning("No candidates added yet."); return

    selected = st.session_state.get("sel_cand", None)
    cols     = st.columns(2, gap="large")
    for i, cand in enumerate(candidates):
        with cols[i % 2]:
            is_sel = selected == cand["id"]
            border = f"border-color:{cand['color']};box-shadow:0 0 0 2px {cand['color']}40;" if is_sel else ""
            st.markdown(
                f'<div class="card" style="{border}">'
                f'<div style="display:flex;align-items:flex-start;gap:.9rem;">'
                f'<div class="cand-avatar" style="background:{cand["color"]}22;flex-shrink:0;">{cand["emoji"]}</div>'
                f'<div style="flex:1;">'
                f'<div class="cand-name">{cand["name"]}</div>'
                f'<div class="cand-party" style="background:{cand["color"]}22;color:{cand["color"]};margin-bottom:.3rem;">{cand["party"]}</div>'
                f'<div class="cand-bio">{cand["bio"] or ""}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True
            )
            if st.button("✓ Selected" if is_sel else "Select", key=f"sel_{cand['id']}"):
                st.session_state.sel_cand = cand["id"]; st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    if selected:
        cname = next(c["name"] for c in candidates if c["id"] == selected)
        st.info(f"Selected: **{cname}** — click below to confirm.")
        if st.button("🗳️ Confirm & Submit Vote", key="submit_vote"):
            ok, msg = cast_vote(voter["id"], election["id"], selected)
            if ok:
                if "sel_cand" in st.session_state: del st.session_state["sel_cand"]
                st.balloons(); st.success("🎉 " + msg); time.sleep(1.2); st.rerun()
            else:
                st.error(msg)
    else:
        st.warning("Select a candidate above to proceed.")


# ─────────────────────────────────────────────────────────
#  VOTER PROFILE
# ─────────────────────────────────────────────────────────
def page_voter_profile():
    voter = st.session_state.voter
    if not voter: nav("voter_login")
    election = st.session_state.active_election

    render_header("My Profile")
    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 1.6], gap="large")

    with col_l:
        initials = "".join(p[0].upper() for p in voter["name"].split()[:2])
        vote     = get_voter_vote(voter["id"], election["id"]) if election else None
        vbadge   = (
            '<span class="voted-badge">✓ VOTED</span>' if vote else
            '<span style="background:#2a1e0f;color:#f5c842;padding:3px 10px;border-radius:20px;'
            'font-size:.75rem;font-weight:700;border:1px solid #f5c84240;">⏳ PENDING</span>'
        )
        st.markdown(
            f'<div class="profile-hero">'
            f'<div class="profile-avatar-big">{initials}</div>'
            f'<div class="profile-name">{voter["name"]}</div>'
            f'<div style="margin:.3rem 0 .5rem;">{vbadge}</div>'
            f'<div style="font-family:monospace;font-size:.78rem;color:#f5c842;">{voter["voter_id"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div class="section-label">Your Voter ID</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="voter-id-box" style="text-align:center;">{voter["voter_id"]}</div>'
            f'<div class="cand-bio" style="text-align:center;margin-top:.3rem;">Unique identifier for this election.</div>',
            unsafe_allow_html=True
        )

    with col_r:
        st.markdown('<div class="section-label">Account Information</div>', unsafe_allow_html=True)
        vstatus = (
            '<span style="color:#2ec27e;font-weight:700;">✓ Vote Cast</span>'
            if (election and get_voter_vote(voter["id"], election["id"])) else
            '<span style="color:#f5c842;">⏳ Not voted yet</span>'
        )
        st.markdown(
            '<div class="card" style="padding:.9rem 1.2rem;">'
            + f'<div class="profile-info-row"><span class="profile-info-label">👤 Name</span><span class="profile-info-value">{voter["name"]}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">📧 Email</span><span class="profile-info-value">{voter["email"]}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">🪪 Voter ID</span><span class="profile-info-value" style="font-family:monospace;color:#f5c842;">{voter["voter_id"]}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">📅 Registered</span><span class="profile-info-value">{voter["created_at"][:16]}</span></div>'
            + f'<div class="profile-info-row" style="border:none;"><span class="profile-info-label">🗳️ Status</span><span class="profile-info-value">{vstatus}</span></div>'
            + '</div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="section-label" style="margin-top:.8rem;">My Registered Elections</div>', unsafe_allow_html=True)
        regs = get_voter_elections(voter["email"])
        for reg in regs:
            conn = get_conn()
            vr   = conn.execute(
                "SELECT id FROM voters WHERE election_id=? AND email=?",
                (reg["election_id"], voter["email"])
            ).fetchone()
            conn.close()
            rv = get_voter_vote(vr[0], reg["election_id"]) if vr else None
            st.markdown(
                f'<div class="card-flat" style="padding:.8rem 1.1rem;margin-bottom:.4rem;">'
                f'<div style="display:flex;align-items:center;gap:.6rem;">'
                f'<div style="flex:1;"><div style="font-weight:600;font-size:.88rem;">{reg["election_name"]}</div>'
                f'<div style="font-size:.72rem;color:#cc5de8;">{reg["org_name"]}</div></div>'
                f'{sbadge(reg["election_status"])}&nbsp;'
                + (f'<span class="voted-badge" style="font-size:.68rem;">✓ Voted</span>'
                   if rv else '<span style="font-size:.72rem;color:#f5c842;">⏳ Pending</span>')
                + '</div></div>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────────────────
#  PUBLIC RESULTS
# ─────────────────────────────────────────────────────────
def page_public_results():
    render_header("Election Results")
    view_id = st.session_state.get("viewing_election")
    if not view_id:
        st.info("Select an election to view results."); nav("home"); return

    election = get_election(view_id)
    if not election:
        st.error("Election not found."); nav("home"); return

    conn = get_conn()
    org  = conn.execute("SELECT name FROM organizations WHERE id=?", (election["org_id"],)).fetchone()
    conn.close()

    st.markdown(
        f'<div class="card-flat" style="margin-bottom:.9rem;">'
        f'<div class="section-label">Election</div>'
        f'<span style="font-family:\'Playfair Display\',serif;font-size:1.25rem;font-weight:700;">{election["name"]}</span>'
        f'&nbsp;{sbadge(election["status"])}'
        f'<div style="font-size:.75rem;color:#cc5de8;margin-top:.2rem;">🏢 {org["name"] if org else "—"}</div>'
        + (f'<div class="cand-bio" style="margin-top:.2rem;">{election["description"]}</div>' if election.get("description") else "")
        + '</div>',
        unsafe_allow_html=True
    )

    df    = get_results(view_id)
    total = int(df["votes"].sum())

    st.download_button(
        "📥 Download Results CSV",
        data=results_to_csv(view_id, election["name"]),
        file_name=f"{election['name'].replace(' ','_')}_results.csv",
        mime="text/csv"
    )

    if total == 0:
        st.info("No votes cast yet.")
        if st.button("← Back"): nav("home")
        return

    winner = df.iloc[0]
    w_pct  = round(winner["votes"] / total * 100, 1)
    st.markdown(
        f'<div class="card" style="background:linear-gradient(135deg,{winner["color"]}18,#161923);'
        f'border-color:{winner["color"]}50;padding:1.6rem;margin-bottom:.9rem;">'
        f'<div class="section-label">🏆 Current Leader</div>'
        f'<div style="display:flex;align-items:center;gap:.9rem;margin-top:.3rem;">'
        f'<div style="font-size:2.4rem;">{winner["emoji"]}</div>'
        f'<div><div style="font-family:\'Playfair Display\',serif;font-size:1.5rem;font-weight:700;">{winner["name"]}</div>'
        f'<div class="cand-party" style="background:{winner["color"]}22;color:{winner["color"]};">{winner["party"]}</div></div>'
        f'<div style="margin-left:auto;text-align:right;">'
        f'<div class="metric-num">{winner["votes"]}</div>'
        f'<div class="metric-label">Votes ({w_pct}%)</div></div>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    fig = pgo.Figure()
    for _, row in df.iterrows():
        pct = round(row["votes"] / total * 100, 1) if total else 0
        fig.add_trace(pgo.Bar(
            x=[row["name"]], y=[row["votes"]],
            marker=dict(color=row["color"], opacity=.9, line=dict(color="rgba(0,0,0,0)", width=0)),
            text=[f"{row['votes']} ({pct}%)"], textposition="outside",
            textfont=dict(color="#e8e8e8", size=11),
            hovertemplate=f"<b>{row['name']}</b><br>{row['votes']} votes ({pct}%)<extra></extra>"
        ))
    fig.update_layout(
        plot_bgcolor="#161923", paper_bgcolor="#161923",
        font=dict(family="DM Sans", color="#e8e8e8"),
        showlegend=False, bargap=.35, height=300,
        margin=dict(t=16, b=8, l=0, r=0),
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#2a2f42", showline=False, zeroline=False,
                   title=dict(text="Votes", font=dict(color="#6b7080")))
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label" style="margin-top:.6rem;">Breakdown</div>', unsafe_allow_html=True)
    for _, row in df.iterrows():
        pct = round(row["votes"] / total * 100, 1) if total else 0
        st.markdown(
            f'<div class="card-flat" style="margin-bottom:.35rem;">'
            f'<div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.3rem;">'
            f'<span style="font-size:1.25rem;">{row["emoji"]}</span>'
            f'<span style="font-weight:600;flex:1;font-size:.88rem;">{row["name"]}</span>'
            f'<span class="cand-party" style="background:{row["color"]}22;color:{row["color"]};">{row["party"]}</span>'
            f'<span style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;color:{row["color"]};">{row["votes"]}</span>'
            f'</div>'
            f'<div style="background:#2a2f42;border-radius:999px;height:6px;overflow:hidden;">'
            f'<div style="background:{row["color"]};width:{pct}%;height:100%;border-radius:999px;"></div></div>'
            f'<div style="font-size:.71rem;color:#6b7080;margin-top:2px;">{pct}% of total votes</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    if st.button("← Back"): nav("home")