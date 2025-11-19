-- schema.sql
-- Loan Default Prediction Project
-- PostgreSQL DDL: crea tablas base para customers, accounts, loans, payments,
-- credit_history, delinquencies, además de tablas para modelos y predicciones.
-- Recomendación: ejecutar en una base de datos vacía. No subir datos sensibles.

-- Requisitos: extensión para UUID
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ==========================
-- Tipos ENUMs
-- ==========================
CREATE TYPE loan_status AS ENUM ('active','closed','defaulted','charged_off','past_due');
CREATE TYPE gender_type AS ENUM ('male','female','other');

-- ==========================
-- Tabla: customers
-- ==========================
CREATE TABLE IF NOT EXISTS customers (
    customer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_customer_id varchar(100), -- ID proveniente de sistemas legacy
    first_name varchar(150),
    last_name varchar(150),
    birth_date date,
    gender gender_type,
    job varchar(100),  -- <-- ¡ESTA ES LA LÍNEA QUE AÑADIMOS!
    zip_code varchar(20),
    region varchar(100),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Indices útiles
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers (external_customer_id);
CREATE INDEX IF NOT EXISTS idx_customers_region ON customers (region);

-- ==========================
-- Tabla: accounts
-- ==========================
CREATE TABLE IF NOT EXISTS accounts (
    account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    account_type varchar(50),
    account_open_date date,
    account_status varchar(50),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts (customer_id);

-- ==========================
-- Tabla: loans
-- ==========================
CREATE TABLE IF NOT EXISTS loans (
    loan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    product_type varchar(100),
    origination_date date,
    principal_amount numeric(14,2) NOT NULL,
    outstanding_balance numeric(14,2) DEFAULT 0.00,
    term_months integer,
    interest_rate numeric(7,4), -- e.g. 0.0750 = 7.5%
    loan_status loan_status DEFAULT 'active',
    next_payment_due_date date,
    last_payment_date date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_loans_account_id ON loans (account_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans (loan_status);
CREATE INDEX IF NOT EXISTS idx_loans_origination_date ON loans (origination_date);

-- ==========================
-- Tabla: payments
-- ==========================
CREATE TABLE IF NOT EXISTS payments (
    payment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id uuid NOT NULL REFERENCES loans(loan_id) ON DELETE CASCADE,
    payment_date date NOT NULL,
    payment_amount numeric(14,2) NOT NULL,
    payment_method varchar(50),
    balance_after numeric(14,2),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payments_loan_id ON payments (loan_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments (payment_date);

-- ==========================
-- Tabla: credit_history
-- ==========================
CREATE TABLE IF NOT EXISTS credit_history (
    credit_history_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    report_date date NOT NULL,
    score_source varchar(100),
    score_value numeric(8,2),
    total_accounts integer,
    delinquent_accounts integer,
    revolving_utilization numeric(6,4),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_credit_history_customer_id ON credit_history (customer_id);
CREATE INDEX IF NOT EXISTS idx_credit_history_report_date ON credit_history (report_date);

-- ==========================
-- Tabla: delinquencies (target)
-- ==========================
-- Aquí definimos el target de default (ej. default_flag = 1 si >90 días past due dentro del horizonte)
CREATE TABLE IF NOT EXISTS delinquencies (
    delinquency_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id uuid NOT NULL REFERENCES loans(loan_id) ON DELETE CASCADE,
    as_of_date date NOT NULL,
    days_past_due integer DEFAULT 0,
    d30 boolean DEFAULT false,
    d60 boolean DEFAULT false,
    d90 boolean DEFAULT false,
    default_flag boolean DEFAULT false,
    default_date date,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_delinquencies_loan_id ON delinquencies (loan_id);
CREATE INDEX IF NOT EXISTS idx_delinquencies_as_of_date ON delinquencies (as_of_date);
CREATE INDEX IF NOT EXISTS idx_delinquencies_default_flag ON delinquencies (default_flag);

-- ==========================
-- Tabla: feature_store (opcional)
-- ==========================
-- Almacena features calculados listos para training/predicción.
CREATE TABLE IF NOT EXISTS feature_store (
    feature_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id uuid NOT NULL REFERENCES loans(loan_id) ON DELETE CASCADE,
    snapshot_date date NOT NULL, -- fecha a la que corresponden las features
    feature_json jsonb,         -- features arbitrarias en formato JSON
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feature_store_loan_snapshot ON feature_store (loan_id, snapshot_date);

-- ==========================
-- Tablas: model_runs y predictions
-- ==========================
-- Model runs contiene metadatos de ejecuciones de entrenamiento
CREATE TABLE IF NOT EXISTS model_runs (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name varchar(200) NOT NULL,
    model_version varchar(50),
    run_date timestamptz NOT NULL DEFAULT now(),
    metrics jsonb,
    artifact_path varchar(500)
);

-- Predictions guarda las predicciones realizadas en producción o durante pruebas
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id uuid REFERENCES model_runs(run_id) ON DELETE SET NULL,
    loan_id uuid REFERENCES loans(loan_id) ON DELETE SET NULL,
    snapshot_date date NOT NULL,
    probability numeric(6,4) NOT NULL,
    threshold numeric(6,4),
    predicted_label boolean,
    explain_json jsonb, -- p.ej. top features y valores (SHAP-like)
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_predictions_loan_snapshot ON predictions (loan_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_predictions_run ON predictions (run_id);

-- ==========================
-- Triggers: updated_at automático
-- ==========================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = now();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a tablas que usan updated_at
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_customers') THEN
    CREATE TRIGGER set_updated_at_customers
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_accounts') THEN
    CREATE TRIGGER set_updated_at_accounts
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_loans') THEN
    CREATE TRIGGER set_updated_at_loans
    BEFORE UPDATE ON loans
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
  END IF;
END$$;

-- ==========================
-- Constraints y comprobaciones útiles
-- ==========================
ALTER TABLE loans
  ADD CONSTRAINT chk_principal_positive CHECK (principal_amount >= 0);

ALTER TABLE payments
  ADD CONSTRAINT chk_payment_nonnegative CHECK (payment_amount >= 0);

-- ==========================
-- Ejemplos de vistas (helpers)
-- ==========================
-- Vista: saldo mensual por loan (resumen)
CREATE OR REPLACE VIEW vw_monthly_balances AS
SELECT
  l.loan_id,
  date_trunc('month', p.payment_date)::date AS month,
  SUM(p.payment_amount) AS total_paid_in_month,
  MAX(p.balance_after) AS closing_balance
FROM loans l
LEFT JOIN payments p ON p.loan_id = l.loan_id
GROUP BY l.loan_id, date_trunc('month', p.payment_date);

-- Vista: resumen de comportamiento por loan
CREATE OR REPLACE VIEW vw_loan_summary AS
SELECT
  l.loan_id,
  l.account_id,
  l.origination_date,
  l.principal_amount,
  l.outstanding_balance,
  l.term_months,
  l.interest_rate,
  COUNT(p.payment_id) FILTER (WHERE p.payment_date IS NOT NULL) AS n_payments,
  MAX(d.days_past_due) AS max_days_past_due,
  MAX(d.default_flag::int) AS ever_defaulted
FROM loans l
LEFT JOIN payments p ON p.loan_id = l.loan_id
LEFT JOIN delinquencies d ON d.loan_id = l.loan_id
GROUP BY l.loan_id;

-- ==========================
-- Fin del schema
-- ==========================
COMMENT ON TABLE customers IS 'Clientes: tabla maestra de clientes (sin datos sensibles en el repo)';
COMMENT ON TABLE loans IS 'Préstamos: información de producto y estado';
COMMENT ON TABLE delinquencies IS 'Registro de delinquencias y target de default';

-- Agrega cualquier otro índice o vista que necesites durante la ingeniería de features.

-- Nota final: evita subir información real o PII al repositorio público. Usa scripts de "seeding"
-- para crear datos de ejemplo si necesitas mostrar el proyecto en línea.
