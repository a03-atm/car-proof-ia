import streamlit as st
import openai
import urllib.parse
from serpapi import GoogleSearch

# ─── Ton prompt système amélioré ──────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es Car Proof IA, un assistant automobile expert et pédagogue.
- Tu analyses chaque demande (marque, modèle, année, motorisation, panne, accessoire, entretien…) comme un technicien ou un conseiller automobile.
- Tu peux extraire du texte fourni (ex. « BMW Série 1 E87 118d 2009 ») tous les paramètres :  
    • Marque, modèle, génération (E87/E81…)  
    • Motorisation (diesel, essence, cylindrée…)  
    • Année de fabrication  
- Pour chaque pièce ou opération, tu donnes :  
    1. La **fonction** de la pièce (ex. « Le filtre à huile nettoie l’huile moteur de ses impuretés »).  
    2. Les **symptômes** d’usure ou de panne (ex. « débit irrégulier, voyants moteur, bruit de chaîne »).  
    3. Les **étapes** de remplacement ou de diagnostic.  
- Lorsque l’utilisateur parle d’entretien périodique, tu rappelles les **intervalles conseillés** (km ou mois) et les **références OEM** si possible.  
- Tu signales les **rappels de sécurité** connus (airbags, freins) pour le modèle donné, si disponibles.  
- Tu fournis toujours des **liens** vers :  
    • Sites d’annonces pour pièces (LebonCoin, Oscaro, Mister Auto…)  
    • Sites d’annonces de véhicules d’occasion (LeBonCoin Voitures, LaCentrale, AutoScout24…) sur commande explicite  
- Tu proposes une **estimation de prix** (± 10 %) pour la pièce ou la main-d’œuvre, en te basant sur des moyennes de marché.  
- Tu suggères systématiquement au moins une **question de relance** pour affiner le diagnostic ou l’achat (ex. « Quel est le kilométrage actuel ? », « As-tu déjà vérifié l’état du filtre à air ? »).  
- Tu réponds en **français**, de manière **structurée** avec titres, listes à puces et encadrés si nécessaire.  
- Tu adoptes un ton **professionnel**, **clair** et **bienveillant**.
"""

# ─── Interface & Historique ──────────────────────────────────────────────

st.set_page_config(page_title="Car Proof IA", page_icon="🚗", layout="wide")

st.title("🚗 Car Proof IA")
st.markdown("Bonjour, j'espère que vous allez bien ? Je suis Car Proof, ton assistant IA spécialisé dans l'automobile.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

# Affiche l'historique (on masque le system)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# … le reste de ton code demeure inchangé …


# ─── Saisie utilisateur ─────────────────────────────────────────────────

user_input = st.chat_input("💬 Ta demande ici :")

if user_input:
    # Affiche la question
    with st.chat_message("user"):
        st.markdown(user_input)

    # Ajoute à l'historique
    st.session_state.messages.append({"role":"user","content":user_input})

    text = user_input.lower()

    # 1) Recherche web si demandé
    web_triggers = ["cherche sur le web","recherche web","voir sur le web","google","site internet"]
    if any(kw in text for kw in web_triggers):
        st.markdown("🌐 **Résultats Web :**")
        for wr in fetch_web_results(user_input):
            st.markdown(f"**[{wr['title']}]({wr['link']})**  \n{wr['snippet']}\n")

    # 2) Annonces shopping si pièces auto
    shopping_triggers = ["filtre","huile","pneu","jante","roue","chaine"]
    if any(kw in text for kw in shopping_triggers) or any(kw in text for kw in web_triggers):
        st.markdown("🛍️ **Annonces Google Shopping :**")
        for p in fetch_shopping_results(user_input):
            cols = st.columns([1,3])
            with cols[0]:
                if p["thumbnail"]:
                    st.image(p["thumbnail"], width=80)
            with cols[1]:
                st.markdown(
                    f"**[{p['title']}]({p['link']})**  \n"
                    f"Prix : {p['price']}  \n"
                    f"Source : {p['source']}"
                )

    # Mémorise la dernière requête métier
    if not any(kw in text for kw in ["voir annonce", "montre annonce", "affiche annonce"]):
        st.session_state.base_query = user_input

    # 3) Liens voitures **uniquement** sur commande explicite
    show_car_cmds = ["voir annonce voiture", "montre annonce voiture", "affiche annonce voiture"]
    if any(cmd in text for cmd in show_car_cmds):
        q = st.session_state.base_query
        st.markdown("🚗 **Annonces de voitures d’occasion :**")
        for name, url in generate_car_links(q).items():
            st.markdown(f"- [{name}]({url})")

    # 4) Appel à l’IA
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                temperature=0.9,
                max_tokens=900,
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content.strip()
            st.markdown(reply)

    # 5) Sauvegarde la réponse
    st.session_state.messages.append({"role":"assistant","content":reply})
