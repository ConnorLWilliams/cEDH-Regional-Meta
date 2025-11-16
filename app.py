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

# I had Claude help to rewrite this part of the front end to add caching to make the UI Experience better

supabase = init_supabase()
geolocator = Nominatim(user_agent="Geopy Library", timeout=10)
st.set_page_config(layout="wide")

if "selected_tourney" not in st.session_state:
    st.session_state.selected_tourney = None

# Track previous map parameters to detect changes
if "prev_map_params" not in st.session_state:
    st.session_state.prev_map_params = None

url = "https://topdeck.gg"
st.title('Regional cEDH Meta from [TopDeck](%s) Data' % url)

# CACHE GEOCODING
@st.cache_data(ttl=3600)  # Cache for 1 hour
def geocode_address(address):
    location = geolocator.geocode(address)
    return location.latitude, location.longitude

# CACHE DATABASE QUERIES
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_date_range(_supabase):
    min_resp = _supabase.rpc("exec_sql", {"query": sql_queries.GET_MIN_DATE}).execute()
    max_resp = _supabase.rpc("exec_sql", {"query": sql_queries.GET_MAX_DATE}).execute()
    min_date = datetime.fromtimestamp(min_resp.data, tz=timezone.utc)
    max_date = datetime.fromtimestamp(max_resp.data, tz=timezone.utc)
    return min_date, max_date

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_regional_data(_supabase, center_lat, center_lon, radius, start_ts, end_ts):
    return get_entries_within_radius(_supabase, center_lat, center_lon, radius, start_ts, end_ts)

address_input, date_range_input, radius_input = st.columns(3, vertical_alignment="top")
address = address_input.text_input("Enter an Address", "Tulsa, Oklahoma")

min_date, max_date = get_date_range(supabase)
initial_selection = (min_date, max_date)

selected_start_date, selected_end_date = date_range_input.slider(
    "Select a Date Range",
    min_value=min_date,
    max_value=max_date,
    value=initial_selection
)

radius = radius_input.number_input("Insert a Radius", value=100)

# Get cached location
center_lat, center_lon = geocode_address(address)

# Get Regional Meta with caching
region_data = get_cached_regional_data(
    supabase, center_lat, center_lon, radius, 
    int(selected_start_date.timestamp()), 
    int(selected_end_date.timestamp())
)

#st.write(f"DEBUG: Radius: {radius} miles")
#st.write(f"DEBUG: Total entries returned: {len(region_data)}")
#st.write(f"DEBUG: Center coordinates: ({center_lat}, {center_lon})")

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
    # Extract unique tournaments from entries
    unique_tournaments = {}
    for row in region_data:
        tid = row['TID']
        if tid not in unique_tournaments:
            unique_tournaments[tid] = {
                'TID': tid,
                'lat': row['lat'],
                'lng': row['lng']
            }
    
    unique_tournament_list = list(unique_tournaments.values())
    
    #st.write(f"DEBUG: Unique tournaments: {len(unique_tournaments)}")
    #st.write(f"DEBUG: Tournament IDs: {sorted(list(unique_tournaments.keys()))}")

    # Create parameters tuple to detect changes
    current_map_params = (
        center_lat, center_lon, radius,
        selected_start_date, selected_end_date,
        len(unique_tournament_list)
    )
    
    # Only recreate map if parameters changed
    map_changed = current_map_params != st.session_state.prev_map_params
    
    # Create the map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    
    # Add markers for unique tournaments only
    for tournament in unique_tournament_list:
        popup = Popup(html=str(tournament["TID"]), max_width="auto")
        folium.Marker(
            [tournament['lat'], tournament['lng']],
            tooltip=tournament['TID'],
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
    
    # Use a dynamic key that changes only when map parameters change
    if map_changed:
        st.session_state.prev_map_params = current_map_params
        map_key = f"map_{hash(current_map_params)}"
    else:
        map_key = f"map_{hash(st.session_state.prev_map_params)}"
    
    # Display tournament count
    st.caption(f"Showing {len(unique_tournament_list)} tournaments")
    
    # Render the map
    map_state = st_folium(m, height=500, width="100%", key=map_key)
    
    # Handle marker clicks - only update if actually changed
    if map_state:
        clicked = map_state.get("last_object_clicked_popup")
        if clicked and clicked != st.session_state.selected_tourney:
            st.session_state.selected_tourney = clicked
            st.rerun()

with tour_col:
    if st.session_state.selected_tourney is None:
        st.info("<- Click a marker to view tournament meta")
    else:
        st.subheader(st.session_state.selected_tourney)
        tourney_data = get_entries_from_TID(supabase, st.session_state.selected_tourney)
        tourney_meta = construct_meta(tourney_data)
        tourney_sorted_meta = meta_to_percent(tourney_meta)
        sorted_tourney_df = pd.DataFrame(tourney_sorted_meta, columns=["Commander", "Percent"])
        st.dataframe(sorted_tourney_df, use_container_width=True)
