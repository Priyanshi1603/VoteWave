"""
app.py — VoteWave Entry Point
Run with: streamlit run app.py
"""
import streamlit as st
# ── Page config must be the very first Streamlit call ──
st.set_page_config(
    page_title="VoteWave",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import init_db
from ui import inject_css, init_session, render_sidebar, nav

# ── Super Admin pages ──
from pages_super import (
    page_super_login,
    page_super_orgs,
    page_super_requests,
    page_super_admins,
    page_super_overview,
)

# ── Org Admin pages ──
from pages_admin import (
    page_admin_register,
    page_admin_login,
    page_admin_profile,
    page_admin_panel,
)

# ── Voter-facing pages ──
from pages_voter import (
    page_home,
    page_voter_register,
    page_voter_login,
    page_my_elections,
    page_ballot,
    page_voter_profile,
    page_public_results,
)


def main():
    init_db()           # create / migrate tables
    inject_css()        # global CSS
    init_session()      # session state + timeout enforcement
    render_sidebar()    # left nav

    # ── Router ──
    p = st.session_state.page

    if   p == "home":             page_home()
    elif p == "voter_register":   page_voter_register()
    elif p == "voter_login":      page_voter_login()
    elif p == "my_elections":     page_my_elections()
    elif p == "ballot":           page_ballot()
    elif p == "voter_profile":    page_voter_profile()
    elif p == "public_results":   page_public_results()
    elif p == "admin_register":   page_admin_register()
    elif p == "admin_login":      page_admin_login()
    elif p == "admin_panel":      page_admin_panel()
    elif p == "admin_profile":    page_admin_profile()
    elif p == "super_login":      page_super_login()
    elif p == "super_orgs":       page_super_orgs()
    elif p == "super_requests":   page_super_requests()
    elif p == "super_admins":     page_super_admins()
    elif p == "super_overview":   page_super_overview()
    else:
        nav("home")


if __name__ == "__main__":
    main()
