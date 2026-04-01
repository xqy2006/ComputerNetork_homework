from sliding_window_sim import simulate_sliding_window


def main() -> None:
    result = simulate_sliding_window(total_frames=6, window_size=3, loss_rate=0.1, seed=2)
    assert result.delivered == [0, 1, 2, 3, 4, 5]
    assert len(result.snapshots) >= 1
    last = result.snapshots[-1]
    assert last.advertised_window == 3
    print("All sliding-window tests passed.")


if __name__ == "__main__":
    main()
