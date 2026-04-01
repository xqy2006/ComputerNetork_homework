from icmp_ping import PingServer


if __name__ == "__main__":
    PingServer("0.0.0.0").serve_forever()
