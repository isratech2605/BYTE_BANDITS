import streamlit as st
import pandas as pd

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="ProcureTrace",
    page_icon="🔎",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("🔎 ProcureTrace")
st.subheader("Procurement Financial Pattern Intelligence")

st.write(
    "ProcureTrace analyzes procurement transactions to identify "
    "unusual pricing and repeated financial patterns that may "
    "require further investigation."
)

st.info(
    "⚠️ ProcureTrace identifies risk patterns. "
    "It does not determine whether corruption or fraud has occurred."
)

# =========================================================
# LOAD DATA
# =========================================================

try:
    df = pd.read_csv("procurementdata.csv")
except Exception:
    st.error(
        "Could not find procurementdata.csv. "
        "Make sure the CSV is uploaded to the GitHub repository."
    )
    st.stop()

# =========================================================
# CLEAN DATA
# =========================================================

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

df["Declared_Unit_Price"] = pd.to_numeric(
    df["Declared_Unit_Price"],
    errors="coerce"
)

df["Reference_Unit_Price"] = pd.to_numeric(
    df["Reference_Unit_Price"],
    errors="coerce"
)

df["Quantity"] = pd.to_numeric(
    df["Quantity"],
    errors="coerce"
)

# =========================================================
# PRICE ANOMALY
# =========================================================

df["Markup_%"] = (
    (
        df["Declared_Unit_Price"]
        - df["Reference_Unit_Price"]
    )
    / df["Reference_Unit_Price"]
) * 100

# =========================================================
# TRANSACTION RISK SCORE
# =========================================================

def calculate_risk(row):

    score = 0

    if row["Markup_%"] >= 80:
        score += 60

    elif row["Markup_%"] >= 50:
        score += 45

    elif row["Markup_%"] >= 20:
        score += 25

    elif row["Markup_%"] >= 10:
        score += 10

    if row["Quantity"] >= 1000:
        score += 10

    return min(score, 100)


df["Risk_Score"] = df.apply(
    calculate_risk,
    axis=1
)


def risk_level(score):

    if score >= 60:
        return "HIGH"

    elif score >= 30:
        return "MEDIUM"

    else:
        return "LOW"


df["Risk_Level"] = df["Risk_Score"].apply(
    risk_level
)

# =========================================================
# CONTRACTOR-SUPPLIER ANALYSIS
# =========================================================

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

# =========================================================
# RELATIONSHIP RISK
# =========================================================

def relationship_risk(row):

    score = 0

    if row["Transaction_Count"] >= 3:
        score += 25

    elif row["Transaction_Count"] >= 2:
        score += 10

    if row["Project_Count"] >= 3:
        score += 25

    elif row["Project_Count"] >= 2:
        score += 10

    if row["Average_Markup"] >= 50:
        score += 30

    elif row["Average_Markup"] >= 20:
        score += 15

    if row["Maximum_Markup"] >= 80:
        score += 20

    return min(score, 100)


relationship_analysis["Pattern_Risk_Score"] = (
    relationship_analysis.apply(
        relationship_risk,
        axis=1
    )
)


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

relationship_analysis = relationship_analysis.sort_values(
    "Pattern_Risk_Score",
    ascending=False
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("🔍 Filters")

location_options = [
    "All"
] + sorted(
    df["Location"].dropna().unique().tolist()
)

selected_location = st.sidebar.selectbox(
    "Location",
    location_options
)

risk_options = [
    "All",
    "HIGH",
    "MEDIUM",
    "LOW"
]

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

# =========================================================
# OVERVIEW
# =========================================================

st.divider()

st.header("📊 Transaction Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Transactions",
        len(filtered_df)
    )

with col2:
    st.metric(
        "Projects",
        filtered_df["Project_ID"].nunique()
    )

with col3:
    st.metric(
        "Contractors",
        filtered_df["Contractor_ID"].nunique()
    )

with col4:
    st.metric(
        "Suppliers",
        filtered_df["Supplier_ID"].nunique()
    )

# =========================================================
# RISK OVERVIEW
# =========================================================

st.header("⚠️ Risk Overview")

risk_counts = filtered_df["Risk_Level"].value_counts()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🔴 High Risk",
        risk_counts.get("HIGH", 0)
    )

with col2:
    st.metric(
        "🟠 Medium Risk",
        risk_counts.get("MEDIUM", 0)
    )

