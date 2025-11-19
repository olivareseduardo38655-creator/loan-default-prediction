import pandas as pd
import joblib
import os
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

# --- 1. CONFIGURACIÓN Y CARGA DEL MODELO ---

print("Iniciando API (v2)...")
app = FastAPI(title="API de Predicción de Default de Préstamos", version="2.0")

# Definimos las rutas a los "activos"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "loan_model.joblib")
COLUMNS_PATH = os.path.join(MODEL_DIR, "model_columns.joblib")

# Cargamos el "cerebro" Y la "lista de ingredientes"
print(f"Cargando modelo desde: {MODEL_PATH}")
model = joblib.load(MODEL_PATH)
print("¡Modelo cargado!")

print(f"Cargando lista de columnas desde: {COLUMNS_PATH}")
model_columns = joblib.load(COLUMNS_PATH)
print(f"¡Columnas cargadas! (Total: {len(model_columns)})")

# --- 2. DEFINICIÓN DEL "PEDIDO" (Input Data Model) ---
class LoanRequest(BaseModel):
    principal_amount: float
    term_months: int
    age: int
    gender: str  # 'male' o 'female'
    job: str     # 'skilled', 'unskilled', etc.
    product_type: str # 'car', 'education', etc.

    # Ejemplo: { "principal_amount": 5000, "term_months": 36, "age": 30, 
    #            "gender": "male", "job": "skilled", "product_type": "car" }

# --- 3. ENDPOINT DE BIENVENIDA ---
@app.get("/")
def read_root():
    return {"status": "OK", "message": "Bienvenido a la API de Predicción de Préstamos"}

# --- 4. ENDPOINT DE PREDICCIÓN ---
@app.post("/predict")
def predict(request: LoanRequest):
    print(f"Recibida petición de predicción: {request.dict()}")

    # --- 5. TRADUCCIÓN (Feature Engineering en Tiempo Real) ---

    # 1. Convertir la "orden" (request) en un DataFrame de 1 fila
    input_data = pd.DataFrame([request.dict()])

    # 2. Traducir 'gender'
    input_data['gender_numeric'] = input_data['gender'].map({'female': 0, 'male': 1, 'other': 0}).fillna(0)

    # 3. Traducir 'job' y 'product_type' (One-Hot Encoding)
    # Esto crea columnas como 'job_skilled', 'product_type_car', etc.
    input_data = pd.get_dummies(input_data, columns=['job', 'product_type'])

    # --- 6. ¡EL TRUCO MÁGICO! (Alineación de Columnas) ---
    # Alinear el DataFrame de entrada con las columnas del modelo

    # 1. Crea un DataFrame vacío con las columnas EXACTAS del modelo
    final_input = pd.DataFrame(columns=model_columns)

    # 2. "Pega" los datos de entrada en este DataFrame
    final_input = pd.concat([final_input, input_data]).fillna(0)

    # 3. Asegurarnos de que solo tenemos las columnas del modelo
    #    y en el ORDEN correcto.
    final_input = final_input[model_columns] 

    print("Datos de entrada listos para el modelo (alineados).")

    # --- 7. PREDICCIÓN ---
    # ¡Ahora sí, el formulario coincide con el examen!
    prediction = model.predict(final_input)
    prediction_proba = model.predict_proba(final_input)

    # --- 8. LA RESPUESTA ---
    # El "mesero" devuelve la respuesta

    pred_label = int(prediction[0])
    prob_default = float(prediction_proba[0][1]) # Probabilidad de NO Pagar (clase 1)

    print(f"Predicción: {pred_label} (Probabilidad de Default: {prob_default:.2f})")

    return {
        "prediction_label": pred_label, # 0 = Paga, 1 = No Paga
        "probability_default": prob_default # Probabilidad de NO Pagar
    }
