from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import (
    Color,
    plot_matchload_time_series,
    plot_trainingload_timeseries,
    plot_day_duration_time_series,
    normalize_df,
    plot_heartdata,
    DATA_DIR,
    plot_gps_heatmap,
    return_json_cell,
    upper_color,
    lower_color,
    feature_names,
    get_ai_analysis,
    load_gps_data,
)
from config import client, general_role, model
from millify import millify
import warnings

# Configuration
warnings.filterwarnings("ignore")

st.set_page_config(page_title="GPS", page_icon="🛰️", layout="wide")

# Data loading and preprocessing with optimizations

gps_df = load_gps_data()
seasons = sorted(gps_df["season"].unique())

# Sidebar filters with larger font
with st.sidebar:
    st.markdown("## Filters", unsafe_allow_html=True)
    view = st.selectbox(
        "View", ("Heatmap", "Time Series"), key="view_select"
    )

with st.sidebar:
    player_id = st.selectbox(
        "Player", gps_df.player_id.unique(), key="player_select"
    )
    season = st.selectbox("Season", seasons, key="season_select")
    normalize_day_duration = st.selectbox(
        "Normalize by Day Duration?", (False, True), key="normalize_select"
    )

    # Filter data once for the season
    season_df = gps_df[gps_df.season == season]

    dates_choice = st.selectbox("Mode", ("Matches", "Training"), key="mode_select")

    if normalize_day_duration:
        season_df = normalize_df(season_df)

# Remove 0 duration more efficiently
match_week_duration_options = sorted(
    {x for x in gps_df["match_week_duration"].unique() if x != 0}
)

# Main content based on view
if dates_choice == "Matches":
    selected_df = season_df[season_df.md_plus_code == 0]
    # Inject custom CSS to override font size in st.metric

    st.markdown("## Last Match Performance:")
    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    mins_played = selected_df["day_duration"].iloc[-1]
    delta_mins_played = (
        selected_df["day_duration"].iloc[-1] - selected_df["day_duration"].iloc[-2]
    )
    kpi_1.metric(
        "Match Time (mins)",
        millify(mins_played),
        millify(delta_mins_played),
        border=True,
    )

    distance = selected_df["distance"].iloc[-1]
    delta_distance = (
        selected_df["distance"].iloc[-1] - selected_df["distance"].iloc[-2]
    )
    kpi_2.metric(
        "Distance (m)", millify(distance), millify(delta_distance), border=True
    )

    peak_speed = selected_df["peak_speed"].iloc[-1]
    delta_peak_speed = (
        selected_df["peak_speed"].iloc[-1] - selected_df["peak_speed"].iloc[-2]
    )
    kpi_3.metric(
        "Peak Speed (m/s)",
        millify(peak_speed),
        millify(delta_peak_speed),
        border=True,
    )

    heart_zone_5 = selected_df["hr_zone_5_m"].iloc[-1]
    delta_heart_zone_5 = (
        selected_df["hr_zone_5_m"].iloc[-1] - selected_df["hr_zone_5_m"].iloc[-2]
    )
    kpi_4.metric(
        "Heart Rate Zone 5 (mins)",
        heart_zone_5,
        delta_heart_zone_5,
        delta_color="inverse",
        border=True,
        help='Heart rate zone 5, also known as the "maximal effort" or "very hard" zone, involves pushing your heart rate to 90-100% of your maximum heart rate.',
    )

    if view == "Time Series":
        st.markdown(
            f"## Player Performance Analysis over Matches", unsafe_allow_html=True
        )
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Minutes Played in the Season", unsafe_allow_html=True)
            st.plotly_chart(
                plot_day_duration_time_series(selected_df), use_container_width=True
            )
            st.markdown("### Heart Zones", unsafe_allow_html=True)
            st.plotly_chart(plot_heartdata(selected_df), use_container_width=True)
        with col2:
            st.markdown("### Physical KPIs", unsafe_allow_html=True)
            st.plotly_chart(
                plot_matchload_time_series(selected_df), use_container_width=True
            )

    elif view == "Heatmap":
        st.markdown("## Match Days Overview", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:20px;'>The darker the  <span style='color:#96272D; font-weight:bold;'>red</span>, the higher the KPI value.</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(plot_gps_heatmap(selected_df), use_container_width=True)

        st.subheader("AI Sports Scientist's Opinion: 💻")

        df_json = selected_df.to_json(orient="records")
        st.write(get_ai_analysis(df_json, mode="gps"))

elif dates_choice == "Training":
    if view == "Time Series":
        with st.sidebar:
            match_week_duration = st.selectbox(
                "Match Week Duration?",
                match_week_duration_options,
                key="duration_select",
            )

        fig, n_weeks = plot_trainingload_timeseries(season_df, match_week_duration)
        st.markdown(
            f"## {'Normalized' if normalize_day_duration else ''} Training Average Performance - {n_weeks} Week{'s' if n_weeks > 1 else ''}",
            unsafe_allow_html=True,
        )
        st.pyplot(fig, use_container_width=True)

    elif view == "Heatmap":
        st.markdown(
            "## Intensity of GPS KPIs over Time (Training)", unsafe_allow_html=True
        )
        st.markdown(
            "<p style='font-size:20px;'>For each KPI, higher values correspond to greater <span style='color:#96272D; font-weight: bold;'>Red</span> specific to that KPI</p>",
            unsafe_allow_html=True,
        )
        selected_df = season_df[season_df.opposition_code.isna()]
        st.plotly_chart(
            plot_gps_heatmap(selected_df, is_match=False), use_container_width=True
        )