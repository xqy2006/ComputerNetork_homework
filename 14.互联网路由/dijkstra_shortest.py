from __future__ import annotations

import heapq
from collections import defaultdict


def shortest_path(edges: list[tuple[str, str, int]], start: str, goal: str) -> tuple[int, list[str]]:
    graph: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for src, dst, weight in edges:
        graph[src].append((dst, weight))
        graph[dst].append((src, weight))

    pq: list[tuple[int, str]] = [(0, start)]
    dist = {start: 0}
    prev: dict[str, str | None] = {start: None}

    while pq:
        current_dist, node = heapq.heappop(pq)
        if node == goal:
            break
        if current_dist != dist[node]:
            continue
        for neighbor, weight in graph[node]:
            cand = current_dist + weight
            if cand < dist.get(neighbor, 1 << 60):
                dist[neighbor] = cand
                prev[neighbor] = node
                heapq.heappush(pq, (cand, neighbor))

    if goal not in dist:
        raise ValueError("goal unreachable")

    path = []
    node: str | None = goal
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return dist[goal], path


if __name__ == "__main__":
    edges = [
        ("r1", "r2", 2),
        ("r1", "r3", 5),
        ("r2", "r3", 1),
        ("r2", "r4", 4),
        ("r3", "r4", 1),
    ]
    distance, path = shortest_path(edges, "r1", "r4")
    print("distance:", distance)
    print("path:", " -> ".join(path))
