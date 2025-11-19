import pandas as pd
from sqlalchemy import create_engine
import sys
import os
from datetime import datetime
from dotenv import load_dotenv  # <-- ¡NUEVO!

# --- ¡NUEVO! ---
load_dotenv()

# --- 1. CONFIGURACIÓN DE LA CONEXIÓN (¡SEGURA!) ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
    print("Error: Faltan variables de entorno en el archivo .env")
    sys.exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- 2. RUTAS DE ARCHIVOS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_OUTPUT_PATH = os.path.join(BASE_DIR, "data", "training_dataset.csv")

def main():
    print("Iniciando script 'Ingeniería de Características' (vFinal - Con .env)...")
    
    try:
        # --- 3. EXTRACCIÓN (Extract) ---
        print("Conectando a la base de datos...")
        engine = create_engine(DATABASE_URL)
        
        QUERY = """
        SELECT c.job, c.gender, c.birth_date,
               l.principal_amount, l.term_months, l.product_type,
               d.default_flag
        FROM loans l
        JOIN accounts a ON l.account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        JOIN delinquencies d ON l.loan_id = d.loan_id;
        """
        df = pd.read_sql(QUERY, engine)
        print(f"Datos crudos cargados: {len(df)} filas.")

        # --- 4. TRADUCCIÓN (Feature Engineering) ---
        print("Traduciendo datos a formato numérico...")

        # A. Traducir 'birth_date' (texto) a 'age' (número)
        df['birth_date'] = pd.to_datetime(df['birth_date'])
        df['age'] = (datetime.now().year - df['birth_date'].dt.year)
        
        # B. Traducir 'gender' (texto) a binario (0 o 1)
        df['gender_numeric'] = df['gender'].map({'female': 0, 'male': 1, 'other': 0}).fillna(0)

        # C. Traducir 'default_flag' (True/False) a binario (0 o 1)
        df['target'] = df['default_flag'].astype(int)

        # D. Traducir 'job' y 'product_type' (texto categórico) a One-Hot Encoding
        df_features = pd.get_dummies(df, columns=['job', 'product_type'], drop_first=True)
        
        # --- 5. ENSAMBLAJE FINAL ---
        print("Creando el dataset de entrenamiento final...")
        
        columnas_finales = [
            'principal_amount', 'term_months', 'age',
            'gender_numeric', 'target'
        ]
        
        dummy_cols = [col for col in df_features.columns if 'job_' in col or 'product_type_' in col]
        columnas_finales.extend(dummy_cols)
        
        df_train = df_features[columnas_finales]
        
        # --- 6. CARGA (Load) ---
        df_train.to_csv(DATA_OUTPUT_PATH, index=False)
        
        print("\n--- ¡ÉXITO! ---")
        print(f"El dataset 'traducido' se ha guardado en: {DATA_OUTPUT_PATH}")
        print(f"Total de {len(df_train)} filas y {len(df_train.columns)} columnas listas para la IA.")

    except Exception as e:
        print(f"Ha ocurrido un error durante la creación de features: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
