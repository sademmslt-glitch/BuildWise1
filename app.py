import streamlit as st
import pandas as pd
from predict_logic import predict

# ---------------------------------
# Page Config
# ---------------------------------
st.set_page_config(
    page_title="BuildWise",
    page_icon="🏗️",
    layout="centered"
)

# ---------------------------------
# Session State
# ---------------------------------
if "predicted_projects" not in st.session_state:
    st.session_state.predicted_projects = []

if "company_projects" not in st.session_state:
    st.session_state.company_projects = []

# ---------------------------------
# Sidebar
# ---------------------------------
st.sidebar.title("🏗️ BuildWise")
page = st.sidebar.radio("Navigate", ["User", "Admin"])

# ---------------------------------
# Constants
# ---------------------------------
PROJECT_TYPES = [
    "Residential Construction",
    "Commercial Fit-Out",
    "Building Finishing",
    "Electrical Works",
    "HVAC Installation",
    "Smart Home System",
    "Security Systems",
    "FTTH Infrastructure",
    "Digital Screen Installation"
]

PROJECT_SIZES = ["Small", "Medium", "Large"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "buildwise123")

# =================================
# USER PAGE
# =================================
if page == "User":

    st.title("BuildWise")
    st.caption(
        "AI-powered planning assistant that estimates cost and predicts delay risk before execution."
    )

    st.subheader("🧱 Project Setup")
    st.write("Fill the project details to get an instant risk-aware estimate.")

    project_type = st.selectbox("Project Type", PROJECT_TYPES)
    project_size = st.selectbox("Project Size", PROJECT_SIZES)
    area_m2 = st.number_input("Project Area (m²)", 50, 200000, 300, step=50)
    duration_months = st.number_input("Expected Duration (months)", 0.5, 60.0, 3.0, step=0.5)
    workers = st.number_input("Number of Workers", 1, 500, 10)

    if st.button("Go 🚀"):

        with st.spinner("Analyzing project..."):
            result = predict(
                project_type,
                project_size,
                area_m2,
                duration_months,
                workers
            )

        cost = float(result["estimated_cost"])
        margin = 0.10
        cost_low = cost * (1 - margin)
        cost_high = cost * (1 + margin)

        st.session_state.predicted_projects.append({
            "Project Type": project_type,
            "Project Size": project_size,
            "Area (m²)": area_m2,
            "Duration (months)": duration_months,
            "Workers": workers,
            "Estimated Cost (SAR)": round(cost, 0),
            "Cost Range (SAR)": f"{cost_low:,.0f} – {cost_high:,.0f}",
            "Delay Probability (%)": result["delay_probability"],
            "Risk Level": result["risk_level"]
        })

        # ---------- Results ----------
        st.subheader("📊 AI Prediction Results")

        st.metric("Estimated Cost (SAR)", f"{cost:,.0f}")
        st.caption(
            f"Expected Cost Range: **{cost_low:,.0f} – {cost_high:,.0f} SAR**"
        )

        st.metric(
            "Risk of Delay",
            f"{result['delay_probability']}%",
            help="Estimated likelihood of schedule overrun based on workload pressure and learned patterns."
        )

        if result["risk_level"] == "Low":
            st.success("🟢 Low Delay Risk")
        elif result["risk_level"] == "Medium":
            st.warning("🟡 Medium Delay Risk")
        else:
            st.error("🔴 High Delay Risk")

        st.subheader("⚠️ Decision Support")
        for rec in result["recommendations"]:
            st.write(f"✅ {rec}")

        st.info(
            "This prediction is intended for planning stage decision-making "
            "and may vary with on-site conditions."
        )

# =================================
# ADMIN PAGE
# =================================
else:

    st.title("🔐 Admin Dashboard")

    password = st.text_input("Admin Password", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Enter admin password to continue.")
        st.stop()

    st.success("Welcome, Admin")

    st.subheader("📊 Predicted Projects Analysis")

    if st.session_state.predicted_projects:
        df_pred = pd.DataFrame(st.session_state.predicted_projects)

        total = len(df_pred)
        high = len(df_pred[df_pred["Risk Level"] == "High"])
        medium = len(df_pred[df_pred["Risk Level"] == "Medium"])
        low = len(df_pred[df_pred["Risk Level"] == "Low"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Predicted", total)
        c2.metric("High Risk", high)
        c3.metric("Medium Risk", medium)
        c4.metric("Low Risk", low)

        st.dataframe(df_pred, use_container_width=True)
    else:
        st.info("No predicted projects yet.")

    st.subheader("🏢 Company Projects (Administrative)")

    if st.session_state.company_projects:
        df_company = pd.DataFrame(st.session_state.company_projects)
        st.dataframe(df_company, use_container_width=True)
    else:
        st.info("No company projects added yet.")

    st.subheader("➕ Add Company Project")

    with st.form("add_company_project"):
        p_type = st.selectbox("Project Type", PROJECT_TYPES)
        p_area = st.number_input("Area (m²)", 50, 200000, 300, step=50)
        p_duration = st.number_input("Duration (months)", 0.5, 60.0, 3.0, step=0.5)
        p_workers = st.number_input("Workers", 1, 500, 10)
        p_cost = st.number_input(
            "Estimated Budget (SAR)",
            min_value=0,
            step=10000,
            value=500000
        )

        add = st.form_submit_button("Add Project")

        if add:
            st.session_state.company_projects.append({
                "Project Type": p_type,
                "Area (m²)": p_area,
                "Duration (months)": p_duration,
                "Workers": p_workers,
                "Estimated Cost (SAR)": f"{p_cost:,.0f}",
                "Status": "Planning"
            })
            st.success("Company project added successfully.")
