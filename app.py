import streamlit as st
import openai

# 1) configure ta clé
openai.api_key = st.secrets["openai_api_key"]

# 2) initialise ton historique AVANT tout usage
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant automobile expert. Tu analyses chaque demande (pièce, voiture, panne, etc.) "
                "et tu réponds comme un professionnel de l'automobile."
            )
        }
    ]

# 3) affiche titre + description
st.title("🚗 Car Proof IA")
st.write("Pose-moi ta question liée à l'automobile !")

# 4) saisis l’utilisateur
user_input = st.chat_input("💬 Ta demande ici :")

# 5) affiche l'historique COMPLET
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6) dès qu'il y a du texte, appelle l’API
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis…"):
            res = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages
            )
            reply = res.choices[0].message.content.strip()
            st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

            reply = response.choices[0].message.content.strip()
            st.markdown(reply)

    # Sauvegarder la réponse dans l'historique
    st.session_state.messages.append({"role": "assistant", "content": reply})# car-proof-ia
