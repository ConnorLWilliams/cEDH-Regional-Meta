import streamlit as st
from datetime import datetime, timezone
import json
from analyze_data import strip_data, construct_meta, meta_to_percent
from scrape_data import scrape_data
from supabase_connections import init_supabase, get_entries_within_radius, get_entries_from_TID
from geopy.geocoders import Nominatim
import sql_queries
import folium
from folium import Popup, Icon
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px

supabase = init_supabase()
geolocator = Nominatim(user_agent="Geopy Library")

st.set_page_config(layout="wide")
if "selected_tourney" not in st.session_state:
    st.session_state.selected_tourney = None
st.title('Regional cEDH Meta from TopDeck Data')

address_input, date_range_input, radius_input = st.columns(3, vertical_alignment="top")

address = address_input.text_input("Enter an Address", "Tulsa, Oklahoma")
#st.write("Current Location: ", address)


min_resp = supabase.rpc("exec_sql", {"query": sql_queries.GET_MIN_DATE}).execute()
max_resp = supabase.rpc("exec_sql", {"query": sql_queries.GET_MAX_DATE}).execute()

min_date = datetime.fromtimestamp(min_resp.data, tz=timezone.utc)
max_date = datetime.fromtimestamp(max_resp.data, tz=timezone.utc)
initial_selection = (min_date, max_date)

# Create the datetime slider
selected_start_date, selected_end_date = date_range_input.slider(
    "Select a Date Range",
    min_value=min_date,
    max_value=max_date,
    value=initial_selection
)
#st.write("Current Date Range: ", selected_start_date, selected_end_date)

radius = radius_input.number_input("Insert a Radius", value = 100)
#st.write("Current Radius: ", radius)

location = geolocator.geocode(address)

center_lat = location.latitude
center_lon = location.longitude

# Get Regional Meta
region_data = get_entries_within_radius(supabase, center_lat, center_lon, radius) 

meta = construct_meta(region_data)
sorted_meta = meta_to_percent(meta)


reg_col, reg_pie_chart = st.columns([1, 2])

# -- Regional Meta --
with reg_col:
    st.header("Regional Meta")
    sorted_regional_df = pd.DataFrame(sorted_meta, columns=["Commander", "Percent"])
    st.dataframe(sorted_regional_df, use_container_width=True)
    fig = px.pie(sorted_regional_df, names="Commander", values="Percent", title="Regional Meta Pie Chart")

with reg_pie_chart:
    st.plotly_chart(fig, use_container_width=True)

map_col, tour_col = st.columns([2, 1])

# -- Map --
with map_col:
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

    for row in region_data:
        popup = Popup(html=str(row["TID"]), max_width="auto")
        folium.Marker(
            [row['lat'], row['lng']],
            tooltip=row['TID'],
            popup=popup,
            icon=Icon()
        ).add_to(m)
    
    radius_meters = radius * 1609.34

    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_meters,
        color="red",
        fill=False,
        weight=2
    ).add_to(m)

    map_state = st_folium(m, height = 500, width = "100%", key="map")

    if map_state and map_state.get("last_object_clicked_popup"):
        st.session_state.selected_tourney = map_state["last_object_clicked_popup"]

with tour_col:
    st.header("Tournament Breakdown")

    if st.session_state.selected_tourney is None:
        st.info("<- Click a marker to view tournament meta")
    else:
        tourney_data = get_entries_from_TID(supabase, st.session_state.selected_tourney)
        tourney_meta = construct_meta(tourney_data)
        tourney_sorted_meta = meta_to_percent(tourney_meta)
        sorted_tourney_df = pd.DataFrame(tourney_sorted_meta, columns=["Commander", "Percent"])
        st.dataframe(sorted_tourney_df, use_container_width=True)
