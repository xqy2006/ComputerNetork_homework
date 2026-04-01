from dhcp_fixed import DHCP_DISCOVER, DHCP_REQUEST, build_dhcp_reply, parse_dhcp_message
from test_dhcp_fixed_server import make_request


def main() -> None:
    discover = parse_dhcp_message(make_request(DHCP_DISCOVER))
    offer = parse_dhcp_message(build_dhcp_reply(discover, "192.168.1.1", "192.168.1.2", 2))
    request = parse_dhcp_message(make_request(DHCP_REQUEST))
    ack = parse_dhcp_message(build_dhcp_reply(request, "192.168.1.1", "192.168.1.2", 5))
    print(f"discover xid=0x{discover.xid:08x}")
    print(f"offer ip={offer.yiaddr}")
    print(f"ack ip={ack.yiaddr}")


if __name__ == "__main__":
    main()
