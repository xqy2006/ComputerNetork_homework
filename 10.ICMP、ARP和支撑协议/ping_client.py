import sys

from icmp_ping import PingClient


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    client = PingClient(target)
    for seq in range(1, 5):
        rtt = client.ping_once(seq)
        print(f"reply from {target}: seq={seq} time={rtt:.2f} ms")
