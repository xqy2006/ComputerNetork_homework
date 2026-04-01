from icmp_timestamp import TimestampServer


if __name__ == "__main__":
    TimestampServer("0.0.0.0").serve_forever()
