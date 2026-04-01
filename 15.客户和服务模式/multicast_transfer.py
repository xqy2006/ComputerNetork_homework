from __future__ import annotations

import socket
import struct
from pathlib import Path


CHUNK_SIZE = 1024


def encode_chunk(seq: int, payload: bytes, eof: bool = False) -> bytes:
    header = struct.pack("!IB", seq, 1 if eof else 0)
    return header + payload


def decode_chunk(packet: bytes) -> tuple[int, bool, bytes]:
    seq, eof = struct.unpack("!IB", packet[:5])
    return seq, bool(eof), packet[5:]


def send_file(path: str, group: str = "239.255.0.1", port: int = 5007) -> None:
    data = Path(path).read_bytes()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        for seq in range(0, len(data), CHUNK_SIZE):
            payload = data[seq : seq + CHUNK_SIZE]
            packet = encode_chunk(seq // CHUNK_SIZE, payload, False)
            sock.sendto(packet, (group, port))
        sock.sendto(encode_chunk(len(data) // CHUNK_SIZE + 1, b"", True), (group, port))


def receive_file(output: str, group: str = "239.255.0.1", port: int = 5007) -> None:
    received: dict[int, bytes] = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", port))
        mreq = struct.pack("4s4s", socket.inet_aton(group), socket.inet_aton("0.0.0.0"))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        eof_seq = None
        while True:
            packet, _ = sock.recvfrom(2048)
            seq, eof, payload = decode_chunk(packet)
            if eof:
                eof_seq = seq
                break
            received[seq] = payload
        if eof_seq is None:
            raise RuntimeError("did not receive EOF packet")
    data = b"".join(received[idx] for idx in sorted(received))
    Path(output).write_bytes(data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multicast file sender/receiver")
    sub = parser.add_subparsers(dest="mode", required=True)
    send_parser = sub.add_parser("send")
    send_parser.add_argument("path")
    send_parser.add_argument("--group", default="239.255.0.1")
    send_parser.add_argument("--port", type=int, default=5007)

    recv_parser = sub.add_parser("recv")
    recv_parser.add_argument("output")
    recv_parser.add_argument("--group", default="239.255.0.1")
    recv_parser.add_argument("--port", type=int, default=5007)

    args = parser.parse_args()
    if args.mode == "send":
        send_file(args.path, args.group, args.port)
        print(f"sent {args.path} to {args.group}:{args.port}")
    else:
        receive_file(args.output, args.group, args.port)
        print(f"received file saved to {args.output}")
