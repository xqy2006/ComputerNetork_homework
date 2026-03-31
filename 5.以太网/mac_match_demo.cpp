#include <cstdio>
#include <cstring>

#include "mac_match.hpp"

static EthernetFrame make_frame(const unsigned char destination[MAC_ADDRESS_LENGTH])
{
    EthernetFrame frame = {};
    std::memcpy(frame.destination, destination, MAC_ADDRESS_LENGTH);
    std::memcpy(frame.source, this_mac_address, MAC_ADDRESS_LENGTH);
    frame.type = 0x0800;
    return frame;
}

static void print_result(const char *name, const EthernetFrame *frame)
{
    std::printf("%s -> %s\n", name, mac_address_match(frame) ? "accept" : "drop");
}

int main(void)
{
    const unsigned char local[MAC_ADDRESS_LENGTH] = { 0x00, 0x50, 0x56, 0xC0, 0x00, 0x01 };
    const unsigned char multicast[MAC_ADDRESS_LENGTH] = { 0x01, 0x00, 0x5E, 0x00, 0x00, 0x01 };
    const unsigned char broadcast[MAC_ADDRESS_LENGTH] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
    const unsigned char other[MAC_ADDRESS_LENGTH] = { 0x00, 0x50, 0x56, 0xC0, 0x00, 0x02 };
    EthernetFrame local_frame = make_frame(local);
    EthernetFrame multicast_frame = make_frame(multicast);
    EthernetFrame broadcast_frame = make_frame(broadcast);
    EthernetFrame other_frame = make_frame(other);

    print_result("local frame", &local_frame);
    print_result("multicast frame", &multicast_frame);
    print_result("broadcast frame", &broadcast_frame);
    print_result("other unicast frame", &other_frame);
    return 0;
}
