import dash
from dash import dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
import config
import json
import database as db


db.init_db([config.NOM_RESTO])

def get_statut(quantite, seuil):
    if quantite == 0: return "🔴 RUPTURE"
    if quantite <= seuil: return "🟠 ALERTE"
    return "🟢 OK"

# ══════════════════════════════════════════════════════════════════════════════
#  INITIALISATION DE L'APP
# ══════════════════════════════════════════════════════════════════════════════
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title=f"{config.NOM_RESTO} - Stocks",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0"}]
)
server = app.server

# ══════════════════════════════════════════════════════════════════════════════
#  LAYOUT GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
app.layout = html.Div([
    dcc.Store(id="store-session", storage_type="session"),

    # ── ÉCRAN DE CONNEXION ──
    html.Div(id="section-login", className="p-3", children=[
        html.Div([
            html.H1("🍔", className="text-center mb-2", style={"fontSize": "50px"}),
            html.H2(config.NOM_RESTO, className="text-center text-white mb-1", style={"fontWeight": "bold"}),
            html.P("Gestion des stocks", className="text-center mb-5", style={"color": config.COULEUR_PRINCIPALE}),
            
            dbc.Card([
                dbc.CardBody([
                    html.Label("Mot de passe", className="form-label text-warning fw-bold text-uppercase mb-2", style={"fontSize": "12px"}),
                    dbc.Input(
                        id="inp-password", type="password", 
                        placeholder="Saisir le mot de passe...",
                        className="mb-4 p-3",
                        style={"background": "#222", "color": "#FFF", "border": "none", "borderRadius": "10px"}
                    ),
                    html.Button("Entrer", id="btn-login", className="btn-smash w-100 p-3", style={"borderRadius": "10px", "fontSize": "18px"}),
                    html.Div(id="login-msg", className="text-center text-danger mt-3 fw-bold")
                ])
            ], style={"background": "#1A1A1A", "border": "1px solid #333", "borderRadius": "15px"})
        ], style={"marginTop": "10vh", "maxWidth": "400px", "marginLeft": "auto", "marginRight": "auto"})
    ]),

    # ── VUE EMPLOYÉ (Saisie Rapide) ──
    html.Div(id="section-employe", style={"display": "none"}, children=[
        html.Div([
            html.Div([
                html.Span("🍔", style={"fontSize": "24px", "marginRight": "10px"}),
                html.Div(config.NOM_RESTO, className="fw-bold text-white", style={"fontSize": "18px"}),
            ], className="d-flex align-items-center"),
            html.Button("🚪", id="btn-logout-emp", className="btn-logout")
        ], className="navbar-mobile"),

        html.Div(id="notification-toast", className="fixed-top px-3", style={"top": "70px", "zIndex": 1050}),

        html.Div(className="content-mobile", children=[
            html.Div(id="kpis-employe", className="row g-2 mb-4"),
            html.H6("INVENTAIRE", className="section-header"),
            html.Div(id="liste-produits", className="d-flex flex-column gap-3 mb-5")
        ])
    ]),

    # ── VUE PATRON (Dashboard) ──
    html.Div(id="section-patron", style={"display": "none"}, children=[
        html.Div([
            html.Div([
                html.Span("📊", style={"fontSize": "24px", "marginRight": "10px"}),
                html.Div("Dashboard Patron", className="fw-bold text-white", style={"fontSize": "18px"}),
            ], className="d-flex align-items-center"),
            html.Button("🚪", id="btn-logout-patron", className="btn-logout")
        ], className="navbar-mobile"),

        html.Div(className="content-mobile", children=[
            html.Div(id="kpis-patron", className="row g-2 mb-4"),
            html.H6("PRODUITS CRITIQUES", className="section-header"),
            html.Div(id="liste-alertes", className="d-flex flex-column gap-2 mb-5")
        ])
    ])

], style={"minHeight": "100vh", "background": "#0D0D0D", "fontFamily": "Inter, sans-serif"})


