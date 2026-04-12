"""
pages_admin.py — Org Admin pages
Registration is now a request system — super admin must approve before login is allowed.
Voter registration requires email OTP verification.
"""
import streamlit as st
import io
import time
import plotly.express as px
import plotly.graph_objects as pgo
from datetime import datetime
from database import get_conn
from helpers import (
    get_all_orgs, get_org, get_org_admins,
    get_elections, get_election,
    get_candidates, get_results, get_stats, get_voters_for_election,
    create_election, update_election, delete_election, set_election_status,
    add_candidate, update_candidate, delete_candidate,
    reset_election_voters, reset_election_votes, delete_voter,
    register_org_admin, login_org_admin, update_org_admin, delete_org_admin,
    submit_admin_request,
    results_to_csv, COLORS, EMOJIS
)
from ui import render_header, metric, sbadge, nav, render_countdown


# ═══════════════════════════════════════════════════════
#  ADMIN REGISTER  (submit a request, await approval)
# ═══════════════════════════════════════════════════════
def page_admin_register():
    render_header("Admin Registration")
    orgs = get_all_orgs()
    if not orgs:
        st.warning("No organizations exist yet. Contact the platform super admin to create one.")
        if st.button("← Back"): nav("home")
        return

    col, _ = st.columns([1.4, 1])
    with col:
        # ── Info banner ──────────────────────────────
        st.markdown(
            '<div class="card-flat" style="border-color:#cc5de840;margin-bottom:1rem;">'
            '<div style="font-size:.82rem;color:#cc5de8;font-weight:600;margin-bottom:.3rem;">📋 How it works</div>'
            '<div class="cand-bio">Fill in your details and submit a registration request. '
            'A <strong style="color:#f5c842;">super admin</strong> will review and approve your account. '
            'You will be able to log in only after approval.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="card"><div class="section-label">Request Admin Access</div>', unsafe_allow_html=True)
        org_map  = {o["id"]: o["name"] for o in orgs}
        sel_org  = st.selectbox("Organization *", list(org_map.keys()), format_func=lambda x: org_map[x])
        name     = st.text_input("Full Name *")
        username = st.text_input("Username *")
        email    = st.text_input("Work / Official Email *",
                                 help="Use a real email — a super admin will verify your identity.")
        password = st.text_input("Password *", type="password")
        confirm  = st.text_input("Confirm Password", type="password")
        reason   = st.text_area("Reason / Purpose *",
                                placeholder="Briefly explain why you need admin access for this organization…",
                                height=80,
                                help="This helps the super admin verify your request.")
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1: submit = st.button("📤 Submit Request")
        with c2:
            if st.button("← Back"): nav("home")

        if submit:
            if not all([name, username, email, password, sel_org, reason.strip()]):
                st.error("All fields including the reason are required.")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, msg = submit_admin_request(sel_org, name, username, email, password, reason.strip())
                if ok:
                    st.success("✅ Request submitted successfully!")
                    st.markdown(
                        '<div class="card-flat" style="border-color:#2ec27e40;margin-top:.8rem;">'
                        '<div style="color:#2ec27e;font-weight:600;margin-bottom:.3rem;">What happens next?</div>'
                        '<div class="cand-bio">'
                        '1. The super admin will review your request.<br>'
                        '2. Once approved, your account will be activated.<br>'
                        '3. You can then log in with your username and password.<br>'
                        '<span style="color:#f5c842;">Check back here to try logging in.</span>'
                        '</div></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error(msg)


# ═══════════════════════════════════════════════════════
#  ADMIN LOGIN  (only approved accounts can log in)
# ═══════════════════════════════════════════════════════
def page_admin_login():
    render_header("Admin Login")
    col, _ = st.columns([1.2, 1])
    with col:
        st.markdown('<div class="card"><div class="section-label">Organization Admin</div>', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔐 Login"):
                if not username or not password:
                    st.error("Please enter your username and password.")
                else:
                    admin = login_org_admin(username, password)
                    if admin:
                        st.session_state.admin = admin
                        st.session_state["session_start"] = datetime.now().isoformat()
                        nav("admin_panel")
                    else:
                        # Check if there's a pending/rejected request to give helpful feedback
                        conn = get_conn()
                        req = conn.execute(
                            "SELECT status FROM admin_requests WHERE username=?", (username,)
                        ).fetchone()
                        conn.close()
                        if req:
                            if req["status"] == "pending":
                                st.warning("⏳ Your registration request is still **pending approval** by the super admin. Please check back later.")
                            elif req["status"] == "rejected":
                                st.error("❌ Your registration request was **rejected**. Contact the super admin for details.")
                            else:
                                st.error("Invalid password.")
                        else:
                            st.error("Invalid credentials. Not registered? Submit a request below.")
        with c2:
            if st.button("← Back"): nav("home")

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            if st.button("📝 Request Admin Access"): nav("admin_register")
        with c4:
            if st.button("⚡ Super Admin"): nav("super_login")


# ═══════════════════════════════════════════════════════
#  ADMIN PROFILE
# ═══════════════════════════════════════════════════════
def page_admin_profile():
    if not st.session_state.admin: nav("admin_login")
    a   = st.session_state.admin
    org = get_org(a["org_id"])
    render_header("Admin Profile")
    col_l, col_r = st.columns([1, 1.6], gap="large")

    with col_l:
        initials = "".join(p[0].upper() for p in a["name"].split()[:2])
        st.markdown(
            f'<div class="profile-hero">'
            f'<div class="profile-avatar-big">{initials}</div>'
            f'<div class="profile-name">{a["name"]}</div>'
            f'<div style="margin:.3rem 0 .5rem;"><span class="org-badge">{org["name"] if org else "—"}</span></div>'
            f'<div style="font-size:.78rem;color:#6b7080;">@{a["username"]} · {a["role"].title()}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_r:
        st.markdown('<div class="section-label">Account Details</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card" style="padding:1rem 1.3rem;">'
            + f'<div class="profile-info-row"><span class="profile-info-label">👤 Name</span><span class="profile-info-value">{a["name"]}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">🔑 Username</span><span class="profile-info-value">@{a["username"]}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">📧 Email</span><span class="profile-info-value">{a["email"]}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">🏢 Organization</span><span class="profile-info-value">{org["name"] if org else "—"}</span></div>'
            + f'<div class="profile-info-row"><span class="profile-info-label">🎖️ Role</span><span class="profile-info-value">{a["role"].title()}</span></div>'
            + f'<div class="profile-info-row" style="border:none;"><span class="profile-info-label">📅 Joined</span><span class="profile-info-value">{a["created_at"][:10]}</span></div>'
            + '</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div class="section-label" style="margin-top:.8rem;">Update Password</div>', unsafe_allow_html=True)
        with st.expander("🔒 Change Password"):
            np1 = st.text_input("New Password", type="password", key="ap_np1")
            np2 = st.text_input("Confirm New Password", type="password", key="ap_np2")
            if st.button("Update Password", key="ap_update"):
                if not np1 or np1 != np2:
                    st.error("Passwords must match.")
                elif len(np1) < 6:
                    st.error("Minimum 6 characters.")
                else:
                    update_org_admin(a["id"], a["name"], a["email"], a["role"], new_pw=np1)
                    st.success("Password updated!")


# ═══════════════════════════════════════════════════════
#  ADMIN PANEL  (full dashboard)
# ═══════════════════════════════════════════════════════
def page_admin_panel():
    if not st.session_state.admin: nav("admin_login")
    a      = st.session_state.admin
    org    = get_org(a["org_id"])
    org_id = a["org_id"]

    render_header(f"Admin Dashboard — {org['name'] if org else ''}")
    c1h, c2h = st.columns([5, 1])
    with c2h:
        if st.button("🚪 Logout", key="adm_logout"):
            st.session_state.admin = None; nav("home")

    active_elections = get_elections(org_id, "active")
    if active_elections:
        sel_active_id = st.session_state.get("admin_sel_active", active_elections[0]["id"])
        if len(active_elections) > 1:
            emap = {e["id"]: e["name"] for e in active_elections}
            sel_active_id = st.selectbox("View stats for:", list(emap.keys()),
                                         format_func=lambda x: emap[x], key="admin_sel_active")
        stats = get_stats(sel_active_id)
    else:
        stats = {"total_voters":0,"total_voted":0,"total_cands":0,"turnout_pct":0}

    mc1, mc2, mc3, mc4 = st.columns(4)
    metric("Registered Voters", stats["total_voters"], mc1)
    metric("Votes Cast",        stats["total_voted"],  mc2)
    metric("Candidates",        stats["total_cands"],  mc3)
    metric("Turnout",           f"{stats['turnout_pct']}%", mc4)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs(["🗳️ Elections","👤 Candidates","📊 Results","👥 Voters","👮 Admins","⚙️ System"])

    # ════════════════════════════════
    #  TAB 1 — ELECTIONS
    # ════════════════════════════════
    with tab1:
        st.markdown('<div class="section-label">Manage Elections</div>', unsafe_allow_html=True)
        with st.expander("➕ Create New Election", expanded=False):
            ne1, ne2 = st.columns(2)
            with ne1:
                ename   = st.text_input("Election Name *", key="ne_name")
                estatus = st.selectbox("Status", ["draft","active","closed"], key="ne_status")
            with ne2:
                estart = st.text_input("Start (YYYY-MM-DD HH:MM)", key="ne_start")
                eend   = st.text_input("End   (YYYY-MM-DD HH:MM)", key="ne_end")
            edesc = st.text_area("Description", key="ne_desc", height=68)
            if st.button("✅ Create Election", key="create_election"):
                if not ename.strip(): st.error("Name required.")
                else:
                    create_election(org_id, ename.strip(), edesc.strip(), estatus, estart.strip(), eend.strip())
                    st.success(f"'{ename}' created!"); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        elections = get_elections(org_id)
        if not elections:
            st.info("No elections yet.")
        else:
            for e in elections:
                ccount = len(get_candidates(e["id"]))
                vcount = get_stats(e["id"])["total_voted"]
                ea,eb,ec,ed,ee = st.columns([3.5,1.1,.8,1,.7])
                with ea:
                    st.markdown(
                        f'<span style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;">{e["name"]}</span>'
                        f'&nbsp;{sbadge(e["status"])}'
                        + (f'<div class="cand-bio">{e["description"]}</div>' if e.get("description") else "")
                        + f'<div style="font-size:.7rem;color:#6b7080;margin-top:2px;">📋 {ccount} candidates · 🗳️ {vcount} votes · {e["created_at"][:10]}</div>',
                        unsafe_allow_html=True
                    )
                with eb:
                    ns = st.selectbox("", ["draft","active","closed"],
                                      index=["draft","active","closed"].index(e["status"]),
                                      key=f"es_{e['id']}", label_visibility="collapsed")
                    if ns != e["status"]: set_election_status(e["id"], ns); st.rerun()
                with ec:
                    if st.button("✏️", key=f"ee_{e['id']}"): st.session_state["edit_e"]=e["id"]; st.rerun()
                with ed:
                    st.download_button("📥 CSV",
                                       data=results_to_csv(e["id"], e["name"]),
                                       file_name=f"{e['name'].replace(' ','_')}_results.csv",
                                       mime="text/csv", key=f"csv_{e['id']}")
                with ee:
                    if st.button("🗑️", key=f"de_{e['id']}"): st.session_state[f"confirm_del_e_{e['id']}"]=True; st.rerun()

                if st.session_state.get(f"confirm_del_e_{e['id']}"):
                    st.warning(f"Delete **{e['name']}**? All candidates, voters and votes will be erased.")
                    dy,dn = st.columns(2)
                    with dy:
                        if st.button("Yes, Delete", key=f"yde_{e['id']}"):
                            delete_election(e["id"]); del st.session_state[f"confirm_del_e_{e['id']}"]; st.success("Deleted."); st.rerun()
                    with dn:
                        if st.button("Cancel", key=f"nde_{e['id']}"): del st.session_state[f"confirm_del_e_{e['id']}"]; st.rerun()

                if st.session_state.get("edit_e") == e["id"]:
                    st.markdown('<div class="card-flat">', unsafe_allow_html=True)
                    eu1,eu2 = st.columns(2)
                    with eu1:
                        un = st.text_input("Name", value=e["name"], key=f"un_{e['id']}")
                        us = st.selectbox("Status", ["draft","active","closed"],
                                          index=["draft","active","closed"].index(e["status"]), key=f"us_{e['id']}")
                    with eu2:
                        ust = st.text_input("Start", value=e.get("start_date","") or "", key=f"ust_{e['id']}")
                        uen = st.text_input("End",   value=e.get("end_date","")   or "", key=f"uen_{e['id']}")
                    ud = st.text_area("Description", value=e.get("description","") or "", key=f"ud_{e['id']}", height=60)
                    st.markdown("</div>", unsafe_allow_html=True)
                    sv1,sv2 = st.columns(2)
                    with sv1:
                        if st.button("💾 Save", key=f"se_{e['id']}"):
                            update_election(e["id"],un,ud,us,ust,uen)
                            del st.session_state["edit_e"]; st.success("Updated!"); st.rerun()
                    with sv2:
                        if st.button("Cancel", key=f"ce_{e['id']}"): del st.session_state["edit_e"]; st.rerun()
                st.markdown("<hr>", unsafe_allow_html=True)

    # ════════════════════════════════
    #  TAB 2 — CANDIDATES
    # ════════════════════════════════
    with tab2:
        elections = get_elections(org_id)
        if not elections:
            st.info("Create an election first.")
        else:
            emap    = {e["id"]: f"{e['name']} [{e['status'].upper()}]" for e in elections}
            sel_eid = st.selectbox("Election", list(emap.keys()), format_func=lambda x: emap[x], key="cand_sel")
            with st.expander("➕ Add Candidate", expanded=False):
                ac1,ac2 = st.columns(2)
                with ac1:
                    cn = st.text_input("Name *",  key="nc_name")
                    cp = st.text_input("Party *", key="nc_party")
                with ac2:
                    ce = st.selectbox("Emoji", EMOJIS, key="nc_emoji")
                    cc = st.selectbox("Color", COLORS, key="nc_color")
                cb = st.text_area("Bio", key="nc_bio", height=68)
                if st.button("✅ Add", key="add_cand"):
                    if not cn.strip() or not cp.strip(): st.error("Name and party required.")
                    else:
                        add_candidate(sel_eid, cn.strip(), cp.strip(), cb.strip(), ce, cc)
                        st.success(f"'{cn}' added!"); st.rerun()

            cands = get_candidates(sel_eid)
            if not cands: st.info("No candidates yet.")
            for cand in cands:
                cc1,cc2,cc3 = st.columns([4,.9,.9])
                with cc1:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:.7rem;padding:.2rem 0;">'
                        f'<div style="font-size:1.6rem;background:{cand["color"]}22;border-radius:50%;'
                        f'width:40px;height:40px;display:flex;align-items:center;justify-content:center;">{cand["emoji"]}</div>'
                        f'<div><div style="font-weight:700;font-size:.92rem;">{cand["name"]}</div>'
                        f'<div class="cand-party" style="background:{cand["color"]}22;color:{cand["color"]};">{cand["party"]}</div>'
                        + (f'<div class="cand-bio">{cand["bio"]}</div>' if cand.get("bio") else "")
                        + '</div></div>', unsafe_allow_html=True
                    )
                with cc2:
                    if st.button("✏️", key=f"ec_{cand['id']}"): st.session_state["edit_c"]=cand["id"]; st.rerun()
                with cc3:
                    if st.button("🗑️", key=f"dc_{cand['id']}"): st.session_state[f"confirm_dc_{cand['id']}"]=True; st.rerun()

                if st.session_state.get(f"confirm_dc_{cand['id']}"):
                    st.warning(f"Delete **{cand['name']}**?")
                    dy,dn = st.columns(2)
                    with dy:
                        if st.button("Yes", key=f"ydc_{cand['id']}"):
                            delete_candidate(cand["id"]); del st.session_state[f"confirm_dc_{cand['id']}"]; st.rerun()
                    with dn:
                        if st.button("No",  key=f"ndc_{cand['id']}"): del st.session_state[f"confirm_dc_{cand['id']}"]; st.rerun()

                if st.session_state.get("edit_c") == cand["id"]:
                    st.markdown('<div class="card-flat">', unsafe_allow_html=True)
                    e1,e2 = st.columns(2)
                    with e1:
                        ucn = st.text_input("Name",  value=cand["name"],  key=f"ucn_{cand['id']}")
                        ucp = st.text_input("Party", value=cand["party"], key=f"ucp_{cand['id']}")
                    with e2:
                        uce = st.selectbox("Emoji", EMOJIS, index=EMOJIS.index(cand["emoji"]) if cand["emoji"] in EMOJIS else 0, key=f"uce_{cand['id']}")
                        ucc = st.selectbox("Color", COLORS, index=COLORS.index(cand["color"]) if cand["color"] in COLORS else 0, key=f"ucc_{cand['id']}")
                    ucb = st.text_area("Bio", value=cand.get("bio","") or "", key=f"ucb_{cand['id']}", height=60)
                    st.markdown("</div>", unsafe_allow_html=True)
                    s1,s2 = st.columns(2)
                    with s1:
                        if st.button("💾 Save", key=f"sc_{cand['id']}"):
                            update_candidate(cand["id"],ucn,ucp,ucb,uce,ucc)
                            del st.session_state["edit_c"]; st.success("Updated!"); st.rerun()
                    with s2:
                        if st.button("Cancel", key=f"cancelc_{cand['id']}"): del st.session_state["edit_c"]; st.rerun()
                st.markdown("<hr>", unsafe_allow_html=True)

    # ════════════════════════════════
    #  TAB 3 — RESULTS
    # ════════════════════════════════
    with tab3:
        elections = get_elections(org_id)
        if not elections:
            st.info("No elections yet.")
        else:
            emap    = {e["id"]: f"{e['name']} [{e['status'].upper()}]" for e in elections}
            res_eid = st.selectbox("Select Election", list(emap.keys()), format_func=lambda x: emap[x], key="res_sel")
            df      = get_results(res_eid)
            total   = int(df["votes"].sum())
            rel     = get_election(res_eid)
            st.download_button("📥 Download Results CSV",
                               data=results_to_csv(res_eid, rel["name"]),
                               file_name=f"{rel['name'].replace(' ','_')}_results.csv",
                               mime="text/csv", key="dl_res_tab")
            if total == 0:
                st.info("No votes cast yet.")
            else:
                col_chart, col_table = st.columns([1.2,1], gap="large")
                with col_chart:
                    fig = px.pie(df, names="name", values="votes",
                                 color_discrete_sequence=df["color"].tolist(), hole=0.52)
                    fig.update_traces(textinfo="label+percent", textfont=dict(family="DM Sans",size=11))
                    fig.update_layout(paper_bgcolor="#161923", plot_bgcolor="#161923",
                                      font=dict(color="#e8e8e8"), showlegend=False,
                                      margin=dict(t=8,b=8,l=0,r=0), height=260)
                    st.plotly_chart(fig, use_container_width=True)
                with col_table:
                    st.markdown('<div class="section-label">Vote Count</div>', unsafe_allow_html=True)
                    for _, row in df.iterrows():
                        pct = round(row["votes"]/total*100,1) if total else 0
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:.5rem;padding:.4rem 0;border-bottom:1px solid #2a2f42;">'
                            f'<span>{row["emoji"]}</span><span style="flex:1;font-size:.85rem;">{row["name"]}</span>'
                            f'<span style="font-weight:700;color:{row["color"]};">{row["votes"]}</span>'
                            f'<span style="font-size:.72rem;color:#6b7080;min-width:34px;text-align:right;">{pct}%</span>'
                            f'</div>', unsafe_allow_html=True
                        )
                st.markdown("<br>", unsafe_allow_html=True)
                fig2 = pgo.Figure()
                for _, row in df.iterrows():
                    fig2.add_trace(pgo.Bar(x=[row["name"]], y=[row["votes"]],
                                           marker=dict(color=row["color"],opacity=.85),
                                           text=[row["votes"]], textposition="outside",
                                           textfont=dict(color="#e8e8e8")))
                fig2.update_layout(plot_bgcolor="#161923",paper_bgcolor="#161923",
                                   font=dict(family="DM Sans",color="#e8e8e8"),
                                   showlegend=False,bargap=.38,
                                   margin=dict(t=8,b=8,l=0,r=0),
                                   xaxis=dict(showgrid=False),
                                   yaxis=dict(gridcolor="#2a2f42",showline=False),height=260)
                st.plotly_chart(fig2, use_container_width=True)

    # ════════════════════════════════
    #  TAB 4 — VOTERS
    # ════════════════════════════════
    with tab4:
        elections = get_elections(org_id)
        if not elections:
            st.info("No elections yet.")
        else:
            emap  = {e["id"]: f"{e['name']} [{e['status'].upper()}]" for e in elections}
            v_eid = st.selectbox("Select Election", list(emap.keys()), format_func=lambda x: emap[x], key="v_sel")
            vdf   = get_voters_for_election(v_eid)

            c_search, c_reset, c_reset_votes, c_dl = st.columns([3,.9,1,1])
            with c_search:
                search = st.text_input("🔍 Search", placeholder="Name, email, voter ID…",
                                       key="v_search", label_visibility="collapsed")
            with c_reset:
                if st.button("🗑️ All Voters", key="reset_voters_btn"):
                    st.session_state["confirm_reset_voters"] = True; st.rerun()
            with c_reset_votes:
                if st.button("🗑️ Votes Only", key="reset_votes_btn"):
                    st.session_state["confirm_reset_votes"] = True; st.rerun()
            with c_dl:
                if not vdf.empty:
                    csv_buf = io.StringIO()
                    vdf.to_csv(csv_buf, index=False)
                    st.download_button("📥 Export", data=csv_buf.getvalue().encode(),
                                       file_name="voters.csv", mime="text/csv", key="dl_voters")

            if st.session_state.get("confirm_reset_voters"):
                st.warning("⚠️ Delete ALL voters AND votes for this election?")
                rc1,rc2 = st.columns(2)
                with rc1:
                    if st.button("Yes, Reset All", key="yes_rv"):
                        reset_election_voters(v_eid); del st.session_state["confirm_reset_voters"]
                        st.success("All voters reset."); st.rerun()
                with rc2:
                    if st.button("Cancel", key="no_rv"): del st.session_state["confirm_reset_voters"]; st.rerun()

            if st.session_state.get("confirm_reset_votes"):
                st.warning("⚠️ Delete all VOTES (voters stay registered)?")
                rc1,rc2 = st.columns(2)
                with rc1:
                    if st.button("Yes, Reset Votes", key="yes_rvt"):
                        reset_election_votes(v_eid); del st.session_state["confirm_reset_votes"]
                        st.success("All votes reset."); st.rerun()
                with rc2:
                    if st.button("Cancel", key="no_rvt"): del st.session_state["confirm_reset_votes"]; st.rerun()

            if vdf.empty:
                st.info("No voters registered for this election.")
            else:
                if search:
                    mask = vdf.apply(lambda r: search.lower() in r.to_string().lower(), axis=1)
                    vdf  = vdf[mask]
                st.dataframe(vdf, use_container_width=True, hide_index=True,
                             column_config={
                                 "voter_id":     st.column_config.TextColumn("Voter ID"),
                                 "name":         st.column_config.TextColumn("Name"),
                                 "email":        st.column_config.TextColumn("Email"),
                                 "email_status": st.column_config.TextColumn("Email"),
                                 "vote_status":  st.column_config.TextColumn("Vote"),
                                 "voted_for":    st.column_config.TextColumn("Voted For"),
                                 "created_at":   st.column_config.TextColumn("Registered"),
                             })

                with st.expander("🔧 Manage Individual Voter"):
                    conn = get_conn()
                    raw  = conn.execute("SELECT id, voter_id, name, email FROM voters WHERE election_id=?", (v_eid,)).fetchall()
                    conn.close()
                    if raw:
                        vmap    = {r[0]: f"{r[2]} ({r[3]})" for r in raw}
                        sel_vid = st.selectbox("Select Voter", list(vmap.keys()),
                                               format_func=lambda x: vmap[x], key="sel_vmanage")
                        mc1,mc2 = st.columns(2)
                        with mc1:
                            if st.button("🗑️ Remove This Voter", key="del_single_voter"):
                                delete_voter(sel_vid); st.success("Voter removed."); st.rerun()
                        with mc2:
                            if st.button("🔄 Reset Their Vote", key="reset_single_vote"):
                                conn = get_conn()
                                conn.execute("DELETE FROM votes WHERE voter_id=? AND election_id=?", (sel_vid, v_eid))
                                conn.commit(); conn.close()
                                st.success("Vote reset."); st.rerun()

    # ════════════════════════════════
    #  TAB 5 — ADMINS
    # ════════════════════════════════
    with tab5:
        st.markdown('<div class="section-label">Admins in this Organization</div>', unsafe_allow_html=True)
        with st.expander("➕ Add Admin Directly"):
            an = st.text_input("Full Name *", key="na_name")
            au = st.text_input("Username *",  key="na_user")
            ae = st.text_input("Email *",     key="na_email")
            ap = st.text_input("Password *",  type="password", key="na_pass")
            ar = st.selectbox("Role", ["admin","moderator"], key="na_role")
            if st.button("✅ Add Admin", key="add_admin_btn"):
                if not all([an,au,ae,ap]): st.error("All fields required.")
                else:
                    ok, msg = register_org_admin(org_id, an, au, ae, ap, ar)
                    if ok: st.success("Admin added!"); st.rerun()
                    else:  st.error(msg)

        admins = get_org_admins(org_id)
        if not admins:
            st.info("No admins yet.")
        for adm in admins:
            is_me = adm["id"] == a["id"]
            c1,c2,c3 = st.columns([4,1,1])
            with c1:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:.7rem;padding:.2rem 0;">'
                    f'<div style="width:36px;height:36px;border-radius:50%;background:#f5c84222;'
                    f'display:flex;align-items:center;justify-content:center;font-weight:700;">'
                    f'{"".join(p[0].upper() for p in adm["name"].split()[:2])}</div>'
                    f'<div><div style="font-weight:600;font-size:.92rem;">{adm["name"]} {"(You)" if is_me else ""}</div>'
                    f'<div style="font-size:.76rem;color:#6b7080;">@{adm["username"]} · {adm["email"]} · {adm["role"].title()}</div>'
                    f'</div></div>', unsafe_allow_html=True
                )
            with c2:
                if st.button("✏️", key=f"ea_{adm['id']}"): st.session_state["edit_a"]=adm["id"]; st.rerun()
            with c3:
                if not is_me:
                    if st.button("🗑️", key=f"da_{adm['id']}"): delete_org_admin(adm["id"]); st.success("Removed."); st.rerun()

            if st.session_state.get("edit_a") == adm["id"]:
                st.markdown('<div class="card-flat">', unsafe_allow_html=True)
                ua1,ua2 = st.columns(2)
                with ua1:
                    uan = st.text_input("Name",  value=adm["name"],  key=f"uan_{adm['id']}")
                    uae = st.text_input("Email", value=adm["email"], key=f"uae_{adm['id']}")
                with ua2:
                    uar = st.selectbox("Role", ["admin","moderator"],
                                       index=["admin","moderator"].index(adm["role"]) if adm["role"] in ["admin","moderator"] else 0,
                                       key=f"uar_{adm['id']}")
                    uap = st.text_input("New Password (leave blank to keep)", type="password", key=f"uap_{adm['id']}")
                st.markdown("</div>", unsafe_allow_html=True)
                sv1,sv2 = st.columns(2)
                with sv1:
                    if st.button("💾 Save", key=f"sa_{adm['id']}"):
                        update_org_admin(adm["id"],uan,uae,uar,uap if uap else None)
                        del st.session_state["edit_a"]; st.success("Updated!"); st.rerun()
                with sv2:
                    if st.button("Cancel", key=f"ca_{adm['id']}"): del st.session_state["edit_a"]; st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)

    # ════════════════════════════════
    #  TAB 6 — SYSTEM
    # ════════════════════════════════
    with tab6:
        org = get_org(org_id)
        st.markdown('<div class="section-label">Organization Info</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card-flat">'
            f'<div class="profile-info-row"><span class="profile-info-label">🏢 Name</span><span class="profile-info-value">{org["name"]}</span></div>'
            f'<div class="profile-info-row"><span class="profile-info-label">🔑 Slug</span><span class="profile-info-value">{org["slug"]}</span></div>'
            f'<div class="profile-info-row" style="border:none;"><span class="profile-info-label">📅 Created</span><span class="profile-info-value">{org["created_at"][:10]}</span></div>'
            f'</div>', unsafe_allow_html=True
        )
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown('<div class="section-label" style="margin-top:.9rem;">System</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-flat">'
            f'<div class="profile-info-row"><span class="profile-info-label">🗄️ Database</span><span class="profile-info-value">SQLite · votewave.db</span></div>'
            f'<div class="profile-info-row"><span class="profile-info-label">⚙️ Framework</span><span class="profile-info-value">Streamlit + Plotly</span></div>'
            f'<div class="profile-info-row" style="border:none;"><span class="profile-info-label">🕐 Server Time</span><span class="profile-info-value">{now_str}</span></div>'
            '</div>', unsafe_allow_html=True
        )