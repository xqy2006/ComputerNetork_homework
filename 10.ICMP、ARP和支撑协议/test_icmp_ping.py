from icmp_ping import ICMPPacket, ICMP_ECHO_REPLY, ICMP_ECHO_REQUEST, checksum, strip_ip_header


def main() -> None:
    packet = ICMPPacket(ICMP_ECHO_REQUEST, 0, 0x1234, 7, b"hello")
    raw = packet.to_bytes()
    parsed = ICMPPacket.from_bytes(raw)
    assert parsed.type == ICMP_ECHO_REQUEST
    assert parsed.identifier == 0x1234
    assert parsed.sequence == 7
    assert parsed.payload == b"hello"

    reply = ICMPPacket(ICMP_ECHO_REPLY, 0, parsed.identifier, parsed.sequence, parsed.payload)
    reply_raw = reply.to_bytes()
    assert checksum(reply_raw) == 0

    fake_ip = bytes([0x45, 0, 0, 28, 0, 0, 0, 0, 64, 1, 0, 0, 127, 0, 0, 1, 127, 0, 0, 1]) + raw
    assert strip_ip_header(fake_ip) == raw
    print("All ICMP ping tests passed.")


if __name__ == "__main__":
    main()
