import enum
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import re
from st_aggrid import JsCode
from typing import Dict, List, Tuple
from functools import lru_cache
from config import client, general_role, model
import streamlit as st
import requests
from bs4 import BeautifulSoup
from wikidata.client import Client

DATA_DIR = Path("data")


# Custom styling configuration
class StyleConfig:
    FONT_SIZES = {
        "title": 32,
        "header": 28,
        "subheader": 24,
        "regular": 20,
        "sidebar": 18,
        "table": 16,
        "plot_title": 18,
        "plot_axis": 16,
        "plot_tick": 14,
        "plot_legend": 16,
        "hover": 16,
    }

    COLORS = {"background": "#FFFFFF", "grid": "rgba(0,0,0,0.1)", "text": "#000000"}


class Color(enum.Enum):
    LIGHTBLUE = "#7A9DCF"
    BLUE = "#08407E"
    GREEN = "#365213"
    GREEN10 = "#EEF1E7"
    GREEN20 = "#E0E3D0"
    GREEN40 = "#C0C7A1"
    ORANGE = "#704F12"
    RED = "#96272D"
    GREY = "#575757"
    LIGHTRED = "#C55D57"
    LIGHTORANGE = "#BBA471"
    LIGHTGREEN = "#A1AB71"
    LIGHTGREY = "#A9A9A9"
    LIGHTPURPLE = "#CA6CAE"
    LIGHTPETROL = "#66AFC0"
    BLACK = "black"
    RED10 = "#F8EBEA"
    RED20 = "#F1D7D5"
    RED40 = "#E2AEAB"
    RED60 = "#D48681"
    RED80 = "#C55D57"
    RED120 = "#96272D"


# Constants
upper_color = Color.GREEN40.value
lower_color = Color.RED40.value

feature_names = {
    "day_duration": "Day Duration (mins)",
    "distance": "Distance",
    "distance_over_21": "Distance > 21 km/h",
    "distance_over_24": "Distance > 24 km/h",
    "distance_over_27": "Distance > 27 km/h",
    "peak_speed": "Peak Speed (m/s)",
    "accel_decel_over_2_5": r"Accel/Decel > 2.5 m/s²",
    "accel_decel_over_3_5": r"Accel/Decel > 3.5 m/s²",
    "accel_decel_over_4_5": r"Accel/Decel > 4.5 m/s²",
    "hr_zone_1_m": "Heart Rate Zone 1 (mins)",
    "hr_zone_2_m": "Heart Rate Zone 2 (mins)",
    "hr_zone_3_m": "Heart Rate Zone 3 (mins)",
    "hr_zone_4_m": "Heart Rate Zone 4 (mins)",
    "hr_zone_5_m": "Heart Rate Zone 5 (mins)",
}

color_dict = {
    "day_duration": Color.GREY,
    "distance": Color.LIGHTBLUE,
    "distance_over_21": Color.LIGHTGREEN,
    "distance_over_24": Color.LIGHTPETROL,
    "distance_over_27": Color.LIGHTORANGE,
    "peak_speed": Color.LIGHTRED,
    "accel_decel_over_2_5": Color.LIGHTGREY,
    "accel_decel_over_3_5": Color.BLACK,
    "accel_decel_over_4_5": Color.LIGHTPURPLE,
    "hr_zone_1_m": Color.RED10,
    "hr_zone_2_m": Color.RED40,
    "hr_zone_3_m": Color.RED60,
    "hr_zone_4_m": Color.RED80,
    "hr_zone_5_m": Color.RED120,
}


# Helper functions
def apply_plotly_style(fig: go.Figure, title: str = None) -> go.Figure:
    """Apply consistent styling to Plotly figures."""
    fig.update_layout(
        template="plotly_white",
        font=dict(
            size=StyleConfig.FONT_SIZES["regular"], color=StyleConfig.COLORS["text"]
        ),
        hoverlabel=dict(font_size=StyleConfig.FONT_SIZES["hover"]),
        margin=dict(l=0, r=0, t=40 if title else 0, b=0),
        plot_bgcolor=StyleConfig.COLORS["background"],
        paper_bgcolor=StyleConfig.COLORS["background"],
    )

    if title:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(
                    size=StyleConfig.FONT_SIZES["title"],
                    color=StyleConfig.COLORS["text"],
                ),
                x=0.5,
                xanchor="center",
            )
        )

    return fig


