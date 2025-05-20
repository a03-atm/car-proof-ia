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

# ─── Interface & Historique ──────────────────────────────────────────────

st.set_page_config(page_title="Car Proof IA", page_icon="🚗", layout="wide")

st.title("🚗 Car Proof IA")
st.markdown("Bonjour ! Je suis Car Proof, ton assistant IA automobile.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role":"system",
            "content":(
                "Tu es ChatGPT, un assistant automobile expert. "
                "Tu analyses chaque demande (pièce, voiture, panne, etc.) et tu réponds "
                "comme un professionnel de l'automobile."
            )
        }
    ]

# Affiche l'historique
for msg in st.session_state.messages:
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

    # 3) Appel à l’IA
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content.strip()
            st.markdown(reply)

    # 4) Sauvegarde la réponse
    st.session_state.messages.append({"role":"assistant","content":reply})

