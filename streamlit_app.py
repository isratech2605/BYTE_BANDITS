import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="ProcureTrace",
    page_icon="🔎",
    layout="wide"
)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🔎 ProcureTrace")
st.subheader("Procurement Risk Intelligence")

st.write(
    "An explainable prototype for identifying suspicious financial "
    "patterns across procurement transactions."
)

st.info(
    "⚠️ ProcureTrace identifies RISK INDICATORS. "
    "It does not automatically declare a transaction as corruption."
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

try:
    df = pd.read_csv("procurementdata.csv")
except FileNotFoundError:
    st.error(
        "procurementdata.csv was not found. "
        "Make sure it is uploaded to the GitHub repository."
    )
    st.stop()

# ---------------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------------

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

df["Declared_Unit_Price"] = pd.to_numeric(
    df["Declared_Unit_Price"], errors="coerce"
)

df["Reference_Unit_Price"] = pd.to_numeric(
    df["Reference_Unit_Price"], errors="coerce"
)

df["Quantity"] = pd.to_numeric(
    df["Quantity"], errors="coerce"
)

# ---------------------------------------------------------
# CALCULATE OVERPRICING
# ---------------------------------------------------------

df["Overpricing_%"] = (
    (df["Declared_Unit_Price"] - df["Reference_Unit_Price"])
    / df["Reference_Unit_Price"]
) * 100

df["Overpricing_%"] = df["Overpricing_%"].clip(lower=0)

# ---------------------------------------------------------
# CONTRACTOR PATTERNS
# ---------------------------------------------------------

contractor_avg = (
    df.groupby("Contractor_ID")["Overpricing_%"]
    .mean()
    .to_dict()
)

contractor_count = (
    df.groupby("Contractor_ID")["Transaction_ID"]
    .count()
    .to_dict()
)

df["Contractor_Avg_Overpricing"] = df["Contractor_ID"].map(
    contractor_avg
)

df["Contractor_Transaction_Count"] = df["Contractor_ID"].map(
    contractor_count
)

# ---------------------------------------------------------
# SUPPLIER PATTERNS
# ---------------------------------------------------------

supplier_avg = (
    df.groupby("Supplier_ID")["Overpricing_%"]
    .mean()
    .to_dict()
)

df["Supplier_Avg_Overpricing"] = df["Supplier_ID"].map(
    supplier_avg
)

# ---------------------------------------------------------
# RISK SCORE
# ---------------------------------------------------------

def calculate_risk(row):

    score = 0

    # 1. Price anomaly
    if row["Overpricing_%"] > 30:
        score += 50
    elif row["Overpricing_%"] > 20:
        score += 40
    elif row["Overpricing_%"] > 10:
        score += 25
    elif row["Overpricing_%"] > 5:
        score += 10

    # 2. Repeated contractor pattern
    if row["Contractor_Avg_Overpricing"] > 20:
        score += 25
    elif row["Contractor_Avg_Overpricing"] > 10:
        score += 15

    # 3. Repeated transactions
    if row["Contractor_Transaction_Count"] >= 3:
        score += 10

    # 4. Supplier pattern
    if row["Supplier_Avg_Overpricing"] > 15:
        score += 10

    return min(score, 100)


df["Risk_Score"] = df.apply(calculate_risk, axis=1)

# ---------------------------------------------------------
# RISK LEVEL
# ---------------------------------------------------------

def risk_level(score):

    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


df["Risk_Level"] = df["Risk_Score"].apply(risk_level)

# ---------------------------------------------------------
# RISK REASONS
# ---------------------------------------------------------

def generate_reason(row):

    reasons = []

    if row["Overpricing_%"] > 30:
        reasons.append("Severe price deviation")
    elif row["Overpricing_%"] > 10:
        reasons.append("Price above reference")

    if row["Contractor_Avg_Overpricing"] > 20:
        reasons.append("Repeated contractor price pattern")

    if row["Contractor_Transaction_Count"] >= 3:
        reasons.append("Repeated contractor activity")

    if row["Supplier_Avg_Overpricing"] > 15:
        reasons.append("Supplier shows price pattern")

    if not reasons:
        reasons.append("No major anomaly detected")

    return ", ".join(reasons)


df["Risk_Reasons"] = df.apply(generate_reason, axis=1)

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.header("🔍 Filters")

locations = ["All"] + sorted(df["Location"].dropna().unique().tolist())

selected_location = st.sidebar.selectbox(
    "Location",
    locations
)

risk_options = ["All", "HIGH", "MEDIUM", "LOW"]

selected_risk = st.sidebar.selectbox(
    "Risk Level",
    risk_options
)

filtered_df = df.copy()

if selected_location != "All":
    filtered_df = filtered_df[
        filtered_df["Location"] == selected_location
    ]

if selected_risk != "All":
    filtered_df = filtered_df[
        filtered_df["Risk_Level"] == selected_risk
    ]

# ---------------------------------------------------------
# DASHBOARD METRICS
# ---------------------------------------------------------

st.header("📊 Risk Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Transactions Analysed",
        len(filtered_df)
    )

with col2:
    st.metric(
        "High Risk",
        len(filtered_df[filtered_df["Risk_Level"] == "HIGH"])
    )

with col3:
    st.metric(
        "Medium Risk",
        len(filtered_df[filtered_df["Risk_Level"] == "MEDIUM"])
    )

with col4:
    avg_overpricing = filtered_df["Overpricing_%"].mean()

    st.metric(
        "Avg Price Deviation",
        f"{avg_overpricing:.1f}%"
    )

# ---------------------------------------------------------
# HIGH RISK ALERT
# ---------------------------------------------------------

high_risk = filtered_df[
    filtered_df["Risk_Level"] == "HIGH"
].sort_values(
    "Risk_Score",
    ascending=False
)

if len(high_risk) > 0:

    st.warning(
        f"🚨 {len(high_risk)} high-risk transaction(s) require review."
    )

# ---------------------------------------------------------
# TRANSACTION TABLE
# ---------------------------------------------------------

st.header("📋 Transaction Risk Analysis")

display_columns = [
    "Transaction_ID",
    "Date",
    "Project_ID",
    "Contractor_ID",
    "Supplier_ID",
    "Material",
    "Quantity",
    "Declared_Unit_Price",
    "Reference_Unit_Price",
    "Overpricing_%",
    "Risk_Score",
    "Risk_Level",
    "Risk_Reasons"
]

st.dataframe(
    filtered_df[display_columns].sort_values(
        "Risk_Score",
        ascending=False
    ),
    use_container_width=True
)

# ---------------------------------------------------------
# PRICE DEVIATION CHART
# ---------------------------------------------------------

st.header("📈 Price Deviation")

chart_data = filtered_df[
    ["Transaction_ID", "Overpricing_%"]
].set_index("Transaction_ID")

st.bar_chart(chart_data)

# ---------------------------------------------------------
# CONTRACTOR PATTERN
# ---------------------------------------------------------

st.header("🏢 Contractor Pattern Analysis")

contractor_data = (
    filtered_df
    .groupby("Contractor_ID")["Overpricing_%"]
    .mean()
    .sort_values(ascending=False)
)

st.bar_chart(contractor_data)

# ---------------------------------------------------------
# PROJECT PATTERN
# ---------------------------------------------------------

st.header("🏗️ Project Risk Pattern")

project_data = (
    filtered_df
    .groupby("Project_ID")["Risk_Score"]
    .mean()
    .sort_values(ascending=False)
)

st.bar_chart(project_data)

# ---------------------------------------------------------
# INVESTIGATOR VIEW
# ---------------------------------------------------------

st.header("🕵️ Investigator View")

if len(high_risk) > 0:

    selected_transaction = st.selectbox(
        "Select a high-risk transaction",
        high_risk["Transaction_ID"].tolist()
    )

    transaction = high_risk[
        high_risk["Transaction_ID"] == selected_transaction
    ].iloc[0]

    st.subheader(
        f"Transaction {transaction['Transaction_ID']}"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Risk Score",
            f"{transaction['Risk_Score']}/100"
        )

    with c2:
        st.metric(
            "Price Deviation",
            f"{transaction['Overpricing_%']:.1f}%"
        )

    with c3:
        st.metric(
            "Risk Level",
            transaction["Risk_Level"]
        )

    st.write("### Why was this transaction flagged?")

    st.write(transaction["Risk_Reasons"])

    st.write("### Transaction Details")

    st.write(
        {
            "Project": transaction["Project_ID"],
            "Contractor": transaction["Contractor_ID"],
            "Supplier": transaction["Supplier_ID"],
            "Material": transaction["Material"],
            "Location": transaction["Location"],
            "Quantity": transaction["Quantity"],
            "Declared Price": transaction["Declared_Unit_Price"],
            "Reference Price": transaction["Reference_Unit_Price"]
        }
    )

else:

    st.success(
        "No high-risk transactions found under the current filters."
    )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "ProcureTrace — Prototype for pattern-based financial risk detection. "
    "Risk scores are analytical indicators and require human investigation."
)
