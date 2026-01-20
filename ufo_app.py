import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title="US UFO Anomaly Dashboard", layout="wide")

def get_data(query, params=()):
    conn = sqlite3.connect('ufo_analytics.db', check_same_thread=False)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

st.title("🇺🇸 US UFO Anomaly Analytics")
st.markdown("Correlating high-speed anomalies with US Military reveals and Hollywood quality pulses.")

# 1. SIDEBAR FILTERS
st.sidebar.header("Temporal & Shape Filters")

# Date Slider
year_range = st.sidebar.slider(
    "Select Year Range", 
    min_value=1981, 
    max_value=2014, 
    value=(1990, 2010)
)

# Shape Multi-select
shape_list = get_data("SELECT DISTINCT refined_shape FROM sightings")['refined_shape'].tolist()
selected_shapes = st.sidebar.multiselect("Select Shapes", shape_list, default=['triangle', 'disk', 'chevron'])

# 2. THE CORRELATION CHART (Filtered by Year Range)
st.subheader("The Trinity Correlation: Tech, Media, & Anomalies")
trend_df = get_data("SELECT * FROM movie_quality WHERE Year BETWEEN ? AND ?", params=year_range)
mil_df = get_data("SELECT * FROM military_tech WHERE Year BETWEEN ? AND ?", params=year_range)

fig = go.Figure()
fig.add_trace(go.Scatter(x=trend_df['Year'], y=trend_df['sighting_count'], 
                         name="US Sightings", line=dict(color='crimson', width=3)))

fig.add_trace(go.Scatter(x=trend_df['Year'], y=trend_df['imdb_rating'] * 500, 
                         name="Movie Quality Pulse", line=dict(color='teal', dash='dot')))

# Overlay Military Tech
for _, row in mil_df.iterrows():
    fig.add_vline(x=row['Year'], line_width=1, line_dash="dash", line_color="gray")
    fig.add_annotation(x=row['Year'], y=max(trend_df['sighting_count']), text=row['Aircraft'], showarrow=False)

fig.update_layout(template="plotly_dark", hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig, use_container_width=True)

# 3. THE US MAP (With Date Slider logic)
st.subheader(f"Geographic Distribution: {year_range[0]} - {year_range[1]}")

if selected_shapes:
    # Use tuple for SQL IN clause
    placeholders = ', '.join(['?'] * len(selected_shapes))
    map_query = f"""
        SELECT latitude as lat, longitude as lon, year, refined_shape 
        FROM sightings 
        WHERE country = 'us' 
        AND refined_shape IN ({placeholders})
        AND year BETWEEN ? AND ?
    """
    query_params = list(selected_shapes) + [year_range[0], year_range[1]]
    map_df = get_data(map_query, params=query_params)
    
    # Using st.map for a clean view, or st.pydeck_chart if you want a true "Heatmap"
    st.map(map_df)
    st.write(f"Showing **{len(map_df)}** verified high-speed anomalies.")
else:
    st.warning("Select shapes in the sidebar to populate the map.")
