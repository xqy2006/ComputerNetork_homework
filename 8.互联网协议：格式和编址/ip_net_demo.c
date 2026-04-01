#include <stdio.h>

#include "ip_net_utils.h"

static void print_ip(const unsigned char *ip)
{
    printf("%u.%u.%u.%u", ip[0], ip[1], ip[2], ip[3]);
}

int main(void)
{
    unsigned char ip[4] = {192, 168, 1, 10};
    unsigned char net[4] = {192, 168, 1, 0};
    unsigned char mask[4] = {255, 255, 255, 0};
    unsigned char class_ip[4] = {224, 1, 2, 3};

    print_ip(ip);
    printf(" in ");
    print_ip(net);
    printf("/24 -> %s\n", is_in_net(ip, net, mask) ? "match" : "not match");

    print_ip(class_ip);
    printf(" class index -> %d\n", classwise(class_ip));
    return 0;
}
