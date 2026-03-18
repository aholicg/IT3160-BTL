import pandas as pd
import networkx as nx
import collections

stations = pd.read_csv('stations_sh.csv')
G = nx.read_gml('PrimalGraph_sh_2020.gml')

# Let's understand mapping from line ID to line Name
line_id_to_name = {}
for idx, row in stations.iterrows():
    lineids_str = str(row['lineids'])
    linenames_str = str(row['linenames'])

    # Simple parse
    ids = lineids_str.strip('"{').strip('}"').split(',')
    names_raw = linenames_str.strip('"{').strip('}"').split(',')

    # Handle quotes inside names
    names = [n.strip('"\' ') for n in names_raw]

    for i, i_str in enumerate(ids):
        i_str = i_str.strip()
        if i_str:
            i_val = int(i_str)
            if i < len(names):
                line_id_to_name[i_val] = names[i]

for i in sorted(line_id_to_name.keys()):
    print(f"{i}: {line_id_to_name[i]}")

# Are there multiple stations with the same name?
name_counts = collections.Counter(stations['stationname'])
duplicates = {k: v for k, v in name_counts.items() if v > 1}
print(f"\nDuplicate station names: {duplicates}")
