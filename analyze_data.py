import json
from geopy.geocoders import Nominatim

"""
data_entry =
{   
    "TID":
    "tournamentName":
    "startDate"
    "lat": 
    "lon":
    "city":
    "state":
    "location":
    "averageElo":
    "modeElo":
    "topElo":
    "commanders":
    "player":
    "wins":
    "draws":
    "losses":
    "standing":
}
"""

def strip_data(data):

    geolocator = Nominatim(user_agent="Geopy Library")
    
    tournament_rows = []
    player_rows = []

    for tournament in data:
        copy_keys = ["TID", "tournamentName", "startDate", "averageElo", "modeElo", "topElo"]
        
        tourney_dict = {}
        #print(type(tournament))
        #print(tournament.keys())
        try:
            if tournament['eventData'] == {}:
                continue # We want to ignore events where we cannot get location data
        except:
            continue

        for key in copy_keys:
            try:
                tourney_dict[key] = tournament[key] # set of known keys on top level
            except:
                tourney_dict[key] = None

        for k in tournament['eventData']:
            if k == "headerImage":
                continue
            tourney_dict[k] = tournament['eventData'][k]
        
        if 'lat' not in tourney_dict.keys():
            try: # There is likely to be some undefined behavior here, but I have yet to see it.
                location = geolocator.geocode(tourney_dict['location'])
                tourney_dict['lat'] = location.latitude
                tourney_dict['lng'] = location.longitude
            except Exception as e:
                continue

        tournament_rows.append(tourney_dict)
        #print(tourney_dict)

        for player in tournament['standings']:
            player_dict = {} # Second level --> actaully goes to database 

            carry_over_keys = ["TID", "startDate", "lat", "lng"]

            for k in carry_over_keys:
                player_dict[k] = tourney_dict[k]
            try:
                player_dict["player"] = player["name"]
                player_dict["wins"] = player["wins"]
                player_dict["draws"] = player["draws"]
                player_dict["losses"] = player["losses"]
                Commanders = list(player["deckObj"]["Commanders"].keys()) # Get the keys
                player_dict["commanders"] = Commanders # Might change how this is stored later

            except Exception as e:
                #print(e)
                continue # if the player is missing some part of the info skip
            #print(player_dict)
            player_rows.append(player_dict)
    
    return tournament_rows, player_rows

def construct_meta(data):
    #TODO Update for displaying the Win Loss Draw of each commander
    meta = {}
    for entry in data:
        if len(entry['commanders']) == 2:
            if entry['commanders'][0] < entry['commanders'][1]:
                commanders = (entry['commanders'][0], entry['commanders'][1])
            else:
                commanders = (entry['commanders'][1], entry['commanders'][0])
            commanders = " -- ".join(commanders)
        else:
            commanders = entry['commanders'][0]
        
        if commanders in meta.keys():
            meta[commanders] = meta[commanders] + 1
        else:
            meta[commanders] = 0
    
    return meta

def meta_to_percent(meta):
    total = 0
    for com in meta:
        total += meta[com]
    
    sorted_meta = []
    for com in meta:
        sorted_meta.append((com, meta[com] / total))
    
    sorted_meta.sort(key=lambda x: x[1], reverse=True)
    return sorted_meta

if __name__ == "__main__":
    with open("output_tournament_data.json", 'r') as file:
        data = json.load(file)

    data_out = strip_data(data)
    
    with open("output_stripped_data_tournament.json", "w") as f:
        json.dump(data_out[0], f, indent=4)

    with open("output_stripped_data_entries.json", "w") as f:
        json.dump(data_out[1], f, indent=4)
