import streamlit as st
import requests
import json

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Predicción de Préstamos",
    page_icon="💸",
    layout="centered"
)

st.title('💸 Simulador de Riesgo de Préstamo')
st.write("Ingresa los datos del solicitante para predecir el riesgo de default.")

# --- 2. URL DE NUESTRA API ---
API_URL = "http://127.0.0.1:8000/predict"

# --- ¡ARREGLO v3! - Creamos el "Marco de Fotos" vacío ---
# Este 'placeholder' es donde mostraremos todos los resultados.
placeholder = st.empty()

# --- 3. FORMULARIO DE ENTRADA ---
with st.form(key="loan_form"):

    st.subheader("Información Financiera")
    col1, col2 = st.columns(2)

    with col1:
        principal_amount = st.slider("Monto del Préstamo (en DM)", 250.0, 20000.0, 5000.0, 100.0)
    with col2:
        term_months = st.slider("Plazo (en meses)", 4, 72, 24, 1)

    product_type = st.selectbox(
        "Propósito del Préstamo",
        ('car', 'radio/TV', 'furniture/equipment', 'education', 'business', 'other')
    )

    st.subheader("Información Demográfica")
    col3, col4 = st.columns(2)

    with col3:
        age = st.slider("Edad", 18, 75, 30, 1)
    with col4:
        gender = st.selectbox("Género", ('male', 'female', 'other'))

    job = st.selectbox(
        "Tipo de Trabajo",
        ('skilled', 'unskilled', 'management-self-employed') 
    )

    submit_button = st.form_submit_button(label='¡Predecir Riesgo!')

# --- 4. LÓGICA DE PREDICCIÓN ---
if submit_button:
    # 1. Creamos la "orden" (JSON)
    loan_request = {
        "principal_amount": principal_amount,
        "term_months": term_months,
        "age": age,
        "gender": gender,
        "job": job,
        "product_type": product_type
    }

    # --- ¡ARREGLO v3! - Usamos el 'placeholder' ---

    # 2. Ponemos el mensaje "Cargando" DENTRO del placeholder
    placeholder.info("Contactando al 'Chef' (IA) para la predicción...")

    try:
        # 3. Enviamos la "orden"
        response = requests.post(API_URL, json=loan_request)

        if response.status_code == 200:
            # 4. Recibimos la respuesta
            prediction_data = response.json()
            label = prediction_data['prediction_label']
            probability = prediction_data['probability_default']

            # 5. Borramos "Cargando" y ponemos el resultado DENTRO del MISMO placeholder
            if label == 1:
                placeholder.error(f"ALERTA: RIESGO DE DEFAULT (NO PAGO)\n\n"
                                  f"El modelo tiene una confianza del **{probability*100:.2f}%** de que este préstamo **fallará**.")
            else:
                placeholder.success(f"APROBADO: BAJO RIESGO (SÍ PAGO)\n\n"
                                    f"El modelo predice que este préstamo será pagado (probabilidad de default: {probability*100:.2f}%).")

        else:
            placeholder.error(f"Error del servidor de API (Mesero): {response.text}")

    except requests.exceptions.ConnectionError:
        placeholder.error("Error: No se pudo conectar con la API (el 'Mesero').\n\n"
                          "¿Estás seguro de que la terminal de FastAPI/Uvicorn está corriendo?")
