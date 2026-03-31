#include <stdio.h>
#include <stdlib.h>

#include "ethernet_frame_header.h"

static void expect_int(const char *name, int actual, int expected)
{
    if (actual != expected) {
        fprintf(stderr, "%s failed: expected %d, got %d\n", name, expected, actual);
        exit(1);
    }
}

int main(void)
{
    struct ethernet_frame_header header = {
        { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff },
        { 0x00, 0x50, 0x56, 0xc0, 0x00, 0x01 },
        0x0800
    };

    expect_int("header_size", (int) sizeof(header), 14);
    expect_int("destination_length", (int) sizeof(header.destination), ETHERNET_MAC_LENGTH);
    expect_int("source_length", (int) sizeof(header.source), ETHERNET_MAC_LENGTH);

    puts("All ethernet_frame_header tests passed.");
    return 0;
}
