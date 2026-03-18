import networkx as nx
import pandas as pd

stations = pd.read_csv('stations_sh.csv')
print(stations.head())

G = nx.read_gml('PrimalGraph_sh_2020.gml')
print(list(G.nodes(data=True))[:5])
print(list(G.edges(data=True))[:5])
