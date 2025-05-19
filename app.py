import streamlit as st
import openai
import urllib.parse

# Initialisation OpenAI
openai.api_key = st.secrets["openai_api_key"]

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
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content.strip()
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
