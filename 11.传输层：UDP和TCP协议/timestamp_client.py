import sys

from icmp_timestamp import TimestampClient


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    rtt, reply = TimestampClient(target).query()
    print(f"reply from {target}: rtt={rtt:.2f} ms receive={reply.receive_ts} transmit={reply.transmit_ts}")
