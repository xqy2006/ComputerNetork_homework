#ifndef IP_NET_UTILS_H
#define IP_NET_UTILS_H

int is_in_net(unsigned char *ip, unsigned char *netip, unsigned char *mask);
int classwise(unsigned char *ip);

#endif
