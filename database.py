import sqlite3
import pandas as pd
from datetime import datetime

DB = "stocks.db"

PRODUITS = [
    # (nom, categorie, fournisseur, unite, seuil_alerte)
    ("Steak Strié 80g",              "Surgelés / Viandes",  "Fournisseur 2", "pcs",        5),
    ("Bacon de bœuf 500g",           "Surgelés / Viandes",  "Fournisseur 2", "paquets",    3),
    ("Nuggets Farmer 810g",          "Surgelés / Viandes",  "Fournisseur 2", "kg",         2),
    ("Aiguillette crunchy halal 1kg","Surgelés / Viandes",  "Metro",         "kg",         3),
    ("Country style steak poulet",   "Surgelés / Viandes",  "Metro",         "kg",         4),
    ("Country style wings hot",      "Surgelés / Viandes",  "Metro",         "kg",         4),
    ("Oumaty Chicken tex mex 2.5kg", "Surgelés / Viandes",  "Metro",         "kg",         2),
    ("Mozzarella stick Metro 1kg",   "Snacks & Entrées",    "Metro",         "kg",         2),
    ("Chilli cheese nuggets 1kg",    "Snacks & Entrées",    "Metro",         "kg",         2),
    ("Onions rings Metro 1kg",       "Snacks & Entrées",    "Metro",         "kg",         2),
    ("Bouchée camembert 1kg",        "Snacks & Entrées",    "Fournisseur 2", "kg",         2),
    ("Galette de pomme de terre",    "Snacks & Entrées",    "Fournisseur 2", "paquets",    2),
    ("Buche de Chèvre Soignon 1kg",  "Fromages",            "Metro",         "kg",         2),
    ("Raclette Rochambeau",          "Fromages",            "Metro",         "barquettes", 2),
    ("Cheddar liquide Dairymaid 1L", "Fromages",            "Fournisseur 2", "L",          2),
    ("Cheddar Dairymaid 88 tr.",     "Fromages",            "Fournisseur 2", "paquets",    2),
    ("Salade Iceberg",               "Légumes & Frais",     "Metro",         "pcs",        4),
    ("Coleslaw Metro 1.5kg",         "Légumes & Frais",     "Metro",         "kg",         2),
    ("Oignons rouges 5kg",           "Légumes & Frais",     "Metro",         "sacs",       1),
    ("Pomme de terre Agria 25kg",    "Légumes & Frais",     "Metro",         "sacs",       2),
    ("Cornichons Classic Foods",     "Sauces & Condiments", "Metro",         "boites",     2),
    ("Jalapeños 810g",               "Sauces & Condiments", "Metro",         "boites",     2),
    ("Sriracha Flying Goose 455ml",  "Sauces & Condiments", "Metro",         "bouteilles", 2),
    ("Moutarde French's 2.9kg",      "Sauces & Condiments", "Metro",         "kg",         2),
    ("Mayonnaise Snack 4.7kg",       "Sauces & Condiments", "Metro",         "kg",         2),
    ("Lune de Miel 1kg",             "Sauces & Condiments", "Metro",         "kg",         2),
    ("Ketchup The Farm",             "Sauces & Condiments", "Fournisseur 2", "bidons",     1),
    ("Sauce blanche",                "Sauces & Condiments", "Fournisseur 2", "seaux",      1),
    ("Magic Onions",                 "Sauces & Condiments", "Fournisseur 2", "biberons",   1),
    ("Paprika doux",                 "Épices",              "Metro",         "unités",     1),
    ("Poivre concassé",              "Épices",              "Metro",         "unités",     1),
    ("Ail en poudre",                "Épices",              "Metro",         "unités",     1),
    ("Poivre noir",                  "Épices",              "Fournisseur 2", "unités",     1),
    ("Huile tournesol Aro 10L",      "Huiles",              "Metro",         "bouteilles", 2),
    ("Coca Cola 33cl",               "Boissons",            "Metro",         "unités",     12),
    ("Coca Cherry 33cl",             "Boissons",            "Metro",         "unités",     12),
    ("Coca Zero 33cl",               "Boissons",            "Metro",         "unités",     12),
    ("Cristalline Pêche 50cl",       "Boissons",            "Metro",         "bouteilles", 6),
    ("Cristalline Fraise 50cl",      "Boissons",            "Metro",         "bouteilles", 6),
    ("Ice Tea 33cl x24",             "Boissons",            "Metro",         "packs",      2),
    ("Oasis Tropical 33cl x24",      "Boissons",            "Metro",         "packs",      2),
    ("Sprite 33cl",                  "Boissons",            "Fournisseur 2", "unités",     6),
    ("Fanta 33cl",                   "Boissons",            "Fournisseur 2", "unités",     6),
    ("Coca Cola 1.25L",              "Boissons",            "Fournisseur 2", "bouteilles", 4),
    ("Tartes chocolat coco x8",      "Desserts",            "Fournisseur 2", "tartes",     1),
    ("Tartes aux Daims x12",         "Desserts",            "Fournisseur 2", "tartes",     1),
    ("Spéculoos topping",            "Desserts",            "Metro",         "flacons",    2),
    ("Oreo biscuits",                "Desserts",            "Metro",         "sachets",    2),
    ("Metro Chef biscuit cuiller",   "Desserts",            "Metro",         "cartons",    1),
    ("Gants noirs L",                "Hygiène",             "Metro",         "boites",     2),
    ("Liquide vaisselle",            "Hygiène",             "Metro",         "bouteilles", 2),
    ("Sac poubelle 130L",            "Hygiène",             "Metro",         "rouleaux",   2),
    ("Barquette frites x200",        "Emballages",          "Metro",         "cartons",    1),
    ("Sac kraft x250",               "Emballages",          "Fournisseur 2", "paquets",    1),
    ("Papier frites SC13",           "Emballages",          "Fournisseur 2", "rouleaux",   1),
]

