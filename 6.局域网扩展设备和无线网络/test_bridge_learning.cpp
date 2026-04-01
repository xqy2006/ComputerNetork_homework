#include <cstdlib>
#include <iostream>
#include <map>
#include <string>

#include "bridge_learning.hpp"

static void expect(const char *name, const std::string &actual, const std::string &expected)
{
    if (actual != expected) {
        std::cerr << name << " failed: expected [" << expected << "] got [" << actual << "]\n";
        std::exit(1);
    }
}

int main()
{
    std::map<int, int> mac_table;

    expect("unknown_flood", process_frame({0x1, 1, 0x2}, mac_table), "unknown destination, flood to port 2");
    expect("known_forward", process_frame({0x2, 2, 0x1}, mac_table), "forward to port 1");
    expect("broadcast", process_frame({0x3, 1, 0xF}, mac_table), "broadcast to port 2");
    expect("same_port_filter", process_frame({0x4, 1, 0x3}, mac_table), "filter on port 1");

    std::cout << "All bridge learning tests passed.\n";
    return 0;
}