def plot_day_duration_time_series(df: pd.DataFrame) -> go.Figure:
    """Plot day duration time series with enhanced styling."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["match"],
            y=df["day_duration"],
            mode="lines+markers",
            marker=dict(
                color=color_dict["day_duration"].value,
                size=8,
                line=dict(width=1, color="DarkSlateGrey"),
            ),
            name="Day Duration",
            hoverinfo="y+text",
            text=df[["opposition_full", "date"]],
            hovertemplate=(
                "<b>Opponent:</b> %{text[0]}<br>"
                "<b>Date:</b> %{text[1]}<br>"
                "<b>Duration:</b> %{y} mins"
            ),
            line=dict(width=2),
        )
    )

    fig.update_layout(
        xaxis=dict(
            title=dict(
                text="Match", font=dict(size=StyleConfig.FONT_SIZES["plot_title"])
            ),
            tickangle=-45,
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_tick"]),
            showline=True,
            zeroline=False,
            showgrid=True,
            gridcolor=StyleConfig.COLORS["grid"],
        ),
        yaxis=dict(
            title=dict(
                text="Day Duration (minutes)",
                font=dict(size=StyleConfig.FONT_SIZES["plot_title"]),
            ),
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_tick"]),
            showline=True,
            zeroline=False,
            showgrid=True,
            gridcolor=StyleConfig.COLORS["grid"],
        ),
        showlegend=False,
    )

    return apply_plotly_style(fig)


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe by day duration."""
    for key in feature_names.keys():
        if key == "day_duration":
            continue
        # Vectorized operation for better performance
        df[key] = df[key].div(df["day_duration"].replace(0, np.nan)).round(2)
    return df


def plot_heartdata(df: pd.DataFrame) -> go.Figure:
    """Plot heart rate zone data with enhanced styling."""
    # Convert to long format more efficiently
    hr_cols = [f"hr_zone_{i}_m" for i in range(1, 6)]
    gps_long = pd.melt(
        df,
        id_vars=["match", "opposition_full", "date"],
        value_vars=hr_cols,
        var_name="Heart Rate Zone",
        value_name="minutes",
    )

    # Create color mapping
    pallete = {zone: color_dict[zone].value for zone in color_dict if zone in hr_cols}

    # Define stacking order
    stacking_order = [
        "hr_zone_5_m",  # Bottom
        "hr_zone_4_m",
        "hr_zone_3_m",
        "hr_zone_2_m",
        "hr_zone_1_m",  # Top
    ]

    # Update legend labels
    zone_labels = {
        "hr_zone_5_m": "5",
        "hr_zone_4_m": "4",
        "hr_zone_3_m": "3",
        "hr_zone_2_m": "2",
        "hr_zone_1_m": "1",
    }

    fig = go.Figure()

    gps_long["zone_shorten"] = gps_long["Heart Rate Zone"].apply(
        lambda x: zone_labels[x]
    )
    # Add bars for each Heart Rate Zone
    for zone in stacking_order:
        zone_data = gps_long[gps_long["Heart Rate Zone"] == zone]
        fig.add_trace(
            go.Bar(
                x=zone_data["minutes"],
                y=zone_data["match"],
                name=zone,
                orientation="h",
                hoverinfo="x+y+text",
                text=zone_data[["opposition_full", "date", "zone_shorten"]],
                hovertemplate=(
                    "<b>Opponent:</b> %{text[0]}<br>"
                    "<b>Date:</b> %{text[1]}<br>"
                    "<b>Zone %{text[2]}:</b> %{x} mins"
                ),
                marker=dict(
                    color=pallete[zone], line=dict(width=0.5, color="rgba(0,0,0,0.3)")
                ),
            )
        )

    # Update layout
    fig.update_layout(
        barmode="stack",
        xaxis=dict(
            title=dict(
                text="Time (mins)", font=dict(size=StyleConfig.FONT_SIZES["plot_title"])
            ),
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_tick"]),
            gridcolor=StyleConfig.COLORS["grid"],
        ),
        yaxis=dict(
            title=dict(
                text="Match", font=dict(size=StyleConfig.FONT_SIZES["plot_title"])
            ),
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_tick"]),
        ),
        legend=dict(
            title=dict(
                text="HR Zones", font=dict(size=StyleConfig.FONT_SIZES["plot_legend"])
            ),
            font=dict(size=StyleConfig.FONT_SIZES["plot_legend"]),
            traceorder="normal",
        ),
        height=1200,
    )

    fig.for_each_trace(lambda t: t.update(name=zone_labels.get(t.name, t.name)))

    return apply_plotly_style(fig)


