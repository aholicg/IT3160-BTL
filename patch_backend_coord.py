import re

with open("backend/main.py", "r") as f:
    code = f.read()

# Add math for haversine
search_import = """import pandas as pd
from typing import List, Optional"""
replace_import = """import pandas as pd
from typing import List, Optional
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
"""
code = code.replace(search_import, replace_import)


# Replace RouteRequest
search_req = """class RouteRequest(BaseModel):
    start_station: str
    end_station: str
    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []
    excluded_edges: List[Edge] = []"""
replace_req = """class Edge(BaseModel):
    source: str
    target: str

class Coordinate(BaseModel):
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start_station: Optional[str] = None
    start_coord: Optional[Coordinate] = None
    end_station: str
    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []
    excluded_edges: List[Edge] = []"""
code = re.sub(r'class Edge\(BaseModel\).*?excluded_edges: List\[Edge\] = \[\]', replace_req, code, flags=re.DOTALL)


# Replace calculate_route logic for start_station
search_calc = """@app.post("/route")
def calculate_route(req: RouteRequest):
    if req.start_station not in station_name_to_id:
        raise HTTPException(status_code=400, detail="Invalid start station")
    if req.end_station not in station_name_to_id:
        raise HTTPException(status_code=400, detail="Invalid end station")

    start_id = station_name_to_id[req.start_station]
    end_id = station_name_to_id[req.end_station]"""

replace_calc = """@app.post("/route")
def calculate_route(req: RouteRequest):
    if not req.start_station and not req.start_coord:
        raise HTTPException(status_code=400, detail="Must provide start_station or start_coord")

    start_id = None
    actual_start_station = req.start_station

    if req.start_coord:
        # Find nearest station
        min_dist = float('inf')
        nearest_station_id = None
        nearest_station_name = None
        for idx, row in stations_df.iterrows():
            dist = haversine(req.start_coord.lat, req.start_coord.lng, row['lat'], row['lng'])
            if dist < min_dist:
                min_dist = dist
                nearest_station_id = int(row['stationid'])
                nearest_station_name = row['stationname']

        if nearest_station_id is None:
            raise HTTPException(status_code=400, detail="No stations found")
        start_id = nearest_station_id
        actual_start_station = nearest_station_name
    else:
        if req.start_station not in station_name_to_id:
            raise HTTPException(status_code=400, detail="Invalid start station")
        start_id = station_name_to_id[req.start_station]

    if req.end_station not in station_name_to_id:
        raise HTTPException(status_code=400, detail="Invalid end station")

    end_id = station_name_to_id[req.end_station]"""

code = code.replace(search_calc, replace_calc)

# Add start_station_name to response
search_res = """        return {
            "path": route_nodes,
        }"""
replace_res = """        return {
            "start_station_used": actual_start_station,
            "path": route_nodes,
        }"""
code = code.replace(search_res, replace_res)

with open("backend/main.py", "w") as f:
    f.write(code)
