import networkx as nx

def dls_recursive(G, node, target, limit, path):
    if node == target:
        return path
    if limit <= 0:
        return None

    for neighbor in G.neighbors(node):
        if neighbor not in path: # Avoid cycles in the current path
            result = dls_recursive(G, neighbor, target, limit - 1, path + [neighbor])
            if result is not None:
                return result
    return None

def run_dls(G, source, target, weight='weight', heuristic=None, limit=50):
    # Depth-Limited Search does not guarantee the *shortest* path by cost,
    # just a path within the depth limit. It ignores edge weights.
    path = dls_recursive(G, source, target, limit, [source])
    if path is None:
         raise nx.NetworkXNoPath(f"No path found from {source} to {target} within depth limit {limit}")
    return path