def plot_matchload_time_series(df: pd.DataFrame) -> go.Figure:
    """Plot match load time series with enhanced styling."""
    # Create subplots
    fig = sp.make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[
            feature_names["distance"],
            "Distance Over Speed Thresholds",
            "Acceleration/Deceleration Over Thresholds",
            feature_names["peak_speed"],
        ],
        vertical_spacing=0.08,
    )

    # Common hover settings
    hoverinfo = "x+z+y+text+name"  # Added 'name' to show the trace name
    text = df[["opposition_full", "date"]]
    hovertemplate = (
        "%{y:.2f}"
        "<extra></extra>"  # Removes trace0, trace1 labels
    )

    # Plot Distance
    fig.add_trace(
        go.Scatter(
            x=df["match"],
            y=df["distance"],
            mode="lines+markers",
            marker=dict(
                color=color_dict["distance"].value,
                size=8,
                line=dict(width=1, color="DarkSlateGrey"),
            ),
            hoverinfo=hoverinfo,
            text=text,
            hovertemplate=hovertemplate,
            name=feature_names["distance"],  # Use display name
            line=dict(width=2),
        ),
        row=1,
        col=1,
    )

    # Plot Peak Speed
    fig.add_trace(
        go.Scatter(
            x=df["match"],
            y=df["peak_speed"],
            mode="lines+markers",
            hoverinfo=hoverinfo,
            text=text,
            hovertemplate=hovertemplate,
            marker=dict(
                color=color_dict["peak_speed"].value,
                size=8,
                line=dict(width=1, color="DarkSlateGrey"),
            ),
            name=feature_names["peak_speed"],  # Use display name
            line=dict(width=2),
        ),
        row=4,
        col=1,
    )

    # Distance Over Speed Thresholds
    for col in ["distance_over_21", "distance_over_24", "distance_over_27"]:
        fig.add_trace(
            go.Scatter(
                x=df["match"],
                y=df[col],
                mode="lines+markers",
                marker=dict(
                    color=color_dict[col].value,
                    size=8,
                    line=dict(width=1, color="DarkSlateGrey"),
                ),
                hoverinfo=hoverinfo,
                text=text,
                hovertemplate=hovertemplate,
                name=feature_names[col],  # Use display name
                line=dict(width=2),
            ),
            row=2,
            col=1,
        )

    # Acceleration/Deceleration Thresholds
    for col in ["accel_decel_over_2_5", "accel_decel_over_3_5", "accel_decel_over_4_5"]:
        fig.add_trace(
            go.Scatter(
                x=df["match"],
                y=df[col],
                mode="lines+markers",
                marker=dict(
                    color=color_dict[col].value,
                    size=8,
                    line=dict(width=1, color="DarkSlateGrey"),
                ),
                hoverinfo=hoverinfo,
                text=text,
                hovertemplate=hovertemplate,
                name=feature_names[col],  # Use display name
                line=dict(width=2),
            ),
            row=3,
            col=1,
        )

    # Update subplot titles
    for i, title in enumerate(
        [
            feature_names["distance"],
            "Distance Over Speed Thresholds",
            "Acceleration/Deceleration Over Thresholds",
            feature_names["peak_speed"],
        ],
        1,
    ):
        fig.layout.annotations[i - 1].update(
            text=title,
            font=dict(
                size=StyleConfig.FONT_SIZES["subheader"],
                color=StyleConfig.COLORS["text"],
            ),
        )

    # Update layout
    fig.update_layout(
        height=1200,
        width=900,
        showlegend=True,
        legend=dict(
            font=dict(size=StyleConfig.FONT_SIZES["plot_legend"]),
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
        ),
        xaxis4=dict(
            title="Match",
            tickangle=-45,
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_tick"]),
        ),
        hovermode="x unified",  # Shows all values at same x position
    )

    # Style each subplot
    for i in range(1, 5):
        fig.update_yaxes(
            title_font=dict(size=StyleConfig.FONT_SIZES["plot_title"]),
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_tick"]),
            row=i,
            col=1,
        )

    return apply_plotly_style(fig)


