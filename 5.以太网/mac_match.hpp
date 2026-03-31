#ifndef MAC_MATCH_HPP
#define MAC_MATCH_HPP

#define MAC_ADDRESS_LENGTH 6

typedef unsigned char MAC_address[MAC_ADDRESS_LENGTH];

struct EthernetFrame {
    MAC_address destination;
    MAC_address source;
    unsigned short type;
};

extern MAC_address this_mac_address;

int mac_address_match(const struct EthernetFrame *frame);

#endif
