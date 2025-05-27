import os
import streamlit as st
import openai
import urllib.parse
from serpapi import GoogleSearch
from functools import lru_cache

# ─── Page config (doit être le tout premier appel) ───────────────────────
st.set_page_config(page_title="🚗 Car Proof ", page_icon="🚗", layout="wide")

# ─── Clés API ─────────────────────────────────────────────────────────────
openai.api_key = st.secrets.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("🔑 ERREUR : Ta clé OpenAI n'est pas définie.")

SERPAPI_KEY = st.secrets.get("serpapi_api_key") or os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    st.error("🔑 ERREUR : Ta clé SerpAPI n'est pas définie.")

# ─── Localisation (injectée manuellement ici) ────────────────────────────
USER_LOCATION = "Nancy, Grand Est, France"
ville = USER_LOCATION.split(",")[0]

# ─── Services locaux Cap Car ──────────────────────────────────────────────
LOCAL_GARAGES = {
    "Nancy": ["Garage Rapid'Auto Nancy", "Cap Car Nancy", "AutoServices Metz"],
}
MY_AGENT_SERVICE_URLS = {
    "cotation":  "https://www.capcar.fr/rayane.aitmalouk",
    "accueil":    "https://www.capcar.fr?utm_source=agentRAI11032025&utm_medium=mlm&utm_campaign=mlm",
    "catalogue":  "https://www.capcar.fr/voiture-occasion?utm_source=agentRAI11032025&utm_medium=mlm&utm_campaign=mlm",
    "vitrine":    "https://www.capcar.fr/agents/rayane-ait-malouk?utm_source=agentRAI11032025&utm_medium=mlm&utm_campaign=mlm",
}

# ─── Helpers SerpAPI ─────────────────────────────────────────────────────
@lru_cache(maxsize=128)
def fetch_web_results(query: str, num_results: int = 5):
    params = {"engine": "google", "q": query, "api_key": SERPAPI_KEY}
    data   = GoogleSearch(params).get_dict()
    return [
        {
            "title":     i.get("title"),
            "snippet":   i.get("snippet"),
            "link":      i.get("link"),
            "thumbnail": i.get("rich_snippet", {}).get("top", {}).get("thumbnail"),
        }
        for i in data.get("organic_results", [])[:num_results]
    ]

def fetch_shopping_results(query: str, num_results: int = 4):
    params = {"engine": "google_shopping", "q": query, "api_key": SERPAPI_KEY}
    data   = GoogleSearch(params).get_dict()
    return [
        {
            "title":     i.get("title"),
            "price":     i.get("price"),
            "link":      i.get("link"),
            "thumbnail": i.get("thumbnail"),
            "source":    i.get("source"),
        }
        for i in data.get("shopping_results", [])[:num_results]
    ]

def generate_car_links(query: str) -> dict:
    q = urllib.parse.quote(query)
    return {
        "LeBonCoin (voitures)": f"https://www.leboncoin.fr/voitures/offres/?q={q}",
        "LaCentrale":            f"https://www.lacentrale.fr/listing?makesModelsCommercialNames={q}",
        "AutoScout24":           f"https://www.autoscout24.fr/lst?sort=standard&desc=0&ustate=N%2CU&size=20&cy=F&atype=C&zip=&mmvmk0={q}",
        "ParuVendu":             f"https://www.paruvendu.fr/voiture-vehicule-voiture-occasion/recherche/{q}.html",
        "OuestFrance-auto":      f"https://www.ouestfrance-auto.com/voitures-occasion/{q}",
    }

# ─── Nouvel ajout : génération de liens pour pièces auto ─────────────────
def generate_part_links(query: str) -> dict:
    q = urllib.parse.quote(query)
    return {
        "Oscaro":      f"https://www.oscaro.com/recherche?query={q}",
        "Mister Auto": f"https://www.mister-auto.com/search?search={q}",
        "Autodoc":     f"https://www.autodoc.fr/recherche?search={q}",
        "Pièces Auto": f"https://www.piecesauto.fr/recherche?search={q}",
    }

