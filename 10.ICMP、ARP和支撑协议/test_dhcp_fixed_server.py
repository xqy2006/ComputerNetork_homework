import struct

from dhcp_fixed import (
    DHCP_ACK,
    DHCP_DISCOVER,
    DHCP_OFFER,
    DHCP_REQUEST,
    MAGIC_COOKIE,
    build_dhcp_reply,
    parse_dhcp_message,
)


def make_request(message_type: int) -> bytes:
    chaddr = bytes.fromhex("001122334455")
    header = struct.pack(
        "!BBBBIHH4s4s4s4s16s64s128s",
        1,
        1,
        6,
        0,
        0x12345678,
        0,
        0,
        b"\x00\x00\x00\x00",
        b"\x00\x00\x00\x00",
        b"\x00\x00\x00\x00",
        b"\x00\x00\x00\x00",
        chaddr.ljust(16, b"\x00"),
        b"\x00" * 64,
        b"\x00" * 128,
    )
    return header + MAGIC_COOKIE + bytes([53, 1, message_type, 255])


def main() -> None:
    discover = parse_dhcp_message(make_request(DHCP_DISCOVER))
    assert discover.xid == 0x12345678
    assert discover.chaddr == bytes.fromhex("001122334455")
    assert discover.options[53] == bytes([DHCP_DISCOVER])

    offer_raw = build_dhcp_reply(discover, "192.168.1.1", "192.168.1.2", DHCP_OFFER)
    offer = parse_dhcp_message(offer_raw)
    assert offer.yiaddr == "192.168.1.2"
    assert offer.options[53] == bytes([DHCP_OFFER])

    request = parse_dhcp_message(make_request(DHCP_REQUEST))
    ack_raw = build_dhcp_reply(request, "192.168.1.1", "192.168.1.2", DHCP_ACK)
    ack = parse_dhcp_message(ack_raw)
    assert ack.options[53] == bytes([DHCP_ACK])
    print("All DHCP fixed server tests passed.")


if __name__ == "__main__":
    main()
