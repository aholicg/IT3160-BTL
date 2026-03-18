import pandas as pd
import networkx as nx

stations = pd.read_csv('stations_sh.csv')
lines = pd.read_csv('lines_sh.csv')
G = nx.read_gml('PrimalGraph_sh_2020.gml')

# 1. Do line IDs in lines_sh.csv match line IDs in stations_sh.csv?
lines_ids = set(lines['lineid'])
stations_line_ids = set()
for lineids in stations['lineids']:
    if '{' in lineids:
        ids = lineids.strip('{}').split(',')
        for i in ids:
            if i.strip():
                stations_line_ids.add(int(i.strip()))
    else:
        stations_line_ids.add(int(lineids))

print(f"Line IDs in lines_sh.csv not in stations_sh.csv: {lines_ids - stations_line_ids}")
print(f"Line IDs in stations_sh.csv not in lines_sh.csv: {stations_line_ids - lines_ids}")

# 2. Are line names consistent?
inconsistencies = []
for idx, row in lines.iterrows():
    lineid = row['lineid']
    linename = row['linename']

    # Check stations with this line ID
    for s_idx, s_row in stations.iterrows():
        s_lineids = str(s_row['lineids'])
        s_linenames = str(s_row['linenames'])

        if '{' in s_lineids:
            ids = [int(i.strip()) for i in s_lineids.strip('{}').split(',') if i.strip()]
            names = [n.strip('"\' ') for n in s_linenames.strip('"{').strip('}"').split(',')]
        else:
            ids = [int(s_lineids)]
            names = [s_linenames.strip('"\' ')]

        if lineid in ids:
            name_idx = ids.index(lineid)
            if name_idx < len(names):
                if names[name_idx] != linename:
                    inconsistencies.append((lineid, linename, names[name_idx]))

if inconsistencies:
    print(f"Found name inconsistencies: {inconsistencies[:5]}")
else:
    print("Line names are perfectly consistent between lines_sh.csv and stations_sh.csv.")
