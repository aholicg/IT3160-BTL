import re

with open("backend/main.py", "r") as f:
    code = f.read()

# Add import for algorithms
search_import = """from typing import List, Optional
import math"""
replace_import = """from typing import List, Optional
import math
from algorithms import run_dijkstra, run_astar, run_ucs, run_dls, run_ids, run_bidirectional_dijkstra"""
code = code.replace(search_import, replace_import)

# Update RouteRequest to accept algorithm
search_req = """    metric: str # 'distance', 'duration', 'transfers'
    excluded_lines: List[int] = []"""
replace_req = """    metric: str # 'distance', 'duration', 'transfers'
    algorithm: Optional[str] = "dijkstra" # 'dijkstra', 'astar', 'ucs', 'dls', 'ids', 'bidirectional'
    excluded_lines: List[int] = []"""
code = code.replace(search_req, replace_req)

# Update pathfinding logic
search_path = """    try:
        path = nx.dijkstra_path(H, 'START', 'END', weight='weight')
        # Remove START and END
        path = path[1:-1]"""
replace_path = """    try:
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
        path = path[1:-1]"""
code = code.replace(search_path, replace_path)

with open("backend/main.py", "w") as f:
    f.write(code)