with col3:
    st.metric(
        "🟢 Low Risk",
        risk_counts.get("LOW", 0)
    )

# =========================================================
# PRICE ANOMALIES
# =========================================================

st.divider()

st.header("📈 Price Anomalies")

anomalies = filtered_df.sort_values(
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
            "Risk_Score",
            "Risk_Level"
        ]
    ],
    use_container_width=True
)

# =========================================================
# PATTERN INTELLIGENCE
# =========================================================

st.divider()

st.header("🧠 Pattern Intelligence")

st.write(
    "ProcureTrace looks beyond individual transactions "
    "and searches for repeated relationships across projects."
)

st.subheader(
    "Contractor–Supplier Relationship Risk"
)

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

# =========================================================
# STRONGEST RELATIONSHIPS
# =========================================================

st.subheader("🔗 Strongest Relationships")

for _, row in relationship_analysis.head(5).iterrows():

    contractor = row["Contractor_ID"]
    supplier = row["Supplier_ID"]
    transactions = row["Transaction_Count"]
    projects = row["Project_Count"]
    markup = row["Average_Markup"]

    if markup >= 50 and transactions >= 2:

        st.error(
            f"🔴 HIGH-RISK PATTERN: "
            f"{contractor} ↔ {supplier} | "
            f"{transactions} transactions | "
            f"{projects} projects | "
            f"Average markup: {markup:.1f}%"
        )

    elif transactions >= 2:

        st.warning(
            f"🟠 REPEATED RELATIONSHIP: "
            f"{contractor} ↔ {supplier} | "
            f"{transactions} transactions | "
            f"{projects} projects | "
            f"Average markup: {markup:.1f}%"
        )

# =========================================================
# INVESTIGATION QUEUE
# =========================================================

st.divider()

st.header("🚨 Investigation Queue")

high_risk = filtered_df[
    filtered_df["Risk_Level"] == "HIGH"
].sort_values(
    "Risk_Score",
    ascending=False
)

if len(high_risk) > 0:

    st.write(
        "These transactions have the strongest individual "
        "risk signals and may be prioritized for human review."
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
                "Risk_Score",
                "Risk_Level"
            ]
        ],
        use_container_width=True
    )

else:

    st.success(
        "No high-risk transactions detected."
    )

# =========================================================
# INVESTIGATOR VIEW
# =========================================================

st.divider()

st.header("🕵️ Investigator View")

if len(high_risk) > 0:

    selected_transaction = st.selectbox(
        "Select a high-risk transaction",
        high_risk["Transaction_ID"].tolist()
    )

    transaction = high_risk[
        high_risk["Transaction_ID"]
        == selected_transaction
    ].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Risk Score",
            f"{transaction['Risk_Score']}/100"
        )

    with col2:

        st.metric(
            "Price Deviation",
            f"{transaction['Markup_%']:.1f}%"
        )

    with col3:

        st.metric(
            "Risk Level",
            transaction["Risk_Level"]
        )

    st.subheader("Why was this transaction flagged?")

    reasons = []

    if transaction["Markup_%"] >= 80:
        reasons.append(
            "Very large deviation from the reference price."
        )

    elif transaction["Markup_%"] >= 20:
        reasons.append(
            "Declared price is significantly above the reference price."
        )

    contractor = transaction["Contractor_ID"]
    supplier = transaction["Supplier_ID"]

    relationship = relationship_analysis[
        (
            relationship_analysis["Contractor_ID"]
            == contractor
        )
        &
        (
            relationship_analysis["Supplier_ID"]
            == supplier
        )
    ]

    if len(relationship) > 0:

        rel = relationship.iloc[0]

        if rel["Transaction_Count"] >= 2:

            reasons.append(
                "The same contractor-supplier relationship "
                "appears in multiple transactions."
            )

        if rel["Project_Count"] >= 2:

            reasons.append(
                "The relationship appears across multiple projects."
            )

    for reason in reasons:

        st.write("✓ " + reason)

    st.subheader("Transaction Details")

    st.write(
        {
            "Transaction": transaction["Transaction_ID"],
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

    st.info(
        "No high-risk transaction is currently available "
        "for investigation."
    )

# =========================================================
# DISCLAIMER
# =========================================================

st.divider()

st.caption(
    "ProcureTrace is a prototype for financial pattern detection. "
    "Risk scores are indicators for investigation and are not "
    "proof of financial crime."
)
