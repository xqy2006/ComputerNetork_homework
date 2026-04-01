from __future__ import annotations

import os
import socket
import struct
import time
from dataclasses import dataclass


ICMP_ECHO_REPLY = 0
ICMP_ECHO_REQUEST = 8


def checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


@dataclass
class ICMPPacket:
    type: int
    code: int
    identifier: int
    sequence: int
    payload: bytes

    def to_bytes(self) -> bytes:
        header = struct.pack("!BBHHH", self.type, self.code, 0, self.identifier, self.sequence)
        packet = header + self.payload
        cs = checksum(packet)
        return struct.pack("!BBHHH", self.type, self.code, cs, self.identifier, self.sequence) + self.payload

    @staticmethod
    def from_bytes(data: bytes) -> "ICMPPacket":
        if len(data) < 8:
            raise ValueError("ICMP packet too short")
        type_, code, recv_checksum, identifier, sequence = struct.unpack("!BBHHH", data[:8])
        payload = data[8:]
        if checksum(data) != 0 and recv_checksum != 0:
            raise ValueError("invalid ICMP checksum")
        return ICMPPacket(type_, code, identifier, sequence, payload)


def strip_ip_header(packet: bytes) -> bytes:
    if len(packet) >= 20 and (packet[0] >> 4) == 4:
        header_len = (packet[0] & 0x0F) * 4
        if header_len <= len(packet):
            return packet[header_len:]
    return packet


class PingServer:
    def __init__(self, bind_ip: str = "0.0.0.0") -> None:
        self.bind_ip = bind_ip

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.bind((self.bind_ip, 0))
            print(f"ICMP ping server listening on {self.bind_ip}")
            while True:
                data, addr = sock.recvfrom(65535)
                icmp = ICMPPacket.from_bytes(strip_ip_header(data))
                if icmp.type != ICMP_ECHO_REQUEST:
                    continue
                reply = ICMPPacket(ICMP_ECHO_REPLY, 0, icmp.identifier, icmp.sequence, icmp.payload)
                sock.sendto(reply.to_bytes(), addr)
                print(f"reply sent to {addr[0]} id={icmp.identifier} seq={icmp.sequence}")


class PingClient:
    def __init__(self, target: str, timeout: float = 1.0) -> None:
        self.target = target
        self.timeout = timeout

    def ping_once(self, sequence: int = 1) -> float:
        identifier = os.getpid() & 0xFFFF
        payload = struct.pack("!d", time.time()) + b"codex-ping"
        packet = ICMPPacket(ICMP_ECHO_REQUEST, 0, identifier, sequence, payload)

        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.settimeout(self.timeout)
            started = time.time()
            sock.sendto(packet.to_bytes(), (self.target, 0))
            while True:
                data, _ = sock.recvfrom(65535)
                icmp = ICMPPacket.from_bytes(strip_ip_header(data))
                if icmp.type == ICMP_ECHO_REPLY and icmp.identifier == identifier and icmp.sequence == sequence:
                    return (time.time() - started) * 1000.0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple ICMP ping client/server")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    server_parser = subparsers.add_parser("server")
    server_parser.add_argument("--bind", default="0.0.0.0")

    client_parser = subparsers.add_parser("client")
    client_parser.add_argument("target")
    client_parser.add_argument("--count", type=int, default=4)

    args = parser.parse_args()
    if args.mode == "server":
        PingServer(args.bind).serve_forever()
    else:
        client = PingClient(args.target)
        for seq in range(1, args.count + 1):
            rtt = client.ping_once(seq)
            print(f"reply from {args.target}: seq={seq} time={rtt:.2f} ms")
