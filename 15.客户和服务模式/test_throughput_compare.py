from throughput_compare import compare_throughput


def main() -> None:
    result = compare_throughput(512 * 1024)
    assert result["tcp_mbps"] > 0
    assert result["udp_mbps"] > 0
    print("All throughput comparison tests passed.")


if __name__ == "__main__":
    main()
