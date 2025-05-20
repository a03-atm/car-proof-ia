import streamlit as st
import openai
import urllib.parse
from serpapi import GoogleSearch

# ─── Initialisation OpenAI ─────────────────────────────────────────────
openai.api_key = st.secrets["openai_api_key"]

# ─── Fonctions SerpAPI ───────────────────────────────────────────────────

def fetch_shopping_results(query, num_results=4):
    params = {
        "engine":    "google_shopping",
        "q":         query,
        "api_key":   st.secrets["serpapi_api_key"],
    }
    client = GoogleSearch(params)
    data   = client.get_dict()
    items  = data.get("shopping_results", [])[:num_results]
    return [
        {
            "title":     i.get("title"),
            "price":     i.get("price"),
            "link":      i.get("link"),
            "thumbnail": i.get("thumbnail"),
            "source":    i.get("source"),
        }
        for i in items
    ]

def fetch_web_results(query, num_results=5):
    params = {
        "engine":  "google",
        "q":       query,
        "api_key": st.secrets["serpapi_api_key"],
    }
    client = GoogleSearch(params)
    data   = client.get_dict()
    items  = data.get("organic_results", [])[:num_results]
    return [
        {
            "title":   i.get("title"),
            "snippet": i.get("snippet"),
            "link":    i.get("link"),
        }
        for i in items
    ]

# ─── Nouvelle fonction pour les liens voitures d’occasion ───────────────
def generate_car_links(query: str) -> dict:
    q = urllib.parse.quote(query)
    return {
        "LeBonCoin (voitures)":    f"https://www.leboncoin.fr/voitures/offres/?q={q}",
        "LaCentrale":              f"https://www.lacentrale.fr/listing?makesModelsCommercialNames={q}",
        "AutoScout24":             f"https://www.autoscout24.fr/lst?sort=standard&desc=0&ustate=N%2CU&size=20&cy=F&atype=C&zip=&mmvmk0={q}",
        "ParuVendu":               f"https://www.paruvendu.fr/voiture-vehicule-voiture-occasion/recherche/{q}.html",
        "OuestFrance-auto":        f"https://www.ouestfrance-auto.com/voitures-occasion/{q}",
    }

# ─── Interface & Historique ──────────────────────────────────────────────

st.set_page_config(page_title="Car Proof IA", page_icon="🚗", layout="wide")

st.title("🚗 Car Proof IA")
st.markdown("Bonjour, j'espère que vous allez bien ? Je suis Car Proof, ton assistant IA spécialisé dans l'automobile.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role":"system",
            "content":(
                "Tu es ChatGPT, un assistant automobile expert. "
                "Tu analyses chaque demande (pièce, voiture, panne, etc.) et tu réponds "
                "comme un professionnel de l'automobile."
                "Tu proposes automatiquement des liens d’annonces ou de sites spécialisés comme Leboncoin, La Centrale, Oscaro, Mister Auto, etc., quand c'est pertinent. "
                "Tu fais toujours une relance intelligente basée sur la demande précédente. "
                "Tu proposes une cotation de prix pour les voitures selon les réparations à prévoir. "
                "Tu ajoutes des images liées aux annonces générées."
                "Des explications techniques claires (avec définition des termes)."
                "Des conseils pratiques et étapes à suivre."
                "Des liens pertinents (Leboncoin, La Centrale…)."
                "Des suggestions de questions pour guider l’utilisateur."
                "Une estimation de prix quand c’est pertinent."
                "Tu réponds en français, de façon structurée : titres, listes, encadrés."
            )
        }
    ]

# Affiche l'historique
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
