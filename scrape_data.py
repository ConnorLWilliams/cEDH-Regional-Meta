import os
import requests
from dotenv import load_dotenv
import json

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
    
    return r.json()

if __name__ == "__main__":
    filename = "output_tournament_data.json"
    r = scrape_data(5, 15)
    with open(filename, 'w') as f:
        json.dump(r, f, indent=4)
