import networkx as nx
import heapq

def run_ucs(G, source, target, weight='weight', heuristic=None):
    queue = [(0, source, [source])]
    seen = set()

    while queue:
        (cost, node, path) = heapq.heappop(queue)

        if node == target:
            return path

        if node in seen:
            continue

        seen.add(node)

        for neighbor, data in G[node].items():
            if neighbor not in seen:
                if isinstance(data, dict) and 'weight' not in data and len(data) > 0 and 0 in data:
                    min_weight = min(d.get(weight, 1.0) for d in data.values())
                else:
                    min_weight = data.get(weight, 1.0)
                heapq.heappush(queue, (cost + min_weight, neighbor, path + [neighbor]))

    raise nx.NetworkXNoPath(f"No path found from {source} to {target}")
