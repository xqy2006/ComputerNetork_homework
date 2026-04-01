#include <stdio.h>
#include <stdlib.h>

#include "ip_net_utils.h"

static void expect_true(const char *name, int value)
{
    if (!value) {
        fprintf(stderr, "%s failed\n", name);
        exit(1);
    }
}

static void expect_equal(const char *name, int actual, int expected)
{
    if (actual != expected) {
        fprintf(stderr, "%s failed: expected %d got %d\n", name, expected, actual);
        exit(1);
    }
}

int main(void)
{
    unsigned char ip1[4] = {192, 168, 1, 10};
    unsigned char net1[4] = {192, 168, 1, 0};
    unsigned char mask1[4] = {255, 255, 255, 0};
    unsigned char ip2[4] = {192, 168, 2, 10};

    unsigned char a[4] = {10, 1, 2, 3};
    unsigned char b[4] = {172, 16, 0, 1};
    unsigned char c[4] = {192, 168, 0, 1};
    unsigned char d[4] = {224, 0, 0, 1};
    unsigned char e[4] = {240, 0, 0, 1};

    expect_true("is_in_net_true", is_in_net(ip1, net1, mask1));
    expect_true("is_in_net_false", !is_in_net(ip2, net1, mask1));

    expect_equal("class_a", classwise(a), 0);
    expect_equal("class_b", classwise(b), 1);
    expect_equal("class_c", classwise(c), 2);
    expect_equal("class_d", classwise(d), 3);
    expect_equal("class_e", classwise(e), 4);

    printf("All ip_net_utils tests passed.\n");
    return 0;
}