# ══════════════════════════════════════════════════════════════════════════════
#  CSS INTÉGRÉ
# ══════════════════════════════════════════════════════════════════════════════
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body { background-color: #0D0D0D; touch-action: manipulation; }
            .navbar-mobile {
                background: #1A1A1A; padding: 15px 20px;
                border-bottom: 1px solid #333;
                display: flex; align-items: center; justify-content: space-between;
                position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
            }
            .content-mobile { padding: 80px 15px 30px 15px; max-width: 600px; margin: 0 auto; }
            .btn-smash { background: #F5A623; color: #000; font-weight: bold; border: none; cursor: pointer; }
            .btn-smash:active { opacity: 0.8; }
            .btn-logout { background: transparent; border: 1px solid #444; color: #FFF; border-radius: 8px; padding: 6px 12px; }
            .section-header { color: #666; font-weight: 700; letter-spacing: 1px; font-size: 12px; margin-bottom: 15px; }
            
            /* Cartes Produits */
            .card-produit { background: #1A1A1A; border-radius: 12px; padding: 15px; border: 1px solid #222; }
            .btn-qty { 
                background: #2A2A2A; color: #FFF; border: none; border-radius: 8px; 
                width: 45px; height: 45px; font-size: 20px; font-weight: bold;
                display: flex; align-items: center; justify-content: center;
            }
            .btn-qty:active { background: #F5A623; color: #000; }
            .kpi-box { background: #1A1A1A; border-radius: 10px; padding: 15px; text-align: center; border: 1px solid #222;}
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
'''

# ══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS COMPOSANTS
# ══════════════════════════════════════════════════════════════════════════════
def creer_carte_produit(row):
    statut = get_statut(row["quantite"], row["seuil_alerte"])
    couleur_qte = "#FF5252" if statut == "🔴 RUPTURE" else "#FFB74D" if statut == "🟠 ALERTE" else "#69F0AE"
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div(row["produit"], style={"color": "#FFF", "fontWeight": "600", "fontSize": "16px"}),
                html.Div(row["categorie"], style={"color": "#888", "fontSize": "12px"}),
            ]),
            html.Div([
                html.Span(row["quantite"], style={"color": couleur_qte, "fontWeight": "bold", "fontSize": "24px"}),
                html.Span(f" {row['unite']}", style={"color": "#666", "fontSize": "12px", "marginLeft": "4px"})
            ], className="text-end")
        ], className="d-flex justify-content-between align-items-center mb-3"),
        
        html.Div([
            html.Button("−", id={"type": "btn-moins", "id": row["id"]}, className="btn-qty"),
            html.Div(f"Seuil: {row['seuil_alerte']}", style={"color": "#555", "fontSize": "13px"}),
            html.Button("+", id={"type": "btn-plus", "id": row["id"]}, className="btn-qty"),
        ], className="d-flex justify-content-between align-items-center")
    ], className="card-produit")


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

# ── ROUTAGE (LOGIN / LOGOUT) ──
@app.callback(
    Output("store-session", "data"),
    Output("login-msg", "children"),
    Input("btn-login", "n_clicks"),
    State("inp-password", "value"),
    prevent_initial_call=True
)
def login(_, password):
    if password == config.MDP_EMPLOYE: return {"role": "employe","resto": config.NOM_RESTO}, ""
    if password == config.MDP_PATRON:  return {"role": "patron","resto": config.NOM_RESTO}, ""
    return {}, "Mot de passe incorrect"

@app.callback(
    Output("store-session", "data", allow_duplicate=True),
    Input("btn-logout-emp", "n_clicks"),
    Input("btn-logout-patron", "n_clicks"),
    prevent_initial_call=True
)
def logout(*_): return {}

@app.callback(
    Output("section-login", "style"),
    Output("section-employe", "style"),
    Output("section-patron", "style"),
    Input("store-session", "data")
)
def afficher_sections(session):
    if not session: return {"display": "block"}, {"display": "none"}, {"display": "none"}
    if session.get("role") == "employe": return {"display": "none"}, {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "none"}, {"display": "block"}


@app.callback(
    Output("liste-produits", "children"),
    Output("kpis-employe", "children"),
    Input("store-session", "data")
)
def charger_employe(session):
    # 1. Vérification de sécurité (Si pas de session ou pas employe, on vide tout)
    if not session or session.get("role") != "employe":
        return [], []
    
    # 2. Récupération propre du nom du restaurant
    resto = session.get("resto")
    print(f"DEBUG: Chargement pour : {resto}")
    
    # 3. Appel unique à la base de données
    df = db.get_stocks(resto)
    print(f"DEBUG: Nombre de lignes trouvées : {len(df)}")
    
    # Sécurité supplémentaire : si la base est vide, on retourne des listes vides
    if df.empty:
        return [], []

    # 4. Construction des cartes
    cartes = [creer_carte_produit(row) for _, row in df.iterrows()]
    
    # 5. Calcul des KPIs basés sur le vrai DataFrame 'df'
    nb_ruptures = sum(1 for _, r in df.iterrows() if r["quantite"] == 0)
    
    kpis = [
        html.Div(className="col-6", children=[
            html.Div(className="kpi-box", children=[
                html.Div("RUPTURES", style={"color": "#888", "fontSize": "11px", "fontWeight": "bold"}),
                html.Div(nb_ruptures, style={"color": "#FF5252", "fontSize": "28px", "fontWeight": "bold"})
            ])
        ]),
        html.Div(className="col-6", children=[
            html.Div(className="kpi-box", children=[
                html.Div("TOTAL PRODUITS", style={"color": "#888", "fontSize": "11px", "fontWeight": "bold"}),
                html.Div(len(df), style={"color": "#FFF", "fontSize": "28px", "fontWeight": "bold"})
            ])
        ])
    ]
    
    return cartes, kpis
# ── ACTIONS BOUTONS + / - ──
# ── ACTIONS BOUTONS + / - ──
@app.callback(
    Output("notification-toast", "children"),
    Output("liste-produits", "children", allow_duplicate=True),
    Output("kpis-employe", "children", allow_duplicate=True),
    Input({"type": "btn-plus", "id": ALL}, "n_clicks"),
    Input({"type": "btn-moins", "id": ALL}, "n_clicks"),
    State("store-session", "data"), # On a besoin de la session pour savoir quel resto
    prevent_initial_call=True
)
def update_stock(clicks_plus, clicks_moins, session):
    ctx = dash.callback_context
    if not ctx.triggered: return dash.no_update
    
    bouton_clique = ctx.triggered[0]["prop_id"].split(".")[0]
    info_bouton = json.loads(bouton_clique)
    
    action = info_bouton["type"]
    produit_id = info_bouton["id"]
    restaurant = session.get("resto") # Utilise le rôle comme nom de resto
    
    # 1. Lire la base actuelle
    df = db.get_stocks(restaurant)
    produit_row = df[df["id"] == produit_id].iloc[0]
    qte_actuelle = produit_row["quantite"]
    
    # 2. Calculer la nouvelle quantité
    nouvelle_qte = qte_actuelle + 1 if action == "btn-plus" else max(0, qte_actuelle - 1)
    
    # 3. ÉCRIRE DANS LA BASE SQL
    db.update_stock(restaurant, produit_row["produit"], qte_actuelle, nouvelle_qte)
    
    # ... (suite du code de la fonction)

    # 4. Rafraîchir l'affichage (re-lire la base après mise à jour)
    df = db.get_stocks(restaurant)
    toast = dbc.Alert(f"{produit_row['produit']} mis à jour", color="success", duration=2000, 
                      style={"background": "#00C853", "color": "#FFF", "border": "none", "textAlign": "center", "fontWeight": "bold"})
    
    cartes = [creer_carte_produit(row) for _, row in df.iterrows()]
    
    nb_ruptures = sum(1 for _, r in df.iterrows() if r["quantite"] == 0)
    
    kpis = [
        html.Div(className="col-6", children=[
            html.Div(className="kpi-box", children=[
                html.Div("RUPTURES", style={"color": "#888", "fontSize": "11px", "fontWeight": "bold"}),
                html.Div(nb_ruptures, style={"color": "#FF5252", "fontSize": "28px", "fontWeight": "bold"})
            ])
        ]),
        html.Div(className="col-6", children=[
            html.Div(className="kpi-box", children=[
                html.Div("TOTAL PRODUITS", style={"color": "#888", "fontSize": "11px", "fontWeight": "bold"}),
                html.Div(len(df), style={"color": "#FFF", "fontSize": "28px", "fontWeight": "bold"})
            ])
        ])
    ]
    
    return toast, cartes, kpis


# ── CHARGEMENT VUE PATRON ──
@app.callback(
    Output("liste-alertes", "children"),
    Output("kpis-patron", "children"),
    Input("store-session", "data")
)
def charger_patron(session):
    if not session or session.get("role") != "patron": return [], []
    
    df = db.get_stocks() # <--- ICI : Récupère toute la base
    df_alertes = df[df["quantite"] <= df["seuil_alerte"]]
    
    alertes_html = []
    for _, row in df_alertes.iterrows():
        statut = get_statut(row["quantite"], row["seuil_alerte"])
        couleur = "#FF5252" if statut == "🔴 RUPTURE" else "#FFB74D"
        alertes_html.append(
            html.Div([
                html.Div(row["produit"], style={"color": "#FFF", "fontWeight": "bold"}),
                html.Div(f"Stock: {row['quantite']} (Seuil: {row['seuil_alerte']})", style={"color": couleur, "fontWeight": "bold"})
            ], className="d-flex justify-content-between p-3 mb-2", style={"background": "#1A1A1A", "borderRadius": "8px", "borderLeft": f"4px solid {couleur}"})
        )
        
    if not alertes_html:
        alertes_html = [html.Div("Aucune rupture ou alerte.", style={"color": "#69F0AE", "padding": "15px"})]

    nb_ruptures = sum(1 for _, r in df.iterrows() if r["quantite"] == 0)
    nb_alertes = sum(1 for _, r in df.iterrows() if 0 < r["quantite"] <= r["seuil_alerte"])
    
    kpis = [
        html.Div(className="col-6", children=[
            html.Div(className="kpi-box", style={"borderBottom": "3px solid #FF5252"}, children=[
                html.Div("RUPTURES", style={"color": "#888", "fontSize": "11px", "fontWeight": "bold"}),
                html.Div(nb_ruptures, style={"color": "#FFF", "fontSize": "28px", "fontWeight": "bold"})
            ])
        ]),
        html.Div(className="col-6", children=[
            html.Div(className="kpi-box", style={"borderBottom": "3px solid #FFB74D"}, children=[
                html.Div("ALERTES", style={"color": "#888", "fontSize": "11px", "fontWeight": "bold"}),
                html.Div(nb_alertes, style={"color": "#FFF", "fontSize": "28px", "fontWeight": "bold"})
            ])
        ])
    ]
    return alertes_html, kpis

if __name__ == "__main__":
    app.run(debug=True)