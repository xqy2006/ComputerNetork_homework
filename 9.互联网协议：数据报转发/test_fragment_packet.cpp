#include <cstdlib>
#include <iostream>
#include <vector>

#include "fragment_packet.hpp"

static void expect_true(const char *name, bool condition)
{
    if (!condition) {
        std::cerr << name << " failed\n";
        std::exit(1);
    }
}

int main()
{
    const std::vector<Fragment> fragments =
        fragmentPacket(24576, std::vector<int>{4325, 2346, 1500, 4464, 2346});

    expect_true("fragment_count", fragments.size() == 23);
    expect_true("first_length", fragments.front().packet_length == 1500);
    expect_true("first_offset", fragments.front().offset == 0);
    expect_true("last_length", fragments.back().packet_length == 736);
    expect_true("last_offset", fragments.back().offset == 2980);

    for (std::size_t i = 1; i < fragments.size(); ++i) {
        expect_true("offset_order", fragments[i].offset > fragments[i - 1].offset);
    }

    std::cout << "All fragmentPacket tests passed.\n";
    return 0;
}
