import re

with open("backend/main.py", "r") as f:
    code = f.read()

# Replace RouteRequest
search_req = """class RouteRequest(BaseModel):
    start_station: Optional[str] = None
    start_coord: Optional[Coordinate] = None
    end_station: str
    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []
    excluded_edges: List[Edge] = []"""
replace_req = """class RouteRequest(BaseModel):
    start_station: Optional[str] = None
    start_coord: Optional[Coordinate] = None
    end_station: Optional[str] = None
    end_coord: Optional[Coordinate] = None
    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []
    excluded_edges: List[Edge] = []"""
code = code.replace(search_req, replace_req)


# Replace calculate_route logic for end_station
search_calc = """    if req.end_station not in station_name_to_id:
        raise HTTPException(status_code=400, detail="Invalid end station")

    end_id = station_name_to_id[req.end_station]"""

replace_calc = """    if not req.end_station and not req.end_coord:
        raise HTTPException(status_code=400, detail="Must provide end_station or end_coord")

    end_id = None
    actual_end_station = req.end_station

    if req.end_coord:
        # Find nearest station
        min_dist = float('inf')
        nearest_station_id = None
        nearest_station_name = None
        for idx, row in stations_df.iterrows():
            dist = haversine(req.end_coord.lat, req.end_coord.lng, row['lat'], row['lng'])
            if dist < min_dist:
                min_dist = dist
                nearest_station_id = int(row['stationid'])
                nearest_station_name = row['stationname']

        if nearest_station_id is None:
            raise HTTPException(status_code=400, detail="No stations found")
        end_id = nearest_station_id
        actual_end_station = nearest_station_name
    else:
        if req.end_station not in station_name_to_id:
            raise HTTPException(status_code=400, detail="Invalid end station")
        end_id = station_name_to_id[req.end_station]"""

code = code.replace(search_calc, replace_calc)

# Add end_station_name to response
search_res = """        return {
            "start_station_used": actual_start_station,
            "path": route_nodes,
        }"""
replace_res = """        return {
            "start_station_used": actual_start_station,
            "end_station_used": actual_end_station,
            "path": route_nodes,
        }"""
code = code.replace(search_res, replace_res)

with open("backend/main.py", "w") as f:
    f.write(code)
