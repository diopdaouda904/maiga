import os
import pandas as pd
from datetime import datetime
from supabase import create_client

# ── Connexion ──────────────────────────────────────────────────────────────────
def get_client():
    try:
        import streamlit as st
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)

RESTAURANTS = ["Maïga Smash"]

def init_db():
    pass  # Tables créées via SQL Editor Supabase

# ── Lectures ───────────────────────────────────────────────────────────────────
def get_stocks(restaurant=None):
    sb = get_client()
    stocks = sb.table("stocks").select("*").execute().data
    produits = sb.table("produits").select("*").execute().data

    df_s = pd.DataFrame(stocks)
    df_p = pd.DataFrame(produits)

    if df_s.empty or df_p.empty:
        return pd.DataFrame()

    df = df_s.merge(df_p, left_on="produit", right_on="nom", suffixes=("", "_p"))
    df = df[["restaurant", "produit", "quantite", "date_maj",
             "categorie", "fournisseur", "unite", "seuil_alerte"]]

    if restaurant:
        df = df[df["restaurant"] == restaurant]

    return df.sort_values(["categorie", "produit"]).reset_index(drop=True)

def get_historique(n_jours=30):
    sb = get_client()
    rows = sb.table("historique").select("*").order("date", desc=True).limit(200).execute().data
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def get_produit_by_barcode(code_barres):
    sb = get_client()
    res = sb.table("produits").select("nom").eq("code_barres", code_barres).execute()
    return res.data[0]["nom"] if res.data else None

def enregistrer_code_barres(produit_nom, code_barres):
    sb = get_client()
    sb.table("produits").update({"code_barres": code_barres}).eq("nom", produit_nom).execute()

# ── Écriture ───────────────────────────────────────────────────────────────────
def update_stock(restaurant, produit, ancienne_qte, nouvelle_qte):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sb  = get_client()

    sb.table("stocks").upsert({
        "restaurant": restaurant,
        "produit":    produit,
        "quantite":   nouvelle_qte,
        "date_maj":   now
    }, on_conflict="restaurant,produit").execute()

    sb.table("historique").insert({
        "date":         now,
        "restaurant":   restaurant,
        "produit":      produit,
        "ancienne_qte": ancienne_qte,
        "nouvelle_qte": nouvelle_qte
    }).execute()
