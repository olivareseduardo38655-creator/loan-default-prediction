import pandas as pd
import joblib
import sys
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# --- 1. RUTAS DE ARCHIVOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_INPUT_PATH = os.path.join(BASE_DIR, "data", "training_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_OUTPUT_PATH = os.path.join(MODEL_DIR, "loan_model.joblib")

# --- ¡AQUÍ ESTÁ LA LÍNEA NUEVA! ---
# Dónde guardaremos la "lista de ingredientes" (columnas)
COLUMNS_OUTPUT_PATH = os.path.join(MODEL_DIR, "model_columns.joblib")

def main():
    print("Iniciando el script de 'Entrenamiento de Modelo' (v4 - Guardando Columnas)...")

    try:
        # --- 2. EXTRACCIÓN (Extract) ---
        df = pd.read_csv(DATA_INPUT_PATH)
        if 'target' not in df.columns:
            print("Error: La columna 'target' no se encontró en el dataset.")
            sys.exit(1)

        # --- 3. PREPARACIÓN (Separar Features y Target) ---
        print("Separando características (X) y objetivo (y)...")
        y = df['target']
        X = df.drop('target', axis=1)

        # --- ¡AQUÍ ESTÁ LA LÍNEA NUEVA! ---
        # Guardamos la lista de columnas de 'X' ANTES de entrenar
        model_columns = X.columns.tolist()

        # --- 4. DIVISIÓN (Train-Test Split) ---
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        print(f"Datos divididos: {len(X_train)} para entrenar, {len(X_test)} para probar.")

        # --- 5. ENTRENAMIENTO (El Bueno!) ---
        print("Entrenando el modelo 'Random Forest'...")
        model = RandomForestClassifier(class_weight="balanced", random_state=42)
        model.fit(X_train, y_train)
        print("¡Modelo entrenado!")

        # --- 6. EVALUACIÓN (Evaluation) ---
        print("Evaluando el modelo con los datos de prueba...")
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print("\n--- ¡RESULTADOS DEL EXAMEN (Random Forest)! ---")
        print(f"Precisión (Accuracy): {accuracy * 100:.2f}%")
        print(classification_report(y_test, y_pred))
        print(confusion_matrix(y_test, y_pred))

        # --- 7. GUARDADO (¡Con las columnas!) ---
        os.makedirs(MODEL_DIR, exist_ok=True)

        print(f"\nGuardando el 'cerebro' (modelo) en: {MODEL_OUTPUT_PATH}")
        joblib.dump(model, MODEL_OUTPUT_PATH)

        # --- ¡AQUÍ ESTÁ LA LÍNEA NUEVA! ---
        print(f"Guardando la 'lista de ingredientes' (columnas) en: {COLUMNS_OUTPUT_PATH}")
        joblib.dump(model_columns, COLUMNS_OUTPUT_PATH)

        print("\n--- ¡ÉXITO! ---")
        print("El 'cerebro' (Random Forest) Y la 'lista de ingredientes' han sido guardados.")

    except Exception as e:
        print(f"Ha ocurrido un error durante el entrenamiento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
