from dhcp_fixed import FixedDHCPServer


if __name__ == "__main__":
    FixedDHCPServer("192.168.1.1", "192.168.1.2").serve_forever()
