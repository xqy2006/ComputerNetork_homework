#include <sstream>

#include "bridge_learning.hpp"

std::string to_hex4(int value)
{
    std::ostringstream oss;
    oss << "0x" << std::hex << std::uppercase << value;
    return oss.str();
}

std::string process_frame(const Frame &frame, std::map<int, int> &mac_table)
{
    mac_table[frame.source] = frame.source_port;

    if (frame.destination == 0xF) {
        return "broadcast to port " + std::to_string(frame.source_port == 1 ? 2 : 1);
    } else {
        std::map<int, int>::const_iterator it = mac_table.find(frame.destination);
        if (it == mac_table.end()) {
            return "unknown destination, flood to port " +
                   std::to_string(frame.source_port == 1 ? 2 : 1);
        } else if (it->second == frame.source_port) {
            return "filter on port " + std::to_string(frame.source_port);
        } else {
            return "forward to port " + std::to_string(it->second);
        }
    }
}
