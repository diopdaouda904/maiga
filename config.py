# config.py
import hashlib

NOM_RESTO = "Maïga Smash"
COULEUR_PRINCIPALE = "#F5A623"

# Identifiants hashés (plus sécurisé)
MDP_EMPLOYE_HASH  = hashlib.sha256("smash2024".encode()).hexdigest()
MDP_PATRON_HASH   = hashlib.sha256("patron2024".encode()).hexdigest()

def verifier_mdp(mdp_saisi, role):
    h = hashlib.sha256(mdp_saisi.encode()).hexdigest()
    if role == "employe":
        return h == MDP_EMPLOYE_HASH
    elif role == "patron":
        return h == MDP_PATRON_HASH
    return False
