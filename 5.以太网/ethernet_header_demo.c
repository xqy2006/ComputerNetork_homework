#include <stdio.h>

#include "ethernet_frame_header.h"

int main(void)
{
    struct ethernet_frame_header header = {
        { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff },
        { 0x00, 0x50, 0x56, 0xc0, 0x00, 0x01 },
        0x0800
    };
    int i;

    printf("ethernet_frame_header size: %d bytes\n", (int) sizeof(header));
    printf("destination:");
    for (i = 0; i < ETHERNET_MAC_LENGTH; ++i) {
        printf(" %02X", header.destination[i]);
    }
    printf("\nsource:");
    for (i = 0; i < ETHERNET_MAC_LENGTH; ++i) {
        printf(" %02X", header.source[i]);
    }
    printf("\ntype_or_length: 0x%04X\n", header.type_or_length);
    return 0;
}
