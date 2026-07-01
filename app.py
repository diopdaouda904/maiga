"""
app.py — Maïga Smash | Gestion de stock
Lancement : streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import threading
import hmac
import hashlib
import time
from datetime import datetime
from streamlit_cookies_controller import CookieController

from config import NOM_RESTO, COULEUR_PRINCIPALE, verifier_mdp
from database import (
    init_db, get_stocks, get_historique, update_stock,
    get_produit_by_barcode, enregistrer_code_barres, RESTAURANTS,
    get_all_produits, get_categories, add_produit, update_produit,
    delete_produit, produit_existe
)

init_db()

st.set_page_config(
    page_title=NOM_RESTO,
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PERSISTANTE (cookie "rester connecté" — 7 jours)
# ═══════════════════════════════════════════════════════════════════════════════
# On stocke un jeton signé côté navigateur. Comme les cookies sont visibles par
# l'utilisateur, on ne stocke JAMAIS le mot de passe : juste le rôle + une date
# d'expiration + une signature HMAC pour empêcher toute falsification.
COOKIE_NAME    = "maiga_session"
COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 jours en secondes

def _cookie_secret():
    try:
        return st.secrets["COOKIE_SECRET"]
    except Exception:
        # Fallback local (dev). En prod, définir COOKIE_SECRET dans les secrets Streamlit.
        return "maiga-dev-secret-a-remplacer-en-prod"

def _sign(payload: str) -> str:
    return hmac.new(_cookie_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()

def _make_token(role: str) -> str:
    exp = int(time.time()) + COOKIE_MAX_AGE
    payload = f"{role}|{exp}"
    return f"{payload}|{_sign(payload)}"

def _read_token(token: str):
    """Retourne le rôle si le jeton est valide et non expiré, sinon None."""
    if not token or token.count("|") != 2:
        return None
    role, exp_str, sig = token.split("|")
    if _sign(f"{role}|{exp_str}") != sig:
        return None
    try:
        if int(exp_str) < int(time.time()):
            return None
    except ValueError:
        return None
    return role if role in ("employe", "patron") else None

cookies = CookieController()

# ── Palette pro ───────────────────────────────────────────────────────────────
# Accent piloté depuis config.py (source unique de la marque) + neutres resserrés
ACC   = COULEUR_PRINCIPALE
ACC2  = "#E0954A"  # variante claire de l'accent (hover, highlights)
BG    = "#0A0A0B"
SURF  = "#141415"
SURF2 = "#1B1B1D"
BDR   = "#262628"
TXT   = "#EDEDEC"
SUB   = "#8A8A8E"
MUT   = "#4A4A4D"
OK    = "#3AA66B"
WARN  = "#C2872E"
DNGR  = "#C84B3C"

# Rayons resserrés (look outil pro plutôt que app ludique)
R_SM  = "5px"
R_MD  = "7px"
R_LG  = "10px"

# ── SVG icons ─────────────────────────────────────────────────────────────────
ICO_BOX   = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>'
ICO_SCAN  = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>'
ICO_HIST  = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
ICO_ADM   = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>'
ICO_OUT   = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
ICO_WARN  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600;700&display=swap" rel="stylesheet">

<style>
/* ── Base ──────────────────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}

.stApp {{
  background: {BG} !important;
  color: {TXT};
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
}}

.mono {{ font-family: 'IBM Plex Mono', monospace !important; font-variant-numeric: tabular-nums; }}

header[data-testid="stHeader"],
.stDeployButton,
footer,
section[data-testid="stSidebar"] {{ display: none !important; }}

.block-container {{
  padding: 0 16px 60px !important;
  max-width: 460px !important;
  margin: 0 auto !important;
}}

/* ── Topbar ─────────────────────────────────────────────────────────────────── */
.topbar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 12px;
  position: sticky;
  top: 0;
  background: {BG};
  z-index: 100;
  border-bottom: 1px solid {BDR};
  margin-bottom: 16px;
}}
.topbar-brand {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.topbar-mark {{
  width: 22px; height: 22px;
  background: {ACC};
  border-radius: 5px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.68rem;
  font-weight: 700;
  color: {BG};
  font-family: 'IBM Plex Mono', monospace;
  flex-shrink: 0;
}}
.topbar-name {{
  font-size: 0.92rem;
  font-weight: 700;
  color: {TXT};
  letter-spacing: -0.2px;
}}
.topbar-right {{ display: flex; align-items: center; gap: 6px; }}
.badge-role {{
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: {SUB};
  background: {SURF};
  border: 1px solid {BDR};
  padding: 3px 9px;
  border-radius: {R_SM};
}}

/* ── Bouton logout ── */
div[data-testid="column"]:has(button[key="logout"]) .stButton > button {{
  background: {SURF} !important;
  border: 1px solid {BDR} !important;
  color: {SUB} !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  padding: 4px 10px !important;
  border-radius: 6px !important;
  height: auto !important;
  min-height: unset !important;
  width: auto !important;
  letter-spacing: 0.2px;
}}
div[data-testid="column"]:has(button[key="logout"]) .stButton > button:hover {{
  border-color: {DNGR} !important;
  color: {DNGR} !important;
}}

/* ── Tabs ───────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  gap: 0;
  background: transparent;
  border-bottom: 1px solid {BDR};
  border-radius: 0;
  padding: 0;
  margin-bottom: 20px;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent;
  border-radius: 0;
  color: {SUB};
  font-weight: 500;
  font-size: 0.82rem;
  padding: 10px 16px;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  flex: unset;
  letter-spacing: 0.1px;
}}
.stTabs [aria-selected="true"] {{
  background: transparent !important;
  color: {TXT} !important;
  border-bottom: 2px solid {ACC} !important;
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* ── KPI cards ──────────────────────────────────────────────────────────────── */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}}
.kpi-card {{
  background: {SURF};
  border: 1px solid {BDR};
  border-radius: {R_MD};
  padding: 14px 10px 12px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s;
  position: relative;
  overflow: hidden;
}}
.kpi-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--kpi-color);
  opacity: 0;
  transition: opacity 0.15s;
}}
.kpi-card.active::before {{ opacity: 1; }}
.kpi-card.active {{ border-color: var(--kpi-color); }}
.kpi-num {{
  font-family: 'IBM Plex Mono', monospace;
  font-variant-numeric: tabular-nums;
  font-size: 1.6rem;
  font-weight: 600;
  line-height: 1;
  color: var(--kpi-color);
  letter-spacing: -0.5px;
}}
.kpi-label {{
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: {SUB};
  margin-top: 6px;
}}
/* Boutons KPI invisibles par-dessus les cartes */
.kpi-btn-row div[data-testid="column"] .stButton > button {{
  background: transparent !important;
  border: none !important;
  color: transparent !important;
  width: 100% !important;
  min-height: unset !important;
  height: 80px !important;
  padding: 0 !important;
  margin-top: -84px;
  position: relative;
  z-index: 10;
}}

/* ── Inputs ─────────────────────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input {{
  background: {SURF} !important;
  border: 1px solid {BDR} !important;
  border-radius: {R_MD} !important;
  color: {TXT} !important;
  padding: 9px 13px !important;
  font-size: 0.88rem !important;
  font-family: 'Inter', sans-serif !important;
}}
.stTextInput input:focus, .stNumberInput input:focus {{
  border-color: {ACC} !important;
  outline: none !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, {ACC} 12%, transparent) !important;
}}
.stTextInput label,
.stNumberInput label {{ display: none; }}

/* ── Selectbox ──────────────────────────────────────────────────────────────── */
div[data-testid="stSelectbox"] > div > div {{
  background: {SURF} !important;
  border: 1px solid {BDR} !important;
  border-radius: {R_MD} !important;
  color: {TXT} !important;
  font-size: 0.85rem !important;
}}
.stSelectbox label {{ font-size: 0.72rem !important; color: {SUB} !important; font-weight: 500 !important; }}

/* ── Suggestions ────────────────────────────────────────────────────────────── */
.sugg-box {{
  background: {SURF2};
  border: 1px solid {BDR};
  border-radius: {R_MD};
  margin-top: -4px;
  margin-bottom: 14px;
  overflow: hidden;
}}
.sugg-item {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 13px;
  border-bottom: 1px solid {BDR};
  font-size: 0.83rem;
}}
.sugg-item:last-child {{ border-bottom: none; }}
.sugg-name {{ font-weight: 500; color: {TXT}; }}
.sugg-cat  {{ font-size: 0.63rem; color: {SUB}; margin-top: 1px; }}
.sugg-qty  {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; font-size: 0.92rem; font-weight: 600; }}

/* ── Section catégorie ──────────────────────────────────────────────────────── */
.section-label {{
  font-size: 0.63rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: {MUT};
  padding: 14px 0 7px;
}}

/* ── Ligne produit ──────────────────────────────────────────────────────────── */
.prod-name {{ font-size: 0.87rem; font-weight: 600; color: {TXT}; letter-spacing: -0.1px; }}
.prod-meta {{ font-size: 0.65rem; color: {SUB}; margin-top: 2px; }}
.prod-qty  {{
  font-family: 'IBM Plex Mono', monospace;
  font-variant-numeric: tabular-nums;
  font-size: 1.35rem; font-weight: 600; line-height: 1;
  text-align: center; letter-spacing: -0.5px;
}}
.prod-unit {{ font-size: 0.6rem; color: {SUB}; text-align: center; margin-top: 2px; font-weight: 500; }}
.prod-ok   {{ color: {OK}; }}
.prod-warn {{ color: {WARN}; }}
.prod-dngr {{ color: {DNGR}; }}
.prod-sep  {{ border: none; border-top: 1px solid {SURF2}; margin: 6px 0 2px; }}

/* ── Boutons +/− ────────────────────────────────────────────────────────────── */
.stButton > button {{
  background: {SURF} !important;
  color: {SUB} !important;
  border: 1px solid {BDR} !important;
  border-radius: {R_SM} !important;
  font-size: 1.15rem !important;
  font-weight: 400 !important;
  padding: 0 !important;
  min-height: unset !important;
  line-height: 1 !important;
  transition: all 0.12s;
}}
.stButton > button:hover {{
  background: {SURF2} !important;
  border-color: {SUB} !important;
  color: {TXT} !important;
}}
div[data-testid="column"]:has(button[key^="m_"]) .stButton > button,
div[data-testid="column"]:has(button[key^="p_"]) .stButton > button {{
  width: 100% !important;
  height: 40px !important;
  font-size: 1.25rem !important;
}}

/* ── Badge filtre actif ──────────────────────────────────────────────────────── */
.filter-badge {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: {SUB};
  background: {SURF};
  border: 1px solid {BDR};
  padding: 4px 10px;
  border-radius: {R_SM};
  margin-bottom: 12px;
}}

/* ── Connexion ──────────────────────────────────────────────────────────────── */
.login-wrap {{
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
}}
.login-logo {{
  width: 44px; height: 44px;
  background: {ACC};
  border-radius: {R_MD};
  display: flex; align-items: center; justify-content: center;
  font-size: 1.05rem;
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
  color: {BG};
  margin: 0 auto 22px;
}}
.login-title {{
  font-size: 1.2rem;
  font-weight: 700;
  color: {TXT};
  text-align: center;
  letter-spacing: -0.3px;
}}
.login-sub {{
  font-size: 0.78rem;
  color: {SUB};
  text-align: center;
  margin-top: 4px;
  margin-bottom: 32px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}}

/* ── Bouton primaire ────────────────────────────────────────────────────────── */
div[data-testid="column"]:has(button[key="login_btn"]) .stButton > button,
button[key="login_btn"],
div:has(> button[key="login_btn"]) > button {{
  background: {ACC} !important;
  color: #0A0A0B !important;
  font-weight: 700 !important;
  font-size: 0.88rem !important;
  height: 42px !important;
  border-radius: {R_MD} !important;
  border: none !important;
  width: 100% !important;
  letter-spacing: 0.1px;
}}
div:has(> button[key="login_btn"]) > button:hover {{
  background: {ACC2} !important;
}}

/* ── Scanner ────────────────────────────────────────────────────────────────── */
.scan-wrap {{
  border: 1px solid {BDR};
  border-radius: {R_LG};
  overflow: hidden;
  margin-bottom: 16px;
}}
.box-ok {{
  background: {SURF};
  border: 1px solid {BDR};
  border-left: 2px solid {OK};
  border-radius: {R_MD}; padding: 14px; margin: 12px 0;
}}
.box-ok strong {{ font-size: 0.9rem; font-weight: 600; color: {TXT}; }}
.box-ok p {{ font-size: 0.77rem; color: {SUB}; margin-top: 4px; }}
.box-ko {{
  background: {SURF};
  border: 1px solid {BDR};
  border-left: 2px solid {DNGR};
  border-radius: {R_MD}; padding: 14px; margin: 12px 0;
}}
.box-ko strong {{ font-size: 0.9rem; font-weight: 600; color: {TXT}; }}
.box-ko p {{ font-size: 0.77rem; color: {SUB}; margin-top: 4px; }}

/* ── Historique ─────────────────────────────────────────────────────────────── */
.histo-item {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 0;
  border-bottom: 1px solid {SURF2};
  font-size: 0.83rem;
}}
.histo-left {{ flex: 1; min-width: 0; }}
.histo-name {{ font-weight: 500; color: {TXT}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.histo-meta {{ font-size: 0.63rem; color: {SUB}; margin-top: 2px; }}
.histo-right {{ text-align: right; flex-shrink: 0; padding-left: 12px; }}
.histo-var  {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; font-size: 0.86rem; font-weight: 600; }}
.histo-flow {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; font-size: 0.65rem; color: {SUB}; margin-top: 1px; }}

/* ── Gestion produits ───────────────────────────────────────────────────────── */
.pm-header {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 4px;
}}
.pm-count {{ font-size: 0.72rem; color: {SUB}; }}
.pm-card {{
  background: {SURF};
  border: 1px solid {BDR};
  border-radius: {R_MD};
  padding: 12px 14px;
  margin-bottom: 8px;
}}
.pm-name {{ font-size: 0.88rem; font-weight: 600; color: {TXT}; }}
.pm-meta {{ font-size: 0.66rem; color: {SUB}; margin-top: 2px; }}
.pm-empty {{
  text-align:center; color:{SUB}; padding:32px 0; font-size:0.85rem;
}}
/* Boutons crayon / poubelle compacts, même largeur, cote à cote */
div[data-testid="column"]:has(button[key^="edit_"]) .stButton > button,
div[data-testid="column"]:has(button[key^="del_"]) .stButton > button,
div[data-testid="column"]:has(button[key^="delconfirm_"]) .stButton > button,
div[data-testid="column"]:has(button[key^="delcancel_"]) .stButton > button {{
  width: 100% !important;
  height: 34px !important;
  font-size: 0.72rem !important;
}}
div[data-testid="column"]:has(button[key^="delconfirm_"]) .stButton > button {{
  border-color: {DNGR} !important;
  color: {DNGR} !important;
}}
/* Bouton "+ Nouveau produit" pleine largeur, accent */
div[data-testid="column"]:has(button[key="toggle_add"]) .stButton > button,
button[key="save_new_produit"],
div:has(> button[key="save_new_produit"]) > button {{
  background: {ACC} !important;
  color: #0A0A0B !important;
  border: none !important;
  font-weight: 700 !important;
}}

/* ── Streamlit overrides ────────────────────────────────────────────────────── */
.stRadio > div {{ gap: 0 !important; }}
.stRadio [data-testid="stMarkdownContainer"] p {{ font-size: 0.82rem; }}
div[data-testid="stNumberInput"] {{ margin-top: 8px; }}
.stAlert {{ border-radius: 8px !important; font-size: 0.82rem !important; }}
.element-container {{ margin-bottom: 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in {
    "connecte": False, "role": None,
    "restaurant": RESTAURANTS[0], "kpi_filter": None,
    "pm_show_add": False, "pm_editing": None, "pm_confirm_delete": None,
    "stock_overrides": {},
    "cookie_checked": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-reconnexion via cookie (une seule fois par session) ──
if not st.session_state.connecte and not st.session_state.cookie_checked:
    st.session_state.cookie_checked = True
    token = cookies.get(COOKIE_NAME)
    if token:
        role = _read_token(token)
        if role:
            st.session_state.connecte = True
            st.session_state.role = role

# ═══════════════════════════════════════════════════════════════════════════════
# CONNEXION
# ═══════════════════════════════════════════════════════════════════════════════
def page_connexion():
    st.markdown(f"""
    <div style="text-align:center; padding: 60px 0 32px;">
      <div class="login-logo">{NOM_RESTO[0]}</div>
      <div class="login-title">{NOM_RESTO}</div>
      <div class="login-sub">Gestion des stocks</div>
    </div>
    """, unsafe_allow_html=True)

    role = st.selectbox("Rôle", ["Employé", "Patron"])
    mdp  = st.text_input("Mot de passe", type="password", placeholder="••••••••")
    rester = st.checkbox("Rester connecté pendant 7 jours", value=True, key="stay_logged")

    if st.button("Se connecter", key="login_btn", use_container_width=True):
        role_key = "employe" if role == "Employé" else "patron"
        if verifier_mdp(mdp, role_key):
            st.session_state.connecte = True
            st.session_state.role = role_key
            if rester:
                cookies.set(COOKIE_NAME, _make_token(role_key),
                            max_age=COOKIE_MAX_AGE, secure=True, same_site="lax")
            st.rerun()
        else:
            st.error("Mot de passe incorrect")

# ═══════════════════════════════════════════════════════════════════════════════
# ÉCRITURE ASYNCHRONE (mise à jour optimiste)
# ═══════════════════════════════════════════════════════════════════════════════
def _write_stock_async(resto, produit, ancienne_qte, nouvelle_qte):
    """Écrit dans Supabase en arrière-plan pour ne jamais bloquer l'affichage."""
    threading.Thread(
        target=update_stock, args=(resto, produit, ancienne_qte, nouvelle_qte), daemon=True
    ).start()

