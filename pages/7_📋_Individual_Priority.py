from pathlib import Path
import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
import warnings
from utils import Color, DATA_DIR, return_json_cell, upper_color, lower_color

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Individual Priority", page_icon="📋", layout="wide")

# Initialize session state for data persistence
if "individual_priority_df" not in st.session_state:
    individual_priority_df = pd.read_csv(DATA_DIR / "CFC Individual Priority Areas.csv")
    for col in ["Review Date", "Target set"]:
        individual_priority_df[col] = pd.to_datetime(
            individual_priority_df[col], dayfirst=True
        ).dt.date
    individual_priority_df["player_id"] = "P1"
    st.session_state.individual_priority_df = individual_priority_df[
        [
            "player_id",
            "Priority",
            "Category",
            "Area",
            "Performance Type",
            "Review Date",
            "Tracking",
            "Target set",
        ]
    ]


# Function to update Gantt chart
def update_gantt_chart():
    gantt_df = st.session_state.individual_priority_df.copy()
    gantt_df["Priority"] = gantt_df["Priority"].astype(int)
    gantt_df["Review Date"] = pd.to_datetime(gantt_df["Review Date"], errors="coerce")
    gantt_df["Target set"] = pd.to_datetime(gantt_df["Target set"], errors="coerce")

    today_str = datetime.date.today().isoformat()

    fig = px.timeline(
        gantt_df,
        x_start="Review Date",
        x_end="Target set",
        y="Priority",
        color="Tracking",
        color_discrete_map={
            "On Track": "#FFA726",
            "Achieved": "#4CAF50",
        },
        hover_name="Performance Type",
        hover_data={"Priority": True, "Category": True, "Area": True, "Tracking": True},
    )

    fig.update_yaxes(categoryorder="array", autorange="reversed")
    fig.add_vline(x=today_str, line_dash="dash", line_color="red")

    fig.update_layout(
        bargap=0.3,
        height=300,
        showlegend=True,
        xaxis_title="Timeline",
        yaxis_title="Goals",
        hovermode="closest",
        annotations=[
            dict(
                x=today_str,
                y=1,
                xref="x",
                yref="paper",
                text=f"Today: {today_str}",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-40,
                font=dict(size=14, color="black"),
            )
        ],
    )

    return fig


# Sidebar filter
player_id = st.sidebar.selectbox(
    "Player", st.session_state.individual_priority_df.player_id.unique()
)

st.title("📋 Individual Priority List")

# Gantt Chart
st.subheader("Gantt Chart:")
st.plotly_chart(update_gantt_chart(), use_container_width=True)

# Tables with data editors
st.subheader("Table:")

# Split data into On Track and Achieved
on_track_df = st.session_state.individual_priority_df[
    st.session_state.individual_priority_df["Tracking"] == "On Track"
]
achieved_df = st.session_state.individual_priority_df[
    st.session_state.individual_priority_df["Tracking"] == "Achieved"
]

# Display editable tables
st.subheader("🎯 On Track Goals:")
on_track_edited_df = st.data_editor(
    on_track_df.drop(columns=["player_id", "Tracking"]).reset_index(drop=True),
    use_container_width=True,
    num_rows="dynamic",
    key="on_track_editor",
)

st.subheader("✅ Achieved Goals:")
achieved_edited_df = st.data_editor(
    achieved_df.drop(columns=["player_id", "Priority", "Tracking"]).reset_index(
        drop=True
    ),
    use_container_width=True,
    num_rows="dynamic",
    key="achieved_editor",
)

# Update button to sync changes
if st.button("Update Gantt Chart"):
    # Combine edited data
    new_on_track = on_track_edited_df.copy()
    new_on_track["Tracking"] = "On Track"
    new_on_track["player_id"] = player_id

    new_achieved = achieved_edited_df.copy()
    new_achieved["Tracking"] = "Achieved"
    new_achieved["player_id"] = player_id

    # Reconstruct priority column for achieved goals if needed
    if "Priority" not in new_achieved.columns:
        new_achieved["Priority"] = 0  # Or some default value

    # Update the main dataframe
    updated_df = pd.concat([new_on_track, new_achieved])
    st.session_state.individual_priority_df = updated_df

    # Rerun to update the Gantt chart
    st.rerun()
