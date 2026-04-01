from __future__ import annotations

import argparse
import datetime as dt
import socket
import struct
from dataclasses import dataclass


NTP_EPOCH = dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc)


def unix_to_ntp_timestamp(timestamp: float) -> tuple[int, int]:
    seconds = int(timestamp)
    fraction = int((timestamp - seconds) * (1 << 32)) & 0xFFFFFFFF
    return seconds, fraction


def datetime_to_ntp_fields(value: dt.datetime) -> tuple[int, int]:
    delta = value.astimezone(dt.timezone.utc) - NTP_EPOCH
    return unix_to_ntp_timestamp(delta.total_seconds())


@dataclass
class NTPPacket:
    li_vn_mode: int
    stratum: int
    poll: int
    precision: int
    root_delay: int
    root_dispersion: int
    ref_id: int
    ref_ts_sec: int
    ref_ts_frac: int
    orig_ts_sec: int
    orig_ts_frac: int
    recv_ts_sec: int
    recv_ts_frac: int
    tx_ts_sec: int
    tx_ts_frac: int

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!BBBbIIIIIIIIIII",
            self.li_vn_mode,
            self.stratum,
            self.poll,
            self.precision,
            self.root_delay,
            self.root_dispersion,
            self.ref_id,
            self.ref_ts_sec,
            self.ref_ts_frac,
            self.orig_ts_sec,
            self.orig_ts_frac,
            self.recv_ts_sec,
            self.recv_ts_frac,
            self.tx_ts_sec,
            self.tx_ts_frac,
        )

    @staticmethod
    def from_bytes(data: bytes) -> "NTPPacket":
        fields = struct.unpack("!BBBbIIIIIIIIIII", data[:48])
        return NTPPacket(*fields)


def build_ntp_reply(request: bytes, fixed_time: dt.datetime) -> bytes:
    request_packet = NTPPacket.from_bytes(request)
    sec, frac = datetime_to_ntp_fields(fixed_time)
    reply = NTPPacket(
        li_vn_mode=(0 << 6) | (4 << 3) | 4,
        stratum=1,
        poll=request_packet.poll,
        precision=-20,
        root_delay=0,
        root_dispersion=0,
        ref_id=0x4C4F434C,
        ref_ts_sec=sec,
        ref_ts_frac=frac,
        orig_ts_sec=request_packet.tx_ts_sec,
        orig_ts_frac=request_packet.tx_ts_frac,
        recv_ts_sec=sec,
        recv_ts_frac=frac,
        tx_ts_sec=sec,
        tx_ts_frac=frac,
    )
    return reply.to_bytes()


def parse_time_string(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)


def serve_fixed_time(time_string: str, bind_ip: str = "0.0.0.0", port: int = 123) -> None:
    fixed_time = parse_time_string(time_string)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((bind_ip, port))
        print(f"NTP server listening on {bind_ip}:{port}, fixed time={time_string} UTC")
        while True:
            data, addr = sock.recvfrom(4096)
            if len(data) < 48:
                continue
            sock.sendto(build_ntp_reply(data, fixed_time), addr)
            print(f"reply sent to {addr[0]}:{addr[1]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fixed-time NTP server")
    parser.add_argument("time_string", help='e.g. "2019-05-01 10:41:00"')
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=123)
    args = parser.parse_args()
    serve_fixed_time(args.time_string, args.bind, args.port)
