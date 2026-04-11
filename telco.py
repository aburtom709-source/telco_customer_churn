import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

# =========================
# CONFIGURACIÓN VISUAL
# =========================
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (8, 5)

# =========================
# PREGUNTAS DE NEGOCIO
# =========================
# 1. ¿Cuál es la tasa de abandono actual de la empresa?
# 2. ¿Qué servicios o condiciones contractuales están más correlacionados con la pérdida de clientes?
# 3. ¿La falta de soporte técnico es un detonante de abandono, especialmente en contratos de corto plazo?

# =========================
# CARGA DE DATOS
# =========================
df = pd.read_excel("Telco_customer_churn.xlsx")

# =========================
# COMPROBACIONES RAPIDAS
# =========================
print(df.shape)
print(df.info())
print(df.describe())
print(df.isna().sum())
print(df.duplicated().sum())
print(df.dtypes)

# =========================
# LIMPIEZA DE DATOS
# =========================
clean_data = df.copy()
clean_data['Total Charges'] = pd.to_numeric(clean_data['Total Charges'], errors='coerce')
clean_data = clean_data.drop(columns=['Count'])

# =========================
# GUARDAR EN BASE DE DATOS (SQL)
# =========================
conn = sqlite3.connect("telco.db")
clean_data.to_sql("telco_clean", conn, if_exists="replace", index=False)

# =========================
# ANÁLISIS EXPLORATORIO
# =========================

# Churn general
churn_general = pd.read_sql_query("""
    SELECT 
        "Churn Label",
        COUNT(*) as quantity
    FROM telco_clean
    GROUP BY "Churn Label"
""", conn)

sns.barplot(data=churn_general, x='Churn Label', y='quantity', hue='Churn Label')
plt.title("Distribución general de churn")
plt.ylabel("Cantidad de clientes")
plt.xlabel("")
plt.savefig("churn_general.png", bbox_inches='tight')
plt.show()
plt.close()

# Churn por soporte técnico
tech_churn = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Tech Support"
    FROM telco_clean
    GROUP BY "Tech Support"
""", conn)

sns.barplot(data=tech_churn, x='Tech Support', y='churn_rate')
plt.title("Churn por soporte técnico")
plt.ylabel("Churn (%)")
plt.savefig("churn_tech_support.png", bbox_inches='tight')
plt.show()
plt.close()

# Churn por contrato
contract_churn = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Contract"
    FROM telco_clean
    GROUP BY "Contract"
""", conn)

sns.barplot(data=contract_churn, x='Contract', y='churn_rate')
plt.title("Churn por tipo de contrato")
plt.ylabel("Churn (%)")
plt.savefig("churn_contract.png", bbox_inches='tight')
plt.show()
plt.close()

# Churn por contrato y soporte técnico
contract_tech = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Contract",
        "Tech Support"
    FROM telco_clean
    GROUP BY "Contract", "Tech Support"
""", conn)

sns.barplot(data=contract_tech, x='Contract', y='churn_rate', hue='Tech Support')
plt.title("Churn por tipo de contrato y soporte técnico")
plt.ylabel("Churn (%)")
plt.savefig("churn_contract_tech.png", bbox_inches='tight')
plt.show()
plt.close()

# Churn por antigüedad
tenure_churn = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Tenure Months"
    FROM telco_clean
    GROUP BY "Tenure Months"
""", conn)

sns.lineplot(data=tenure_churn, x='Tenure Months', y='churn_rate')
plt.title("Churn por antigüedad")
plt.ylabel("Churn (%)")
plt.show()

# =========================
# CHURN GENERAL
# =========================
churn_summary = pd.read_sql_query("""
    SELECT 
        COUNT(*) AS total_clients,
        SUM("Churn Value") AS total_churn,
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate
    FROM telco_clean
""", conn)

print("\n--- CHURN GENERAL ---")
print(churn_summary)

