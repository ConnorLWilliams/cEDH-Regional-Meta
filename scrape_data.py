import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta, timezone
import time

def chunk_time_range(start_ts: int, end_ts: int, chunk_days: int = 15):   
    start = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    chunk_size = timedelta(days=chunk_days)

    chunks = []
    current = start

    while current < end:
        chunk_end = min(current + chunk_size, end)
        chunks.append((int(current.timestamp()), int(chunk_end.timestamp())))
        current = chunk_end

    return chunks

def scrape_data(last, part_min):

    load_dotenv()

    api_key = os.getenv("API_KEY")

    payload = {
        "last": last,
        "columns": ["name", "decklist", "wins", "draws", "losses"],
        "rounds": "true",
        "tables": ["table", "players", "winner", "status"],
        "players": ["name", "id", "decklist"],
        "game": "Magic: The Gathering",
        "format": "EDH",
        "participantMin": part_min
    }

    headers = {
        "Authorization": api_key
    }

    r = requests.post('https://topdeck.gg/api/v2/tournaments', json=payload, headers = headers)

    if r.status_code != 200:
        print(f"Request failed with status {r.status_code}")
    print(r.text)
    return None
    
    if not r.text.strip():
        print("Empty response from API")
        return None
    
    return r.json()

def scrape_by_dates(start, end, part_min = 10):
    load_dotenv()

    api_key = os.getenv("API_KEY")
    
    chunks = chunk_time_range(start, end)
    
    to_return = []

    for chunk in chunks:
        payload = {
            "start": chunk[0],
            "end": chunk[1],
            "columns": ["name", "decklist", "wins", "draws", "losses"],
            "rounds": "true",
            "tables": ["table", "players", "winner", "status"],
            "players": ["name", "id", "decklist"],
            "game": "Magic: The Gathering",
            "format": "EDH",
            "participantMin": part_min
        }

        headers = {
            "Authorization": api_key
        }

        r = requests.post('https://topdeck.gg/api/v2/tournaments', json=payload, headers = headers)

        if r.status_code != 200:
            print(f"Request failed with status {r.status_code}")
            print(r.text)
            #return None
    
        if not r.text.strip():
            print("Empty response from API")
            #return None
        
        to_return.extend(r.json())

        #print(to_return)

        time.sleep(60) #Time for API call to reset


    return to_return

if __name__ == "__main__":
    dt = datetime(2025, 5, 15, 1, 0, 0, tzinfo=timezone.utc)
    start_time = int(dt.timestamp())
    
    dt = datetime(2025, 11, 15, 1, 0, 0, tzinfo=timezone.utc)
    end_time = int(dt.timestamp())

    data = scrape_by_dates(start_time, end_time)
    
    print(data)
    #filename = "output_tournament_data.json"
    #r = scrape_data(5, 15)
    #with open(filename, 'w') as f:
    #    json.dump(r, f, indent=4)


