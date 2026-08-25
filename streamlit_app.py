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

st.markdown(
    """
    ### Tracing Financial Crime Across Procurement Patterns

    **Detect → Connect → Investigate**

    ProcureTrace analyzes procurement transactions to identify
    unusual pricing, repeated contractor-supplier relationships,
    and persistent patterns over time.
    """
)

st.caption(
    "YEL × IGDTUW | Fintech Hackathon | Problem Statement 5"
)

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
    reference_prices = pd.read_csv("reference_prices.csv")
except Exception:
    st.error(
        "Could not find procurementdata.csv. "
        "Make sure the CSV is uploaded to the GitHub repository."
    )
    st.stop()
# =========================================================
# REFERENCE PRICE DATA
# =========================================================

st.sidebar.success(
    f"Reference prices loaded: {len(reference_prices)} materials"
)
# =========================================================
# CONNECT REFERENCE PRICES TO TRANSACTIONS
# =========================================================

# Match each transaction's material with its reference price
df = df.drop(columns=["Reference_Unit_Price"], errors="ignore")

df = df.merge(
    reference_prices[["Material", "Reference_Price"]],
    on="Material",
    how="left"
)

# Use the reference dataset as the official prototype reference price
df["Reference_Unit_Price"] = df["Reference_Price"]

# Calculate how much higher/lower the declared price is
df["Markup_%"] = (
    (df["Declared_Unit_Price"] - df["Reference_Unit_Price"])
    / df["Reference_Unit_Price"]
) * 100

df.drop(columns=["Reference_Price"], inplace=True)
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
# TEMPORAL PATTERN DETECTION
# =========================================================

st.divider()

st.header("📅 Temporal Pattern Detection")

st.write(
    "ProcureTrace checks whether unusual procurement activity "
    "repeats over time instead of occurring as an isolated event."
)

# Group transactions by contractor and supplier
temporal_analysis = (
    df.groupby(
        ["Contractor_ID", "Supplier_ID"]
    )
    .agg(
        Transaction_Count=("Transaction_ID", "count"),
        First_Transaction=("Date", "min"),
        Last_Transaction=("Date", "max"),
        Average_Markup=("Markup_%", "mean")
    )
    .reset_index()
)

# Calculate duration of activity
temporal_analysis["Activity_Days"] = (
    temporal_analysis["Last_Transaction"]
    - temporal_analysis["First_Transaction"]
).dt.days

# Identify persistent relationships
temporal_analysis["Persistent_Pattern"] = (
    (temporal_analysis["Transaction_Count"] >= 3)
    &
    (temporal_analysis["Activity_Days"] >= 30)
)

st.subheader("Repeated Activity Over Time")

st.dataframe(
    temporal_analysis[
        [
            "Contractor_ID",
            "Supplier_ID",
            "Transaction_Count",
            "First_Transaction",
            "Last_Transaction",
            "Activity_Days",
            "Average_Markup",
            "Persistent_Pattern"
        ]
    ],
    use_container_width=True
)

# Highlight persistent patterns

persistent = temporal_analysis[
    temporal_analysis["Persistent_Pattern"] == True
]

if len(persistent) > 0:

    st.warning(
        f"⏱️ {len(persistent)} relationship(s) show "
        "persistent activity across time."
    )

else:

    st.success(
        "No persistent relationship patterns detected."
    )
# =========================================================
# PRICE DEVIATION OVER TIME
# =========================================================

st.subheader("📈 Price Deviation Over Time")

st.write(
    "This chart shows how procurement price deviations "
    "change across transactions over time."
)

chart_data = df[
    [
        "Date",
        "Markup_%"
    ]
].dropna().sort_values("Date")

chart_data = chart_data.set_index("Date")

st.line_chart(
    chart_data["Markup_%"]
)

st.caption(
    "Higher values indicate a larger difference between "
    "declared and reference prices."
)
        
# =========================================================
# COMBINED PATTERN RISK SCORE
# =========================================================

st.divider()

st.header("🎯 Combined Financial Pattern Risk")

st.write(
    "ProcureTrace combines pricing, relationship and temporal "
    "signals into a single investigation-priority score."
)

# Start with a copy of the relationship analysis
combined_risk = relationship_analysis.copy()

