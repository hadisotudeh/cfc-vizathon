from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import DATA_DIR, return_json_cell, upper_color, lower_color, get_ai_analysis, load_capability_data,adjust_sidebar_width
import warnings
from datetime import datetime, timedelta

# Constants
COLUMN_RENAMES = {
    "testDate": "Test Date",
    "benchmarkPct": "Benchmark",
    "movement": "Movement",
    "quality": "Quality",
    "expression": "Expression",
}
BENCHMARK_COL = "Benchmark"
DATE_COL = "Test Date"
MOVEMENT_COL = "Movement"
QUALITY_COL = "Quality"
EXPRESSION_COL = "Expression"
REQUIRED_COLS = [DATE_COL, MOVEMENT_COL, QUALITY_COL, EXPRESSION_COL, BENCHMARK_COL]

THRESHOLDS = [
    {"y0": 0, "y1": 25, "color": "#F1D7D5", "name": "Bottom 25%"},
    {"y0": 25, "y1": 75, "color": "white", "name": "Middle 50%"},
    {"y0": 75, "y1": 100, "color": "#E0E3D0", "name": "Top 25%"},
]

# Configuration
warnings.filterwarnings("ignore")
st.set_page_config(page_title="Physical Development", page_icon="💪", layout="wide")
adjust_sidebar_width()


def create_time_series_plot(df, movement_filter):
    """Create time series plot for selected movement."""
    filtered_df = df.loc[
        df[MOVEMENT_COL] == movement_filter, REQUIRED_COLS + ["class"]
    ].copy()

    fig = make_subplots(rows=1, cols=1)

    # Add shaded regions
    for region in THRESHOLDS:
        fig.add_shape(
            type="rect",
            x0=filtered_df[DATE_COL].min(),
            x1=filtered_df[DATE_COL].max(),
            y0=region["y0"],
            y1=region["y1"],
            fillcolor=region["color"],
            layer="below",
            line_width=0,
        )

    # Add line plot
    line_fig = px.line(
        filtered_df,
        x=DATE_COL,
        y=BENCHMARK_COL,
        color="class",
        labels={BENCHMARK_COL: "Benchmark Percentile (%)"},
        color_discrete_sequence=px.colors.qualitative.T10,
        hover_data={BENCHMARK_COL: ":.1f"},
    )

    for trace in line_fig.data:
        fig.add_trace(trace)

    # Add threshold lines
    for y in [25, 75]:
        fig.add_hline(y=y, line_dash="dot", line_color="gray", line_width=1)

    # Format x-axis ticks
    unique_months = filtered_df[DATE_COL].dt.to_period("M").unique()
    tickvals = unique_months.to_timestamp()
    ticktext = unique_months.strftime("%Y-%m")

    # Update layout with right-side legend
    fig.update_layout(
        title=f"{movement_filter.title()} Performance Over Time",
        yaxis_title="Benchmark Percentile (%)",
        yaxis_range=[0, 100],
        hovermode="x unified",
        title_font_size=20,
        xaxis=dict(
            title_text="Date",
            title_font_size=18,
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont_size=16,
            tickangle=-45,
        ),
        yaxis=dict(
            title_text="Benchmark Percentile (%)",
            title_font_size=18,
            range=[0, 100],
            tickfont_size=16,
        ),
        template="plotly_white",
        legend=dict(
            title_text="Class",
            title_font_size=18,
            font_size=16,
            orientation="v",  # Vertical orientation
            yanchor="top",
            y=1,  # Position at top of plot
            xanchor="left",
            x=1.02,  # Position to right of plot
            bgcolor="rgba(255,255,255,0.5)",  # Semi-transparent background
        ),
        margin=dict(r=150),  # Add right margin to accommodate legend
        hoverlabel=dict(font_size=16),
    )

    fig.update_traces(hovertemplate="%{y:.1f}%<extra></extra>")
    return fig, filtered_df


