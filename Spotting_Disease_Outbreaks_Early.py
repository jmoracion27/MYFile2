import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="PIDSR Outbreak Forecasting Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a clean, professional healthcare dashboard look
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 2rem; }
    .card-critical { padding: 1.5rem; background-color: #FEF2F2; border-left: 5px solid #EF4444; border-radius: 4px; }
    .card-warning { padding: 1.5rem; background-color: #FFFBEB; border-left: 5px solid #F59E0B; border-radius: 4px; }
    .card-normal { padding: 1.5rem; background-color: #ECFDF5; border-left: 5px solid #10B981; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOCK DATA GENERATION (Replace with your actual data loader)
# ==========================================
@st.cache_data
def load_data():
    """
    Simulates the PIDSR historical and forecasted data structure from the notebook.
    Replace the internal logic here with your actual pd.read_csv() or model inference.
    """
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", end="2026-06-01", freq="W")
    cities = ["Manila", "Quezon City", "Cebu City", "Davao City", "Iloilo City"]
    diseases = ["Cholera", "Typhoid Fever", "Acute Bloody Diarrhea"]
    
    rows = []
    for city in cities:
        for disease in diseases:
            # Base caseload varying by city and disease
            base = np.random.randint(1, 5) if disease == "Cholera" else np.random.randint(5, 15)
            for d in dates:
                # Add seasonality (higher cases during rainy season: June - October)
                seasonality = 4 if d.month in [6, 7, 8, 9, 10] else 0
                noise = np.random.randint(-2, 3)
                cases = max(0, base + seasonality + noise)
                
                # Tag real vs forecasted (e.g., everything after Jan 2026 is a forecast)
                is_forecast = d > datetime(2026, 1, 1)
                
                rows.append({
                    "Date": d,
                    "City": city,
                    "Disease": disease,
                    "Cases": cases if not is_forecast else max(0, cases + np.random.randint(-1, 2)),
                    "Type": "Forecasted" if is_forecast else "Historical"
                })
                
    df = pd.DataFrame(rows)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ==========================================
# 3. SIDEBAR CONTROLS & FILTERS
# ==========================================
st.sidebar.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-medical-health-care-medical-flatart-icons-flat-flatarticons-1.png", width=80)
st.sidebar.title("PIDSR Control Panel")
st.sidebar.markdown("---")

# Filters
selected_disease = st.sidebar.selectbox("Select Notifiable Disease", df["Disease"].unique())
selected_city = st.sidebar.selectbox("Select Target City/LGU", df["City"].unique())

st.sidebar.markdown("### 🚨 Alert Thresholds")
st.sidebar.caption("Dynamic triggers based on Notebook Recommendation 1")

# Dynamic defaults depending on disease risk profile (Cholera has lower thresholds)
if selected_disease == "Cholera":
    watch_trigger = st.sidebar.slider("Watch Level (Yellow)", 1, 5, 1)
    outbreak_trigger = st.sidebar.slider("Outbreak Level (Red)", 6, 20, 4)
else:
    watch_trigger = st.sidebar.slider("Watch Level (Yellow)", 1, 15, 4)
    outbreak_trigger = st.sidebar.slider("Outbreak Level (Red)", 16, 50, 10)

# Filter dataframe based on selections
filtered_df = df[(df["Disease"] == selected_disease) & (df["City"] == selected_city)].sort_values("Date")
latest_data = filtered_df.iloc[-1]
previous_data = filtered_df.iloc[-2]

# ==========================================
# 4. MAIN DASHBOARD DISPLAY
# ==========================================
st.markdown(f"<div class='main-header'>Philippine Integrated Disease Surveillance System (PIDSR)</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Time Series Analysis & Early Outbreak Forecasting for Waterborne Diseases</div>", unsafe_allow_html=True)

# --- Row 1: Key Metrics & Active Alerts ---
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    delta_val = int(latest_data["Cases"] - previous_data["Cases"])
    st.metric(
        label=f"Latest Weekly Count ({latest_data['Date'].strftime('%b %d, %Y')})",
        value=f"{latest_data['Cases']} Cases",
        delta=f"{delta_val} from last week" if delta_val != 0 else "No change",
        delta_color="inverse"
    )

with col2:
    # Estimate total upcoming caseload for the month
    upcoming_month = filtered_df[filtered_df["Type"] == "Forecasted"].head(4)["Cases"].sum()
    st.metric(
        label="Projected Cases (Next 4 Weeks)",
        value=f"~ {upcoming_month} Cases",
        delta="Model Predictive Window"
    )

with col3:
    # Recommendation 1 implementation: Alert levels
    current_cases = latest_data["Cases"]
    if current_cases >= outbreak_trigger:
        status_class = "card-critical"
        status_title = "🚨 OUTBREAK ALERT"
        status_desc = f"Immediate deployment of medical supplies, water quality testing, and sanitization kits needed in {selected_city}."
    elif current_cases >= watch_trigger:
        status_class = "card-warning"
        status_title = "⚠️ WATCH STATUS"
        status_desc = f"Elevated case levels detected. Increase hospital resource tracking and active surveillance."
    else:
        status_class = "card-normal"
        status_title = "✅ SYSTEM NORMAL"
        status_desc = f"Case numbers are within safe seasonal baselines for {selected_city}."

    st.markdown(f"""
        <div class='{status_class}'>
            <strong>{status_title}</strong><br>
            <span style='font-size: 0.9rem;'>{status_desc}</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Row 2: Visualizations ---
st.subheader(f"Epidemiological Curve & Projections: {selected_disease} in {selected_city}")

# Split historical and forecasted for custom chart plotting
hist_df = filtered_df[filtered_df["Type"] == "Historical"]
fore_df = filtered_df[filtered_df["Type"] == "Forecasted"]

fig = go.Figure()

# Historical Line
fig.add_trace(go.Scatter(
    x=hist_df["Date"], y=hist_df["Cases"],
    mode='lines', name='Historical Data',
    line=dict(color='#2563EB', width=2.5)
))

# Forecasted Line
fig.add_trace(go.Scatter(
    x=fore_df["Date"], y=fore_df["Cases"],
    mode='lines', name='Model Forecast',
    line=dict(color='#EF4444', width=2.5, dash='dash')
))

# Threshold Zones
fig.add_hline(y=outbreak_trigger, line_dash="dot", line_color="#EF4444", 
              annotation_text="Outbreak Level", annotation_position="top left")
fig.add_hline(y=watch_trigger, line_dash="dot", line_color="#F59E0B", 
              annotation_text="Watch Level", annotation_position="bottom left")

fig.update_layout(
    xaxis_title="Timeline",
    yaxis_title="Number of Reported Cases",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=30, b=20),
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# --- Row 3: Strategic Recommendations ---
st.markdown("---")
st.subheader("💡 Strategic Health Directives")

rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.markdown("### 📋 Operational Recommendations")
    st.markdown(f"""
    * **Early Warning Implementation:** Use this dashboard to gauge dynamic alerts instead of static hard values. Thresholds should be routinely re-evaluated alongside local epidemiologists.
    * **Resource Maximization:** Prioritize logistics towards high-risk hotspots during high-precipitative rainy cycles (traditionally ramping up around **June**).
    """)

with rec_col2:
    st.markdown("### 🔄 Model Governance & Maintenance")
    st.markdown("""
    * **Quarterly Maintenance:** Retrain data models quarterly using fresh uploads from local rural health units (RHUs) to maintain calibration.
    * **Feature Engineering Expansion:** Integrate secondary exogenous features—such as weekly millimeter rainfall gauges or local water district contamination metrics—to optimize the precision of the predictive layer.
    """)
