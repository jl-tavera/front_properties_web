import streamlit as st
import pandas as pd
import random
import requests
from render_utils import render_map, render_results, render_comparison_report

API_URL = "http://137.184.7.80:8000/ask"

# ---------- Configuración de la página ----------
st.set_page_config(
    page_title="Apartment Agent",
    page_icon="🏠",
    layout="wide"
)

# ---------- Inicialización de sesión ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = random.randint(1, 1000000)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_df" not in st.session_state:
    st.session_state.last_df = None

st.subheader("**Apartment Agent**")

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": """👋 ¡Hola! Estoy aquí para ayudarte a encontrar el apartamento ideal. Tengo **tres funcionalidades principales** que puedes usar:

1️⃣ **Buscar apartamentos**: Solo descríbeme el apartamento de tus sueños. Por ejemplo:

- "Busco apartamento en Chapinero por menos de 3 millones"
- "Quiero algo con 2 habitaciones de más de 60 metros cuadrados con iluminación natural por menos de 2 millones de pesos"

2️⃣ **Ver detalles**: Si ya viste un apartamento interesante, puedes escribir solo su número de ID en el chat para ver más información detallada.

3️⃣ **Comparar resultados**: Usa el comando **comparar** para generar un reporte visual y comparativo de los apartamentos más recientes que encontré para ti.

Cuando estés listo, dime lo que estás buscando. 🏠"""
    })

# ---------- Estilos personalizados ----------
st.markdown("""
    <style>
    .stChatMessage { max-width: 100%; }
    .stTextInput > div > div { width: 100% !important; }
    .map-container { padding-top: 10px; }
    </style>
""", unsafe_allow_html=True)



# ---------- Mostrar historial de chat ----------
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("comparison"):
            df = pd.DataFrame(msg["map_info"])
            render_comparison_report(df)

        elif msg["role"] == "assistant" and msg.get("map_info"):
            df = pd.DataFrame(msg["map_info"])
            if "coordinates" in df.columns:
                render_map(df, key=f"map-{i}")
                render_results(df)


# ---------- Entrada del usuario ----------
if user_input := st.chat_input("Escribe tu pregunta sobre apartamentos..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # --- Intercepta comando "comparar" ---
    if user_input.strip().lower() == "comparar":
        if st.session_state.last_df is not None:
            render_comparison_report(df)
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Aquí tienes la comparación de los apartamentos:",
                "comparison": True,
                "map_info": st.session_state.last_df.to_dict(orient="records")
            })
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Primero necesitas buscar apartamentos antes de comparar."
            })
        st.stop()


    # --- Llama al backend si no es comparar ---
    payload = {
        "query": user_input,
        "session_id": st.session_state.session_id
    }

    try:
        res = requests.post(API_URL, json=payload)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        st.error(f"Error llamando al backend: {e}")
        st.stop()

    assistant_msg = {
        "role": "assistant",
        "content": data["response"],
        "map_info": data.get("map_info", [])
    }

    st.session_state.session_id = data["session_id"]
    st.session_state.messages.append(assistant_msg)

    with st.chat_message("assistant"):
        st.markdown(assistant_msg["content"])

        df = pd.DataFrame(assistant_msg["map_info"])
        if "coordinates" in df.columns:
            st.session_state.last_df = df.copy()
            render_map(df, key=f"map-final-{len(st.session_state.messages)}")
            render_results(df)
