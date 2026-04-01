#include "fragment_packet.hpp"

#include <stdexcept>

std::vector<Fragment> fragmentPacket(int packetLength, const std::vector<int> &pathMTUs)
{
    if (packetLength < 20) {
        throw std::invalid_argument("packet length must include 20-byte IP header");
    }

    std::vector<Fragment> fragments(1, Fragment{packetLength, 0});

    for (std::size_t i = 0; i < pathMTUs.size(); ++i) {
        const int mtu = pathMTUs[i];
        if (mtu < 28) {
            throw std::invalid_argument("mtu too small for fragmentation");
        }

        std::vector<Fragment> next;
        const int max_payload = ((mtu - 20) / 8) * 8;

        for (std::size_t j = 0; j < fragments.size(); ++j) {
            const Fragment &fragment = fragments[j];
            if (fragment.packet_length <= mtu) {
                next.push_back(fragment);
                continue;
            }

            const int payload = fragment.packet_length - 20;
            int emitted_payload = 0;
            while (payload - emitted_payload > max_payload) {
                next.push_back(Fragment{20 + max_payload, fragment.offset + emitted_payload / 8});
                emitted_payload += max_payload;
            }
            next.push_back(Fragment{20 + payload - emitted_payload, fragment.offset + emitted_payload / 8});
        }

        fragments.swap(next);
    }

    return fragments;
}
