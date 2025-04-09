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
    load_capability_data,
    load_recovery_data,
)
from st_aggrid import AgGrid, GridOptionsBuilder, StAggridTheme
from config import client, general_role, model
from millify import millify
import warnings

# Configuration
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Case Explorer", page_icon="🔎", layout="wide")

player_id = st.sidebar.selectbox("Player", ["P1"])
data_type = st.sidebar.selectbox("Source", ["GPS", "Capability", "Recovery"])

st.markdown(f"# {data_type} Case Explorer", unsafe_allow_html=True)

if data_type == "Capability":
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

    physical_capability_df = load_capability_data()
    
    gb = GridOptionsBuilder.from_dataframe(physical_capability_df[REQUIRED_COLS])
    gb.configure_side_bar()

    for column in REQUIRED_COLS:
        if column == DATE_COL:
            gb.configure_column(
                column,
                filter="agDateColumnFilter",
                type=["dateColumn"],
                valueFormatter="(d=new Date(value), d.getFullYear() + '-' + ('0' + (d.getMonth()+1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2))",
            )
        elif column == BENCHMARK_COL:
            gb.configure_column(
                column,
                filter="agNumberColumnFilter",
                type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                valueFormatter="value.toFixed(2)",
                cellStyle=return_json_cell(60, 30, upper_color, lower_color),
            )
        else:
            gb.configure_column(column, filter=True)

    grid_options =  gb.build()

    AgGrid(
        physical_capability_df[REQUIRED_COLS],
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
    )

elif data_type == "GPS":
    gps_df = load_gps_data()
    # Prepare columns more efficiently
    shown_cols = [
        "season",
        "date",
        "day_duration",
        "opposition_full",
        "md_plus_code",
        "md_minus_code",
        "distance",
        "distance_over_21",
        "distance_over_24",
        "distance_over_27",
        "accel_decel_over_2_5",
        "accel_decel_over_3_5",
        "accel_decel_over_4_5",
        "peak_speed",
        "hr_zone_1_m",
        "hr_zone_2_m",
        "hr_zone_3_m",
        "hr_zone_4_m",
        "hr_zone_5_m",
    ]

    explorer_df = gps_df[shown_cols].rename(columns={"opposition_full": "opposition"})

    # Precompute statistics for styling
    numeric_cols = [
        "distance",
        "distance_over_21",
        "distance_over_24",
        "distance_over_27",
        "accel_decel_over_2_5",
        "accel_decel_over_3_5",
        "accel_decel_over_4_5",
        "day_duration",
        "peak_speed",
        "hr_zone_1_m",
        "hr_zone_2_m",
        "hr_zone_3_m",
        "hr_zone_4_m",
        "hr_zone_5_m",
    ]
    explorer_df["date"] = pd.to_datetime(explorer_df["date"], dayfirst=True).astype(
        "datetime64[ns]"
    )

    stats = {
        col: (explorer_df[col].mean(), explorer_df[col].std()) for col in numeric_cols
    }

    # Configure AgGrid options with larger font
    gb = GridOptionsBuilder.from_dataframe(explorer_df)
    gb.configure_side_bar()

    for column in explorer_df.columns:
        if column == "date":
            gb.configure_column(
                "date",
                header_name="Date",
                type=["dateColumnFilter", "customDateTimeFormat"],
                custom_format_string="yyyy-MM-dd",
                filter="agDateColumnFilter",
                # 👇 Format as "DD/MM/YYYY" (no time)
                value_formatter="data.date ? new Date(data.date).toLocaleDateString('en-GB') : ''",
                filter_params={
                    "comparator": """function(filterLocalDateAtMidnight, cellValue) {
                        if (!cellValue) return 0;
                        const cellDate = new Date(cellValue);
                        if (filterLocalDateAtMidnight.getTime() === cellDate.getTime()) return 0;
                        return cellDate < filterLocalDateAtMidnight ? -1 : 1;
                    }""",
                    "browserDatePicker": True,
                },
            )
        elif column in numeric_cols:
            mean, std = stats[column]
            upper_threshold = mean + std
            lower_threshold = mean - std

            # Determine colors
            upper_col = upper_color
            lower_col = lower_color
            if column.startswith("hr"):
                upper_col, lower_col = lower_col, upper_col
            elif column == "day_duration":
                upper_col = lower_col

            gb.configure_column(
                column,
                filter="agNumberColumnFilter",
                type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                valueFormatter="value.toFixed(2)",
                cellStyle=return_json_cell(
                    upper_threshold, lower_threshold, upper_col, lower_col
                ),
            )
        elif column in ["md_plus_code", "md_minus_code"]:
            gb.configure_column(
                column,
                filter="agNumberColumnFilter",
                type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                valueFormatter="value.toFixed(0)",
            )
        else:
            gb.configure_column(column, filter=True)

    grid_options = gb.build()

    # Configure AgGrid to use larger font
    grid_options["defaultColDef"] = {
        "flex": 1,
        "minWidth": 100,
        "resizable": True,
        "wrapText": True,
        "autoHeight": True,
        "cellStyle": {"fontSize": "14px"},
    }

    AgGrid(
        explorer_df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        height=600,
        theme="streamlit",
        update_mode="MODEL_CHANGED",  # Updates on filter/sort/edit
        fit_columns_on_grid_load=True,
    )
elif data_type == "Recovery":
    recovery_df = load_recovery_data()
    recovery_df.drop(columns={"player_id"},inplace=True)
    recovery_df = recovery_df[["seasonName","sessionDate","category","metric","value"]]
    recovery_df["metric"] = recovery_df["metric"].apply(lambda x: x.split("_")[-1] if x!="emboss_baseline_score" else x)
    recovery_df["sessionDate"] = pd.to_datetime(recovery_df["sessionDate"]).dt.date

    recovery_df.rename(columns={"sessionDate": "Session Date", "seasonName": "Season", "category": "Category", "metric": "Metric", "value": "Value"}, inplace=True)

    gb = GridOptionsBuilder.from_dataframe(recovery_df)
    gb.configure_side_bar()

    for column in recovery_df.columns:
        if column == "Session Date":
            gb.configure_column(
                "Session Date",
                header_name="Session Date",
                type=["dateColumnFilter", "customDateTimeFormat"],
                custom_format_string="yyyy-MM-dd",
                filter="agDateColumnFilter",
                # 👇 Format as "DD/MM/YYYY" (no time)
                value_formatter="data.date ? new Date(data.date).toLocaleDateString('en-GB') : ''",
                filter_params={
                    "comparator": """function(filterLocalDateAtMidnight, cellValue) {
                        if (!cellValue) return 0;
                        const cellDate = new Date(cellValue);
                        if (filterLocalDateAtMidnight.getTime() === cellDate.getTime()) return 0;
                        return cellDate < filterLocalDateAtMidnight ? -1 : 1;
                    }""",
                    "browserDatePicker": True,
                },
            )
        else:
            gb.configure_column(column, filter=True)

    grid_options = gb.build()

    # Configure AgGrid to use larger font
    grid_options["defaultColDef"] = {
        "flex": 1,
        "minWidth": 100,
        "resizable": True,
        "wrapText": True,
        "autoHeight": True,
        "cellStyle": {"fontSize": "14px"},
    }

    AgGrid(
        recovery_df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        height=600,
        theme="streamlit",
        update_mode="MODEL_CHANGED",  # Updates on filter/sort/edit
        fit_columns_on_grid_load=True,
    )
