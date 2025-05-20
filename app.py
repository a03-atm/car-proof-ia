import streamlit as st
import openai
import urllib.parse
from serpapi import GoogleSearch  # ← Ajouté

# Initialisation OpenAI
openai.api_key = st.secrets["openai_api_key"]

# ─── Fonction SerpAPI ────────────────────────────────────────────────────
def fetch_shopping_results(query, num_results=4):
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": st.secrets["serpapi_api_key"],  # à configurer dans tes Secrets
    }
    client = GoogleSearch(params)
    data = client.get_dict()
    results = []
    for item in data.get("shopping_results", [])[:num_results]:
        results.append({
            "title":     item.get("title"),
            "price":     item.get("price"),
            "link":      item.get("link"),
            "thumbnail": item.get("thumbnail"),
            "source":    item.get("source")
        })
    return results

# Titre de l'application
st.markdown("🚗 **Car Proof IA**")
st.markdown("Bonjour, j'espère que vous allez bien ? Je suis Car Proof, ton assistant IA spécialisé dans l'automobile.")

# Historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Tu es ChatGPT, un assistant automobile expert. Tu réponds comme un professionnel auto. "
                "Tu analyses chaque demande (pièce, voiture, panne, etc.) et tu donnes des réponses précises, claires et utiles. "
                "Tu proposes automatiquement des liens d’annonces ou de sites spécialisés comme Leboncoin, La Centrale, Oscaro, Mister Auto, etc., quand c'est pertinent. "
                "Tu fais toujours une relance intelligente basée sur la demande précédente. "
                "Tu proposes une cotation de prix pour les voitures selon les réparations à prévoir. "
                "Tu ajoutes des images liées aux annonces générées."
            )
        }
    ]

# Zone de saisie utilisateur
user_input = st.chat_input("💬 Ta demande ici :")

# Affichage de l'historique
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Traitement du message utilisateur
if user_input:
    # Affiche la question de l’utilisateur
    with st.chat_message("user"):
        st.markdown(user_input)

    # Sauvegarde dans l’historique
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ─── Affichage des annonces Google Shopping via SerpAPI ─────────────
    st.markdown("🛍️ **Annonces Google Shopping :**")
    products = fetch_shopping_results(user_input)
    for p in products:
        cols = st.columns([1, 3])
        with cols[0]:
            if p["thumbnail"]:
                st.image(p["thumbnail"], width=80)
        with cols[1]:
            st.markdown(
                f"**[{p['title']}]({p['link']})**  \n"
                f"Prix : {p['price']}  \n"
                f"Source : {p['source']}"
            )

    # L’IA réfléchit et répond
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content.strip()
            st.markdown(reply)

    # Sauvegarde la réponse de l’assistant
    st.session_state.messages.append({"role": "assistant", "content": reply})
