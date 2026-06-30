"""
app.py — Maïga Smash | Gestion de stock mobile
Lancement : streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

from config import NOM_RESTO, COULEUR_PRINCIPALE, verifier_mdp
from database import (
    init_db, get_stocks, get_historique, update_stock,
    get_produit_by_barcode, enregistrer_code_barres, RESTAURANTS
)

init_db()

st.set_page_config(
    page_title=NOM_RESTO,
    page_icon="🍔",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ACC = COULEUR_PRINCIPALE  # #F5A623

st.markdown(f"""
<style>
  * {{ box-sizing: border-box; }}
  .stApp {{ background: #161616 !important; color: #f0f0f0; font-family: 'Inter', sans-serif; }}
  header[data-testid="stHeader"] {{ display: none; }}
  .stDeployButton, footer {{ display: none; }}
  section[data-testid="stSidebar"] {{ display: none; }}
  .block-container {{ padding: 0 12px 40px !important; max-width: 480px !important; margin: auto; }}

  /* ── Topbar ── */
  .topbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 0 10px; position: sticky; top: 0;
    background: #161616; z-index: 100;
  }}
  .topbar-title {{ font-size: 1.15rem; font-weight: 900; color: {ACC}; }}
  .topbar-right  {{ display: flex; align-items: center; gap: 8px; }}
  .topbar-role   {{ font-size: 0.7rem; color: #666; background: #222; padding: 3px 9px; border-radius: 20px; }}
  .topbar-logout {{
    font-size: 0.7rem; color: #555; background: #1e1e1e;
    border: 1px solid #2e2e2e; border-radius: 20px; padding: 3px 10px;
    cursor: pointer; text-decoration: none;
  }}

  /* ── KPI ── */
  .kpi-row {{ display: flex; gap: 8px; margin-bottom: 8px; }}
  .kpi {{
    flex: 1; background: #212121; border-radius: 12px 12px 0 0;
    padding: 12px 8px 8px; text-align: center; border: 1px solid #2e2e2e;
    border-bottom: none;
  }}
  .kpi .num {{ font-size: 1.9rem; font-weight: 800; line-height: 1; }}
  .kpi .lab {{ font-size: 0.6rem; color: #666; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; }}
  .kpi.rouge .num  {{ color: #ff4444; }}
  .kpi.orange .num {{ color: {ACC}; }}
  .kpi.blanc .num  {{ color: #f0f0f0; }}

  /* Bouton "tap to filter" collé sous chaque carte KPI, même largeur, coins arrondis en bas */
  div[data-testid="column"]:has(button[key^="kpi_"]) .stButton > button {{
    width: 100% !important; height: 22px !important;
    border-radius: 0 0 12px 12px !important;
    border: 1px solid #2e2e2e !important; border-top: none !important;
    background: #1a1a1a !important; color: #444 !important;
    font-size: 0.62rem !important; font-weight: 600 !important;
    padding: 0 !important; min-height: unset !important; margin-top: -1px;
  }}
  div[data-testid="column"]:has(button[key^="kpi_"]) .stButton > button:hover {{
    color: {ACC} !important; border-color: {ACC} !important;
  }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    gap: 4px; background: #1e1e1e; border-radius: 12px;
    padding: 4px; margin-bottom: 14px;
  }}
  .stTabs [data-baseweb="tab"] {{
    background: transparent; border-radius: 9px; color: #555;
    font-weight: 600; font-size: 0.85rem; padding: 8px 0;
    flex: 1; justify-content: center; border: none !important;
  }}
  .stTabs [aria-selected="true"] {{ background: #2e2e2e !important; color: {ACC} !important; }}
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

  /* ── Recherche ── */
  .stTextInput input {{
    background: #212121 !important; border: 1px solid #2e2e2e !important;
    border-radius: 10px !important; color: #f0f0f0 !important;
    padding: 10px 14px !important; font-size: 0.9rem !important;
  }}
  .stTextInput label {{ display: none; }}

  /* Suggestions dropdown */
  .suggestion-box {{
    background: #242424; border: 1px solid #333; border-radius: 10px;
    margin-top: -8px; margin-bottom: 12px; overflow: hidden;
  }}
  .suggestion-item {{
    padding: 10px 14px; font-size: 0.85rem; cursor: pointer;
    border-bottom: 1px solid #2e2e2e; display: flex;
    justify-content: space-between; align-items: center;
  }}
  .suggestion-item:last-child {{ border-bottom: none; }}
  .suggestion-cat {{ font-size: 0.65rem; color: #555; }}

  /* ── Filtre catégorie (selectbox) ── */
  div[data-testid="stSelectbox"] {{ margin-bottom: 12px; }}
  div[data-testid="stSelectbox"] > div > div {{
    background: #212121 !important; border: 1px solid #2e2e2e !important;
    border-radius: 10px !important; color: #f0f0f0 !important;
  }}

  /* ── Label catégorie section ── */
  .cat-label {{
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.2px; color: #444;
    padding: 10px 0 5px; border-bottom: 1px solid #222; margin-bottom: 6px;
  }}

  /* ── Ligne produit ── */
  .prod-nom  {{ font-size: 0.88rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .prod-sub  {{ font-size: 0.67rem; color: #555; margin-top: 1px; }}
  .prod-seuil {{ font-size: 0.62rem; color: #383838; margin-top: 4px; }}

  .prod-qty {{ font-size: 1.55rem; font-weight: 800; line-height: 1; text-align: center; }}
  .prod-qty.ok     {{ color: #22cc55; }}
  .prod-qty.warn   {{ color: {ACC}; }}
  .prod-qty.danger {{ color: #ff4444; }}
  .prod-unite {{ font-size: 0.63rem; color: #555; text-align: center; margin-top: 1px; }}

  /* Boutons +/- (page stock) */
  .stButton > button {{
    background: #252525 !important; color: #bbb !important;
    border: 1px solid #333 !important; border-radius: 8px !important;
    font-size: 1.2rem !important; font-weight: 700 !important;
    width: 36px !important; height: 36px !important;
    padding: 0 !important; line-height: 1 !important; min-height: unset !important;
  }}
  .stButton > button:hover {{ border-color: {ACC} !important; color: {ACC} !important; }}

  /* Boutons +/- larges sur la carte produit (2 lignes) */
  div[data-testid="column"]:has(button[key^="m_"]) .stButton > button,
  div[data-testid="column"]:has(button[key^="p_"]) .stButton > button {{
    width: 100% !important; height: 44px !important; font-size: 1.4rem !important;
  }}

  .prod-sep {{ border: none; border-top: 1px solid #1e1e1e; margin: 2px 0 4px; }}

  /* ── Scanner ── */
  .scan-area {{
    background: #1e1e1e; border: 2px dashed #2e2e2e;
    border-radius: 14px; padding: 32px 20px; text-align: center; margin: 8px 0 18px;
  }}
  .scan-icon {{ font-size: 3rem; margin-bottom: 8px; }}
  .scan-hint {{ font-size: 0.78rem; color: #555; line-height: 1.6; }}
  .box-ok {{ background: #1a2e1a; border: 1px solid #22aa44; border-radius: 10px; padding: 14px; margin: 10px 0; }}
  .box-ko {{ background: #2e1a1a; border: 1px solid #ff4444; border-radius: 10px; padding: 14px; margin: 10px 0; }}
  .box-ok strong, .box-ko strong {{ font-size: 0.92rem; }}
  .box-ok p, .box-ko p {{ font-size: 0.77rem; color: #aaa; margin-top: 4px; }}

  /* ── Historique ── */
  .histo-item {{
    background: #212121; border-radius: 10px;
    padding: 11px 14px; margin-bottom: 7px;
    border-left: 3px solid #333; font-size: 0.82rem;
  }}
  .histo-item.plus  {{ border-color: #22cc55; }}
  .histo-item.moins {{ border-color: #ff4444; }}
  .histo-meta {{ color: #555; font-size: 0.67rem; margin-top: 3px; }}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "connecte": False, "role": None,
    "restaurant": RESTAURANTS[0], "kpi_filter": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════════
# CONNEXION
# ═══════════════════════════════════════════════════════════════════════════════
def page_connexion():
    st.markdown(f"""
    <div style="text-align:center; padding: 52px 0 36px;">
      <div style="font-size:3.5rem;">🍔</div>
      <div style="font-size:1.6rem; font-weight:900; color:{ACC}; margin-top:8px;">{NOM_RESTO}</div>
      <div style="font-size:0.8rem; color:#555; margin-top:4px;">Gestion des stocks</div>
    </div>
    """, unsafe_allow_html=True)
    role = st.selectbox("", ["Employé", "Patron"], label_visibility="collapsed")
    mdp  = st.text_input("", type="password", placeholder="Mot de passe", label_visibility="collapsed")
    if st.button("Se connecter", use_container_width=True):
        role_key = "employe" if role == "Employé" else "patron"
        if verifier_mdp(mdp, role_key):
            st.session_state.connecte = True
            st.session_state.role = role_key
            st.rerun()
        else:
            st.error("Mot de passe incorrect")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE STOCK
# ═══════════════════════════════════════════════════════════════════════════════
def page_stock():
    resto = st.session_state.restaurant
    df    = get_stocks(resto)

    n_total   = len(df)
    n_alertes = int((df["quantite"] <= df["seuil_alerte"]).sum())
    n_rupture = int((df["quantite"] == 0).sum())

    # KPI cliquables (filtre rupture / alerte)
    kpi_filter = st.session_state.kpi_filter
    bg_r = f"background:{('#ff444422')};border-color:#ff4444;" if kpi_filter == "rupture" else ""
    bg_a = f"background:{ACC}22;border-color:{ACC};" if kpi_filter == "alerte" else ""

    col_r, col_a, col_t = st.columns(3)
    with col_r:
        st.markdown(f'<div class="kpi rouge" style="{bg_r}"><div class="num">{n_rupture}</div><div class="lab">Ruptures</div></div>', unsafe_allow_html=True)
        if st.button("voir" if kpi_filter != "rupture" else "✓ actif", key="kpi_rupture_btn", use_container_width=True):
            st.session_state.kpi_filter = None if kpi_filter == "rupture" else "rupture"
            st.rerun()
    with col_a:
        st.markdown(f'<div class="kpi orange" style="{bg_a}"><div class="num">{n_alertes}</div><div class="lab">Alertes</div></div>', unsafe_allow_html=True)
        if st.button("voir" if kpi_filter != "alerte" else "✓ actif", key="kpi_alerte_btn", use_container_width=True):
            st.session_state.kpi_filter = None if kpi_filter == "alerte" else "alerte"
            st.rerun()
    with col_t:
        st.markdown(f'<div class="kpi blanc"><div class="num">{n_total}</div><div class="lab">Produits</div></div>', unsafe_allow_html=True)
        if st.button("tout", key="kpi_total_btn", use_container_width=True):
            st.session_state.kpi_filter = None
            st.rerun()

    if kpi_filter:
        label = "🚨 Ruptures uniquement" if kpi_filter == "rupture" else "⚠️ Alertes stock bas uniquement"
        st.caption(f"{label} — touchez à nouveau le KPI pour annuler")

    # Recherche avec suggestions
    recherche = st.text_input("", placeholder="🔍 Rechercher un produit...", key="search", label_visibility="collapsed")

    if recherche and len(recherche) >= 2:
        suggestions = df[df["produit"].str.contains(recherche, case=False, na=False)].head(6)
        if not suggestions.empty:
            html_sugg = '<div class="suggestion-box">'
            for _, s in suggestions.iterrows():
                qte = int(s["quantite"])
                seuil = int(s["seuil_alerte"])
                couleur = "#ff4444" if qte == 0 else (ACC if qte <= seuil else "#22cc55")
                html_sugg += f"""
                <div class="suggestion-item">
                  <div>
                    <span>{s['produit']}</span><br>
                    <span class="suggestion-cat">{s['categorie']}</span>
                  </div>
                  <span style="color:{couleur}; font-weight:700; font-size:1rem;">{qte} <span style="font-size:0.65rem;color:#555;">{s['unite']}</span></span>
                </div>"""
            html_sugg += '</div>'
            st.markdown(html_sugg, unsafe_allow_html=True)

    # Filtre catégorie — menu déroulant simple
    categories = ["Toutes les catégories"] + sorted(df["categorie"].unique().tolist())
    cat_active = st.selectbox("Filtrer par catégorie", categories, key="cat_select", label_visibility="collapsed")

    # Filtrage
    df_filtre = df.copy()
    if recherche:
        df_filtre = df_filtre[df_filtre["produit"].str.contains(recherche, case=False, na=False)]
    if cat_active != "Toutes les catégories":
        df_filtre = df_filtre[df_filtre["categorie"] == cat_active]
    if kpi_filter == "rupture":
        df_filtre = df_filtre[df_filtre["quantite"] == 0]
    elif kpi_filter == "alerte":
        df_filtre = df_filtre[(df_filtre["quantite"] > 0) & (df_filtre["quantite"] <= df_filtre["seuil_alerte"])]

    # Produits par catégorie
    for cat in df_filtre["categorie"].unique():
        bloc = df_filtre[df_filtre["categorie"] == cat]
        st.markdown(f'<div class="cat-label">{cat}</div>', unsafe_allow_html=True)

        for _, row in bloc.iterrows():
            qte     = int(row["quantite"])
            seuil   = int(row["seuil_alerte"])
            unite   = row["unite"]
            produit = row["produit"]
            qty_cls = "danger" if qte == 0 else ("warn" if qte <= seuil else "ok")

            # Ligne 1 : nom + fournisseur + seuil
            st.markdown(f"""
            <div style="padding: 8px 0 2px;">
              <div class="prod-nom">{produit}</div>
              <div class="prod-sub">{row['fournisseur']} · Seuil : {seuil} {unite}</div>
            </div>
            """, unsafe_allow_html=True)

            # Ligne 2 : − | quantité | +
            col_moins, col_qty, col_plus = st.columns([1, 2, 1])
            with col_moins:
                if st.button("−", key=f"m_{produit}", use_container_width=True):
                    if qte > 0:
                        update_stock(resto, produit, qte, qte - 1)
                        st.rerun()
            with col_qty:
                st.markdown(f"""
                <div style="text-align:center;">
                  <div class="prod-qty {qty_cls}">{qte}</div>
                  <div class="prod-unite">{unite}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_plus:
                if st.button("+", key=f"p_{produit}", use_container_width=True):
                    update_stock(resto, produit, qte, qte + 1)
                    st.rerun()

            st.markdown("<hr class='prod-sep'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE SCANNER
# ═══════════════════════════════════════════════════════════════════════════════
def page_scanner():
    resto = st.session_state.restaurant

    mode = st.radio("Mode", ["📷 Caméra", "⌨️ Saisie manuelle"], horizontal=True, label_visibility="collapsed")

    code = None

    if mode == "📷 Caméra":
        st.caption("Autorisez l'accès à la caméra si demandé, puis visez le code-barres.")

        scan_html = f"""
        <div id="reader" style="width:100%; border-radius:12px; overflow:hidden;"></div>
        <div id="scan-result" style="margin-top:10px; padding:10px; border-radius:8px;
             background:#1a2e1a; color:#22cc55; font-size:0.85rem; text-align:center; display:none;">
        </div>
        <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
        <script>
          function startScanner() {{
            const resultBox = document.getElementById('scan-result');
            const html5QrCode = new Html5Qrcode("reader");
            const config = {{ fps: 10, qrbox: {{ width: 250, height: 150 }} }};

            function onScanSuccess(decodedText) {{
              resultBox.style.display = "block";
              resultBox.innerText = "✅ Code détecté : " + decodedText + " — mise à jour...";
              html5QrCode.stop().then(() => {{
                const topUrl = window.parent.location.href.split('?')[0];
                window.parent.location.href = topUrl + "?scanned_code=" + encodeURIComponent(decodedText);
              }});
            }}

            html5QrCode.start(
              {{ facingMode: "environment" }},
              config,
              onScanSuccess
            ).catch(err => {{
              resultBox.style.display = "block";
              resultBox.style.background = "#2e1a1a";
              resultBox.style.color = "#ff4444";
              resultBox.innerText = "❌ Caméra inaccessible : " + err;
            }});
          }}
          startScanner();
        </script>
        """
        components.html(scan_html, height=320)

        # Récupération du code scanné via query params
        query_code = st.query_params.get("scanned_code")
        if query_code:
            code = query_code
            st.query_params.clear()

        st.divider()
        st.caption("Le scan ne fonctionne pas ? Utilisez la saisie manuelle ci-dessous.")
        code_manuel = st.text_input("", placeholder="Ou tapez le code ici...", key="barcode_fallback", label_visibility="collapsed")
        if code_manuel:
            code = code_manuel
    else:
        code = st.text_input("", placeholder="Entrez le code-barres", key="barcode_manual", label_visibility="collapsed")

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
                qty_cls = "danger" if qte == 0 else ("warn" if qte <= seuil else "ok")

                st.markdown(f"""
                <div class="box-ok">
                  <strong>✅ {produit_nom}</strong>
                  <p>Stock actuel : <span class="prod-qty {qty_cls}" style="font-size:1.1rem;display:inline;">{qte}</span> {unite}</p>
                </div>
                """, unsafe_allow_html=True)

                qte_retrait = st.number_input("Quantité à retirer", min_value=1, max_value=max(1, qte), value=1, step=1)
                if st.button(f"✅ Retirer {qte_retrait} {unite}", use_container_width=True):
                    nouvelle_qte = max(0, qte - qte_retrait)
                    update_stock(resto, produit_nom, qte, nouvelle_qte)
                    st.success(f"✅ {produit_nom} : {qte} → {nouvelle_qte} {unite}")
                    if nouvelle_qte <= seuil:
                        st.warning(f"⚠️ Stock bas sur {produit_nom} !")
                    st.rerun()
        else:
            st.markdown(f"""
            <div class="box-ko">
              <strong>❓ Code inconnu : {code}</strong>
              <p>Associez ce code à un produit pour les prochains scans</p>
            </div>
            """, unsafe_allow_html=True)
            df = get_stocks(resto)
            produits_liste = sorted(df["produit"].tolist())
            choix = st.selectbox("Associer à :", produits_liste)
            if st.button("💾 Enregistrer l'association", use_container_width=True):
                enregistrer_code_barres(choix, code)
                st.success(f"✅ Code {code} associé à « {choix} »")
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════
def page_historique():
    df = get_historique(30)
    if df.empty:
        st.info("Aucun mouvement sur les 30 derniers jours.")
        return

    df["variation"] = df["nouvelle_qte"] - df["ancienne_qte"]
    n_plus  = int((df["variation"] > 0).sum())
    n_moins = int((df["variation"] < 0).sum())

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi blanc"><div class="num">{len(df)}</div><div class="lab">Mouvements</div></div>
      <div class="kpi rouge"><div class="num">↓{n_moins}</div><div class="lab">Retraits</div></div>
      <div class="kpi orange"><div class="num">↑{n_plus}</div><div class="lab">Ajouts</div></div>
    </div>
    """, unsafe_allow_html=True)

    for _, row in df.head(60).iterrows():
        var = int(row["variation"])
        cls = "plus" if var > 0 else "moins"
        signe = f"+{var}" if var > 0 else str(var)
        couleur = "#22cc55" if var > 0 else "#ff4444"
        date_str = str(row["date"])[:16]
        st.markdown(f"""
        <div class="histo-item {cls}">
          <strong>{row['produit']}</strong>
          &nbsp;<span style="color:{couleur}; font-weight:700;">{signe}</span>
          &nbsp;<span style="color:#555;">({row['ancienne_qte']} → {row['nouvelle_qte']})</span>
          <div class="histo-meta">{date_str} · {row['restaurant']}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
def page_admin():
    df = get_stocks()
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exporter CSV", data=csv,
        file_name=f"stock_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv", use_container_width=True
    )

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.connecte:
    page_connexion()
else:
    role_label = "👑 Patron" if st.session_state.role == "patron" else "👤 Employé"

    # Topbar avec déconnexion toujours visible
    col_title, col_right = st.columns([3, 2])
    with col_title:
        st.markdown(f'<div class="topbar-title" style="padding-top:14px;">🍔 {NOM_RESTO}</div>', unsafe_allow_html=True)
    with col_right:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f'<div style="padding-top:14px;"><span class="topbar-role">{role_label}</span></div>', unsafe_allow_html=True)
        with c2:
            if st.button("🚪 Quitter", key="logout"):
                st.session_state.connecte = False
                st.session_state.role = None
                st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Onglets en haut
    tab_labels = ["📦 Stock", "📷 Scanner", "📊 Historique"]
    if st.session_state.role == "patron":
        tab_labels.append("⚙️ Admin")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        page_stock()
    with tabs[1]:
        page_scanner()
    with tabs[2]:
        page_historique()
    if st.session_state.role == "patron" and len(tabs) == 4:
        with tabs[3]:
            page_admin()