def plot_trainingload_timeseries(
    df: pd.DataFrame, match_week_duration: int
) -> Tuple[plt.Figure, int]:
    """Plot training load time series with enhanced styling."""
    # Precompute shifted values
    df["next_week_duration"] = df.match_week_duration.shift(-1)
    df["pre_week_duration"] = df.match_week_duration.shift(1)

    # Filter data
    df = df[df.match_week_duration == match_week_duration].copy()
    df["code"] = df["md_plus_code"].astype(str)

    # Get match data
    md_df = df[df.next_week_duration == match_week_duration].copy()
    md_df["code"] = "match"

    # Get next match data
    next_md_df = df[df.pre_week_duration == match_week_duration].copy()
    next_md_df["code"] = "next match"

    # Combine data
    df = pd.concat([df, md_df, next_md_df])

    # Define custom order
    my_order = ["match"]
    my_order.extend(str(i) for i in range(1, match_week_duration))
    my_order.append("next match")

    # Categorical ordering
    df["code"] = pd.Categorical(df["code"], categories=my_order, ordered=True)
    df.sort_values("code", inplace=True)

    # Aggregate data
    agg_funcs = {col: "mean" for col in feature_names.keys()}
    md_groups = df.groupby("code").agg(agg_funcs).reset_index()

    # Create figure
    n_features = len(feature_names)
    fig, axes = plt.subplots(n_features, 1, figsize=(12, 4 * n_features), dpi=300)

    # Style adjustments
    plt.rcParams.update(
        {
            "font.size": StyleConfig.FONT_SIZES["plot_tick"],
            "axes.titlesize": StyleConfig.FONT_SIZES["plot_title"],
            "axes.labelsize": StyleConfig.FONT_SIZES["plot_title"],
            "xtick.labelsize": StyleConfig.FONT_SIZES["plot_tick"],
            "ytick.labelsize": StyleConfig.FONT_SIZES["plot_tick"],
            "legend.fontsize": StyleConfig.FONT_SIZES["plot_legend"],
        }
    )

    for i, (feature, ax) in enumerate(zip(feature_names.keys(), axes.flatten())):
        # Clean up axes
        for spine in ["right", "top"]:
            ax.spines[spine].set_visible(False)

        # Create bars
        bars = ax.bar(
            md_groups["code"],
            md_groups[feature],
            width=0.5,
            color=color_dict[feature].value,
            zorder=3,
            edgecolor="white",
            linewidth=1,
        )

        # Labels and titles
        ax.set_ylabel(feature_names[feature])
        ax.set_xlabel("Week Day")
        ax.set_xticks(range(len(md_groups["code"])))
        ax.set_xticklabels(md_groups["code"], rotation=0)

        # Grid
        ax.grid(
            axis="y", linestyle="-", alpha=0.2, color=Color.LIGHTGREY.value, zorder=0
        )

        # Value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + (0.02 * height),
                f"{height:.0f}" if height.is_integer() else f"{height:.1f}",
                ha="center",
                va="bottom",
                fontsize=StyleConfig.FONT_SIZES["plot_tick"],
            )

    plt.tight_layout()
    n_weeks = len(md_df)

    return fig, n_weeks


