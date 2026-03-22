import networkx as nx
from .dls import dls_recursive

def run_ids(G, source, target, weight='weight', heuristic=None, max_depth=100):
    # Iterative Deepening Search
    for depth in range(1, max_depth + 1):
        path = dls_recursive(G, source, target, depth, [source])
        if path is not None:
            return path
    raise nx.NetworkXNoPath(f"No path found from {source} to {target} within max depth {max_depth}")
