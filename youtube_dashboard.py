import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
import xlsxwriter
from PIL import Image
from io import BytesIO
import zipfile
from PIL import Image
import matplotlib.pyplot as plt

# Function to load sample data (fallback if no file is uploaded)
def load_sample_data():
    data = {
        "Date": pd.date_range(start="2019-01-01", end="2019-12-31", freq="D"),
        "Subscribers": [i * 10 for i in range(365)],
        "Views": [i * 100 for i in range(365)],
        "Watch Hours": [i * 5 for i in range(365)],
        "Likes": [i * 20 for i in range(365)],
        "Comments": [i * 2 for i in range(365)],
        "Shares": [i * 1 for i in range(365)],
        "Video Title": ["Video " + str(i) for i in range(365)],
    }
    return pd.DataFrame(data)

# Function to format numbers (e.g., 5000 -> (5K), 3,000,000 -> (3M), 1,000,000,000 -> (1B))
def format_number(num):
    if num >= 1_000_000_000:
        return f"({num / 1_000_000_000:.1f}B)"
    elif num >= 1_000_000:
        return f"({num / 1_000_000:.1f}M)"
    elif num >= 1_000:
        return f"({num / 1_000:.1f}K)"
    else:
        return ""

# Define specific colors for each metric
metric_colors = {
    "Subscribers": "#1f77b4",  # Blue
    "Views": "#ff7f0e",       # Orange
    "Watch Hours": "#2ca02c",  # Green
    "Likes": "#d62728",       # Red
    "Comments": "#9467bd",    # Purple
    "Shares": "#8c564b"       # Brown
}

# Define color palettes for each chart type (used when multiple series are shown together)
chart_color_palettes = {
    "Bar Chart": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    "Area Chart": ["#a6cee3", "#b2df8a", "#fb9a99", "#fdbf6f"],
    "Line Chart": ["#9467bd", "#8c564b", "#e377c2", "#7f7f7f"],
    "Pie Chart": ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3"],
}

# Custom CSS for layout adjustments, tooltips, and metric styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: grey;
        padding-left: 10px;
    }
    .stSidebar {
        background-color: black;
        width: 300px;
    }
    .metric-box {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 1em;
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.5em;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-format {
        font-size: 0.8em;
        color: #666;
    }
    .stPlotlyChart {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load logo
try:
    logo = Image.open("logo.png")
except:
    logo = None

# Sidebar for title, settings, and filters
if logo:
    st.sidebar.image(logo, width=100)
st.sidebar.title("YouTube Channel Dashboard")
    
# Help Section
with st.sidebar.expander("❓ Help"):
    st.write("""
    - Upload a CSV file with required columns
    - Use filters to adjust date range
    - Customize chart types and themes
    - Export data in multiple formats
    """)

# Settings dropdown
with st.sidebar.expander("⚙️ Settings"):
    show_all_time_stats = st.checkbox("Show All-Time Statistics", value=True)
    show_selected_duration_metrics = st.checkbox("Show Selected Duration Metrics", value=True)
    show_detailed_data_table = st.checkbox("Show Detailed Data Table", value=True)
    chart_theme = st.selectbox("Chart Theme", ["plotly", "plotly_white", "plotly_dark"])

# Filters in the sidebar
st.sidebar.header("Filters")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        required_columns = ["Date", "Subscribers", "Views", "Watch Hours", "Likes", "Comments", "Shares", "Video Title"]
        if not all(col in df.columns for col in required_columns):
            st.error("Missing required columns in uploaded file")
            df = load_sample_data()
        else:
            df["Date"] = pd.to_datetime(df["Date"])
    except Exception as e:
        st.error(f"Error reading file: {e}")
        df = load_sample_data()
else:
    df = load_sample_data()

# Date range filter
min_date = df["Date"].min()
max_date = df["Date"].max()
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Additional filters
time_frame = st.sidebar.selectbox("Time Frame", ["Daily", "Weekly", "Monthly", "Quarterly"])
chart_type = st.sidebar.selectbox("Chart Type", ["Bar Chart", "Area Chart", "Line Chart", "Pie Chart"])

# Filter data
filtered_df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

# Resample data based on time frame
if time_frame == "Weekly":
    resampled_df = filtered_df.resample("W", on="Date").sum().reset_index()
elif time_frame == "Monthly":
    resampled_df = filtered_df.resample("M", on="Date").sum().reset_index()
elif time_frame == "Quarterly":
    resampled_df = filtered_df.resample("Q", on="Date").sum().reset_index()
else:
    resampled_df = filtered_df.copy()

# Function to create charts with metric-specific colors
def create_chart(metric, title):
    color = metric_colors.get(metric, "#1f77b4")  # Default to blue if metric not found
    
    if chart_type == "Bar Chart":
        fig = px.bar(resampled_df, x="Date", y=metric, title=f"{title} ({time_frame})",
                    color_discrete_sequence=[color])
    elif chart_type == "Area Chart":
        fig = px.area(resampled_df, x="Date", y=metric, title=f"{title} ({time_frame})",
                     color_discrete_sequence=[color])
    elif chart_type == "Pie Chart":
        fig = px.pie(resampled_df, values=metric, names="Date", title=f"{title} ({time_frame})",
                    color_discrete_sequence=[color])
    else:  # Line Chart
        fig = px.line(resampled_df, x="Date", y=metric, title=f"{title} ({time_frame})",
                     color_discrete_sequence=[color])
    
    fig.update_layout(template=chart_theme)
    return fig

# Main content layout
st.title("YouTube Analytics Dashboard")

if show_all_time_stats:
    st.header("All-Time Statistics")
    
    # Create columns for metrics
    cols = st.columns(4)
    metrics = [
        ("Subscribers", df["Subscribers"].sum()),
        ("Views", df["Views"].sum()),
        ("Watch Hours", df["Watch Hours"].sum()),
        ("Likes", df["Likes"].sum())
    ]
    
    for i, (name, value) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">{name}</div>
                <div class="metric-value">{value:,}</div>
                <div class="metric-format">{format_number(value)}</div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_chart(name, name), use_container_width=True)

if show_selected_duration_metrics:
    st.header("Selected Duration Metrics")
    
    cols = st.columns(4)
    metrics = [
        ("Subscribers", resampled_df["Subscribers"].sum()),
        ("Views", resampled_df["Views"].sum()),
        ("Watch Hours", resampled_df["Watch Hours"].sum()),
        ("Likes", resampled_df["Likes"].sum())
    ]
    
    for i, (name, value) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">{name} (Selected)</div>
                <div class="metric-value">{value:,}</div>
                <div class="metric-format">{format_number(value)}</div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_chart(name, f"{name} (Selected)"), use_container_width=True)

if show_detailed_data_table:
    st.header("Detailed Data")
    st.dataframe(resampled_df)

# Add download dropdown for CSV, XLSX, and PDF
st.sidebar.header("Export Data")
export_format = st.sidebar.selectbox("Format", ["CSV", "Excel", "JSON"])

if st.sidebar.button("Export Data"):
    if export_format == "CSV":
        csv = resampled_df.to_csv(index=False)
        st.sidebar.download_button(
            "Download CSV",
            csv,
            "youtube_data.csv",
            "text/csv"
        )
    elif export_format == "Excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            resampled_df.to_excel(writer, index=False)
        st.sidebar.download_button(
            "Download Excel",
            output.getvalue(),
            "youtube_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif export_format == "JSON":
        json = resampled_df.to_json(orient="records")
        st.sidebar.download_button(
            "Download JSON",
            json,
            "youtube_data.json",
            "application/json"
        )
