from __future__ import annotations

import datetime as _dt
import os
import socket
import struct
import time
from dataclasses import dataclass


ICMP_TIMESTAMP_REQUEST = 13
ICMP_TIMESTAMP_REPLY = 14


def checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def ms_since_midnight_utc(now: _dt.datetime | None = None) -> int:
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((now - midnight).total_seconds() * 1000)


@dataclass
class ICMPTimestampPacket:
    type: int
    code: int
    identifier: int
    sequence: int
    originate_ts: int
    receive_ts: int
    transmit_ts: int

    def to_bytes(self) -> bytes:
        header = struct.pack(
            "!BBHHHIII",
            self.type,
            self.code,
            0,
            self.identifier,
            self.sequence,
            self.originate_ts,
            self.receive_ts,
            self.transmit_ts,
        )
        cs = checksum(header)
        return struct.pack(
            "!BBHHHIII",
            self.type,
            self.code,
            cs,
            self.identifier,
            self.sequence,
            self.originate_ts,
            self.receive_ts,
            self.transmit_ts,
        )

    @staticmethod
    def from_bytes(data: bytes) -> "ICMPTimestampPacket":
        if len(data) < 20:
            raise ValueError("ICMP timestamp packet too short")
        fields = struct.unpack("!BBHHHIII", data[:20])
        if checksum(data[:20]) != 0 and fields[2] != 0:
            raise ValueError("invalid ICMP checksum")
        return ICMPTimestampPacket(
            type=fields[0],
            code=fields[1],
            identifier=fields[3],
            sequence=fields[4],
            originate_ts=fields[5],
            receive_ts=fields[6],
            transmit_ts=fields[7],
        )


def strip_ip_header(packet: bytes) -> bytes:
    if len(packet) >= 20 and (packet[0] >> 4) == 4:
        header_len = (packet[0] & 0x0F) * 4
        if header_len <= len(packet):
            return packet[header_len:]
    return packet


class TimestampServer:
    def __init__(self, bind_ip: str = "0.0.0.0") -> None:
        self.bind_ip = bind_ip

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.bind((self.bind_ip, 0))
            print(f"ICMP timestamp server listening on {self.bind_ip}")
            while True:
                data, addr = sock.recvfrom(65535)
                packet = ICMPTimestampPacket.from_bytes(strip_ip_header(data))
                if packet.type != ICMP_TIMESTAMP_REQUEST:
                    continue
                now = ms_since_midnight_utc()
                reply = ICMPTimestampPacket(
                    ICMP_TIMESTAMP_REPLY,
                    0,
                    packet.identifier,
                    packet.sequence,
                    packet.originate_ts,
                    now,
                    now,
                )
                sock.sendto(reply.to_bytes(), addr)
                print(f"timestamp reply sent to {addr[0]} seq={packet.sequence}")


class TimestampClient:
    def __init__(self, target: str, timeout: float = 1.0) -> None:
        self.target = target
        self.timeout = timeout

    def query(self, sequence: int = 1) -> tuple[float, ICMPTimestampPacket]:
        identifier = os.getpid() & 0xFFFF
        originate = ms_since_midnight_utc()
        packet = ICMPTimestampPacket(
            ICMP_TIMESTAMP_REQUEST,
            0,
            identifier,
            sequence,
            originate,
            0,
            0,
        )
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.settimeout(self.timeout)
            started = time.time()
            sock.sendto(packet.to_bytes(), (self.target, 0))
            while True:
                data, _ = sock.recvfrom(65535)
                reply = ICMPTimestampPacket.from_bytes(strip_ip_header(data))
                if reply.type == ICMP_TIMESTAMP_REPLY and reply.identifier == identifier and reply.sequence == sequence:
                    return (time.time() - started) * 1000.0, reply


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ICMP timestamp client/server")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    server_parser = subparsers.add_parser("server")
    server_parser.add_argument("--bind", default="0.0.0.0")

    client_parser = subparsers.add_parser("client")
    client_parser.add_argument("target")

    args = parser.parse_args()
    if args.mode == "server":
        TimestampServer(args.bind).serve_forever()
    else:
        rtt, reply = TimestampClient(args.target).query()
        print(f"reply from {args.target}: rtt={rtt:.2f} ms remote_ms={reply.transmit_ts}")
