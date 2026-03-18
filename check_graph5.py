import pandas as pd
import networkx as nx

stations = pd.read_csv('stations_sh.csv')
G = nx.read_gml('PrimalGraph_sh_2020.gml')

# Nodes in G are strings like "1-28" (line_id-station_id)
# Let's check if all station_ids in the graph exist in the CSV, and vice versa.

graph_station_ids = set()
graph_line_ids = set()
for node in G.nodes():
    line_id, station_id = map(int, node.split('-'))
    graph_station_ids.add(station_id)
    graph_line_ids.add(line_id)

csv_station_ids = set(stations['stationid'])

# Any station in Graph but NOT in CSV?
print(f"Graph station IDs not in CSV: {graph_station_ids - csv_station_ids}")

# Any station in CSV but NOT in Graph?
print(f"CSV station IDs not in Graph: {csv_station_ids - graph_station_ids}")

# Do line IDs in the graph match line IDs in the CSV?
csv_line_ids = set()
for lineids in stations['lineids']:
    if '{' in lineids:
        ids = lineids.strip('{}').split(',')
        for i in ids:
            if i.strip():
                csv_line_ids.add(int(i.strip()))
    else:
        csv_line_ids.add(int(lineids))

print(f"Graph line IDs not in CSV: {graph_line_ids - csv_line_ids}")
print(f"CSV line IDs not in Graph: {csv_line_ids - graph_line_ids}")

# Are all nodes in graph consistent with the CSV's station's lines?
# i.e., if node "2-19" exists, does station 19 have line 2 in its lineids?
inconsistencies = []
for node in G.nodes():
    line_id, station_id = map(int, node.split('-'))
    station_row = stations[stations['stationid'] == station_id]
    if not station_row.empty:
        lineids_str = str(station_row.iloc[0]['lineids'])

        # parse lineids_str
        if '{' in lineids_str:
            ids = [int(i.strip()) for i in lineids_str.strip('{}').split(',') if i.strip()]
        else:
            ids = [int(lineids_str)]

        if line_id not in ids:
            inconsistencies.append((node, ids))

print(f"Inconsistencies between node line_id and CSV lineids: {len(inconsistencies)}")
if inconsistencies:
    print(inconsistencies[:10])
