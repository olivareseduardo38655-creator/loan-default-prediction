import pandas as pd
from sqlalchemy import create_engine, text
import sys
import os
from dotenv import load_dotenv  # <-- ¡NUEVO! Importamos el "lector"

# --- ¡NUEVO! ---
# Esto carga las variables de tu archivo .env en la memoria
load_dotenv()

# --- 1. CONFIGURACIÓN DE LA CONEXIÓN (¡AHORA ES SEGURA!) ---
# Leemos las variables desde 'os.environ' (la memoria del sistema)
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

# Salimos si falta alguna variable
if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
    print("Error: Faltan variables de entorno en el archivo .env")
    sys.exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- 2. RUTA AL ARCHIVO DE DATOS ---
# (El resto del script es idéntico a v12)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE_PATH = os.path.join(BASE_DIR, "data", "german_credit_data.csv")


def main():
    print("Iniciando el script de ingesta (v13 - ¡Con .env!)...")
    
    try:
        # --- 3. EXTRACCIÓN (Extract) ---
        print(f"Cargando datos desde: {DATA_FILE_PATH}")
        df = pd.read_csv(DATA_FILE_PATH)
        df.columns = df.columns.str.strip()
        print("Nombres de columnas limpiados.")

        # --- 4. CONEXIÓN Y LIMPIEZA ---
        print("Creando conexión a la base de datos...")
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("Limpiando tablas (en orden de dependencia)...")
            conn.execute(text("TRUNCATE TABLE delinquencies RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE payments RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE loans RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE accounts RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))
            print("Tablas limpiadas.")

        # --- 5. TRANSFORMACIÓN (Transform) ---
        
        # --- ETAPA 1: CUSTOMERS ---
        print("Mapeando 'customers'...")
        df_customers = df.rename(columns={
            'Age': 'birth_date', 'Sex': 'gender', 'Job': 'job'
        })[['birth_date', 'gender', 'job']]
        df_customers['birth_date'] = pd.to_datetime('today').year - df_customers['birth_date']
        df_customers['birth_date'] = df_customers['birth_date'].apply(lambda x: f"{x}-01-01")

        # --- ETAPA 2: LOANS ---
        print("Mapeando 'loans'...")
        df_loans = df.rename(columns={
            'LoanAmount': 'principal_amount',
            'LoanDuration': 'term_months',
            'LoanPurpose': 'product_type'
        })[['principal_amount', 'term_months', 'product_type']]

        # --- ETAPA 3: DELINQUENCIES (¡Nuestro Target!) ---
        print("Mapeando 'delinquencies' (nuestro target)...")
        df_delinquencies = pd.DataFrame({
            'default_flag': df['Risk'].map({'Risk': True, 'No Risk': False}),
            'as_of_date': pd.to_datetime('today').date()
        })

        # --- 6. CARGA (Load) ---
        
        # --- ETAPA 1: CUSTOMERS ---
        print(f"Cargando {len(df_customers)} registros en 'customers'...")
        df_customers.to_sql('customers', con=engine, if_exists='append', index=False)
        
        # --- ETAPA 2: ACCOUNTS ---
        db_customers_ids = pd.read_sql("SELECT customer_id FROM customers", engine)
        df_accounts = db_customers_ids[['customer_id']].copy()
        df_accounts['account_type'] = 'checking'
        df_accounts['account_open_date'] = '2025-01-01'
        df_accounts['account_status'] = 'active'
        print(f"Cargando {len(df_accounts)} registros en 'accounts'...")
        df_accounts.to_sql('accounts', con=engine, if_exists='append', index=False)

        # --- ETAPA 3: LOANS ---
        db_accounts_ids = pd.read_sql("SELECT account_id FROM accounts", engine)
        df_loans['account_id'] = db_accounts_ids['account_id']
        print(f"Cargando {len(df_loans)} registros en 'loans'...")
        df_loans.to_sql('loans', con=engine, if_exists='append', index=False)
        
        # --- ETAPA 4: DELINQUENCIES ---
        db_loans_ids = pd.read_sql("SELECT loan_id FROM loans", engine)
        df_delinquencies['loan_id'] = db_loans_ids['loan_id']
        print(f"Cargando {len(df_delinquencies)} registros en 'delinquencies'...")
        df_delinquencies.to_sql('delinquencies', con=engine, if_exists='append', index=False)
        
        print("\n--- ¡ÉXITO TOTAL! (AHORA SÍ) ---")
        print("¡Todas las tablas (customers, accounts, loans, delinquencies) se cargaron y conectaron!")
        print("¡La Fase 3 de Ingesta está COMPLETA!")
        
    except Exception as e:
        print(f"Ha ocurrido un error durante la ingesta: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
