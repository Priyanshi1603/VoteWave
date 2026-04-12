"""
pages_super.py — Super Admin pages (platform-level management)
Includes: Organizations, Admin Request Approvals, All Admins, Overview
"""
import streamlit as st
from database import get_conn
from helpers import (
    get_all_orgs, get_org_admins, get_elections,
    create_org, update_org, delete_org, delete_org_admin,
    login_super_admin,
    get_admin_requests, approve_admin_request,
    reject_admin_request, delete_admin_request,
    pending_request_count,
)
from ui import render_header, metric, sbadge, nav


# ═══════════════════════════════════════════════════════
#  SUPER ADMIN LOGIN
# ═══════════════════════════════════════════════════════
def page_super_login():
    render_header("Super Admin Access")
    col, _ = st.columns([1, 1.5])
    with col:
        st.markdown('<div class="card"><div class="section-label">Platform Administrator</div>', unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        st.markdown("</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⚡ Login as Super Admin"):
                if login_super_admin(u, p):
                    import datetime as _dt
                    st.session_state.is_super      = True
                    st.session_state["session_start"] = _dt.datetime.now().isoformat()
                    nav("super_orgs")
                else:
                    st.error("Invalid credentials.")
        with c2:
            if st.button("← Back"): nav("home")
        st.markdown('<div class="cand-bio" style="margin-top:.6rem;">Default: <code>superadmin</code> / <code>super123</code></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  ADMIN REQUESTS  (pending approval queue)
# ═══════════════════════════════════════════════════════
def page_super_requests():
    if not st.session_state.is_super: nav("home")
    render_header("Admin Registration Requests")

    pending = pending_request_count()
    if pending > 0:
        st.markdown(
            f'<div class="card-flat" style="border-color:#cc5de840;margin-bottom:1rem;">'
            f'<div style="color:#cc5de8;font-weight:600;">📥 {pending} pending request{"s" if pending>1 else ""} awaiting your review</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Filter tabs
    filter_tab1, filter_tab2, filter_tab3 = st.tabs(["⏳ Pending", "✅ Approved", "❌ Rejected"])

    for tab, status_filter in [(filter_tab1,"pending"),(filter_tab2,"approved"),(filter_tab3,"rejected")]:
        with tab:
            requests = get_admin_requests(status=status_filter)
            if not requests:
                st.info(f"No {status_filter} requests.")
                continue

            for req in requests:
                with st.container():
                    rc1, rc2 = st.columns([4, 2])
                    with rc1:
                        st.markdown(
                            f'<div style="padding:.3rem 0;">'
                            f'<span style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;">{req["name"]}</span>'
                            f'&nbsp;{sbadge(req["status"])}</div>'
                            f'<div style="font-size:.8rem;color:#8a8fa8;">@{req["username"]} · {req["email"]}</div>'
                            f'<div style="font-size:.75rem;color:#cc5de8;margin-top:1px;">🏢 {req["org_name"]}</div>'
                            + (f'<div class="cand-bio" style="margin-top:.3rem;"><strong>Reason:</strong> {req["reason"]}</div>' if req.get("reason") else "")
                            + f'<div style="font-size:.7rem;color:#6b7080;margin-top:.2rem;">Submitted: {req["created_at"][:16]}</div>'
                            + (f'<div style="font-size:.7rem;color:#6b7080;">Reviewed by: {req["reviewed_by"]} · {req["reviewed_at"][:16] if req.get("reviewed_at") else "—"}</div>' if req.get("reviewed_by") else "")
                            + (f'<div class="cand-bio" style="margin-top:.2rem;"><em>Note: {req["review_note"]}</em></div>' if req.get("review_note") else ""),
                            unsafe_allow_html=True
                        )
                    with rc2:
                        if status_filter == "pending":
                            note = st.text_input("Note (optional)", key=f"note_{req['id']}",
                                                 placeholder="e.g. Verified identity")
                            ap1, ap2, ap3 = st.columns(3)
                            with ap1:
                                if st.button("✅ Approve", key=f"approve_{req['id']}"):
                                    ok, msg = approve_admin_request(req["id"], "superadmin", note)
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with ap2:
                                if st.button("❌ Reject", key=f"reject_{req['id']}"):
                                    reject_admin_request(req["id"], "superadmin", note)
                                    st.success("Request rejected.")
                                    st.rerun()
                            with ap3:
                                if st.button("🗑️", key=f"del_req_{req['id']}"):
                                    delete_admin_request(req["id"])
                                    st.rerun()
                        else:
                            if st.button("🗑️ Delete", key=f"del_req2_{req['id']}"):
                                delete_admin_request(req["id"]); st.rerun()
                    st.markdown("<hr>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  ORGANIZATIONS
# ═══════════════════════════════════════════════════════
def page_super_orgs():
    if not st.session_state.is_super: nav("home")
    render_header("Organizations")

    with st.expander("➕ Create Organization", expanded=False):
        o1, o2 = st.columns(2)
        with o1: oname = st.text_input("Organization Name *", key="new_org_name")
        with o2: odesc = st.text_input("Description", key="new_org_desc")
        if st.button("✅ Create", key="create_org"):
            if not oname.strip(): st.error("Name required.")
            else:
                ok, result = create_org(oname.strip(), odesc.strip())
                if ok: st.success(f"Organization '{oname}' created!"); st.rerun()
                else:  st.error(result)

    orgs = get_all_orgs()
    if not orgs:
        st.info("No organizations yet.")
        return

    for org in orgs:
        admins    = get_org_admins(org["id"])
        elections = get_elections(org["id"])
        with st.container():
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(
                    f'<div style="padding:.3rem 0;">'
                    f'<span style="font-family:\'Playfair Display\',serif;font-size:1.05rem;font-weight:700;">{org["name"]}</span>'
                    f'&nbsp;<span class="org-badge">{org["slug"]}</span></div>'
                    + (f'<div class="cand-bio">{org["description"]}</div>' if org.get("description") else "")
                    + f'<div style="font-size:.72rem;color:#6b7080;margin-top:2px;">👤 {len(admins)} admins · 🗳️ {len(elections)} elections</div>',
                    unsafe_allow_html=True
                )
            with c2:
                if st.button("✏️ Edit", key=f"edit_org_{org['id']}"):
                    st.session_state["editing_org"] = org["id"]; st.rerun()
            with c3:
                if st.button("🗑️ Delete", key=f"del_org_{org['id']}"):
                    st.session_state[f"confirm_del_org_{org['id']}"] = True; st.rerun()

            if st.session_state.get(f"confirm_del_org_{org['id']}"):
                st.warning(f"⚠️ Delete **{org['name']}**? ALL data (admins, elections, voters, votes) will be erased.")
                dy, dn = st.columns(2)
                with dy:
                    if st.button("Yes, Delete", key=f"yes_dorg_{org['id']}"):
                        delete_org(org["id"]); st.success("Deleted."); st.rerun()
                with dn:
                    if st.button("Cancel", key=f"no_dorg_{org['id']}"):
                        del st.session_state[f"confirm_del_org_{org['id']}"]; st.rerun()

            if st.session_state.get("editing_org") == org["id"]:
                st.markdown('<div class="card-flat">', unsafe_allow_html=True)
                eu1, eu2 = st.columns(2)
                with eu1: uoname = st.text_input("Name", value=org["name"], key=f"uoname_{org['id']}")
                with eu2: uodesc = st.text_input("Description", value=org.get("description","") or "", key=f"uodesc_{org['id']}")
                st.markdown("</div>", unsafe_allow_html=True)
                sv1, sv2 = st.columns(2)
                with sv1:
                    if st.button("💾 Save", key=f"save_org_{org['id']}"):
                        update_org(org["id"], uoname, uodesc)
                        del st.session_state["editing_org"]; st.success("Updated!"); st.rerun()
                with sv2:
                    if st.button("Cancel", key=f"cancel_org_{org['id']}"):
                        del st.session_state["editing_org"]; st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  ALL ADMINS
# ═══════════════════════════════════════════════════════
def page_super_admins():
    if not st.session_state.is_super: nav("home")
    render_header("All Org Admins")
    orgs = get_all_orgs()
    if not orgs:
        st.info("No organizations yet."); return

    for org in orgs:
        st.markdown(f'<div class="section-label">{org["name"]}</div>', unsafe_allow_html=True)
        admins = get_org_admins(org["id"])
        if not admins:
            st.markdown('<div class="cand-bio" style="margin-bottom:.5rem;">No admins yet.</div>', unsafe_allow_html=True)
        for a in admins:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:.7rem;padding:.25rem 0;">'
                    f'<div><div style="font-weight:600;">{a["name"]}</div>'
                    f'<div style="font-size:.78rem;color:#6b7080;">@{a["username"]} · {a["email"]} · {a["role"].title()}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
            with c2:
                if st.button("🗑️", key=f"del_sa_{a['id']}"):
                    delete_org_admin(a["id"]); st.success("Removed."); st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  PLATFORM OVERVIEW
# ═══════════════════════════════════════════════════════
def page_super_overview():
    if not st.session_state.is_super: nav("home")
    render_header("Platform Overview")

    orgs = get_all_orgs()
    conn = get_conn()
    total_orgs      = len(orgs)
    total_admins    = conn.execute("SELECT COUNT(*) FROM org_admins").fetchone()[0]
    total_elections = conn.execute("SELECT COUNT(*) FROM elections").fetchone()[0]
    total_voters    = conn.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
    total_votes     = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    total_pending   = conn.execute("SELECT COUNT(*) FROM admin_requests WHERE status='pending'").fetchone()[0]
    conn.close()

    c1,c2,c3 = st.columns(3)
    metric("Organizations",    total_orgs,      c1)
    metric("Approved Admins",  total_admins,     c2)
    metric("Pending Requests", total_pending,    c3)

    c4,c5,c6 = st.columns(3)
    metric("Elections",        total_elections, c4)
    metric("Registered Voters",total_voters,    c5)
    metric("Votes Cast",       total_votes,     c6)

    if total_pending > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning(f"⚠️ You have **{total_pending}** pending admin request(s) waiting for review.")
        if st.button("📥 Review Requests"): nav("super_requests")