def plot_gps_heatmap(df: pd.DataFrame, is_match: bool = True) -> go.Figure:
    """Plot GPS heatmap with enhanced styling."""
    # Hover settings
    hoverinfo = "x+y+z+text"
    text = [df["opposition_full"].values]
    hovertemplate = (
        "<b>Opponent:</b> %{text}<br>"
        "<b>Date:</b> %{x}<br>"
        "<b>%{y}:</b> %{z:.2f}"
        "<extra></extra>"
    )

    if not is_match:
        hoverinfo = "x+z"
        text = [[""] * len(df)]
        hovertemplate = "<b>Date:</b> %{x}<br><b>Value:</b> %{z:.2f}<extra></extra>"

    # Features to plot
    features = list(feature_names.keys())

    # Ensure date is datetime
    df["date"] = pd.to_datetime(df["date"])

    # Create subplots
    fig = make_subplots(
        rows=len(features) + 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
    )

    # Add heatmap for each feature
    for i, feature in enumerate(features):
        # Clean feature name for display
        display_name = feature_names[feature]
        display_name = re.sub(r"\$(\^[0-9]+)\$", r"<sup>\1</sup>", display_name)
        display_name = display_name.replace("^", "")

        fig.add_trace(
            go.Heatmap(
                z=[df[feature].values],
                x=df["date"],
                y=[display_name],
                colorscale="Reds",
                showscale=False,
                hoverinfo=hoverinfo,
                text=text,
                hovertemplate=hovertemplate,
                hoverlabel=dict(font=dict(size=StyleConfig.FONT_SIZES["hover"])),
            ),
            row=i + 2,
            col=1,
        )

    # Update layout - KEY CHANGES HERE
    fig.update_layout(
        width=900,
        height=30 * len(features),
        margin=dict(t=0, b=0, l=0, r=0),  # Increased top margin to 40px
        font=dict(size=StyleConfig.FONT_SIZES["regular"]),
    )

    # Style axes
    for i in range(1, len(features) + 2):
        fig.update_yaxes(
            title_font=dict(size=StyleConfig.FONT_SIZES["plot_title"]),
            tickfont=dict(size=StyleConfig.FONT_SIZES["plot_title"]),
            row=i,
            col=1,
            automargin=True,
            autorange="reversed",
        )

    fig.update_xaxes(
        title_font=dict(size=StyleConfig.FONT_SIZES["plot_title"]),
        tickfont=dict(size=StyleConfig.FONT_SIZES["plot_title"]),
        row=len(features) + 1,  # Apply to bottom subplot only
        col=1,
        automargin=True,
    )

    return apply_plotly_style(fig)


def return_json_cell(
    upper_threshold: float, lower_threshold: float, upper_color: str, lower_color: str
) -> JsCode:
    """Return JS code for conditional cell styling."""
    return JsCode(
        f"""
        function(params) {{
            if (params.value !== null && params.value !== undefined) {{
                if (params.value > {upper_threshold}) {{
                    return {{
                        'backgroundColor': '{upper_color}',
                        'color': 'black',
                        'fontWeight': 'bold',
                        'fontSize': '14px'
                    }};
                }} else if (params.value < {lower_threshold}) {{
                    return {{
                        'backgroundColor': '{lower_color}',
                        'color': 'black',
                        'fontWeight': 'bold',
                        'fontSize': '14px'
                    }};
                }}
            }}
            return {{'fontSize': '14px'}};
        }}
    """
    )


@lru_cache(maxsize=100)  # Cache up to 100 unique requests
def get_ai_analysis(df_json, mode, threshold_date=None, category=None):
    """Get AI analysis for the filtered data."""
    extra_role = {}
    if mode == "gps":
        content = f"""
        **Dataset Context**:  
        GPS and physical performance metrics for a Chelsea FC player over.

        **Task**:  
        Analyze this dataset as a top-tier sports scientist:  
        ```json
        {df_json}
        """
    elif mode == "capability":
        content = f"""
        **Dataset Context**:  
        Physical Capability metrics for a Chelsea FC player  

        **Task**:  
        Analyze this dataset as a top-tier sports scientist:  
        ```json
        {df_json}
        """
    elif mode == "recovery":
        content = f"""
        **Dataset**: Daily {category} test results for a Chelsea FC first-team player after {threshold_date}
        ```json
        {df_json}"""

        extra_role = {
            "role": "system",
            "content": """
            You are Chelsea FC's Lead Recovery Specialist, combining expertise in:
            - Athlete monitoring systems (AMS) and biomarker interpretation
            - Neuromuscular fatigue and musculoskeletal recovery
            - Sleep and subjective wellness analytics
            - Injury risk prediction models

            Your analysis given data, use clinical thresholds to prioritize actionable interventions, and flag any contradictory signals between metrics
            """}
    elif mode == "injury":
        content = f"""
        This is an injury history dataset of the given player
        ```json
        {df_json}"""

    messages = [general_role]

    if extra_role:
        messages.append(extra_role)
    messages.append({"role": "user", "content": content})

    chat_response = client.chat.complete(
        model=model,
        messages=messages,
    )
    return chat_response.choices[0].message.content