def _bump_qte(resto, produit, qte_actuelle, nouvelle_qte):
    """Affiche le nouveau chiffre immédiatement, écrit en base derrière."""
    st.session_state.stock_overrides.setdefault(resto, {})[produit] = nouvelle_qte
    _write_stock_async(resto, produit, qte_actuelle, nouvelle_qte)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE STOCK
# ═══════════════════════════════════════════════════════════════════════════════
def page_stock():
    resto     = st.session_state.restaurant
    df        = get_stocks(resto)
    kpi_filter = st.session_state.kpi_filter

    # ── Réconciliation des mises à jour optimistes ──
    # Tant que le cache Supabase n'a pas confirmé le nouveau chiffre, on affiche
    # la valeur locale (instantanée). Dès que la vraie donnée rejoint l'override,
    # on l'enlève — ça évite de rester bloqué sur une valeur locale périmée.
    overrides = st.session_state.stock_overrides.setdefault(resto, {})
    if overrides and not df.empty:
        for prod in list(overrides.keys()):
            real = df.loc[df["produit"] == prod, "quantite"]
            if not real.empty and int(real.iloc[0]) == overrides[prod]:
                del overrides[prod]
        if overrides:
            df = df.copy()
            for prod, val in overrides.items():
                df.loc[df["produit"] == prod, "quantite"] = val

    n_total   = len(df)
    n_alertes = int((df["quantite"] <= df["seuil_alerte"]).sum())
    n_rupture = int((df["quantite"] == 0).sum())

    # ── KPI cards (HTML) ──
    def kpi_active(k): return "active" if kpi_filter == k else ""

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card {kpi_active('rupture')}" style="--kpi-color:{DNGR}">
        <div class="kpi-num">{n_rupture}</div>
        <div class="kpi-label">Ruptures</div>
      </div>
      <div class="kpi-card {kpi_active('alerte')}" style="--kpi-color:{WARN}">
        <div class="kpi-num">{n_alertes}</div>
        <div class="kpi-label">Alertes</div>
      </div>
      <div class="kpi-card" style="--kpi-color:{SUB}">
        <div class="kpi-num" style="color:{TXT}">{n_total}</div>
        <div class="kpi-label">Produits</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Boutons invisibles par-dessus les KPI
    st.markdown('<div class="kpi-btn-row">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("r", key="kpi_rupture_btn", use_container_width=True):
            st.session_state.kpi_filter = None if kpi_filter == "rupture" else "rupture"
            st.rerun()
    with c2:
        if st.button("a", key="kpi_alerte_btn", use_container_width=True):
            st.session_state.kpi_filter = None if kpi_filter == "alerte" else "alerte"
            st.rerun()
    with c3:
        if st.button("t", key="kpi_total_btn", use_container_width=True):
            st.session_state.kpi_filter = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if kpi_filter:
        label = "Ruptures uniquement" if kpi_filter == "rupture" else "Alertes stock bas"
        icone = ICO_WARN
        st.markdown(f'<div class="filter-badge">{icone}&nbsp;{label} — touchez à nouveau pour annuler</div>', unsafe_allow_html=True)

    # ── Recherche + suggestions ──
    recherche = st.text_input("", placeholder="Rechercher un produit...", key="search", label_visibility="collapsed")

    if recherche and len(recherche) >= 2:
        suggestions = df[df["produit"].str.contains(recherche, case=False, na=False)].head(6)
        if not suggestions.empty:
            html = '<div class="sugg-box">'
            for _, s in suggestions.iterrows():
                qte   = int(s["quantite"])
                seuil = int(s["seuil_alerte"])
                cls   = "prod-dngr" if qte == 0 else ("prod-warn" if qte <= seuil else "prod-ok")
                html += f"""
                <div class="sugg-item">
                  <div><div class="sugg-name">{s['produit']}</div>
                       <div class="sugg-cat">{s['categorie']}</div></div>
                  <span class="sugg-qty {cls}">{qte} <span style="font-size:0.62rem;color:{SUB};font-weight:400">{s['unite']}</span></span>
                </div>"""
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    # ── Filtre catégorie ──
    categories = ["Toutes les catégories"] + sorted(df["categorie"].unique().tolist())
    cat_active = st.selectbox("Catégorie", categories, key="cat_select")

    # ── Filtrage ──
    df_f = df.copy()
    if recherche:
        df_f = df_f[df_f["produit"].str.contains(recherche, case=False, na=False)]
    if cat_active != "Toutes les catégories":
        df_f = df_f[df_f["categorie"] == cat_active]
    if kpi_filter == "rupture":
        df_f = df_f[df_f["quantite"] == 0]
    elif kpi_filter == "alerte":
        df_f = df_f[(df_f["quantite"] > 0) & (df_f["quantite"] <= df_f["seuil_alerte"])]

    if df_f.empty:
        st.markdown(f'<div style="text-align:center;color:{SUB};padding:32px 0;font-size:0.85rem;">Aucun produit trouvé</div>', unsafe_allow_html=True)
        return

    # ── Liste produits ──
    for cat in df_f["categorie"].unique():
        bloc = df_f[df_f["categorie"] == cat]
        st.markdown(f'<div class="section-label">{cat}</div>', unsafe_allow_html=True)

        for _, row in bloc.iterrows():
            qte     = int(row["quantite"])
            seuil   = int(row["seuil_alerte"])
            unite   = row["unite"]
            produit = row["produit"]
            cls     = "prod-dngr" if qte == 0 else ("prod-warn" if qte <= seuil else "prod-ok")

            st.markdown(f"""
            <div style="padding: 8px 0 4px;">
              <div class="prod-name">{produit}</div>
              <div class="prod-meta">{row['fournisseur']} · seuil {seuil} {unite}</div>
            </div>
            """, unsafe_allow_html=True)

            c_m, c_q, c_p = st.columns([1, 2, 1])
            with c_m:
                if st.button("−", key=f"m_{produit}", use_container_width=True):
                    if qte > 0:
                        _bump_qte(resto, produit, qte, qte - 1)
                        st.rerun()
            with c_q:
                st.markdown(f"""
                <div style="text-align:center; padding:4px 0;">
                  <div class="prod-qty {cls}">{qte}</div>
                  <div class="prod-unit">{unite}</div>
                </div>""", unsafe_allow_html=True)
            with c_p:
                if st.button("+", key=f"p_{produit}", use_container_width=True):
                    _bump_qte(resto, produit, qte, qte + 1)
                    st.rerun()

            st.markdown("<hr class='prod-sep'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE SCANNER
# ═══════════════════════════════════════════════════════════════════════════════
def page_scanner():
    resto = st.session_state.restaurant

    mode = st.radio("", ["Caméra", "Saisie manuelle"], horizontal=True, label_visibility="collapsed")
    code = None

    if mode == "Caméra":
        st.caption("Autorisez l'accès à la caméra, puis visez le code-barres.")
        scan_html = f"""
        <div id="reader" style="width:100%;border-radius:10px;overflow:hidden;"></div>
        <div id="scan-result" style="margin-top:10px;padding:10px 14px;border-radius:7px;
             background:{SURF};border-left:2px solid {OK};
             color:{TXT};font-size:0.82rem;display:none;font-family:Inter,sans-serif;">
        </div>
        <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
        <script>
          function startScanner() {{
            const box = document.getElementById('scan-result');
            const scanner = new Html5Qrcode("reader");
            scanner.start(
              {{ facingMode: "environment" }},
              {{ fps: 10, qrbox: {{ width: 240, height: 140 }} }},
              function(code) {{
                box.style.display = "block";
                box.innerText = "Code détecté : " + code;
                scanner.stop().then(() => {{
                  const base = window.parent.location.href.split('?')[0];
                  window.parent.location.href = base + "?scanned_code=" + encodeURIComponent(code);
                }});
              }}
            ).catch(err => {{
              box.style.display = "block";
              box.style.borderLeftColor = "{DNGR}";
              box.innerText = "Caméra inaccessible : " + err;
            }});
          }}
          startScanner();
        </script>"""
        components.html(scan_html, height=300)

        query_code = st.query_params.get("scanned_code")
        if query_code:
            code = query_code
            st.query_params.clear()

        st.markdown(f'<div style="height:8px"></div>', unsafe_allow_html=True)
        fallback = st.text_input("", placeholder="Ou entrez le code manuellement...", key="barcode_fallback", label_visibility="collapsed")
        if fallback:
            code = fallback
    else:
        code = st.text_input("", placeholder="Code-barres...", key="barcode_manual", label_visibility="collapsed")

    if code and len(str(code).strip()) > 3:
        code = str(code).strip()
        produit_nom = get_produit_by_barcode(code)
        df = get_stocks(resto)

        if produit_nom:
            ligne = df[df["produit"] == produit_nom]
            if not ligne.empty:
                qte   = int(ligne.iloc[0]["quantite"])
                unite = ligne.iloc[0]["unite"]
                seuil = int(ligne.iloc[0]["seuil_alerte"])
                cls   = "prod-dngr" if qte == 0 else ("prod-warn" if qte <= seuil else "prod-ok")

                st.markdown(f"""
                <div class="box-ok">
                  <strong>{produit_nom}</strong>
                  <p>Stock actuel : <span class="{cls}" style="font-weight:700">{qte} {unite}</span></p>
                </div>""", unsafe_allow_html=True)

                qte_retrait = st.number_input("Quantité à retirer", min_value=1, max_value=max(1, qte), value=1, step=1)
                if st.button(f"Confirmer le retrait — {qte_retrait} {unite}", use_container_width=True):
                    nv = max(0, qte - qte_retrait)
                    update_stock(resto, produit_nom, qte, nv)
                    st.success(f"{produit_nom} : {qte} → {nv} {unite}")
                    if nv <= seuil:
                        st.warning(f"Stock bas sur {produit_nom}")
                    st.rerun()
        else:
            st.markdown(f"""
            <div class="box-ko">
              <strong>Code inconnu : {code}</strong>
              <p>Associez ce code à un produit pour les prochains scans</p>
            </div>""", unsafe_allow_html=True)
            df = get_stocks(resto)
            choix = st.selectbox("Associer à", sorted(df["produit"].tolist()))
            if st.button("Enregistrer l'association", use_container_width=True):
                enregistrer_code_barres(choix, code)
                st.success(f"Code {code} associé à {choix}")
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════
def page_historique():
    df = get_historique(30)
    if df.empty:
        st.markdown(f'<div style="text-align:center;color:{SUB};padding:40px 0;font-size:0.85rem;">Aucun mouvement sur 30 jours</div>', unsafe_allow_html=True)
        return

    df["variation"] = df["nouvelle_qte"] - df["ancienne_qte"]
    n_plus  = int((df["variation"] > 0).sum())
    n_moins = int((df["variation"] < 0).sum())

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card" style="--kpi-color:{SUB}">
        <div class="kpi-num" style="color:{TXT}">{len(df)}</div>
        <div class="kpi-label">Mouvements</div>
      </div>
      <div class="kpi-card" style="--kpi-color:{DNGR}">
        <div class="kpi-num">{n_moins}</div>
        <div class="kpi-label">Retraits</div>
      </div>
      <div class="kpi-card" style="--kpi-color:{OK}">
        <div class="kpi-num">{n_plus}</div>
        <div class="kpi-label">Ajouts</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="height:4px"></div>', unsafe_allow_html=True)

    html = ""
    for _, row in df.head(60).iterrows():
        var    = int(row["variation"])
        signe  = f"+{var}" if var > 0 else str(var)
        couleur = OK if var > 0 else DNGR
        date_s = str(row["date"])[:16]
        html += f"""
        <div class="histo-item">
          <div class="histo-left">
            <div class="histo-name">{row['produit']}</div>
            <div class="histo-meta">{date_s} · {row['restaurant']}</div>
          </div>
          <div class="histo-right">
            <div class="histo-var" style="color:{couleur}">{signe}</div>
            <div class="histo-flow">{row['ancienne_qte']} → {row['nouvelle_qte']}</div>
          </div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE PRODUITS (catalogue en libre-service, sans passer par Supabase)
# ═══════════════════════════════════════════════════════════════════════════════
UNITES = ["kg", "g", "L", "mL", "unité", "pièce", "boîte", "sachet", "carton"]

def _form_produit(prefix, defaults=None):
    """Formulaire d'ajout/modif, retourne un dict si validé, sinon None."""
    d = defaults or {}
    cats = get_categories()
    cat_options = cats + ["+ Nouvelle catégorie"]

    nom = st.text_input("Nom du produit", value=d.get("nom", ""), key=f"{prefix}_nom",
                         placeholder="Ex : Pain burger brioché")

    if cats:
        idx = cat_options.index(d["categorie"]) if d.get("categorie") in cats else len(cat_options) - 1
        cat_choice = st.selectbox("Catégorie", cat_options, index=idx, key=f"{prefix}_cat_select")
        if cat_choice == "+ Nouvelle catégorie":
            categorie = st.text_input("Nom de la nouvelle catégorie", key=f"{prefix}_cat_new",
                                       placeholder="Ex : Pains & buns")
        else:
            categorie = cat_choice
    else:
        categorie = st.text_input("Catégorie", value=d.get("categorie", ""), key=f"{prefix}_cat_new2",
                                   placeholder="Ex : Pains & buns")

    fournisseur = st.text_input("Fournisseur", value=d.get("fournisseur", ""), key=f"{prefix}_four",
                                 placeholder="Ex : Metro")

    c1, c2 = st.columns(2)
    with c1:
        unite_idx = UNITES.index(d["unite"]) if d.get("unite") in UNITES else 0
        unite = st.selectbox("Unité", UNITES, index=unite_idx, key=f"{prefix}_unite")
    with c2:
        seuil = st.number_input("Seuil d'alerte", min_value=0, step=1,
                                 value=int(d.get("seuil_alerte", 5)), key=f"{prefix}_seuil")

    qte_init = None
    if defaults is None:  # uniquement à la création
        qte_init = st.number_input("Quantité de départ", min_value=0, step=1, value=0, key=f"{prefix}_qte")

    return dict(nom=nom.strip(), categorie=categorie.strip(), fournisseur=fournisseur.strip(),
                unite=unite, seuil_alerte=int(seuil), quantite_initiale=int(qte_init) if qte_init is not None else None)

def page_produits():
    df = get_all_produits()
    n = len(df)

    st.markdown(f"""
    <div class="pm-header">
      <div class="section-label" style="padding:0;">Catalogue</div>
      <div class="pm-count">{n} produit{"s" if n != 1 else ""}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Ajout ──
    label_add = "− Annuler" if st.session_state.pm_show_add else "+ Nouveau produit"
    if st.button(label_add, key="toggle_add", use_container_width=True):
        st.session_state.pm_show_add = not st.session_state.pm_show_add
        st.rerun()

    if st.session_state.pm_show_add:
        with st.container(border=True):
            data = _form_produit("new")
            if st.button("Enregistrer le produit", key="save_new_produit", use_container_width=True):
                if not data["nom"] or not data["categorie"]:
                    st.error("Le nom et la catégorie sont obligatoires.")
                elif produit_existe(data["nom"]):
                    st.error(f"« {data['nom']} » existe déjà.")
                else:
                    add_produit(data["nom"], data["categorie"], data["fournisseur"],
                                data["unite"], data["seuil_alerte"], data["quantite_initiale"])
                    st.success(f"« {data['nom']} » ajouté.")
                    st.session_state.pm_show_add = False
                    st.rerun()

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # ── Liste ──
    if df.empty:
        st.markdown('<div class="pm-empty">Aucun produit dans le catalogue pour l’instant</div>', unsafe_allow_html=True)
        return

    for cat in sorted(df["categorie"].dropna().unique()):
        st.markdown(f'<div class="section-label">{cat}</div>', unsafe_allow_html=True)
        bloc = df[df["categorie"] == cat]

        for _, row in bloc.iterrows():
            nom = row["nom"]
            is_editing = st.session_state.pm_editing == nom
            is_confirming = st.session_state.pm_confirm_delete == nom

            st.markdown(f"""
            <div class="pm-card">
              <div class="pm-name">{nom}</div>
              <div class="pm-meta">{row.get('fournisseur') or '—'} · {row.get('unite') or '—'} · seuil {int(row.get('seuil_alerte') or 0)}</div>
            </div>
            """, unsafe_allow_html=True)

            if is_confirming:
                st.markdown(f'<div class="box-ko"><strong>Supprimer « {nom} » ?</strong><p>Le produit et son historique de stock seront définitivement retirés.</p></div>', unsafe_allow_html=True)
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("Confirmer la suppression", key=f"delconfirm_{nom}", use_container_width=True):
                        delete_produit(nom)
                        st.session_state.pm_confirm_delete = None
                        st.success(f"« {nom} » supprimé.")
                        st.rerun()
                with cc2:
                    if st.button("Annuler", key=f"delcancel_{nom}", use_container_width=True):
                        st.session_state.pm_confirm_delete = None
                        st.rerun()
            elif is_editing:
                with st.container(border=True):
                    data = _form_produit(f"edit_{nom}", defaults=row.to_dict())
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        if st.button("Enregistrer", key=f"savedit_{nom}", use_container_width=True):
                            if not data["nom"] or not data["categorie"]:
                                st.error("Le nom et la catégorie sont obligatoires.")
                            else:
                                update_produit(nom, data["nom"], data["categorie"], data["fournisseur"],
                                               data["unite"], data["seuil_alerte"])
                                st.session_state.pm_editing = None
                                st.success("Produit mis à jour.")
                                st.rerun()
                    with ec2:
                        if st.button("Annuler", key=f"editcancel_{nom}", use_container_width=True):
                            st.session_state.pm_editing = None
                            st.rerun()
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Modifier", key=f"edit_{nom}", use_container_width=True):
                        st.session_state.pm_editing = nom
                        st.rerun()
                with b2:
                    if st.button("Supprimer", key=f"del_{nom}", use_container_width=True):
                        st.session_state.pm_confirm_delete = nom
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
def page_admin():
    df = get_stocks()
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Exporter CSV", data=csv,
        file_name=f"stock_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv", use_container_width=True
    )

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.connecte:
    page_connexion()
else:
    # Topbar
    col_brand, col_right = st.columns([3, 2])
    with col_brand:
        st.markdown(f"""
        <div class="topbar">
          <div class="topbar-brand">
            <div class="topbar-mark">{NOM_RESTO[0]}</div>
            <div class="topbar-name">{NOM_RESTO}</div>
          </div>
        </div>""", unsafe_allow_html=True)
    with col_right:
        role_label = "Patron" if st.session_state.role == "patron" else "Employé"
        st.markdown(f'<div style="padding-top:16px;display:flex;justify-content:flex-end;gap:6px;"><span class="badge-role">{role_label}</span></div>', unsafe_allow_html=True)
        if st.button("Quitter", key="logout"):
            st.session_state.connecte = False
            st.session_state.role = None
            try:
                cookies.remove(COOKIE_NAME)
            except Exception:
                pass
            st.rerun()

    # Tabs
    tab_labels = ["Stock", "Scanner", "Historique"]
    if st.session_state.role == "patron":
        tab_labels += ["Produits", "Admin"]
    tabs = st.tabs(tab_labels)

    with tabs[0]: page_stock()
    with tabs[1]: page_scanner()
    with tabs[2]: page_historique()
    if st.session_state.role == "patron" and len(tabs) == 5:
        with tabs[3]: page_produits()
        with tabs[4]: page_admin()
