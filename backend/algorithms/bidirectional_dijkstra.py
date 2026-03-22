import networkx as nx

def run_bidirectional_dijkstra(G, source, target, weight='weight', heuristic=None):
    length, path = nx.bidirectional_dijkstra(G, source, target, weight=weight)
    return path
