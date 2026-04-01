#ifndef FRAGMENT_PACKET_HPP
#define FRAGMENT_PACKET_HPP

#include <vector>

struct Fragment {
    int packet_length;
    int offset;
};

std::vector<Fragment> fragmentPacket(int packetLength, const std::vector<int> &pathMTUs);

#endif
