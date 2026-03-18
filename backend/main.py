from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
import pandas as pd
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class RouteRequest(BaseModel):
    start_station: str
    end_station: str
    metric: str # 'distance', 'duration', 'transfers'
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
    if req.start_station not in station_name_to_id:
        raise HTTPException(status_code=400, detail="Invalid start station")
    if req.end_station not in station_name_to_id:
        raise HTTPException(status_code=400, detail="Invalid end station")

    start_id = station_name_to_id[req.start_station]
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
    start_platforms = [n for n in H.nodes() if n != 'START' and n != 'END' and int(n.split('-')[1]) == start_id]
    if not start_platforms:
        raise HTTPException(status_code=400, detail="Start station is disconnected or excluded")
    for sp in start_platforms:
        H.add_edge('START', sp, weight=0.0, distance=0.0, duration=0.0, nid=0)

    # Add virtual end node
    H.add_node('END')
    end_platforms = [n for n in H.nodes() if n != 'START' and n != 'END' and int(n.split('-')[1]) == end_id]
    if not end_platforms:
        raise HTTPException(status_code=400, detail="End station is disconnected or excluded")
    for ep in end_platforms:
        H.add_edge(ep, 'END', weight=0.0, distance=0.0, duration=0.0, nid=0)

    try:
        path = nx.dijkstra_path(H, 'START', 'END', weight='weight')
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
            "path": route_nodes,
        }
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=400, detail="No path found between these stations with the given filters.")
