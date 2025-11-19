# 💸 Proyecto de Predicción de Default de Préstamos (End-to-End)

¡Bienvenido! Este es un proyecto completo de Machine Learning que predice el riesgo de default (no pago) de un préstamo. El sistema ingiere datos crudos, los procesa, entrena un modelo de IA y despliega una API y un Dashboard interactivo para realizar predicciones en tiempo real.

---

## ✨ Características Principales

* **Base de Datos Dockerizada:** La base de datos PostgreSQL corre en un contenedor de Docker (`docker-compose`), haciéndola 100% reproducible.
* **Pipeline de ETL:** Un script de Python (`src/etl/ingest.py`) extrae, transforma y carga 5,000 registros de préstamos en la base de datos relacional.
* **Ingeniería de Características:** Un script (`src/features/build_features.py`) "traduce" datos crudos (ej. 'male', 'skilled') a un formato numérico listo para la IA.
* **Modelo de IA (Random Forest):** Un script (`src/models/train.py`) entrena un modelo `RandomForestClassifier` que maneja el desbalanceo de clases para predecir el riesgo (`default_flag`).
* **API de Predicción:** Una API de **FastAPI** (`src/api/main.py`) carga el modelo entrenado y expone un endpoint `/predict` para predicciones en tiempo real.
* **Dashboard Interactivo:** Un Dashboard de **Streamlit** (`src/dashboard/app.py`) consume la API y provee una interfaz de usuario amigable para simular préstamos.

---

## 🛠️ Stack Tecnológico

* **Backend & Servidor:** Python, FastAPI, Uvicorn
* **Frontend (Dashboard):** Streamlit
* **Machine Learning:** Scikit-learn (RandomForest), Pandas
* **Base de Datos:** PostgreSQL
* **Infraestructura:** Docker (Docker Compose)
* **Herramientas de Conexión:** SQLAlchemy, Psycopg2, Requests

---

## 🏃‍♂️ Cómo Ejecutarlo (Instrucciones)

Este proyecto requiere 3 terminales corriendo simultáneamente (BD, API, Dashboard).

### Requisitos
* Tener Docker Desktop instalado y corriendo.
* Tener un entorno de Python (como Anaconda) con las librerías de `requirements.txt` (o instalarlas manualmente).

### 1. Levantar la Base de Datos (Docker)
(Solo se hace una vez)

En una terminal (PowerShell o Anaconda Prompt):
```bash
# 1. Asegúrate de estar en la carpeta raíz del proyecto
cd C:\Users\Eduar\loan-default-project

# 2. Levanta el contenedor de Postgres
docker-compose up -d
