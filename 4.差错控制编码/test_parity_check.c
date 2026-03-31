#include <stdio.h>
#include <stdlib.h>

#include "parity_check.h"

static void expect_int(const char *name, int actual, int expected)
{
    if (actual != expected) {
        fprintf(stderr, "%s failed: expected %d, got %d\n", name, expected, actual);
        exit(1);
    }
}

static void test_accepts_even_parity(void)
{
    const unsigned char msg[] = { 1, 0, 1, 0, 1, 0, 1, 0 };

    expect_int("accepts_even_parity", parity_check(msg, 8), 1);
}

static void test_rejects_odd_parity(void)
{
    const unsigned char msg[] = { 1, 0, 1, 0, 1 };

    expect_int("rejects_odd_parity", parity_check(msg, 5), 0);
}

static void test_accepts_nonzero_as_one(void)
{
    const unsigned char msg[] = { 2, 0, 3, 0 };

    expect_int("accepts_nonzero_as_one", parity_check(msg, 4), 1);
}

static void test_rejects_null(void)
{
    expect_int("rejects_null", parity_check(0, 8), 0);
}

static void test_rejects_empty_sequence(void)
{
    const unsigned char msg[] = { 0 };

    expect_int("rejects_empty_sequence", parity_check(msg, 0), 0);
}

int main(void)
{
    test_accepts_even_parity();
    test_rejects_odd_parity();
    test_accepts_nonzero_as_one();
    test_rejects_null();
    test_rejects_empty_sequence();

    puts("All parity_check tests passed.");
    return 0;
}