def connexion():
    return sqlite3.connect(DB)

def init_db(restaurants):
    """Crée les tables et insère les données si elles n'existent pas encore."""
    con = connexion()
    cur = con.cursor()

    # Tables
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS produits (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nom          TEXT NOT NULL,
            categorie    TEXT,
            fournisseur  TEXT,
            unite        TEXT,
            seuil_alerte INTEGER DEFAULT 2
        );

        CREATE TABLE IF NOT EXISTS stocks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant   TEXT NOT NULL,
            produit      TEXT NOT NULL,
            quantite     INTEGER DEFAULT 0,
            date_maj     TEXT,
            UNIQUE(restaurant, produit)
        );

        CREATE TABLE IF NOT EXISTS historique (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date          TEXT,
            restaurant    TEXT,
            produit       TEXT,
            ancienne_qte  INTEGER,
            nouvelle_qte  INTEGER
        );
    """)

    # Insérer les produits si table vide
    if cur.execute("SELECT COUNT(*) FROM produits").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO produits (nom, categorie, fournisseur, unite, seuil_alerte) VALUES (?,?,?,?,?)",
            PRODUITS
        )
        print(f"✅ {len(PRODUITS)} produits insérés")

    # Insérer les stocks si table vide
    if cur.execute("SELECT COUNT(*) FROM stocks").fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = [
            (resto, p[0], 0, now)
            for resto in restaurants
            for p in PRODUITS
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO stocks (restaurant, produit, quantite, date_maj) VALUES (?,?,?,?)",
            rows
        )
        print(f"✅ Stocks initialisés pour {len(restaurants)} restaurants")

    con.commit()
    con.close()

# ── Lectures ──────────────────────────────────────────────────────────────────

def get_stocks(restaurant=None):
    con = connexion()
    if restaurant:
        df = pd.read_sql("""
            SELECT s.restaurant, s.produit, s.quantite, s.date_maj,p.id,
                   p.categorie, p.fournisseur, p.unite, p.seuil_alerte
            FROM stocks s
            JOIN produits p ON s.produit = p.nom
            WHERE s.restaurant = ?
            ORDER BY p.categorie, s.produit
        """, con, params=(restaurant,))
    else:
        df = pd.read_sql("""
            SELECT s.restaurant, s.produit, s.quantite, s.date_maj,p.id,
                   p.categorie, p.fournisseur, p.unite, p.seuil_alerte
            FROM stocks s
            JOIN produits p ON s.produit = p.nom
            ORDER BY s.restaurant, p.categorie, s.produit
        """, con)
    con.close()
    return df

def get_historique(n_jours=30):
    con = connexion()
    df  = pd.read_sql("""
        SELECT * FROM historique
        WHERE date >= datetime('now', ?)
        ORDER BY date DESC
    """, con, params=(f"-{n_jours} days",))
    con.close()
    return df

# ── Écriture ──────────────────────────────────────────────────────────────────

def update_stock(restaurant, produit, ancienne_qte, nouvelle_qte):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    con = connexion()
    cur = con.cursor()
    cur.execute("""
        UPDATE stocks SET quantite = ?, date_maj = ?
        WHERE restaurant = ? AND produit = ?
    """, (nouvelle_qte, now, restaurant, produit))
    cur.execute("""
        INSERT INTO historique (date, restaurant, produit, ancienne_qte, nouvelle_qte)
        VALUES (?, ?, ?, ?, ?)
    """, (now, restaurant, produit, ancienne_qte, nouvelle_qte))
    con.commit()
    con.close()
