#include <iostream>
#include <map>
#include <vector>

#include "bridge_learning.hpp"

int main()
{
    const std::vector<Frame> frames = {
        { 0x1, 1, 0x2 },
        { 0x2, 2, 0x1 },
        { 0x3, 1, 0xF },
        { 0x4, 2, 0x3 },
        { 0x5, 1, 0x4 }
    };
    std::map<int, int> mac_table;

    for (std::size_t i = 0; i < frames.size(); ++i) {
        std::string action = process_frame(frames[i], mac_table);

        std::cout << "frame " << (i + 1)
                  << ": src=" << to_hex4(frames[i].source)
                  << " src_port=" << frames[i].source_port
                  << " dst=" << to_hex4(frames[i].destination)
                  << " -> " << action << "\n";
        std::cout << "  MAC table:";
        for (std::map<int, int>::const_iterator it = mac_table.begin();
             it != mac_table.end();
             ++it) {
            std::cout << " [" << to_hex4(it->first) << " => port " << it->second << "]";
        }
        std::cout << "\n";
    }

    return 0;
}
