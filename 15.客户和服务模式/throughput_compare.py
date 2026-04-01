from __future__ import annotations

import socket
import threading
import time


def _tcp_server(port: int, total_size: int, done: dict[str, float]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", port))
        server.listen(1)
        conn, _ = server.accept()
        with conn:
            received = 0
            while received < total_size:
                data = conn.recv(65536)
                if not data:
                    break
                received += len(data)
        done["received"] = received


def _udp_server(port: int, total_size: int, done: dict[str, float]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(("127.0.0.1", port))
        received = 0
        while received < total_size:
            data, _ = server.recvfrom(65536)
            received += len(data)
        done["received"] = received


def compare_throughput(total_size: int = 4 * 1024 * 1024) -> dict[str, float]:
    payload = b"x" * 4096

    tcp_done: dict[str, float] = {}
    tcp_thread = threading.Thread(target=_tcp_server, args=(19001, total_size, tcp_done))
    tcp_thread.start()
    time.sleep(0.1)
    started = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(("127.0.0.1", 19001))
        sent = 0
        while sent < total_size:
            client.sendall(payload)
            sent += len(payload)
    tcp_thread.join()
    tcp_elapsed = time.perf_counter() - started

    udp_done: dict[str, float] = {}
    udp_thread = threading.Thread(target=_udp_server, args=(19002, total_size, udp_done))
    udp_thread.start()
    time.sleep(0.1)
    started = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        sent = 0
        while sent < total_size:
            client.sendto(payload, ("127.0.0.1", 19002))
            sent += len(payload)
    udp_thread.join()
    udp_elapsed = time.perf_counter() - started

    return {
        "tcp_mbps": total_size * 8 / tcp_elapsed / 1_000_000,
        "udp_mbps": total_size * 8 / udp_elapsed / 1_000_000,
    }


if __name__ == "__main__":
    result = compare_throughput()
    print(f"TCP throughput: {result['tcp_mbps']:.2f} Mbps")
    print(f"UDP throughput: {result['udp_mbps']:.2f} Mbps")