# Price signal
def price_signal(markup):

    if markup >= 80:
        return 40

    elif markup >= 50:
        return 30

    elif markup >= 20:
        return 15

    else:
        return 0


combined_risk["Price_Signal"] = (
    combined_risk["Average_Markup"]
    .apply(price_signal)
)

# Relationship signal
def relationship_signal(transactions):

    if transactions >= 4:
        return 25

    elif transactions >= 3:
        return 20

    elif transactions >= 2:
        return 10

    else:
        return 0


combined_risk["Relationship_Signal"] = (
    combined_risk["Transaction_Count"]
    .apply(relationship_signal)
)

# Project signal
def project_signal(projects):

    if projects >= 4:
        return 15

    elif projects >= 3:
        return 10

    elif projects >= 2:
        return 5

    else:
        return 0


combined_risk["Project_Signal"] = (
    combined_risk["Project_Count"]
    .apply(project_signal)
)

# Temporal signal
def temporal_signal(row):

    if (
        row["Transaction_Count"] >= 3
        and row["Activity_Days"] >= 30
    ):
        return 20

    elif row["Transaction_Count"] >= 2:
        return 10

    else:
        return 0


# Merge temporal information
combined_risk = combined_risk.merge(
    temporal_analysis[
        [
            "Contractor_ID",
            "Supplier_ID",
            "Activity_Days"
        ]
    ],
    on=[
        "Contractor_ID",
        "Supplier_ID"
    ],
    how="left"
)

combined_risk["Temporal_Signal"] = (
    combined_risk.apply(
        temporal_signal,
        axis=1
    )
)

# Final score
combined_risk["Final_Risk_Score"] = (
    combined_risk["Price_Signal"]
    + combined_risk["Relationship_Signal"]
    + combined_risk["Project_Signal"]
    + combined_risk["Temporal_Signal"]
)

combined_risk["Final_Risk_Score"] = (
    combined_risk["Final_Risk_Score"]
    .clip(upper=100)
)


# Risk category
def final_risk_level(score):

    if score >= 70:
        return "🔴 CRITICAL"

    elif score >= 50:
        return "🔴 HIGH"

    elif score >= 30:
        return "🟠 MEDIUM"

    else:
        return "🟢 LOW"


combined_risk["Final_Risk_Level"] = (
    combined_risk["Final_Risk_Score"]
    .apply(final_risk_level)
)

# Sort highest risk first
combined_risk = combined_risk.sort_values(
    "Final_Risk_Score",
    ascending=False
)

st.subheader("Investigation Priority")

st.dataframe(
    combined_risk[
        [
            "Contractor_ID",
            "Supplier_ID",
            "Transaction_Count",
            "Project_Count",
            "Average_Markup",
            "Activity_Days",
            "Final_Risk_Score",
            "Final_Risk_Level"
        ]
    ],
    use_container_width=True
)

# Highest-risk pattern
if len(combined_risk) > 0:

    top_pattern = combined_risk.iloc[0]

    st.warning(
        f"🚨 Highest Priority Pattern: "
        f"{top_pattern['Contractor_ID']} ↔ "
        f"{top_pattern['Supplier_ID']} | "
        f"Risk Score: "
        f"{top_pattern['Final_Risk_Score']}/100"
    )

# =========================================================
# INVESTIGATION PRIORITY QUEUE
# =========================================================

st.divider()

st.header("🚨 Investigation Priority Queue")
st.subheader("🎚️ Investigation Sensitivity")

risk_threshold = st.slider(
    "Minimum risk score for investigation",
    min_value=0,
    max_value=100,
    value=50,
    step=5
)

st.write(
    f"Showing patterns with a combined risk score "
    f"of **{risk_threshold} or higher**."
)

st.write(
    "Cases are ranked using the combined pattern risk score "
    "so investigators can prioritize the strongest signals first."
)

priority_queue = combined_risk.copy()
priority_queue = priority_queue[
    priority_queue["Final_Risk_Score"] >= risk_threshold
]

priority_queue = priority_queue.sort_values(
    "Final_Risk_Score",
    ascending=False
)

priority_queue["Priority_Rank"] = range(
    1,
    len(priority_queue) + 1
)

# Show top cases first
st.subheader("🏆 Highest-Priority Patterns")

