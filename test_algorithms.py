import requests

payload = {
    "start_station": "PEOPLE'S SQUARE",
    "end_station": "XUJIAHUI",
    "metric": "duration",
    "excluded_lines": [],
    "excluded_edges": []
}

algorithms = ["dijkstra", "astar", "ucs", "bidirectional", "dls", "ids"]

for algo in algorithms:
    p = payload.copy()
    p["algorithm"] = algo
    print(f"Testing {algo}...")
    res = requests.post("http://localhost:8000/route", json=p)
    if res.status_code == 200:
        path = res.json()["path"]
        print(f"  Success! Stops: {len(path)}. Start: {path[0]['name']} End: {path[-1]['name']}")
    else:
        print(f"  Error: {res.text}")
