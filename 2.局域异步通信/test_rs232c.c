#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "rs232c.h"

static int equal_double(double a, double b)
{
    return fabs(a - b) < 1e-9;
}

static void expect_int(const char *name, int actual, int expected)
{
    if (actual != expected) {
        fprintf(stderr, "%s failed: expected %d, got %d\n", name, expected, actual);
        exit(1);
    }
}

static void expect_true(const char *name, int condition)
{
    if (!condition) {
        fprintf(stderr, "%s failed\n", name);
        exit(1);
    }
}

static void test_encode_single_char(void)
{
    const char msg[] = "A";
    double volts[10];
    const double expected[10] = {
        -5.0, 5.0, -5.0, 5.0, 5.0,
        5.0, 5.0, 5.0, -5.0, -5.0
    };
    int written;
    int i;

    written = rs232c_encode(volts, 10, msg, 1);
    expect_int("encode_single_char_count", written, 10);

    for (i = 0; i < 10; ++i) {
        if (!equal_double(volts[i], expected[i])) {
            fprintf(stderr, "encode_single_char_values failed at index %d\n", i);
            exit(1);
        }
    }
}

static void test_round_trip(void)
{
    const char msg[] = "Hi";
    double volts[20];
    char decoded[3];
    int written;
    int read;

    written = rs232c_encode(volts, 20, msg, 2);
    expect_int("round_trip_written", written, 20);

    read = rs232c_decode(decoded, (int) sizeof(decoded), volts, written);
    expect_int("round_trip_read", read, 2);
    expect_true("round_trip_content", strcmp(decoded, msg) == 0);
}

static void test_encode_rejects_non_ascii(void)
{
    const char msg[] = { (char) 0x80 };
    double volts[10];

    expect_int("encode_rejects_non_ascii", rs232c_encode(volts, 10, msg, 1), -1);
}

static void test_encode_rejects_small_buffer(void)
{
    const char msg[] = "A";
    double volts[9];

    expect_int("encode_small_buffer", rs232c_encode(volts, 9, msg, 1), -1);
}

static void test_decode_rejects_bad_frame(void)
{
    const double invalid_start_bit[10] = {
        -5.0, -5.0, -5.0, 5.0, 5.0,
        5.0, 5.0, 5.0, -5.0, -5.0
    };
    char msg[2];

    expect_int("decode_bad_frame", rs232c_decode(msg, (int) sizeof(msg), invalid_start_bit, 10), -1);
}

static void test_decode_accepts_rs232_thresholds(void)
{
    const double volts[10] = {
        -12.0, 12.0, -12.0, -12.0, -12.0,
        -12.0, -12.0, -12.0, -12.0, -12.0
    };
    char msg[2];
    int read;

    read = rs232c_decode(msg, (int) sizeof(msg), volts, 10);
    expect_int("decode_threshold_read", read, 1);
    expect_true("decode_threshold_content", msg[0] == 0x7f && msg[1] == '\0');
}

int main(void)
{
    test_encode_single_char();
    test_round_trip();
    test_encode_rejects_non_ascii();
    test_encode_rejects_small_buffer();
    test_decode_rejects_bad_frame();
    test_decode_accepts_rs232_thresholds();

    puts("All tests passed.");
    return 0;
}
