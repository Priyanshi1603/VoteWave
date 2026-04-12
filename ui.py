"""
ui.py — CSS injection, countdown timer, sidebar, session management, shared UI helpers
"""
import streamlit as st
from datetime import datetime, timedelta
from helpers import get_org, pending_request_count


# ─────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');

html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:#0d0f14;color:#e8e8e8;}
.stApp{background:#0d0f14;}
#MainMenu,footer{visibility:hidden;}
header{visibility:visible;background:transparent!important;}
[data-testid="stHeader"]{background:transparent!important;}
.block-container{padding:1.8rem 2.5rem;max-width:1300px;margin:auto;}

.hero-title{font-family:'Playfair Display',serif;font-size:clamp(2rem,4.5vw,3.6rem);font-weight:900;
  background:linear-gradient(135deg,#f5c842 0%,#ff6b35 60%,#e63946 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  line-height:1.1;margin-bottom:0.2rem;}
.hero-sub{font-size:.95rem;color:#8a8fa8;letter-spacing:.06em;text-transform:uppercase;margin-bottom:1.6rem;}

.card{background:#161923;border:1px solid #2a2f42;border-radius:14px;padding:1.4rem 1.6rem;
  margin-bottom:.9rem;transition:border-color .25s,transform .2s,box-shadow .25s;
  position:relative;overflow:hidden;}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#f5c842,#ff6b35,#e63946);opacity:0;transition:opacity .3s;}
.card:hover::before{opacity:1;}
.card:hover{border-color:#f5c84250;transform:translateY(-2px);box-shadow:0 8px 28px rgba(245,200,66,.07);}
.card-flat{background:#161923;border:1px solid #2a2f42;border-radius:12px;
  padding:1.1rem 1.4rem;margin-bottom:.7rem;}

.cand-avatar{width:58px;height:58px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:1.6rem;margin-bottom:.5rem;}
.cand-name{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#f0f0f0;margin-bottom:.1rem;}
.cand-party{font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  padding:2px 8px;border-radius:20px;display:inline-block;margin-bottom:.4rem;}
.cand-bio{font-size:.83rem;color:#7a7f96;line-height:1.6;}

.metric-pill{background:#1e2333;border-radius:11px;padding:.9rem 1rem;text-align:center;border:1px solid #2a2f42;}
.metric-num{font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:900;color:#f5c842;}
.metric-label{font-size:.68rem;color:#6b7080;text-transform:uppercase;letter-spacing:.1em;}

.stButton>button{font-family:'DM Sans',sans-serif!important;font-weight:600!important;
  border-radius:9px!important;border:none!important;padding:.5rem 1rem!important;
  background:linear-gradient(135deg,#f5c842,#ff6b35)!important;color:#0d0f14!important;
  transition:opacity .2s,transform .15s!important;}
.stButton>button:hover{opacity:.88!important;transform:translateY(-1px)!important;}

.stTextInput>div>input,.stTextArea>div>textarea,.stSelectbox>div>div{
  background:#1e2333!important;border:1px solid #2a2f42!important;
  border-radius:9px!important;color:#e8e8e8!important;}
.stTextInput>label,.stTextArea>label,.stSelectbox>label{color:#8a8fa8!important;font-size:.81rem!important;}

.stTabs [data-baseweb="tab-list"]{background:#161923;border-radius:11px;padding:3px;gap:3px;border:1px solid #2a2f42;}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#6b7080!important;font-weight:500;font-size:.88rem;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#f5c842,#ff6b35)!important;color:#0d0f14!important;}

.stSuccess{background:#0f2a1a!important;border-left:4px solid #2ec27e!important;border-radius:9px!important;}
.stError{background:#2a0f0f!important;border-left:4px solid #e63946!important;border-radius:9px!important;}
.stInfo{background:#0f1a2a!important;border-left:4px solid #4dabf7!important;border-radius:9px!important;}
.stWarning{background:#2a1e0f!important;border-left:4px solid #f5c842!important;border-radius:9px!important;}

.section-label{font-size:.68rem;font-weight:600;letter-spacing:.15em;text-transform:uppercase;
  color:#f5c842;margin-bottom:.45rem;}
.voted-badge{background:linear-gradient(135deg,#f5c842,#ff6b35);color:#0d0f14;font-weight:700;
  padding:3px 11px;border-radius:20px;font-size:.74rem;display:inline-block;}
.voter-id-box{background:#1e2333;border:1px dashed #f5c84260;border-radius:9px;
  padding:.8rem 1rem;font-family:'Courier New',monospace;color:#f5c842;font-size:.92rem;letter-spacing:.08em;}

.ebadge{font-size:.67rem;font-weight:700;letter-spacing:.1em;padding:2px 8px;
  border-radius:20px;display:inline-block;text-transform:uppercase;}
.badge-active{background:#0f2a1a;color:#2ec27e;border:1px solid #2ec27e40;}
.badge-draft{background:#2a1e0f;color:#f5c842;border:1px solid #f5c84240;}
.badge-closed{background:#2a0f0f;color:#e63946;border:1px solid #e6394640;}
.badge-pending{background:#1e1a2e;color:#cc5de8;border:1px solid #cc5de840;}
.badge-approved{background:#0f2a1a;color:#2ec27e;border:1px solid #2ec27e40;}
.badge-rejected{background:#2a0f0f;color:#e63946;border:1px solid #e6394640;}

.org-badge{font-size:.68rem;font-weight:700;letter-spacing:.08em;padding:2px 9px;
  border-radius:20px;background:#1e1a2e;color:#cc5de8;border:1px solid #cc5de840;display:inline-block;}

.notif-dot{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:#e63946;margin-left:4px;vertical-align:middle;box-shadow:0 0 6px #e6394680;}

hr{border-color:#2a2f42!important;margin:.9rem 0!important;}

[data-testid="stSidebar"]{background:#0d0f14!important;border-right:1px solid #2a2f42!important;min-width:230px!important;}
[data-testid="stSidebarNav"]{display:none;}
section[data-testid="stSidebar"] .stButton>button{
  width:100%!important;text-align:left!important;justify-content:flex-start!important;margin-bottom:3px!important;}

.countdown-wrap{background:linear-gradient(135deg,#1a1420,#161923);border:1px solid #3a2f52;
  border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1rem;
  display:flex;align-items:center;gap:1.2rem;position:relative;overflow:hidden;}
.countdown-wrap::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#cc5de8,#f5c842,#ff6b35);}
.countdown-unit{text-align:center;min-width:50px;}
.countdown-num{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;
  background:linear-gradient(135deg,#cc5de8,#f5c842);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1;}
.countdown-lbl{font-size:.58rem;color:#6b7080;text-transform:uppercase;letter-spacing:.15em;margin-top:2px;}
.countdown-sep{font-family:'Playfair Display',serif;font-size:1.7rem;color:#3a2f52;padding-bottom:.2rem;}
.countdown-status{flex:1;}
.countdown-title{font-family:'Playfair Display',serif;font-size:.92rem;font-weight:700;color:#e8e8e8;margin-bottom:.1rem;}
.countdown-sub{font-size:.74rem;color:#6b7080;}
.activity-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px;}

/* ── Mobile responsive ── */
@media (max-width: 768px) {
  .block-container{padding:1rem 1rem!important;}
  .hero-title{font-size:2rem!important;}
  .hero-sub{font-size:.82rem!important;}
  .metric-pill{padding:.7rem .6rem!important;}
  .metric-num{font-size:1.5rem!important;}
  .countdown-wrap{flex-wrap:wrap;gap:.8rem;padding:1rem!important;}
  .countdown-num{font-size:1.5rem!important;}
  .card{padding:1rem 1.1rem!important;}
  .card-flat{padding:.9rem 1rem!important;}
  .election-card{padding:1rem 1.1rem!important;}
  .profile-hero{padding:1.2rem 1rem!important;}
  [data-testid="stSidebar"]{min-width:0!important;}
  .stTabs [data-baseweb="tab"]{font-size:.78rem!important;padding:.3rem .5rem!important;}
}
@media (max-width: 480px) {
  .hero-title{font-size:1.6rem!important;}
  .countdown-sep{display:none;}
  .countdown-unit{min-width:44px!important;}
  .countdown-num{font-size:1.3rem!important;}
}

.profile-hero{background:linear-gradient(135deg,#1a1e2e,#161923);border:1px solid #2a2f42;
  border-radius:14px;padding:1.6rem 1.4rem;text-align:center;position:relative;overflow:hidden;margin-bottom:1rem;}
.profile-hero::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#f5c842,#ff6b35,#e63946);}
.profile-avatar-big{width:72px;height:72px;border-radius:50%;
  background:linear-gradient(135deg,#f5c84230,#ff6b3530);
  border:2px solid #f5c84260;display:flex;align-items:center;
  justify-content:center;font-size:2rem;margin:0 auto .65rem;}
.profile-name{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#f0f0f0;margin-bottom:.15rem;}
.profile-info-row{display:flex;align-items:center;padding:.55rem 0;border-bottom:1px solid #2a2f42;gap:.7rem;}
.profile-info-label{font-size:.71rem;color:#6b7080;text-transform:uppercase;letter-spacing:.1em;min-width:100px;}
.profile-info-value{font-size:.88rem;color:#e8e8e8;font-weight:500;}

.election-card{background:#161923;border:1px solid #2a2f42;border-radius:14px;
  padding:1.3rem 1.5rem;margin-bottom:.8rem;transition:border-color .2s,transform .2s;
  position:relative;overflow:hidden;}
.election-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#f5c842,#ff6b35);opacity:0;transition:opacity .3s;}
.election-card:hover::before{opacity:1;}
.election-card:hover{border-color:#f5c84240;transform:translateY(-1px);}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
#  COUNTDOWN (election)
# ─────────────────────────────────────────────────────────
def election_timer(e: dict) -> dict:
    now    = datetime.now()
    start  = datetime.fromisoformat(e["start_date"]) if e.get("start_date") else None
    end    = datetime.fromisoformat(e["end_date"])   if e.get("end_date")   else None
    status = e["status"]
    if status == "closed" or (end and now > end):
        return {"phase":"closed","label":"Election Closed","sub":"Voting has ended",
                "days":0,"hours":0,"minutes":0,"seconds":0}
    if status == "active" and end:
        d = end - now; t = int(d.total_seconds())
        return {"phase":"active","label":"Voting Closes In",
                "sub":f"Cast your vote before {end.strftime('%b %d, %Y · %H:%M')}",
                "days":d.days,"hours":(t%86400)//3600,"minutes":(t%3600)//60,"seconds":t%60}
    if status == "active":
        return {"phase":"active","label":"Election Active","sub":"Voting is open",
                "days":0,"hours":0,"minutes":0,"seconds":0}
    if start and now < start:
        d = start - now; t = int(d.total_seconds())
        return {"phase":"upcoming","label":"Election Opens In",
                "sub":f"Voting begins {start.strftime('%b %d, %Y · %H:%M')}",
                "days":d.days,"hours":(t%86400)//3600,"minutes":(t%3600)//60,"seconds":t%60}
    return {"phase":"draft","label":"Draft","sub":"Not yet published",
            "days":0,"hours":0,"minutes":0,"seconds":0}


def render_countdown(e: dict) -> str:
    s      = election_timer(e)
    colors = {"active":"#2ec27e","upcoming":"#f5c842","closed":"#e63946","draft":"#6b7080"}
    dot    = colors.get(s["phase"],"#6b7080")
    badge  = {"active":"LIVE","upcoming":"UPCOMING","closed":"ENDED","draft":"DRAFT"}.get(s["phase"],"")
    if s["phase"] in ("closed","draft"):
        units = f'<div class="countdown-unit"><div class="countdown-num" style="font-size:1.3rem;color:{dot};">{badge}</div></div>'
    else:
        units = (
            f'<div class="countdown-unit"><div class="countdown-num">{s["days"]:02d}</div><div class="countdown-lbl">Days</div></div>'
            f'<div class="countdown-sep">:</div>'
            f'<div class="countdown-unit"><div class="countdown-num">{s["hours"]:02d}</div><div class="countdown-lbl">Hours</div></div>'
            f'<div class="countdown-sep">:</div>'
            f'<div class="countdown-unit"><div class="countdown-num">{s["minutes"]:02d}</div><div class="countdown-lbl">Mins</div></div>'
            f'<div class="countdown-sep">:</div>'
            f'<div class="countdown-unit"><div class="countdown-num">{s["seconds"]:02d}</div><div class="countdown-lbl">Secs</div></div>'
        )
    st.markdown(
        '<div class="countdown-wrap">' + units
        + '<div class="countdown-status">'
        + f'<div class="countdown-title"><span class="activity-dot" style="background:{dot};box-shadow:0 0 5px {dot}80;"></span>{s["label"]}'
        + f'<span style="font-size:.6rem;background:{dot}22;color:{dot};padding:2px 7px;border-radius:20px;'
        + f'letter-spacing:.1em;vertical-align:middle;margin-left:5px;">{badge}</span></div>'
        + f'<div class="countdown-sub">{s["sub"]}</div>'
        + '</div></div>',
        unsafe_allow_html=True
    )
    return s["phase"]


# ─────────────────────────────────────────────────────────
#  SHARED UI HELPERS
# ─────────────────────────────────────────────────────────
def render_header(subtitle: str = ""):
    sub = subtitle or "Multi-Tenant Election Platform"
    st.markdown(
        f'<div style="padding:1rem 0 .3rem;">'
        f'<div class="hero-title">VoteWave 🗳️</div>'
        f'<div class="hero-sub">{sub}</div></div>',
        unsafe_allow_html=True
    )


def metric(label: str, value, col):
    with col:
        st.markdown(
            f'<div class="metric-pill"><div class="metric-num">{value}</div>'
            f'<div class="metric-label">{label}</div></div>',
            unsafe_allow_html=True
        )


def sbadge(status: str) -> str:
    cls = {"active":"badge-active","draft":"badge-draft","closed":"badge-closed",
           "pending":"badge-pending","approved":"badge-approved","rejected":"badge-rejected"
           }.get(status,"badge-draft")
    return f'<span class="ebadge {cls}">{status.upper()}</span>'


# ─────────────────────────────────────────────────────────
#  SESSION  —  5 min inactivity timeout, 10 min max session
# ─────────────────────────────────────────────────────────
INACTIVITY_LIMIT_MIN = 5    # logout if idle for 5 minutes
MAX_SESSION_MIN      = 10   # force logout after 10 minutes regardless of activity


def _do_logout(reason: str):
    st.session_state.voter           = None
    st.session_state.admin           = None
    st.session_state.is_super        = False
    st.session_state.active_election = None
    st.session_state.page            = "home"
    st.toast(reason, icon="🔒")


def init_session():
    now_iso = datetime.now().isoformat()
    defaults = {
        "page":             "home",
        "voter":            None,
        "admin":            None,
        "is_super":         False,
        "active_election":  None,
        "last_active":      now_iso,
        "session_start":    now_iso,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Only enforce timeouts when someone is logged in
    is_logged_in = (
        st.session_state.voter or
        st.session_state.admin or
        st.session_state.is_super
    )
    if is_logged_in:
        now          = datetime.now()
        last_active  = datetime.fromisoformat(st.session_state["last_active"])
        session_start= datetime.fromisoformat(st.session_state["session_start"])

        idle_min  = (now - last_active).total_seconds()  / 60
        total_min = (now - session_start).total_seconds() / 60

        if idle_min >= INACTIVITY_LIMIT_MIN:
            _do_logout(f"⏰ Logged out due to {INACTIVITY_LIMIT_MIN} min inactivity.")
            return
        if total_min >= MAX_SESSION_MIN:
            _do_logout(f"🔒 Session expired after {MAX_SESSION_MIN} min. Please log in again.")
            return

    # Refresh last_active on every interaction
    st.session_state.last_active = datetime.now().isoformat()


def nav(page: str):
    st.session_state.page = page
    st.rerun()


# ─────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-family:\'Playfair Display\',serif;font-size:1.25rem;font-weight:900;'
            'background:linear-gradient(135deg,#f5c842,#ff6b35);-webkit-background-clip:text;'
            '-webkit-text-fill-color:transparent;padding:.7rem 0 .3rem;">🗳️ VoteWave</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        if st.session_state.is_super:
            st.markdown("**⚡ Super Admin**")
            pending = pending_request_count()
            if pending > 0:
                st.markdown(
                    f'<div style="font-size:.78rem;color:#e63946;font-weight:600;margin-bottom:.3rem;">'
                    f'🔴 {pending} pending admin request{"s" if pending>1 else ""}</div>',
                    unsafe_allow_html=True
                )
            st.markdown("")
            if st.button("🏢 Organizations",  key="sb_orgs"):    nav("super_orgs")
            if st.button("📥 Admin Requests", key="sb_requests"):nav("super_requests")
            if st.button("👤 All Admins",     key="sb_admins"):  nav("super_admins")
            if st.button("📊 Overview",       key="sb_overview"):nav("super_overview")
            st.markdown("---")
            if st.button("🚪 Logout", key="sb_super_out"):
                st.session_state.is_super = False; nav("home")

        elif st.session_state.admin:
            a   = st.session_state.admin
            org = get_org(a["org_id"])
            st.markdown(f"**{a['name']}**")
            st.caption(f"🏢 {org['name'] if org else '—'}")
            st.caption(f"Role: {a['role'].title()}")
            st.markdown("")
            if st.button("📊 Dashboard",  key="sb_adash"): nav("admin_panel")
            if st.button("👤 My Profile", key="sb_aprof"): nav("admin_profile")
            st.markdown("---")
            if st.button("🚪 Logout", key="sb_aout"):
                st.session_state.admin = None; nav("home")

        elif st.session_state.voter:
            v = st.session_state.voter
            st.markdown(f"**{v['name']}**")
            st.caption(v["voter_id"])
            st.markdown("")
            if st.button("🏠 Home",         key="sb_home"):  nav("home")
            if st.button("🗳️ My Elections", key="sb_myel"):  nav("my_elections")
            if st.button("👤 Profile",      key="sb_vprof"): nav("voter_profile")
            st.markdown("---")
            if st.button("🚪 Logout", key="sb_vout"):
                st.session_state.voter = None
                st.session_state.active_election = None
                nav("home")

        else:
            if st.button("🏠 Home",           key="sb_home2"):  nav("home")
            if st.button("🗳️ Vote / Login",   key="sb_vlogin"): nav("voter_login")
            if st.button("📝 Register",        key="sb_vreg"):   nav("voter_register")
            st.markdown("---")
            if st.button("🔐 Admin Login",     key="sb_alogin"): nav("admin_login")
            if st.button("📝 Admin Register",  key="sb_areg"):   nav("admin_register")