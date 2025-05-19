import streamlit as st
import openai

# 1️⃣ Configure ta clé OpenAI
openai.api_key = st.secrets["openai_api_key"]

# 2️⃣ Initialise l’historique AVANT tout appel
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant automobile expert. "
                "Tu analyses chaque demande (pièce, voiture, panne, etc.) "
                "et tu réponds comme un professionnel de l'automobile."
            )
        }
    ]

# 3️⃣ Affichage du titre
st.markdown("🚗 **Car Proof IA**")
st.markdown("Pose-moi ta question liée à l'automobile !")

# 4️⃣ Champ de saisie
user_input = st.chat_input("💬 Ta demande ici :")

# 5️⃣ Affiche tout l’historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6️⃣ Quand l’utilisateur envoie un texte…
if user_input:
    # a) on l’affiche
    with st.chat_message("user"):
        st.markdown(user_input)
    # b) on l’ajoute à l’historique
    st.session_state.messages.append({"role": "user", "content": user_input})
    # c) on appelle l’API
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis…"):
            res = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages
            )
            reply = res.choices[0].message.content.strip()
            st.markdown(reply)
    # d) on sauvegarde la réponse
    st.session_state.messages.append({"role": "assistant", "content": reply})
