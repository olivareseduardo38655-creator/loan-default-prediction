#%%
# --- CELDA 1: Importar librerías ---
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import os
from dotenv import load_dotenv

print("Librerías importadas.")

#%%
# --- CELDA 2: Conexión y Extracción (¡SEGURA!) ---

# Cargamos los secretos desde .env
# CORRECCIÓN: Usamos '..' (un nivel arriba) porque estamos en 'notebooks/' y .env está en la raíz.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configuración de Conexión
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

# Verificamos que se cargaron
if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
    print("Error: Faltan variables en .env. Asegúrate de que el archivo .env está en la raíz del proyecto.")
else:
    print("¡Variables de entorno (.env) cargadas con éxito!")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Query para unir todas las tablas
QUERY = """
SELECT 
    c.job,
    c.gender,
    c.birth_date,
    l.principal_amount,
    l.term_months,
    l.product_type,
    d.default_flag  -- ¡Nuestro TARGET!
FROM 
    loans l
JOIN 
    accounts a ON l.account_id = a.account_id
JOIN 
    customers c ON a.customer_id = c.customer_id
JOIN 
    delinquencies d ON l.loan_id = d.loan_id;
"""

print("Conectando a la base de datos (¡de forma segura!)...")
try:
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql(QUERY, engine)
    print(f"¡Datos cargados con éxito! Se cargaron {len(df)} filas.")
except Exception as e:
    print(f"Error al conectar o extraer datos: {e}")

#%%
# --- CELDA 3: Ver el Resumen (df.info) ---
# Ahora que 'df' existe, vamos a inspeccionarlo.

print("Resumen del DataFrame:")
df.info()

#%%
# --- CELDA 4: Ver la Tabla (df.head) ---
# Esta celda SÍ mostrará la tabla.

print("Primeras 5 filas:")
df.head()

#%%
# --- CELDA 5: Gráfica (Tasa de Default por Trabajo) ---
print("Generando gráfica: Tasa de Default por Trabajo...")

df_job_risk = df.groupby('job')['default_flag'].mean().reset_index()
df_job_risk = df_job_risk.sort_values(by='default_flag', ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x='default_flag', y='job', data=df_job_risk, palette='viridis')
plt.title('Tasa de Default por Tipo de Trabajo', fontsize=16)
plt.xlabel('Tasa de Default (Promedio)', fontsize=12)
plt.ylabel('Tipo de Trabajo', fontsize=12)
plt.show()

#%%
# --- CELDA 6: Gráfica (Histograma Monto) ---
print("Generando gráfica: Distribución del Monto del Préstamo...")
plt.figure(figsize=(12, 6))
sns.histplot(data=df, x='principal_amount', kde=True, bins=50)
plt.title('Distribución del Monto del Préstamo', fontsize=16)
plt.xlabel('Monto del Préstamo', fontsize=12)
plt.ylabel('Cantidad de Préstamos', fontsize=12)
plt.show()

#%%
# --- CELDA 7: Gráfica (Box Plot - Monto vs. Default) ---
print("Generando gráfica: Diagrama de Caja (Monto vs. Tasa de Default)...")
plt.figure(figsize=(10, 6))
sns.boxplot(x='default_flag', y='principal_amount', data=df, palette='muted')
plt.title('Distribución del Monto del Préstamo vs. Default', fontsize=16)
plt.xlabel('¿Hizo Default? (True=Sí, False=No)', fontsize=12)
plt.ylabel('Monto del Préstamo', fontsize=12)
plt.show()

#%%
# --- CELDA 8: Gráfica (KDE Plot - Monto vs. Default) ---
print("Generando gráfica: Gráfico de Densidad (Monto vs. Tasa de Default)...")
plt.figure(figsize=(12, 6))
sns.kdeplot(data=df, x='principal_amount', hue='default_flag', fill=True, common_norm=False, palette='husl')
plt.title('Distribución del Monto del Préstamo por Estado de Default', fontsize=16)
plt.xlabel('Monto del Préstamo', fontsize=12)
plt.ylabel('Densidad', fontsize=12)
plt.show()

#%%
# --- CELDA 9: Gráfica Interactiva (Plotly Box Plot) ---
print("Generando gráfica interactiva (Diagrama de Caja)...")
fig = px.box(
    df, 
    x='default_flag', 
    y='principal_amount',
    color='default_flag',
    title='Distribución del Monto del Préstamo vs. Default (Interactivo)',
    labels={'default_flag':'¿Hizo Default?', 'principal_amount':'Monto del Préstamo'}
)
fig.show()

#%%
# --- CELDA 10: Gráfica de BI (Rangos de Monto) ---
print("Generando gráfica de BI (Tasa de Default por Rango)...")
# 1. Creamos los rangos (bins)
df['rango_monto'] = pd.qcut(df['principal_amount'], q=4, labels=['Bajo', 'Medio', 'Alto', 'Muy Alto'])
# 2. Agrupamos
df_bi_monto = df.groupby('rango_monto')['default_flag'].mean().reset_index()
print(df_bi_monto)
# 3. Graficamos
plt.figure(figsize=(10, 6))
sns.barplot(x='rango_monto', y='default_flag', data=df_bi_monto, palette='coolwarm')
plt.title('Tasa de Default por Rango de Monto del Préstamo', fontsize=16)
plt.xlabel('Rango del Monto', fontsize=12)
plt.ylabel('Tasa de Default (Promedio)', fontsize=12)
plt.show()

#%%
# --- CELDA 11: Gráfica de BI (Ganancias vs. Pérdidas) ---
print("Generando gráfica de Negocio: Ganancias vs. Pérdidas Totales...")
# 1. Agrupamos y sumamos
df_bi_total = df.groupby('default_flag')['principal_amount'].sum().reset_index()
# 2. Traducimos
df_bi_total['Estado del Préstamo'] = df_bi_total['default_flag'].map({True: 'Pérdida (Default)', False: 'Ganancia (Pagado)'})
df_bi_total = df_bi_total.rename(columns={'principal_amount': 'Monto Total Acumulado'})
print(df_bi_total)
# 3. Graficamos
fig = px.bar(
    df_bi_total,
    x='Estado del Préstamo',
    y='Monto Total Acumulado',
    color='Estado del Préstamo',
    title='Ganancias Totales (Préstamos Pagados) vs. Pérdidas Totales (Default)',
    labels={'Estado del Préstamo': 'Estado del Préstamo', 'Monto Total Acumulado': 'Monto Total (en DM)'},
    text='Monto Total Acumulado'
)
fig.update_traces(texttemplate='%{text:.2s}K', textposition='outside')
fig.show()

#%%
# --- CELDA 12: Encontrar Préstamos Extremos (Min y Max) ---
print("Buscando las características de los préstamos más grande y más pequeño...")
# 1. Encontrar índices
idx_prestamo_max = df['principal_amount'].idxmax()
idx_prestamo_min = df['principal_amount'].idxmin()
# 2. Seleccionar filas
prestamo_max = df.loc[idx_prestamo_max]
prestamo_min = df.loc[idx_prestamo_min]
# 3. Imprimir
print("\n--- 💰 PRÉSTAMO MÁS GRANDE ---")
print(prestamo_max)
print("\n" + "="*40)
print("\n--- 💸 PRÉSTAMO MÁS PEQUEÑO ---")
print(prestamo_min)
