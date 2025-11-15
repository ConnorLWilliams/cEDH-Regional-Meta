import os
from supabase import create_client, Client
from datetime import datetime
import json
from analyze_data import strip_data, construct_meta
from scrape_data import scrape_data
from dotenv import load_dotenv
import sql_queries
import streamlit as st

@st.cache_resource
def init_supabase():
    # Used to get the supabase connection established in streamlit
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

def update_db(supabase, tourney_data, entry_data):
    supabase.table("tournaments").upsert(tourney_data).execute()
    supabase.table("entries").upsert(entry_data).execute()
    
    #supabase.rpc("sql", {"query": sql_queries.UPDATE_GEOM}).execute() --> moved to supabase

def get_entries_within_radius(supabase, lat, lng, miles):
    
    response = supabase.rpc(
        "entries_within_radius",
        {
            "center_lng": lng,
            "center_lat": lat,
            "radius_miles": miles
        }
    ).execute()

    return response.data

def get_entries_from_TID(supabase, TID):

    response = supabase.rpc("get_entries_by_tid", {
        "tid": TID
    }).execute()

    return response.data

if __name__ == "__main__":
    load_dotenv() # Gets the keys to the SUPABASE
    
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    scraped = scrape_data(30, 10)
    #print(type(scraped))
    stripped_tourneys, stripped_entries = strip_data(scraped)
    #print(type(stripped_tourneys))
    #print(type(stripped_entries))
    update_db(supabase, stripped_tourneys, stripped_entries)
    

    example_response = get_entries_within_radius(supabase, 36.061, -95.899, 200)
    #print(example_response)

    meta = construct_meta(example_response)
    
    total = 0
    for com in meta:
        total += meta[com]
    
    sorted_meta = []
    for com in meta:
        sorted_meta.append((com, meta[com] / total))
    
    sorted_meta.sort(key=lambda x: x[1])
    print(sorted_meta)
