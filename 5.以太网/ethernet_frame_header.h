#ifndef ETHERNET_FRAME_HEADER_H
#define ETHERNET_FRAME_HEADER_H

#include <stdint.h>

#define ETHERNET_MAC_LENGTH 6

#pragma pack(push, 1)
struct ethernet_frame_header {
    uint8_t destination[ETHERNET_MAC_LENGTH];
    uint8_t source[ETHERNET_MAC_LENGTH];
    uint16_t type_or_length;
};
#pragma pack(pop)

#endif
