from __future__ import annotations

import ipaddress
import socket
import struct
from dataclasses import dataclass


MAGIC_COOKIE = b"\x63\x82\x53\x63"
DHCP_DISCOVER = 1
DHCP_OFFER = 2
DHCP_REQUEST = 3
DHCP_ACK = 5


def ip_to_bytes(ip: str) -> bytes:
    return ipaddress.IPv4Address(ip).packed


def bytes_to_ip(data: bytes) -> str:
    return str(ipaddress.IPv4Address(data))


@dataclass
class DHCPMessage:
    op: int
    xid: int
    chaddr: bytes
    yiaddr: str
    options: dict[int, bytes]


def parse_dhcp_message(data: bytes) -> DHCPMessage:
    if len(data) < 240:
        raise ValueError("DHCP message too short")
    op, _, _, _, xid, _, _, _, yiaddr, _, _, chaddr = struct.unpack("!BBBBIHH4s4s4s4s16s", data[:44])
    options = {}
    offset = 240
    while offset < len(data):
        code = data[offset]
        offset += 1
        if code == 255:
            break
        if code == 0:
            continue
        length = data[offset]
        offset += 1
        options[code] = data[offset : offset + length]
        offset += length
    return DHCPMessage(op, xid, chaddr[:6], bytes_to_ip(yiaddr), options)


def build_dhcp_reply(
    request: DHCPMessage,
    server_ip: str,
    offered_ip: str,
    message_type: int,
    subnet_mask: str = "255.255.255.0",
    router_ip: str = "192.168.1.1",
    dns_ip: str = "192.168.1.1",
    lease_time: int = 3600,
) -> bytes:
    fixed_header = struct.pack(
        "!BBBBIHH4s4s4s4s16s64s128s",
        2,
        1,
        6,
        0,
        request.xid,
        0,
        0,
        b"\x00\x00\x00\x00",
        ip_to_bytes(offered_ip),
        ip_to_bytes(server_ip),
        b"\x00\x00\x00\x00",
        request.chaddr.ljust(16, b"\x00"),
        b"\x00" * 64,
        b"\x00" * 128,
    )
    options = [
        MAGIC_COOKIE,
        bytes([53, 1, message_type]),
        bytes([54, 4]) + ip_to_bytes(server_ip),
        bytes([1, 4]) + ip_to_bytes(subnet_mask),
        bytes([3, 4]) + ip_to_bytes(router_ip),
        bytes([6, 4]) + ip_to_bytes(dns_ip),
        bytes([51, 4]) + struct.pack("!I", lease_time),
        bytes([255]),
    ]
    return fixed_header + b"".join(options)


class FixedDHCPServer:
    def __init__(self, server_ip: str = "192.168.1.1", fixed_ip: str = "192.168.1.2") -> None:
        self.server_ip = server_ip
        self.fixed_ip = fixed_ip

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", 67))
            print(f"DHCP server listening, fixed address {self.fixed_ip}")
            while True:
                data, addr = sock.recvfrom(4096)
                request = parse_dhcp_message(data)
                msg_type = request.options.get(53, b"\x00")[0]
                if msg_type == DHCP_DISCOVER:
                    reply = build_dhcp_reply(request, self.server_ip, self.fixed_ip, DHCP_OFFER)
                    sock.sendto(reply, ("<broadcast>", 68))
                    print(f"offer sent to {request.chaddr.hex('-')}: {self.fixed_ip}")
                elif msg_type == DHCP_REQUEST:
                    reply = build_dhcp_reply(request, self.server_ip, self.fixed_ip, DHCP_ACK)
                    sock.sendto(reply, ("<broadcast>", 68))
                    print(f"ack sent to {request.chaddr.hex('-')}: {self.fixed_ip}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fixed-address DHCP server")
    parser.add_argument("--server-ip", default="192.168.1.1")
    parser.add_argument("--fixed-ip", default="192.168.1.2")
    args = parser.parse_args()
    FixedDHCPServer(args.server_ip, args.fixed_ip).serve_forever()
