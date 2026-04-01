from stop_and_wait_sim import simulate_stop_and_wait


def main() -> None:
    result = simulate_stop_and_wait(["a", "b", "c"], loss_rate=0.2, seed=3)
    assert result.delivered == ["a", "b", "c"]
    assert result.attempts >= 3
    assert result.retransmissions >= 0
    print("All stop-and-wait tests passed.")


if __name__ == "__main__":
    main()