def create_distribution_plot(df):
    df[DATE_COL] = pd.to_datetime(df[DATE_COL]).dt.date
    # Define the five colored regions
    regions = [
        {"y0": 0, "y1": 20, "color": "#E2AEAB", "name": "Very Low (<20%)"},
        {"y0": 20, "y1": 40, "color": "#D48681", "name": "Low (20-40%)"},
        {"y0": 40, "y1": 60, "color": "#F5F5F5", "name": "Average (40-60%)"},
        {"y0": 60, "y1": 80, "color": "#E0E3D0", "name": "High (60-80%)"},
        {"y0": 80, "y1": 100, "color": "#A1AB71", "name": "Very High (>80%)"},
    ]

    # Create the strip plot
    fig = px.strip(
        df,
        x=MOVEMENT_COL,
        y=BENCHMARK_COL,
        color=QUALITY_COL,
        facet_col=EXPRESSION_COL,
        stripmode="overlay",
        title="<b>Benchmark Percentile Distribution by Movement</b>",
        labels={
            BENCHMARK_COL: "Benchmark Percentile (%)",
            MOVEMENT_COL: "Movement",
            QUALITY_COL: "Quality Level",
            EXPRESSION_COL: "Expression",
        },
        color_discrete_sequence=px.colors.qualitative.T10,
        custom_data=[MOVEMENT_COL, QUALITY_COL, DATE_COL],
    )

    # Add colored regions to each subplot
    for i, expression in enumerate(df[EXPRESSION_COL].unique()):
        for region in regions:
            fig.add_shape(
                type="rect",
                xref=f"x{i+1}" if i > 0 else "x",
                yref=f"y{i+1}" if i > 0 else "y",
                x0=-0.5,
                x1=len(df[MOVEMENT_COL].unique()) - 0.5,
                y0=region["y0"],
                y1=region["y1"],
                fillcolor=region["color"],
                layer="below",
                line_width=0,
                opacity=0.3,
            )

    # Update layout with larger fonts
    fig.update_layout(
        yaxis_range=[0, 100],
        height=550,
        title_font=dict(size=28, family="Arial", color="black"),  # Increased title size
        font=dict(family="Arial", size=18),  # Increased base font size
        legend=dict(
            title_font_size=22,  # Increased legend title size
            font_size=20,  # Increased legend item size
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.5)",
        ),
        margin=dict(r=150, b=120, t=100),  # Adjusted margins
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title_font=dict(size=20),  # Increased x-axis title size
            tickfont=dict(size=18),  # Increased x-axis tick size
        ),
        yaxis=dict(
            title_font=dict(size=20),  # Increased y-axis title size
            tickfont=dict(size=18),  # Increased y-axis tick size
        ),
    )

    # Add threshold lines
    for y in [20, 40, 60, 80]:
        fig.add_hline(
            y=y, line_dash="dot", line_color="gray", line_width=1, opacity=0.7
        )

    # Customize facet/subplot titles
    fig.for_each_annotation(
        lambda a: a.update(text=f"<b>{a.text}</b>", font=dict(size=20))
    )  # Increased facet title size

    fig.for_each_xaxis(
        lambda axis: axis.update(
            title_font=dict(size=20, family="Arial"),  # Match your design
            tickfont=dict(size=18),  # Keep tick labels consistent
        )
    )

    fig.update_traces(
        marker=dict(size=12, symbol="circle", opacity=1)  # Explicitly set symbol type
    )

    # Customize hover template with larger font
    fig.update_traces(
        jitter=1,
        marker=dict(size=8, opacity=0.7),  # Slightly larger markers
        hovertemplate=(
            "<span style='font-size:16px'><b>Movement:</b> %{customdata[0]}</span><br>"
            + "<span style='font-size:16px'><b>Benchmark Percentile:</b> %{y:.1f}%</span><br>"
            + "<span style='font-size:16px'><b>Quality Level:</b> %{customdata[1]}</span><br>"
            "<span style='font-size:16px'><b>Date:</b> %{customdata[2]}</span><extra></extra>"
        ),
    )

    return fig

# Main application
physical_capability_df = load_capability_data()
movement_options = physical_capability_df[MOVEMENT_COL].unique().tolist()

# Sidebar controls
player_id = st.sidebar.selectbox("Player", ["P1"])
view = st.sidebar.selectbox("View", ("Time Series", "Distribution"))

if view == "Time Series":
    movement_filter = st.sidebar.selectbox("Movement", movement_options)
    fig, filtered_df = create_time_series_plot(physical_capability_df, movement_filter)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("AI Sports Scientist's Opinion: 💻")

    sampled_df = filtered_df.set_index(DATE_COL)
    sampled_df = sampled_df.resample("W-MON").first().dropna().reset_index()
    df_json = sampled_df.to_json(orient="records")

    st.write(get_ai_analysis(df_json, mode="capability"))

elif view == "Distribution":
    fig = create_distribution_plot(physical_capability_df)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("AI Sports Scientist's Opinion on Last 15 days: 💻")
    # Calculate the date 365 days ago from today
    one_year = physical_capability_df[DATE_COL].max() - timedelta(days=15)

    # Filter the DataFrame
    sampled_df = physical_capability_df[physical_capability_df[DATE_COL] >= one_year]
    df_json = sampled_df.to_json(orient="records")
    st.write(get_ai_analysis(df_json, mode="capability"))