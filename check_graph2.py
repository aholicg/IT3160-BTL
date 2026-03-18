import networkx as nx
import pandas as pd

stations = pd.read_csv('stations_sh.csv')

G = nx.read_gml('PrimalGraph_sh_2020.gml')

# Find missing stations?
node_ids = set()
for node in G.nodes():
    parts = node.split('-')
    if len(parts) == 2:
        station_id = int(parts[1])
        node_ids.add(station_id)

print(f"Total nodes in graph: {len(G.nodes())}")
print(f"Total unique station IDs in graph: {len(node_ids)}")
print(f"Total stations in CSV: {len(stations)}")

missing_in_graph = set(stations['stationid']) - node_ids
print(f"Missing in graph: {missing_in_graph}")

missing_in_csv = node_ids - set(stations['stationid'])
print(f"Missing in csv: {missing_in_csv}")

print("\nLines present in the graph edge nids:")
edge_nids = set(data.get('nid') for u, v, data in G.edges(data=True))
print(edge_nids)
