import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

# --- VISUAL CONFIGURATION ---
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (8, 5)

# --- BUSINESS QUESTION ---
# 1. What percentage of customers are churning?
# 2. Which type of customers are driving churn?
# 3. Where should the company focus retention efforts?

# --- LOAD DATA ---
df = pd.read_excel("Telco_customer_churn.xlsx")

# Quick checks
# print(df.shape)
# print(df.info())
# print(df.describe())
# print(df.isna().sum())
# print(df.duplicated().sum())
# print(df.dtypes)

# --- BASIC CLEANING ---
clean_data = df.copy()
clean_data['Total Charges'] = pd.to_numeric(clean_data['Total Charges'], errors='coerce')
clean_data = clean_data.drop(columns=['Count'])

# --- SAVE TO DATABASE ---
conn = sqlite3.connect("telco.db")
clean_data.to_sql("telco_clean", conn, if_exists="replace", index=False)


# --- EDA (EXPLORATORY DATA ANALYSIS) ---


# --- METHODOLOGY ---
# Step 1: Measure overall churn
# Step 2: Analyze churn across key dimensions:
#         - Contract type
#         - Tech Support
#         - Tenure
# Step 3: Examine interaction effects
# Step 4: Define and quantify the highest risk segment

# --- STEP 1 – OVERALL CHURN ---

# --- CHURN GENERAL ---
churn_general = pd.read_sql_query("""
    SELECT 
        "Churn Label",
        COUNT(*) as quantity
    FROM telco_clean
    GROUP BY "Churn Label"
""", conn)

sns.barplot(data=churn_general, x='Churn Label', y='quantity', hue='Churn Label')
plt.title("General distribution of Churn")
plt.ylabel("Number of customer")
plt.xlabel("")
plt.savefig("churn_general.png", bbox_inches='tight')
plt.show()
plt.close()

# --- STEP 2 – CHURN BY KEY DIMENSIONS ---

# CHURN BY TECH SUPPORT
tech_churn = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Tech Support"
    FROM telco_clean
    GROUP BY "Tech Support"
""", conn)

sns.barplot(data=tech_churn, x='Tech Support', y='churn_rate')
plt.title("Churn Rate by Tech Support")
plt.ylabel("Churn (%)")
plt.savefig("churn_tech_support.png", bbox_inches='tight')
plt.show()
plt.close()

# --- STEP 3 – INTERACTION EFFECTS ---

# CHURN BY CONTRACT
contract_churn = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Contract"
    FROM telco_clean
    GROUP BY "Contract"
""", conn)

sns.barplot(data=contract_churn, x='Contract', y='churn_rate')
plt.title("Churn Rate by Contract Type")
plt.ylabel("Churn (%)")
plt.savefig("churn_contract.png", bbox_inches='tight')
plt.show()
plt.close()

# CONTRACT BY TECH SUPPORT
contract_tech = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Contract",
        "Tech Support"
    FROM telco_clean
    GROUP BY "Contract", "Tech Support"
""", conn)

sns.barplot(data=contract_tech, x='Contract', y='churn_rate', hue='Tech Support')
plt.title("Churn Rate by Contract and Tech Support")
plt.ylabel("Churn (%)")
plt.savefig("churn_contract_tech.png", bbox_inches='tight')
plt.show()
plt.close()

# CHURN BY TENURE
tenure_churn = pd.read_sql_query("""
    SELECT 
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate,
        "Tenure Months"
    FROM telco_clean
    GROUP BY "Tenure Months"
""", conn)

sns.lineplot(data=tenure_churn, x='Tenure Months', y='churn_rate')
plt.title("Churn Rate by Tenure")
plt.ylabel("Churn (%)")
plt.show()

churn_gen = pd.read_sql_query("""
    SELECT 
        COUNT(*) AS total_clients,
        SUM("Churn Value") AS total_churn,
        ROUND(100.0 * SUM("Churn Value") / COUNT(*), 2) AS churn_rate
    FROM telco_clean
""", conn)

print("\n--- CHURN GENERAL ---")
print(churn_gen)

# --- STEP 4 – HIGH-RISK SEGMENT ANALYSIS ---

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

print("\n--- SEGMENT CHURN RATE ---")
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

print("\n--- SEGMENT IMPACT ON TOTAL CHURN ---")
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


print("\n--- SEGMENT SIZE OVER TOTAL CLIENTS ---")
print(segment_size)
conn.close()

# --- KEY FINDINGS ---
# Total churn is 26%
# Most customers leave in the first 5 months (47–60%)
# New customers have tenure < 5 months
# Month-to-month contracts and no tech support make churn higher

# --- BUSINESS INTERPRETATION ---
# Most leaving customers are new
# They have no long contract and no support
# There is a problem keeping new customers

# --- RECOMMENDATIONS ---
# Help new customers more in the first 90 days
# Encourage annual contracts
# Give tech support to new customers
# Watch high-risk customers early

# --- LIMITATIONS ---
# Only shows data (descriptive)
# We do not know the exact cause
# No predictive models were used
