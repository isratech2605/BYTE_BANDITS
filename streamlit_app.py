import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="ProcureTrace",
    page_icon="🔎",
    layout="wide"
)

# -----------------------------
# TITLE
# -----------------------------

st.title("🔎 ProcureTrace")
st.subheader("Procurement Financial Pattern Intelligence")

st.write(
    "ProcureTrace analyzes procurement transactions to identify "
    "unusual pricing and repeated financial patterns that may "
    "require further investigation."
)

st.info(
    "⚠️ ProcureTrace identifies risk patterns — it does not determine "
    "whether corruption or fraud has occurred."
)

# -----------------------------
# LOAD DATA
# -----------------------------

try:
    df = pd.read_csv("procurementdata.csv")

except Exception:
    st.error(
        "Could not find procurementdata.csv. "
        "Make sure the CSV is uploaded to the GitHub repository."
    )
    st.stop()

# -----------------------------
# CALCULATE PRICE ANOMALY
# -----------------------------

df["Markup_%"] = (
    (df["Declared_Unit_Price"] - df["Reference_Unit_Price"])
    / df["Reference_Unit_Price"]
) * 100

# -----------------------------
# RISK SCORE
# -----------------------------

def calculate_risk(row):

    score = 0

    # Price anomaly
    if row["Markup_%"] >= 50:
        score += 40

    elif row["Markup_%"] >= 20:
        score += 20

    # Very high markup
    if row["Markup_%"] >= 80:
        score += 20

    # Quantity signal
    if row["Quantity"] >= 1000:
        score += 10

    if score >= 60:
        return "HIGH"

    elif score >= 30:
        return "MEDIUM"

    else:
        return "LOW"


df["Risk_Level"] = df.apply(calculate_risk, axis=1)

# -----------------------------
# DASHBOARD METRICS
# -----------------------------

st.divider()

st.header("📊 Transaction Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Transactions",
    len(df)
)

col2.metric(
    "Projects",
    df["Project_ID"].nunique()
)

col3.metric(
    "Contractors",
    df["Contractor_ID"].nunique()
)

col4.metric(
    "Suppliers",
    df["Supplier_ID"].nunique()
)

# -----------------------------
# RISK SUMMARY
# -----------------------------

st.header("⚠️ Risk Overview")

risk_counts = df["Risk_Level"].value_counts()

col1, col2, col3 = st.columns(3)

col1.metric(
    "🔴 High Risk",
    risk_counts.get("HIGH", 0)
)

col2.metric(
    "🟠 Medium Risk",
    risk_counts.get("MEDIUM", 0)
)

col3.metric(
    "🟢 Low Risk",
    risk_counts.get("LOW", 0)
)

# -----------------------------
# PRICE ANOMALIES
# -----------------------------

st.divider()

st.header("📈 Price Anomalies")

anomalies = df.sort_values(
    "Markup_%",
    ascending=False
)

st.dataframe(
    anomalies[
        [
            "Transaction_ID",
            "Project_ID",
            "Contractor_ID",
            "Supplier_ID",
            "Material",
            "Declared_Unit_Price",
            "Reference_Unit_Price",
            "Markup_%",
            "Risk_Level"
        ]
    ],
    use_container_width=True
)

# -----------------------------
# CONTRACTOR-SUPPLIER PATTERNS
# -----------------------------

st.divider()

st.header("🔗 Repeated Contractor–Supplier Patterns")

relationships = (
    df.groupby(
        ["Contractor_ID", "Supplier_ID"]
    )
    .size()
    .reset_index(name="Transaction_Count")
    .sort_values(
        "Transaction_Count",
        ascending=False
    )
)

repeated = relationships[
    relationships["Transaction_Count"] >= 2
]

if len(repeated) > 0:

    st.warning(
        "Repeated contractor–supplier relationships detected."
    )

    st.dataframe(
        repeated,
        use_container_width=True
    )

else:

    st.success(
        "No repeated contractor–supplier relationships detected."
        
    )

# -----------------------------
# PATTERN INTELLIGENCE
# -----------------------------

st.divider()

st.header("🧠 Pattern Intelligence")

st.write(
    "ProcureTrace looks beyond individual transactions and "
    "searches for repeated relationships across projects."
)

# Contractor-Supplier relationship analysis

relationship_analysis = (
    df.groupby(
        ["Contractor_ID", "Supplier_ID"]
    )
    .agg(
        Transaction_Count=("Transaction_ID", "count"),
        Project_Count=("Project_ID", "nunique"),
        Average_Markup=("Markup_%", "mean"),
        Maximum_Markup=("Markup_%", "max")
    )
    .reset_index()
)

# Calculate relationship risk

def relationship_risk(row):

    score = 0

    # Repeated transactions
    if row["Transaction_Count"] >= 3:
        score += 25

    elif row["Transaction_Count"] >= 2:
        score += 10

    # Multiple projects
    if row["Project_Count"] >= 3:
        score += 25

    elif row["Project_Count"] >= 2:
        score += 10

    # Average price anomaly
    if row["Average_Markup"] >= 50:
        score += 30

    elif row["Average_Markup"] >= 20:
        score += 15

    # Extremely high transaction
    if row["Maximum_Markup"] >= 80:
        score += 20

    return min(score, 100)


relationship_analysis["Pattern_Risk_Score"] = (
    relationship_analysis.apply(
        relationship_risk,
        axis=1
    )
)

# Pattern level

def pattern_level(score):

    if score >= 70:
        return "🔴 HIGH"

    elif score >= 40:
        return "🟠 MEDIUM"

    else:
        return "🟢 LOW"


relationship_analysis["Pattern_Risk"] = (
    relationship_analysis["Pattern_Risk_Score"]
    .apply(pattern_level)
)

# Sort highest risk first

relationship_analysis = relationship_analysis.sort_values(
    "Pattern_Risk_Score",
    ascending=False
)

st.subheader("Contractor–Supplier Relationship Risk")

st.dataframe(
    relationship_analysis[
        [
            "Contractor_ID",
            "Supplier_ID",
            "Transaction_Count",
            "Project_Count",
            "Average_Markup",
            "Maximum_Markup",
            "Pattern_Risk_Score",
            "Pattern_Risk"
        ]
    ],
    use_container_width=True
)

# Highlight strongest pattern

high_pattern = relationship_analysis[
    relationship_analysis["Pattern_Risk_Score"] >= 70
]

if len(high_pattern) > 0:

    st.warning(
        f"🚨 {len(high_pattern)} relationship pattern(s) "
        "show multiple elevated risk indicators."
    )

else:

    st.success(
        "No high-risk relationship patterns detected."
    )

# -----------------------------
# INVESTIGATION QUEUE
# -----------------------------

st.divider()

st.header("🚨 Investigation Queue")

high_risk = df[
    df["Risk_Level"] == "HIGH"
].sort_values(
    "Markup_%",
    ascending=False
)

if len(high_risk) > 0:

    st.write(
        "Transactions below have the strongest risk signals "
        "and may be prioritized for human review."
    )

    st.dataframe(
        high_risk[
            [
                "Transaction_ID",
                "Project_ID",
                "Contractor_ID",
                "Supplier_ID",
                "Material",
                "Markup_%",
                "Risk_Level"
            ]
        ],
        use_container_width=True
    )

else:

    st.success(
        "No high-risk transactions detected."
    )

# -----------------------------
# DISCLAIMER
# -----------------------------

st.divider()

st.caption(
    "ProcureTrace is a prototype for pattern detection. "
    "Risk scores are indicators for investigation and are not "
    "proof of financial crime."
)