@st.cache_data
def load_gps_data():
    gps_file = DATA_DIR / "CFC GPS Data.csv"

    # Specify dtype for columns to reduce memory usage
    dtype_dict = {
        "season": "category",
        "opposition_code": "category",
        "md_plus_code": "int8",
        "md_minus_code": "int8",
    }

    # Only parse necessary columns initially
    usecols = [
        "date",
        "season",
        "day_duration",
        "md_plus_code",
        "md_minus_code",
        "opposition_code",
        "opposition_full",
        "distance",
        "distance_over_21",
        "distance_over_24",
        "distance_over_27",
        "accel_decel_over_2_5",
        "accel_decel_over_3_5",
        "accel_decel_over_4_5",
        "peak_speed",
        "hr_zone_1_hms",
        "hr_zone_2_hms",
        "hr_zone_3_hms",
        "hr_zone_4_hms",
        "hr_zone_5_hms",
    ]

    gps_df = pd.read_csv(
        gps_file,
        encoding="ISO-8859-1",
        parse_dates=["date"],
        dayfirst=True,
        dtype=dtype_dict,
        usecols=usecols,
    )

    # Optimized operations
    gps_df["player_id"] = "P1"
    gps_df["day_duration"] = gps_df["day_duration"].round(1)
    gps_df.sort_values(by="date", inplace=True)

    # Add match identifiers
    gps_df["match_week_duration"] = (
        gps_df["md_plus_code"] + gps_df["md_minus_code"].abs()
    )
    gps_df["match"] = (
        gps_df["opposition_code"].astype(str)
        + "_"
        + gps_df["date"].dt.strftime("%m-%d")
    )
    gps_df["date"] = gps_df["date"].dt.date

    # Convert HR zones more efficiently
    for zid in range(1, 6):
        col = f"hr_zone_{zid}_hms"
        gps_df[f"hr_zone_{zid}_m"] = (
            pd.to_timedelta(gps_df[col]).dt.total_seconds().div(60).round(1)
        )
        gps_df.drop(col, axis=1, inplace=True)

    return gps_df

@st.cache_data
def load_capability_data():
    """Load and preprocess the data."""
    
    COLUMN_RENAMES = {
        "testDate": "Test Date",
        "benchmarkPct": "Benchmark",
        "movement": "Movement",
        "quality": "Quality",
        "expression": "Expression",
    }
    BENCHMARK_COL = "Benchmark"
    DATE_COL = "Test Date"
    QUALITY_COL = "Quality"
    EXPRESSION_COL = "Expression"

    df = pd.read_csv(DATA_DIR / "CFC Physical Capability Data_.csv")
    df = df.rename(columns=COLUMN_RENAMES)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], dayfirst=True, cache=True)
    df = df.sort_values(DATE_COL)
    df[BENCHMARK_COL] = df[BENCHMARK_COL].mul(100)
    df["player_id"] = "P1"
    df["class"] = (
        df[QUALITY_COL].str.title().str.replace("_", "-")
        + "-"
        + df[EXPRESSION_COL].str.title().str.replace("_", "-")
    )
    return df

@st.cache_data
def load_recovery_data():
    """Load and preprocess the data."""
    recovery_status_df = pd.read_csv(DATA_DIR / "CFC Recovery status Data.csv")

    # Convert sessionDate to datetime
    recovery_status_df["sessionDate"] = pd.to_datetime(
        recovery_status_df["sessionDate"], format="%d/%m/%Y"
    )
    recovery_status_df["player_id"] = "P1"

    # Ensure the data is sorted by sessionDate
    recovery_status_df = recovery_status_df.sort_values("sessionDate")

    return recovery_status_df

