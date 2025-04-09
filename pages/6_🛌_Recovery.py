from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import Color, DATA_DIR, get_ai_analysis, load_recovery_data
import seaborn as sns
import matplotlib.dates as mdates
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import model, client, Mistral, general_role
from millify import millify
import warnings
from functools import lru_cache

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Recovery Status", page_icon="🛌", layout="wide")

# Ensure the data is sorted by sessionDate
recovery_status_df =load_recovery_data()

# Sidebar filters
player_id = st.sidebar.selectbox("Player", recovery_status_df.player_id.unique())
category_options = [
    "subjective",
    "soreness",
    "sleep",
    "bio",
    "msk_load_tolerance",
    "msk_joint_range",
    "total",
]
category = st.sidebar.selectbox(
    "Category",
    category_options,
)

doc = {
    "subjective": "Perceived level of recovery submitted by the player.<br>Collected on most days except match days and days off.",
    "soreness": "Self reported muscle soreness.",
    "sleep": "Perceived quality of previous nights sleep.",
    "bio": " Blood biomarker analysis to assess signs of inflammation that may be due to fatigue or illness (Collected).",
    "msk_joint_range": "The joint range of ankles, knees and hips.<br>Collected around once per week.",
    "msk_load_tolerance": "The ability of the thigh and hip muscles to produce & tolerate force.<br>Collected around once per week.",
}

# Filter out rows that contain 'composite' in the metric column
selected_df = recovery_status_df[recovery_status_df["category"] == category]

st.header(f"{category.title()} Results Over Time")
if category != "total":
    st.markdown(doc[category], unsafe_allow_html=True)

st.markdown(
    """
**Top 30%** in <span style='color: green;'>green</span> and **bottom 30%** in  <span style='color: red;'>red</span>.
""",
    unsafe_allow_html=True,
)

metrics = list(selected_df.metric.unique())
n_metrics = len(metrics)

# Create subplot figure
if n_metrics == 1:
    fig = make_subplots(rows=1, cols=1)
else:
    fig = make_subplots(
        rows=n_metrics, cols=1, shared_xaxes=True, vertical_spacing=0.03
    )


st.subheader(f"{category} composite score Days:")
kpi_1, kpi_2, kpi_3 = st.columns(3)

if category != "total":
    kpi_df = selected_df[selected_df.metric.str.contains("composite")]
else:
    kpi_df = selected_df
# Calculate y-value ranges for each region (adjust these thresholds as needed)
y_min = kpi_df["value"].min()
y_max = kpi_df["value"].max()

# Define your thresholds (customize these for your use case)
low_threshold = y_min + (y_max - y_min) * 0.3  # Bottom 30% is red
high_threshold = y_min + (y_max - y_min) * 0.7  # Top 30% is green

kpi_1.metric(
    "# :green-badge[Green Days]",
    kpi_df[kpi_df.value > high_threshold].size,
    border=True,
)
kpi_2.metric(
    "# White Days",
    kpi_df[(kpi_df.value <= high_threshold) & (kpi_df.value >= low_threshold)].size,
    border=True,
)
kpi_3.metric(
    "# :red-badge[Red Days]", kpi_df[kpi_df.value < low_threshold].size, border=True
)

colors = ["#575757", "#575757"]

# Define your traffic light colors (red, yellow, green)
traffic_colors = ["#F1D7D5", "white", "#E0E3D0"]

for i, metric in enumerate(sorted(metrics, reverse=True)):
    formatted_metric = metric.split("_")[-1].title()

    # Filter data for the current metric
    metric_data = selected_df[selected_df.metric == metric]

    # Calculate y-value ranges for each region (adjust these thresholds as needed)
    y_min = metric_data["value"].min()
    y_max = metric_data["value"].max()

    # Define your thresholds (customize these for your use case)
    low_threshold = y_min + (y_max - y_min) * 0.3  # Bottom 30% is red
    high_threshold = y_min + (y_max - y_min) * 0.7  # Top 30% is green

    # Add shaded regions first (so they appear behind the lines)
    fig.add_shape(
        type="rect",
        x0=metric_data["sessionDate"].min(),
        x1=metric_data["sessionDate"].max(),
        y0=y_min,
        y1=low_threshold,
        fillcolor=traffic_colors[0],  # Red
        layer="below",
        line_width=0,
        row=i + 1,
        col=1,
    )

    fig.add_shape(
        type="rect",
        x0=metric_data["sessionDate"].min(),
        x1=metric_data["sessionDate"].max(),
        y0=low_threshold,
        y1=high_threshold,
        fillcolor=traffic_colors[1],  # Yellow
        layer="below",
        line_width=0,
        row=i + 1,
        col=1,
    )

    fig.add_shape(
        type="rect",
        x0=metric_data["sessionDate"].min(),
        x1=metric_data["sessionDate"].max(),
        y0=high_threshold,
        y1=y_max,
        fillcolor=traffic_colors[2],  # Green
        layer="below",
        line_width=0,
        row=i + 1,
        col=1,
    )

    # Add line plot for each metric as a subplot
    fig.add_trace(
        go.Scatter(
            x=metric_data["sessionDate"],
            y=metric_data["value"],
            mode="lines",  # Line plot
            name=" ".join(metric.split("_")).title(),
            line=dict(color=colors[i]),
            showlegend=False,
            hoverinfo="x+y",
            hovertemplate="%{y:.2f}",
        ),
        row=i + 1,
        col=1,
    )  # The `row=i+1` specifies the position in the subplot

    # Customize the y-axis title for each subplot
    fig.update_yaxes(
        title_text=f"{formatted_metric} Score",
        tickfont=dict(size=14),  # Increase y-axis tick font size
        row=i + 1,
        col=1,
    )

    # Remove x-axis titles for all except the last subplot
    if i < len(metrics) - 1:
        fig.update_xaxes(showticklabels=False, row=i + 1, col=1)

# Only add x-axis label to the bottom subplot
fig.update_xaxes(
    title_text="Date", row=len(metrics), col=1, tickfont=dict(size=14)
)  # Increase y-axis tick font size

# Adjust layout
fig.update_layout(
    height=200 * len(metrics),
    hoverlabel=dict(font_size=16),
    margin=dict(t=0, l=0, b=0, r=0),  # Increased top margin for title
    hovermode="x unified",  # Shows all values at same x position
)

# Show the plot
st.plotly_chart(fig, use_container_width=True)

threshold_date = "2024-08-01"

st.subheader(f"AI Sports Scientist's Opinion (after {threshold_date}): 💻")

sampled_df = selected_df[selected_df["sessionDate"] >= pd.to_datetime(threshold_date)]

sampled_df.drop(columns={"player_id"}, inplace=True)

df_json = sampled_df.to_json(orient="records")

st.write(
    get_ai_analysis(
        df_json, mode="recovery", threshold_date=threshold_date, category=category
    )
)
