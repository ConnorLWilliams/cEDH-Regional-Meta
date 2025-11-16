import os
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone 
import json
from analyze_data import strip_data, construct_meta
from scrape_data import scrape_data, chunk_time_range, scrape_by_dates
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

def get_entries_within_radius(supabase, lat, lng, miles, start_date, end_date):
     
    response = supabase.rpc(
        "entries_within_radius",
        {
            "center_lng": lng,
            "center_lat": lat,
            "radius_miles": miles,
            "min_start_date": start_date,
            "max_start_date": end_date
        }
    ).limit(10000).execute()

    return response.data

def get_entries_from_TID(supabase, TID):

    response = supabase.rpc("get_entries_by_tid", {
        "tid": TID
    }).execute()

    return response.data

def supabase_scrape_by_date(supabase, start_date, end_date):
    chunks = chunk_time_range(start_date, end_date)

    for chunk in chunks:
        scraped = scrape_by_dates(chunk[0], chunk[1])
        stripped_tourneys, stripped_entries = strip_data(scraped)
        #print(stripped_tourneys)
        #print(stripped_entries)
        if stripped_tourneys and stripped_entries:
            update_db(supabase, stripped_tourneys, stripped_entries)
            print(f"updated Dates {datetime.fromtimestamp(chunk[0])} to {datetime.fromtimestamp(chunk[1])}")
        else:
            print(f"Skipping Dates {datetime.fromtimestamp(chunk[0])} to {datetime.fromtimestamp(chunk[1])} Not Enough Data")

if __name__ == "__main__":
    load_dotenv() # Gets the keys to the SUPABASE
    
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    dt = datetime(2025, 5, 15, 1, 0, 0, tzinfo=timezone.utc)
    start_time = int(dt.timestamp())
    
    dt = datetime(2025, 11, 15, 1, 0, 0, tzinfo=timezone.utc)
    end_time = int(dt.timestamp())

    supabase_scrape_by_date(supabase, start_time, end_time)

    """
    scraped = scrape_data(90, 10)
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
    """