# ─── Prompt système ──────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es Car Proof IA, un assistant automobile expert et pédagogue nqui s'appui sur chat Gpt.
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
- **Quand tu formules cette question de relance, place-la toujours à la fin de ta réponse et ne l’introduis jamais en tête.**
- Tu réponds en **français**, de manière **structurée** avec titres, listes à puces et encadrés si nécessaire.  
- Tu adoptes un ton **professionnel**, **clair** et **bienveillant**.
"""

# ─── Interface & Historique ──────────────────────────────────────────────
st.title("🚗 Car Proof")
st.markdown("Bonjour, J'espère que vous allez bien ? Je suis Car Proof, votre assitant auto. En quoi puis-je vous aider ?")
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
for msg in st.session_state.messages:
    if msg["role"] == "system": continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── Entrée utilisateur ─────────────────────────────────────────────────
user_input = st.chat_input("💬 Ta demande ici :")
if not user_input:
    st.stop()

# 1) Save & display user question
with st.chat_message("user"):
    st.markdown(user_input)
st.session_state.messages.append({"role": "user", "content": user_input})
text = user_input.lower()

# 2) Web Search si demandé
web_triggers = ["cherche", "recherche", "info", "site", "annonce", "google"]
if any(kw in text for kw in web_triggers):
    st.markdown("🌐 **Résultats Web :**")
    for wr in fetch_web_results(user_input):
        cols = st.columns([1, 4])
        with cols[0]:
            if wr["thumbnail"]:
                st.image(wr["thumbnail"], width=80)
        with cols[1]:
            st.markdown(f"**[{wr['title']}]({wr['link']})**  \n{wr['snippet'] or ''}")

# 3) Shopping annonces & pièces auto si trigger
shopping_triggers = ["filtre", "huile", "pneu", "jante", "roue", "chaine", "amortisseur"]
if any(kw in text for kw in shopping_triggers):
    st.markdown("🛍️ **Annonces Google Shopping :**")
    prods = fetch_shopping_results(user_input)
    # Carrousel images
    thumbs = [p["thumbnail"] for p in prods if p["thumbnail"]]
    if thumbs:
        cols = st.columns(len(thumbs))
        for col, img in zip(cols, thumbs):
            col.image(img, width=120)
    # Détail
    st.markdown("**Sélection recommandée :**")
    for p in prods:
        st.markdown(
            f"- **{p['title']}**  \n"
            f"  Prix : {p['price']}  \n"
            f"  Source : {p['source']}  \n"
            f"  [Voir l’annonce]({p['link']})"
        )
    st.markdown("---")
    st.markdown("**Sources :**")
    for src in {p["source"] for p in prods}:
        st.markdown(f"- {src}")

    # ── ICI : liens vers magasins de pièces auto
    st.markdown("🔧 **Magasins de pièces automobiles :**")
    for name, url in generate_part_links(user_input).items():
        st.markdown(f"- [{name}]({url})")

# 4) Appel IA
with st.chat_message("assistant"):
    with st.spinner("Je réfléchis…"):
        # 1) On conserve le system prompt
        system_msg = st.session_state.messages[0]
        # 2) On tronque l'historique utilisateur/assistant aux 10 derniers messages
        history = st.session_state.messages[1:]
        if len(history) > 10:
            history = history[-10:]
        messages_to_send = [system_msg] + history

        resp = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=500,
            timeout=60,
            messages=messages_to_send
        )
        reply = resp.choices[0].message.content.strip()
        st.markdown(reply)

# 5) Voitures d’occasion si demandé
show_car_cmds = ["voir annonce voiture", "affiche annonce voiture", "montre annonce voiture"]
if any(cmd in text for cmd in show_car_cmds):
    st.markdown("🚗 **Annonces de voitures d’occasion :**")
    for name, url in generate_car_links(user_input).items():
        st.markdown(f"- [{name}]({url})")

# 6) Vente & services Cap Car
sell_triggers = ["vendre", "je veux vendre", "à vendre", "vendu"]
if any(kw in text for kw in sell_triggers):
    st.markdown("💼 **Vous souhaitez vendre ?**")
    garages = LOCAL_GARAGES.get(ville, [])
    if garages:
        st.markdown("🔧 **Garages recommandés :**")
        for g in garages:
            st.markdown(f"- {g}")
    st.markdown("💼 **Services Cap Car :**")
    st.markdown(
        f"- [Obtenez votre cotation gratuite]({MY_AGENT_SERVICE_URLS['cotation']})  \n"
        f"- [Accueil CapCar.fr]({MY_AGENT_SERVICE_URLS['accueil']})  \n"
        f"- [Catalogue des véhicules]({MY_AGENT_SERVICE_URLS['catalogue']})  \n"
        f"- [Ma page vitrine Cap Car]({MY_AGENT_SERVICE_URLS['vitrine']})"
    )

    
    if not reply.strip().endswith('?'):
        st.markdown(
            "> **Question de suivi :** "
            "Pouvez-vous préciser si vous souhaitez des pièces neuves ou d'occasion, "
            "et si c'est pour l'avant, l'arrière ou l'ensemble du train ?"
        )

# 7) Sauvegarde de la réponse
st.session_state.messages.append({"role": "assistant", "content": reply})






