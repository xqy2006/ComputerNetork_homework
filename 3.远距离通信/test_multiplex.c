#include <stdio.h>
#include <stdlib.h>

#include "multiplex.h"

static void expect_int(const char *name, int actual, int expected)
{
    if (actual != expected) {
        fprintf(stderr, "%s failed: expected %d, got %d\n", name, expected, actual);
        exit(1);
    }
}

static void expect_sequence(const char *name, const unsigned char *actual, const unsigned char *expected, int size)
{
    int i;

    for (i = 0; i < size; ++i) {
        if (actual[i] != expected[i]) {
            fprintf(stderr, "%s failed at index %d: expected %u, got %u\n", name, i, expected[i], actual[i]);
            exit(1);
        }
    }
}

static void test_round_trip(multiplex_mode_t mode, int expected_signal_len)
{
    const unsigned char source_a[] = { 1, 0, 1, 1 };
    const unsigned char source_b[] = { 0, 1, 0 };
    unsigned char signal[64];
    unsigned char decoded_a[4];
    unsigned char decoded_b[3];
    int written;
    int read;

    multiplex_set_mode(mode);

    written = multiplex(signal, (int) sizeof(signal), source_a, 4, source_b, 3);
    expect_int("round_trip_written", written, expected_signal_len);

    read = demultiplex(decoded_a, 4, decoded_b, 3, signal, written);
    expect_int("round_trip_read", read, 7);
    expect_sequence("round_trip_a", decoded_a, source_a, 4);
    expect_sequence("round_trip_b", decoded_b, source_b, 3);
}

static void test_statistical_demultiplex_rejects_invalid_source(void)
{
    unsigned char decoded_a[1];
    unsigned char decoded_b[1];
    const unsigned char invalid_signal[] = { 2, 1 };

    multiplex_set_mode(MULTIPLEX_MODE_STATISTICAL_TDM);
    expect_int(
        "statistical_invalid_source",
        demultiplex(decoded_a, 1, decoded_b, 1, invalid_signal, 2),
        -1
    );
}

static void test_small_output_buffer_is_rejected(void)
{
    const unsigned char source_a[] = { 1, 0, 1 };
    const unsigned char source_b[] = { 0, 1, 0 };
    unsigned char signal[4];

    multiplex_set_mode(MULTIPLEX_MODE_SYNCHRONOUS_TDM);
    expect_int("small_output_buffer", multiplex(signal, 4, source_a, 3, source_b, 3), -1);
}

static void test_fdm_rejects_invalid_symbol(void)
{
    unsigned char decoded_a[1];
    unsigned char decoded_b[1];
    const unsigned char invalid_signal[] = { 4 };

    multiplex_set_mode(MULTIPLEX_MODE_FDM);
    expect_int("fdm_invalid_symbol", demultiplex(decoded_a, 1, decoded_b, 1, invalid_signal, 1), -1);
}

static void test_cdm_rejects_missing_projection(void)
{
    unsigned char decoded_a[1];
    unsigned char decoded_b[1];
    const unsigned char invalid_signal[] = { 2, 2 };

    multiplex_set_mode(MULTIPLEX_MODE_CDM);
    expect_int("cdm_missing_projection", demultiplex(decoded_a, 1, decoded_b, 1, invalid_signal, 2), -1);
}

int main(void)
{
    test_round_trip(MULTIPLEX_MODE_STATISTICAL_TDM, 14);
    test_round_trip(MULTIPLEX_MODE_SYNCHRONOUS_TDM, 8);
    test_round_trip(MULTIPLEX_MODE_FDM, 4);
    test_round_trip(MULTIPLEX_MODE_CDM, 8);
    test_statistical_demultiplex_rejects_invalid_source();
    test_small_output_buffer_is_rejected();
    test_fdm_rejects_invalid_symbol();
    test_cdm_rejects_missing_projection();

    puts("All multiplex tests passed.");
    return 0;
}
