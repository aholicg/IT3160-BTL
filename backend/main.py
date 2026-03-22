from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
import pandas as pd
from typing import List, Optional
import math
from algorithms import run_dijkstra, run_astar, run_ucs, run_dls, run_ids, run_bidirectional_dijkstra

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Load data
stations_df = pd.read_csv('../stations_sh.csv')
lines_df = pd.read_csv('../lines_sh.csv')
G = nx.read_gml('../PrimalGraph_sh_2020.gml')
is_multigraph = G.is_multigraph()

# Pre-process stations to easily map name to multiple platforms
station_name_to_id = {}
for idx, row in stations_df.iterrows():
    station_name_to_id[row['stationname']] = int(row['stationid'])

# Prepare graph view (for returning the entire graph to draw)
graph_nodes = []
# Ensure every node in the graph has a lat/lng for drawing
node_lat_lng = {}
for node in G.nodes():
    parts = node.split('-')
    if len(parts) == 2:
        station_id = int(parts[1])
        row = stations_df[stations_df['stationid'] == station_id]
        if not row.empty:
            lat, lng = row.iloc[0]['lat'], row.iloc[0]['lng']
            name = row.iloc[0]['stationname']
            node_lat_lng[node] = (lat, lng, name)
            graph_nodes.append({
                'id': node,
                'station_id': station_id,
                'name': name,
                'lat': lat,
                'lng': lng,
                'line_id': int(parts[0])
            })

graph_edges = []
for u, v, data in G.edges(data=True):
    graph_edges.append({
        'source': u,
        'target': v,
        'nid': data.get('nid'),
        'distance': data.get('distance'),
        'duration': data.get('duration')
    })

class Edge(BaseModel):
    source: str
    target: str

class Coordinate(BaseModel):
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start_station: Optional[str] = None
    start_coord: Optional[Coordinate] = None
    end_station: Optional[str] = None
    end_coord: Optional[Coordinate] = None
    metric: str # 'distance', 'duration', 'transfers'
    algorithm: Optional[str] = "dijkstra" # 'dijkstra', 'astar', 'ucs', 'dls', 'ids', 'bidirectional'
    excluded_lines: List[int] = []
    excluded_edges: List[Edge] = []

@app.get("/stations")
def get_stations():
    result = []
    for idx, row in stations_df.iterrows():
        result.append({
            'stationid': row['stationid'],
            'stationname': row['stationname'],
            'lat': row['lat'],
            'lng': row['lng']
        })
    # Sort alphabetically by name
    result.sort(key=lambda x: x['stationname'])
    return result

@app.get("/lines")
def get_lines():
    result = []
    for idx, row in lines_df.iterrows():
        result.append({
            'lineid': row['lineid'],
            'linename': row['linename'],
            'fullnames': row['fullnames']
        })
    return result

@app.get("/graph")
def get_graph():
    return {
        'nodes': graph_nodes,
        'edges': graph_edges
    }

