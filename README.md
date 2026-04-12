# 🗳️ VoteWave — Multi-Tenant Election Platform

A complete, production-ready online voting system built with **Streamlit + SQLite**.

---

## 🌐 Live Demo  
👉 https://votewave.streamlit.app/

---

## 🚀 Deployment

The application is deployed using **Streamlit Cloud** and is publicly accessible.

- 🔗 Live URL: https://votewave.streamlit.app/
- ☁️ Hosting: Streamlit Cloud
- 📦 Code Repository: GitHub

---

## 📁 Project Structure

```
votewave/
├── app.py           ← Entry point — run this
├── database.py      ← SQLite schema & connection
├── helpers.py       ← All business logic & DB queries
├── ui.py            ← CSS, countdown, sidebar, session
├── pages_super.py   ← Super admin pages
├── pages_admin.py   ← Org admin pages (dashboard, elections, candidates, voters)
├── pages_voter.py   ← Voter pages (home, ballot, results, profile)
├── requirements.txt ← Python dependencies
└── README.md        ← This file
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 🔑 Default Credentials

| Role        | Username     | Password   |
|-------------|--------------|------------|
| Super Admin | `superadmin` | `super123` |

> Change these after first login!

---

## 🏗️ Architecture

### Multi-Tenant Design
- **Organizations** are top-level tenants — fully isolated from each other
- **Org Admins** belong to one org and can only see their org's data
- Multiple admins can collaborate on the same org
- **Voters** register **per-election** (not globally)

### Database Tables
| Table          | Purpose                              |
|----------------|--------------------------------------|
| `super_admins` | Platform owner accounts              |
| `organizations`| Tenant orgs (schools, companies etc) |
| `org_admins`   | Admins linked to one org             |
| `elections`    | Elections linked to one org          |
| `candidates`   | Candidates linked to one election    |
| `voters`       | Voters registered per election       |
| `votes`        | One vote per voter per election      |

---

## 👤 User Roles

### Super Admin
- Creates and manages organizations
- Sees all data across the entire platform
- Can remove any org admin

### Org Admin
- Creates elections for their org
- Adds/edits/deletes candidates
- Manages voters (view, remove, reset)
- Views results and exports CSV
- Can invite other admins to their org

### Voter
- Registers per election (separate account per election)
- Can be registered in multiple elections simultaneously
- Casts one vote per election
- Views live results

---

## ✨ Features

- 🏢 **Multi-organization** isolation
- 🗳️ **Multiple simultaneous elections** (voters choose which to join)
- 👤 **Per-election voter registration** (fresh for each election)
- 📊 **Live results** with charts (bar + donut)
- 📥 **CSV export** of results and voter lists
- ⏱️ **Election countdown timer** (upcoming/live/closed)
- 🔒 **Auto-logout** after 30 min inactivity
- 📱 **Mobile responsive** design
- 🎨 **Dark civic theme** with Playfair Display typography

---

## 📱 Mobile Support
The app is fully mobile-responsive. Use it on any device at the Streamlit URL.

---

## 🔧 Configuration

To change the session timeout (default: 30 min), edit `ui.py`:
```python
SESSION_TIMEOUT_MINUTES = 30  # change this
```

To change the super admin credentials, update `database.py`:
```python
c.execute("INSERT OR IGNORE INTO super_admins(username,password) VALUES(?,?)",
          ("superadmin", hash_pw("super123")))  # change here
```
> Note: After first run the credentials are stored in `votewave.db`. 
> Delete the `.db` file to reset all data.