st.dataframe(
    priority_queue[
        [
            "Priority_Rank",
            "Contractor_ID",
            "Supplier_ID",
            "Transaction_Count",
            "Project_Count",
            "Average_Markup",
            "Activity_Days",
            "Final_Risk_Score",
            "Final_Risk_Level"
        ]
    ].head(10),
    use_container_width=True
)

# Top 3 cases
st.subheader("⚡ Immediate Attention")

top_cases = priority_queue.head(3)

for _, case in top_cases.iterrows():

    score = case["Final_Risk_Score"]

    if score >= 70:

        st.error(
            f"🔴 PRIORITY #{int(case['Priority_Rank'])} — "
            f"{case['Contractor_ID']} ↔ "
            f"{case['Supplier_ID']} | "
            f"Risk: {int(score)}/100"
        )

    elif score >= 40:

        st.warning(
            f"🟠 PRIORITY #{int(case['Priority_Rank'])} — "
            f"{case['Contractor_ID']} ↔ "
            f"{case['Supplier_ID']} | "
            f"Risk: {int(score)}/100"
        )

    else:

        st.info(
            f"🟢 PRIORITY #{int(case['Priority_Rank'])} — "
            f"{case['Contractor_ID']} ↔ "
            f"{case['Supplier_ID']} | "
            f"Risk: {int(score)}/100"
        )

st.caption(
    "Risk ranking supports investigation prioritization. "
    "It is not a determination of fraud or corruption."
)
# ============================================================
# INVESTIGATION REPORT
# ============================================================

st.divider()

st.header("📋 Investigation Report")

st.write(
    "ProcureTrace generates an evidence summary for "
    "high-priority financial patterns."
)
if len(combined_risk) > 0:

    # --------------------------------------------------
    # SELECT CONTRACTOR-SUPPLIER PATTERN
    # --------------------------------------------------

    combined_risk["Pattern"] = (
        combined_risk["Contractor_ID"].astype(str)
        + " ↔ "
        + combined_risk["Supplier_ID"].astype(str)
    )

    selected_pattern = st.selectbox(
        "Select a contractor-supplier pattern",
        combined_risk["Pattern"].tolist()
    )

    selected_index = (
        combined_risk["Pattern"] == selected_pattern
    )

    pattern = combined_risk[
        selected_index
    ].iloc[0]

    contractor = pattern["Contractor_ID"]
    supplier = pattern["Supplier_ID"]


    # --------------------------------------------------
    # RISK SUMMARY
    # --------------------------------------------------

    st.subheader(
        f"🔎 {contractor} ↔ {supplier}"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Pattern Risk Score",
            f"{int(pattern['Final_Risk_Score'])}/100"
        )

    with col2:
        st.metric(
            "Transactions",
            int(pattern["Transaction_Count"])
        )

    with col3:
        st.metric(
            "Projects",
            int(pattern["Project_Count"])
        )

    with col4:
        st.metric(
            "Average Markup",
            f"{pattern['Average_Markup']:.1f}%"
        )


    # --------------------------------------------------
    # RISK FACTORS
    # --------------------------------------------------

    st.subheader("⚠️ Risk Factors")

    reasons = []

    if pattern["Average_Markup"] >= 50:
        reasons.append(
            "Significant average price deviation from the reference price."
        )

    elif pattern["Average_Markup"] >= 20:
        reasons.append(
            "Moderate price deviation detected across transactions."
        )

    if pattern["Transaction_Count"] >= 3:
        reasons.append(
            "Repeated transactions detected between the same contractor and supplier."
        )

    if pattern["Project_Count"] >= 2:
        reasons.append(
            "The contractor-supplier relationship appears across multiple projects."
        )

    if len(reasons) == 0:
        reasons.append(
            "No major risk factor identified by the current rules."
        )

    for reason in reasons:
        st.write("✓ " + reason)


    # --------------------------------------------------
    # SUPPORTING TRANSACTIONS
    # --------------------------------------------------

    st.subheader("📋 Supporting Transactions")

    pattern_transactions = df[
        (df["Contractor_ID"] == contractor)
        & (df["Supplier_ID"] == supplier)
    ]

    st.dataframe(
        pattern_transactions,
        use_container_width=True
    )


    # --------------------------------------------------
    # INVESTIGATION RECOMMENDATION
    # --------------------------------------------------

    st.subheader("🔍 Recommended Investigation")

    if pattern["Average_Markup"] >= 50:

        st.warning(
            "High priority investigation recommended. "
            "Verify invoices, supplier quotations, approval records, "
            "and the justification for the declared prices."
        )

    elif pattern["Average_Markup"] >= 20:

        st.info(
            "Moderate priority investigation recommended. "
            "Compare the declared prices with reference prices "
            "and review the supporting procurement documents."
        )

    else:

        st.success(
            "No significant pricing anomaly detected by the current rules. "
            "Continue with standard verification procedures."
        )


