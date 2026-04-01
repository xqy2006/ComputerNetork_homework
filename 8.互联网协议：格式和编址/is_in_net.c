#include "ip_net_utils.h"

int is_in_net(unsigned char *ip, unsigned char *netip, unsigned char *mask)
{
    int i;
    for (i = 0; i < 4; ++i) {
        if ((ip[i] & mask[i]) != (netip[i] & mask[i])) {
            return 0;
        }
    }
    return 1;
}
