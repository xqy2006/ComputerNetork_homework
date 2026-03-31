#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "mac_match.hpp"

static void expect_int(const char *name, int actual, int expected)
{
    if (actual != expected) {
        std::fprintf(stderr, "%s failed: expected %d, got %d\n", name, expected, actual);
        std::exit(1);
    }
}

static EthernetFrame make_frame(const unsigned char destination[MAC_ADDRESS_LENGTH])
{
    EthernetFrame frame = {};
    std::memcpy(frame.destination, destination, MAC_ADDRESS_LENGTH);
    std::memcpy(frame.source, this_mac_address, MAC_ADDRESS_LENGTH);
    frame.type = 0x0800;
    return frame;
}

static void test_local_address_matches(void)
{
    const unsigned char destination[MAC_ADDRESS_LENGTH] = { 0x00, 0x50, 0x56, 0xC0, 0x00, 0x01 };
    EthernetFrame frame = make_frame(destination);

    expect_int("local_address_matches", mac_address_match(&frame), 1);
}

static void test_broadcast_matches(void)
{
    const unsigned char destination[MAC_ADDRESS_LENGTH] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
    EthernetFrame frame = make_frame(destination);

    expect_int("broadcast_matches", mac_address_match(&frame), 1);
}

static void test_multicast_matches(void)
{
    const unsigned char destination[MAC_ADDRESS_LENGTH] = { 0x01, 0x00, 0x5E, 0x00, 0x00, 0x01 };
    EthernetFrame frame = make_frame(destination);

    expect_int("multicast_matches", mac_address_match(&frame), 1);
}

static void test_unrelated_unicast_rejected(void)
{
    const unsigned char destination[MAC_ADDRESS_LENGTH] = { 0x00, 0x50, 0x56, 0xC0, 0x00, 0x02 };
    EthernetFrame frame = make_frame(destination);

    expect_int("unrelated_unicast_rejected", mac_address_match(&frame), 0);
}

static void test_null_frame_rejected(void)
{
    expect_int("null_frame_rejected", mac_address_match(0), 0);
}

int main(void)
{
    test_local_address_matches();
    test_broadcast_matches();
    test_multicast_matches();
    test_unrelated_unicast_rejected();
    test_null_frame_rejected();

    std::puts("All mac_address_match tests passed.");
    return 0;
}