main_url = "https://en.wikipedia.org/wiki/2024%E2%80%9325_Chelsea_F.C._season"
@st.cache_data
def get_chelsea_players():
    player2URL = {}
    try:
        response = requests.get(main_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, "html.parser")

        players = []
        # Find the correct squad table (first-team squad typically appears first)
        squad_tables = soup.find_all("table", class_="wikitable")
        
        if squad_tables:
            # Usually the first wikitable is the squad table
            squad_table = squad_tables[1]
            
            for row in squad_table.find_all("tr")[1:]:  # Skip header row
                cols = row.find_all("td")
                if len(cols) >= 2:  # Player name is typically in the second column
                    player_link = cols[1].find("a")
                    if player_link and "title" in player_link.attrs:
                        player_name = player_link["title"]
                        # Clean up the name by removing "(footballer)" if present
                        player_name = player_name.split(" (")[0].strip()
                        players.append(player_name)
                        player2URL[player_name] =  f'https://en.wikipedia.org/wiki/{player_link["href"].split("/")[-1]}'
        return sorted(list(set(players))), player2URL  # Remove duplicates and sort
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return [],[]

def get_wikidata_entity(wikipedia_title):
    client = Client()
    
    # First search for the entity using the Wikipedia title
    search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={wikipedia_title}&language=en&format=json"
    
    if wikipedia_title == "Reece_James_(footballer,_born_1999)":
        return "Q39076401"
    elif wikipedia_title == "Wesley_Fofana_(footballer)":
        return "Q65029821"
    try:
        response = requests.get(search_url)
        data = response.json()
        
        # Check if we found matching entities
        if data.get('search'):
            # Get the first matching entity ID
            entity_id = data['search'][0]['id']
            entity = client.get(entity_id, load=True)
            return entity.id
        else:
            print(f"No Wikidata entity found for '{wikipedia_title}'")
            return None
            
    except Exception as e:
        print(f"Error searching for entity: {e}")
        return None

def get_wikidata_metadata(wikidata_id):
    # Define the properties we want to retrieve
    properties = {
        'country_of_citizenship': 'P27',          # Country of citizenship
        'native_language': 'P103',                # Native language
        'languages_spoken': 'P1412',              # Languages spoken, written or signed
        'transfermarkt_id': 'P2446',              # Transfermarkt player ID
        'fbref_id': 'P5750'                      # FBref player ID
    }
    
    # Wikidata API endpoint
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        entity = data.get('entities', {}).get(wikidata_id, {})
        claims = entity.get('claims', {})
        
        result = {}
        
        # Helper function to extract values from claims
        def get_property_values(prop_id):
            if prop_id not in claims:
                return None
            values = []
            for claim in claims[prop_id]:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    datavalue = claim['mainsnak']['datavalue']
                    if datavalue['type'] == 'wikibase-entityid':
                        # For entity IDs (like countries, languages), we need to look up the label
                        entity_id = datavalue['value']['id']
                        values.append(get_entity_label(entity_id))
                    else:
                        values.append(datavalue['value'])
            return values[0] if len(values) == 1 else values
        
        # Helper function to get labels for entities
        def get_entity_label(entity_id):
            label_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
            label_response = requests.get(label_url)
            label_data = label_response.json()
            entity = label_data.get('entities', {}).get(entity_id, {})
            return entity.get('labels', {}).get('en', {}).get('value', entity_id)
        
        # Get each property
        result['country_of_citizenship'] = get_property_values(properties['country_of_citizenship'])
        result['native_language'] = get_property_values(properties['native_language'])
        result['languages_spoken'] = get_property_values(properties['languages_spoken'])
        result['transfermarkt_id'] = get_property_values(properties['transfermarkt_id'])
        result['fbref_id'] = get_property_values(properties['fbref_id'])
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def adjust_sidebar_width():
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                min-width: 0px !important;
                max-width: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)