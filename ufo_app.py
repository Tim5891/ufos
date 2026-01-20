import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title="UFO Anomaly Dashboard", layout="wide")

# Database Connection (Cached for performance)
def get_data(query):
    # check_same_thread=False is necessary for Streamlit's threading
    conn = sqlite3.connect('ufo_analytics.db', check_same_thread=False)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🛸 UFO Anomaly & Cultural Correlation")
st.markdown("Exploring the link between military tech, movie quality, and high-speed sightings.")

# 1. SIDEBAR FILTERS
st.sidebar.header("Data Controls")
shape_list = get_data("SELECT DISTINCT refined_shape FROM sightings")['refined_shape'].tolist()
selected_shapes = st.sidebar.multiselect("Select Shapes", shape_list, default=['triangle', 'disk'])

# 2. THE CORRELATION CHART
st.subheader("The Trinity Correlation")
trend_df = get_data("SELECT * FROM movie_quality")
mil_df = get_data("SELECT * FROM military_tech")

fig = go.Figure()

# Add Sightings
fig.add_trace(go.Scatter(x=trend_df['Year'], y=trend_df['sighting_count'], 
                         name="UFO Sightings", line=dict(color='crimson', width=3)))

# Add Movie Quality (Normalized/Scaled)
fig.add_trace(go.Scatter(x=trend_df['Year'], y=trend_df['imdb_rating'] * 500, 
                         name="Movie Quality Pulse", line=dict(color='teal', dash='dot')))

# Overlay Military Reveals
for _, row in mil_df.iterrows():
    fig.add_vline(x=row['Year'], line_width=1, line_dash="dash", line_color="gray")
    fig.add_annotation(x=row['Year'], y=max(trend_df['sighting_count']), text=row['Aircraft'], showarrow=False)

fig.update_layout(template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# 3. GEOGRAPHIC MAP
st.subheader("Anomaly Mapping")
# Filtered query for the map
if selected_shapes:
    shape_str = "('" + "','".join(selected_shapes) + "')"
    map_query = f"SELECT latitude as lat, longitude as lon FROM sightings WHERE refined_shape IN {shape_str}"
    map_df = get_data(map_query)
    st.map(map_df)
else:
    st.warning("Please select at least one shape to view the map.")
