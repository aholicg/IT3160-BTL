with open("backend/main.py", "r") as f:
    code = f.read()

# Replace RouteRequest
search = """class RouteRequest(BaseModel):
    start_station: str
    end_station: str
    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []"""
replace = """class Edge(BaseModel):
    source: str
    target: str

class RouteRequest(BaseModel):
    start_station: str
    end_station: str
    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []
    excluded_edges: List[Edge] = []"""
code = code.replace(search, replace)

# Replace calculate_route filtering logic
search2 = """    # Create a subgraph filtering out excluded lines
    excluded_set = set(req.excluded_lines)

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
                continue"""
replace2 = """    # Create a subgraph filtering out excluded lines and edges
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
                continue"""
code = code.replace(search2, replace2)

search3 = """    else:
        for u, v, d in G.edges(data=True):
            nid = d.get('nid', 0)
            if nid in excluded_set and nid != 0:
                continue"""
replace3 = """    else:
        for u, v, d in G.edges(data=True):
            nid = d.get('nid', 0)
            if nid in excluded_set and nid != 0:
                continue
            if (u, v) in excluded_edges_set:
                continue"""
code = code.replace(search3, replace3)

with open("backend/main.py", "w") as f:
    f.write(code)
