from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RouteEntry:
    network: str
    hops: int
    next_hop: str


def update_rip_table(local: list[RouteEntry], received: list[RouteEntry], neighbor: str) -> list[RouteEntry]:
    table = {entry.network: RouteEntry(entry.network, entry.hops, entry.next_hop) for entry in local}
    for entry in received:
        candidate_hops = min(16, entry.hops + 1)
        current = table.get(entry.network)
        if current is None or candidate_hops < current.hops or current.next_hop == neighbor:
            table[entry.network] = RouteEntry(entry.network, candidate_hops, neighbor)
    return [table[key] for key in sorted(table)]


if __name__ == "__main__":
    local_table = [
        RouteEntry("N1", 1, "R1"),
        RouteEntry("N2", 0, "direct"),
        RouteEntry("N3", 6, "R4"),
        RouteEntry("N4", 8, "R5"),
    ]
    received_table = [
        RouteEntry("N2", 2, "R5"),
        RouteEntry("N3", 3, "R6"),
        RouteEntry("N4", 7, "R7"),
        RouteEntry("N5", 3, "R8"),
    ]
    updated = update_rip_table(local_table, received_table, "R2")
    for entry in updated:
        print(f"{entry.network}: hops={entry.hops}, next_hop={entry.next_hop}")
