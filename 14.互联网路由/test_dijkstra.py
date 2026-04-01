from dijkstra_shortest import shortest_path


def main() -> None:
    edges = [
        ("r1", "r2", 2),
        ("r1", "r3", 5),
        ("r2", "r3", 1),
        ("r2", "r4", 4),
        ("r3", "r4", 1),
    ]
    distance, path = shortest_path(edges, "r1", "r4")
    assert distance == 4
    assert path == ["r1", "r2", "r3", "r4"]
    print("All Dijkstra tests passed.")


if __name__ == "__main__":
    main()
