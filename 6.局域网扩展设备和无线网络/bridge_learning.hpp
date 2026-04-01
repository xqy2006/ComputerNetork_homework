#ifndef BRIDGE_LEARNING_HPP
#define BRIDGE_LEARNING_HPP

#include <map>
#include <string>

struct Frame {
    int source;
    int source_port;
    int destination;
};

std::string process_frame(const Frame &frame, std::map<int, int> &mac_table);
std::string to_hex4(int value);

#endif
