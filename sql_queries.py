
UPDATE_GEOM = """
update tournaments set geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326) where geom is null;
update entries set geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326) where geom is null;
"""

GET_MIN_DATE = "SELECT MIN(\"startDate\") FROM tournaments;"

GET_MAX_DATE = "SELECT MAX(\"startDate\") FROM tournaments;"