@app.post("/route")
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

    if not req.end_station and not req.end_coord:
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
        end_id = station_name_to_id[req.end_station]

    # Create a subgraph filtering out excluded lines and edges
    excluded_set = set(req.excluded_lines)

    # Store excluded edges in both directions since the graph is effectively undirected for travel
    # (even if directed, an excluded segment typically implies both ways)
    excluded_edges_set = set()
    for e in req.excluded_edges:
        excluded_edges_set.add((e.source, e.target))
        excluded_edges_set.add((e.target, e.source))

    if is_multigraph:
        H = nx.MultiDiGraph() if G.is_directed() else nx.MultiGraph()
    else:
        H = nx.DiGraph() if G.is_directed() else nx.Graph()

    for n, d in G.nodes(data=True):
        H.add_node(n, **d)

    if is_multigraph:
        for u, v, k, d in G.edges(keys=True, data=True):
            nid = d.get('nid', 0)
            if nid in excluded_set and nid != 0:
                continue
            if (u, v) in excluded_edges_set:
                continue
            dist = d.get('distance', 1.0)
            dur = d.get('duration', 1.0)
            if req.metric == 'distance':
                weight = dist
            elif req.metric == 'duration':
                weight = dur if nid != 0 else max(dur, 180.0)
            elif req.metric == 'transfers':
                weight = 1000.0 if nid == 0 else 1.0
            else:
                weight = dist
            new_d = d.copy()
            new_d['weight'] = weight
            H.add_edge(u, v, key=k, **new_d)
    else:
        for u, v, d in G.edges(data=True):
            nid = d.get('nid', 0)
            if nid in excluded_set and nid != 0:
                continue
            if (u, v) in excluded_edges_set:
                continue
            dist = d.get('distance', 1.0)
            dur = d.get('duration', 1.0)
            if req.metric == 'distance':
                weight = dist
            elif req.metric == 'duration':
                weight = dur if nid != 0 else max(dur, 180.0)
            elif req.metric == 'transfers':
                weight = 1000.0 if nid == 0 else 1.0
            else:
                weight = dist
            new_d = d.copy()
            new_d['weight'] = weight
            H.add_edge(u, v, **new_d)

    # Add virtual start node
    H.add_node('START')
    start_platforms = [n for n in H.nodes() if n != 'START' and n != 'END' and int(str(n).split('-')[1]) == start_id]
    if not start_platforms:
        raise HTTPException(status_code=400, detail="Start station is disconnected or excluded")
    for sp in start_platforms:
        H.add_edge('START', sp, weight=0.0, distance=0.0, duration=0.0, nid=0)

    # Add virtual end node
    H.add_node('END')
    end_platforms = [n for n in H.nodes() if n != 'START' and n != 'END' and int(str(n).split('-')[1]) == end_id]
    if not end_platforms:
        raise HTTPException(status_code=400, detail="End station is disconnected or excluded")
    for ep in end_platforms:
        H.add_edge(ep, 'END', weight=0.0, distance=0.0, duration=0.0, nid=0)

    try:
        algo = req.algorithm.lower() if req.algorithm else "dijkstra"

        # A* needs a heuristic. Since nodes are lat/lng, we can define one.
        # Virtual START/END nodes don't have lat/lng directly in node_lat_lng,
        # but they are very close to their connected platforms.
        # We'll just define a simple heuristic that returns 0 for virtual nodes.
        def heuristic(u, v):
            if u in ('START', 'END') or v in ('START', 'END'):
                return 0.0
            lat1, lng1, _ = node_lat_lng.get(u, (0, 0, ''))
            lat2, lng2, _ = node_lat_lng.get(v, (0, 0, ''))
            # Calculate haversine distance
            return haversine(lat1, lng1, lat2, lng2)

        if algo == "astar":
            path = run_astar(H, 'START', 'END', weight='weight', heuristic=heuristic)
        elif algo == "ucs":
            path = run_ucs(H, 'START', 'END', weight='weight')
        elif algo == "dls":
            path = run_dls(H, 'START', 'END', weight='weight', limit=50)
        elif algo == "ids":
            path = run_ids(H, 'START', 'END', weight='weight', max_depth=100)
        elif algo == "bidirectional":
            path = run_bidirectional_dijkstra(H, 'START', 'END', weight='weight')
        else: # default to dijkstra
            path = run_dijkstra(H, 'START', 'END', weight='weight')

        # Remove START and END
        path = path[1:-1]

        # Build route result
        route_nodes = []
        for n in path:
            lat, lng, name = node_lat_lng[n]
            parts = n.split('-')
            route_nodes.append({
                'id': n,
                'name': name,
                'lat': lat,
                'lng': lng,
                'line_id': int(parts[0])
            })

        return {
            "start_station_used": actual_start_station,
            "end_station_used": actual_end_station,
            "path": route_nodes,
        }
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=400, detail="No path found between these stations with the given filters.")
