import networkx as nx

def run_dijkstra(G, source, target, weight='weight', heuristic=None):
    return nx.dijkstra_path(G, source, target, weight=weight)
