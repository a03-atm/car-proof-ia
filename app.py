import streamlit as st
import openai
import urllib.parse

# Initialisation OpenAI
openai.api_key = st.secrets["openai_api_key"]

response = openai.ChatCompletion.create(
    model="gpt-4-turbo",
    messages=st.session_state.messages
)

# Titre de l'application
st.markdown("🚗 **Car Proof IA**")
st.markdown("Bonjour, j'espère que vous allez bien ?, je suis Car proof, ton assitant IA spécialisé dans l'automobile")
# Historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Tu es ChatGPT, un assistant automobile expert. Tu réponds comme un professionnel auto. "
                "Tu analyses chaque demande (pièce, voiture, panne, etc.) et tu donnes des réponses précises, claires, et utiles. "
                "Tu proposes automatiquement des liens d’annonces ou de sites spécialisés comme Leboncoin, La Centrale, Oscaro, Mister Auto, etc., quand c'est pertinent. "
                "Tu ne poses jamais de questions génériques. Tu fais toujours une relance intelligente basée sur la demande précédente. "
                "Tu génères des liens adaptés automatiquement sans que l’utilisateur ait besoin de les demander. "
                "Tu fonctionnes comme le vrai ChatGPT, mais uniquement dans le domaine automobile."
                "Tu proposes des qutesions pour en savoir plus sur la demande de l'utilisateur"
                "Tu proposes une cotation de prix pour les voiture en fonction de l'annonce et des réparations eventuelles à réaliser"
                "Tu propose des images en lien avec les annonces que tu généres"
            )
        }
    ]

# Zone de saisie utilisateur
user_input = st.chat_input("💬 Ta demande ici :")

# Affichage de tous les messages précédents
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# Traitement du message utilisateur
if user_input:
    # Afficher le message utilisateur immédiatement
    with st.chat_message("user"):
        st.markdown(user_input)

    # Ajouter à l'historique
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Affichage "en train d’écrire"
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content.strip()
            st.markdown(reply)

    # Sauvegarder la réponse dans l'historique
    st.session_state.messages.append({"role": "assistant", "content": reply})# car-proof-ia
