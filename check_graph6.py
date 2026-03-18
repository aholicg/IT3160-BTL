import pandas as pd
import networkx as nx

stations = pd.read_csv('stations_sh.csv')
G = nx.read_gml('PrimalGraph_sh_2020.gml')

# What is line 19?
print(stations[stations['lineids'].str.contains('19')])