# =========================
# SEGMENTO DE ALTO RIESGO
# =========================
segment_churn_rate = pd.read_sql_query("""
    SELECT 
        COUNT(*) AS segment_clients,
        SUM("Churn Value") AS segment_churn,
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS segment_churn_rate
    FROM telco_clean
    WHERE "Contract" = 'Month-to-month'
    AND "Tech Support" = 'No'
    AND "Tenure Months" < 5
""", conn)

print("\n--- SEGMENTO DE ALTO RIESGO ---")
print(segment_churn_rate)

segment_impact = pd.read_sql_query("""
    SELECT 
        ROUND(
            100.0 * SUM("Churn Value") /
            (SELECT SUM("Churn Value") FROM telco_clean),
            2
        ) AS percent_of_total_churn
    FROM telco_clean
    WHERE "Contract" = 'Month-to-month'
    AND "Tech Support" = 'No'
    AND "Tenure Months" < 5
""", conn)

print("\n--- IMPACTO TOTAL DEL SEGMENTO EN RIESGO ---")
print(segment_impact)

segment_size = pd.read_sql_query("""
    SELECT 
        ROUND(
            100.0 * COUNT(*) /
            (SELECT COUNT(*) FROM telco_clean),
            2
        ) AS segment_share_total_clients
    FROM telco_clean
    WHERE "Contract" = 'Month-to-month'
    AND "Tech Support" = 'No'
    AND "Tenure Months" < 5
""", conn)

print("\n--- TAMAÑO DEL SEGMENTO SOBRE EL TOTAL DE CLIENTES ---")
print(segment_size)
conn.close()

# =========================
# MODELO PREDICTIVO
# =========================
df_ml = clean_data.dropna(subset=['Churn Value'])

X = pd.get_dummies(df_ml[["Tech Support", "Contract", "Tenure Months", "Phone Service", "Internet Service", "Monthly Charges"]], drop_first=True)
y = df_ml["Churn Value"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight={0:1, 1:2},
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print("ROC AUC:", roc_auc_score(y_test, y_pred_proba))

# =========================
# PREDICCIÓN Y SEGMENTACIÓN
# =========================
# Generamos las variables de entrada 
X_full = pd.get_dummies(df_ml[["Tech Support", "Contract", "Tenure Months", "Phone Service", "Internet Service", "Monthly Charges"]], drop_first=True)

# Reindexamos para asegurar que el orden y cantidad de columnas coincidan exactamente con el entrenamiento
X_full = X_full.reindex(columns=X.columns, fill_value=0)

# predict_proba devuelve dos columnas: [prob_quedarse, prob_irse]
df_ml["prob_churn"] = model.predict_proba(X_full)[:, 1]

# Categorizamos el riesgo basándonos en la probabilidad
def risk_segment(p):
    if p > 0.7:
        return "High Risk"
    elif p > 0.6:
        return "Medium Risk"
    else:
        return "Low Risk"

df_ml["risk_segment"] = df_ml["prob_churn"].apply(risk_segment)

# Cantidad de clientes en riesgo
high_risk = df_ml[df_ml["risk_segment"] == "High Risk"]

# =========================
# IMPACTO ECONÓMICO
# =========================
df_ml["Monthly Charges"] = pd.to_numeric(df_ml["Monthly Charges"], errors='coerce')
df_ml["Monthly Charges"] = df_ml["Monthly Charges"].astype(float)

# Suma de los cargos mensuales de TODOS los clientes en riesgo
revenue_at_risk = df_ml.loc[
    df_ml["risk_segment"] == "High Risk", "Monthly Charges"
].sum()

# =========================
# IMPORTANCIA DE VARIABLES
# =========================
importances = pd.Series(model.feature_importances_, index=X.columns)
print(importances.sort_values(ascending=False))

# =========================
# EXPORTACIÓN
# =========================
df_final = df_ml.copy()
df_final.to_csv("telco_dashboard_.csv", index=False, float_format="%.2f")