else:

    st.info(
        "No high-risk contractor-supplier patterns detected."
    )

# ============================================================
# INVESTIGATOR VIEW
# ============================================================

st.divider()

st.header("🕵️ Investigator View")

if len(combined_risk) > 0:
     st.subheader("📋 Transaction Summary")

    pattern_transactions = df[
        (df["Contractor_ID"] == contractor)
        & (df["Supplier_ID"] == supplier)
    ]

    st.dataframe(
        pattern_transactions[
            [
                "Transaction_ID",
                "Date",
                "Project_ID",
                "Material",
                "Quantity",
                "Declared_Unit_Price",
                "Reference_Unit_Price",
                "Location"
            ]
        ],
        use_container_width=True
    )

    # --------------------------------------------------------
    # SELECTED PATTERN INFORMATION
    # --------------------------------------------------------

    st.subheader(
        f"🔎 {contractor} ↔ {supplier}"
    )

    # --------------------------------------------------------
    # INVESTIGATION METRICS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Risk Score",
            f"{pattern['Final_Risk_Score']:.0f}/100"
        )

    with col2:

        st.metric(
            "Transactions",
            pattern["Transaction_Count"]
        )

    with col3:

        st.metric(
            "Average Markup",
            f"{pattern['Average_Markup']:.1f}%"
        )

    # --------------------------------------------------------
    # TRANSACTION HISTORY
    # --------------------------------------------------------

    st.subheader("📊 Transaction History")

    pattern_transactions = df[
        (df["Contractor_ID"] == contractor)
        &
        (df["Supplier_ID"] == supplier)
    ]

    if len(pattern_transactions) > 0:

        st.dataframe(
            pattern_transactions,
            use_container_width=True
        )

    else:

        st.info(
            "No transaction records found for this pattern."
        )
        st.subheader("🔎 Recommended Investigation")

    if pattern["Average_Markup"] >= 50:
        st.warning(
            "High priority: investigate the pricing difference, "
            "supporting invoices, supplier quotations, and approval records."
        )

    elif pattern["Average_Markup"] >= 20:
        st.info(
            "Moderate priority: verify the declared prices against "
            "reference prices and procurement documentation."
        )

    else:
        st.success(
            "Low pricing anomaly detected. Continue with standard verification."
        )

    # --------------------------------------------------------
    # INVESTIGATION SUMMARY
    # --------------------------------------------------------

    st.subheader("📝 Investigation Summary")

    st.write(
        f"The selected pattern involves contractor "
        f"**{contractor}** and supplier **{supplier}**."
    )

    st.write(
        f"The relationship appears in "
        f"**{pattern['Transaction_Count']} transaction(s)** "
        f"across **{pattern['Project_Count']} project(s)**."
    )

    st.write(
        f"The average observed price deviation is "
        f"**{pattern['Average_Markup']:.1f}%** compared "
        f"with the reference price."
    )

    # --------------------------------------------------------
    # INVESTIGATOR ACTION
    # --------------------------------------------------------

    st.subheader("🔍 Recommended Investigation Action")

    if pattern["Average_Markup"] >= 50:

        st.warning(
            "High price deviation detected. "
            "Review supporting invoices, quotations, "
            "and procurement approvals."
        )

    elif pattern["Average_Markup"] >= 20:

        st.info(
            "Moderate price deviation detected. "
            "Compare the tender price with reference "
            "prices and similar procurement transactions."
        )

    else:

        st.success(
            "Price deviation is currently within "
            "the prototype's lower-risk range."
        )

else:

    st.info(
        "Investigator View is unavailable because "
        "no risk patterns were detected."
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
