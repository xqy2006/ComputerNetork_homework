#include <iostream>
#include <vector>

#include "fragment_packet.hpp"

int main()
{
    const int packet_length = 24576;
    const std::vector<int> path_mtus = {4325, 2346, 1500, 4464, 2346};
    const std::vector<Fragment> fragments = fragmentPacket(packet_length, path_mtus);

    std::cout << "final fragment count: " << fragments.size() << "\n";
    for (std::size_t i = 0; i < fragments.size(); ++i) {
        std::cout << "fragment " << (i + 1)
                  << ": length=" << fragments[i].packet_length
                  << ", offset=" << fragments[i].offset << "\n";
    }
    return 0;
}
