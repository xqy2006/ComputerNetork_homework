from icmp_timestamp import (
    ICMP_TIMESTAMP_REPLY,
    ICMP_TIMESTAMP_REQUEST,
    ICMPTimestampPacket,
    checksum,
    ms_since_midnight_utc,
    strip_ip_header,
)


def main() -> None:
    ms = ms_since_midnight_utc()
    assert 0 <= ms < 24 * 60 * 60 * 1000

    packet = ICMPTimestampPacket(ICMP_TIMESTAMP_REQUEST, 0, 0x1111, 3, 123, 0, 0)
    raw = packet.to_bytes()
    parsed = ICMPTimestampPacket.from_bytes(raw)
    assert parsed.type == ICMP_TIMESTAMP_REQUEST
    assert parsed.identifier == 0x1111
    assert parsed.originate_ts == 123

    reply = ICMPTimestampPacket(ICMP_TIMESTAMP_REPLY, 0, 0x1111, 3, 123, 456, 789)
    reply_raw = reply.to_bytes()
    assert checksum(reply_raw) == 0

    fake_ip = bytes([0x45, 0, 0, 40, 0, 0, 0, 0, 64, 1, 0, 0, 127, 0, 0, 1, 127, 0, 0, 1]) + raw
    assert strip_ip_header(fake_ip) == raw
    print("All ICMP timestamp tests passed.")


if __name__ == "__main__":
    main()
