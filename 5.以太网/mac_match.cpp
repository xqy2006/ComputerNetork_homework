#include "mac_match.hpp"

#include <cstring>

MAC_address this_mac_address = { 0x00, 0x50, 0x56, 0xC0, 0x00, 0x01 };

static int is_broadcast_address(const MAC_address address)
{
    int i;

    for (i = 0; i < MAC_ADDRESS_LENGTH; ++i) {
        if (address[i] != 0xFF) {
            return 0;
        }
    }

    return 1;
}

int mac_address_match(const struct EthernetFrame *frame)
{
    if (frame == 0) {
        return 0;
    }

    if (std::memcmp(frame->destination, this_mac_address, MAC_ADDRESS_LENGTH) == 0) {
        return 1;
    }

    if (is_broadcast_address(frame->destination)) {
        return 1;
    }

    if ((frame->destination[0] & 0x01) != 0) {
        return 1;
    }

    return 0;
}
