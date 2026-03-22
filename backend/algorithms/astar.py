import networkx as nx

def run_astar(G, source, target, weight='weight', heuristic=None):
    return nx.astar_path(G, source, target, heuristic=heuristic, weight=weight)
