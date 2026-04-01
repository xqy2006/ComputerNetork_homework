from rip_update import RouteEntry, update_rip_table


def main() -> None:
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
    updated = {entry.network: entry for entry in update_rip_table(local_table, received_table, "R2")}
    assert updated["N2"].hops == 0
    assert updated["N3"].hops == 4
    assert updated["N3"].next_hop == "R2"
    assert updated["N4"].hops == 8
    assert updated["N5"].hops == 4
    assert updated["N5"].next_hop == "R2"
    print("All RIP update tests passed.")


if __name__ == "__main__":
    main()
