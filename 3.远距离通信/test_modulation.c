#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "modulation.h"

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

static int count_sign_changes(const double *data, int start, int end)
{
    int changes = 0;
    int i;

    for (i = start + 1; i < end; ++i) {
        if ((data[i - 1] < 0.0 && data[i] >= 0.0) || (data[i - 1] >= 0.0 && data[i] < 0.0)) {
            ++changes;
        }
    }

    return changes;
}

static void test_generate_cover_signal(void)
{
    double cover[64];

    expect_int("generate_cover_signal", generate_cover_signal(cover, 64), 64);
    expect_true("cover_starts_at_zero", fabs(cover[0]) < 1e-9);
    expect_true("cover_has_positive_peak", cover[1] > 0.0);
}

static void test_simulate_digital_signal(void)
{
    unsigned char message[8];

    expect_int("simulate_digital_signal", simulate_digital_modulation_signal(message, 8), 8);
    expect_true("digital_pattern_0", message[0] == 1);
    expect_true("digital_pattern_1", message[1] == 0);
    expect_true("digital_pattern_2", message[2] == 1);
    expect_true("digital_pattern_3", message[3] == 1);
}

static void test_simulate_analog_signal(void)
{
    double message[64];
    int i;

    expect_int("simulate_analog_signal", simulate_analog_modulation_signal(message, 64), 64);
    for (i = 0; i < 64; ++i) {
        expect_true("analog_signal_range", message[i] <= 0.8 + 1e-9 && message[i] >= -0.8 - 1e-9);
    }
}

static void test_digital_frequency_modulation(void)
{
    double cover[128];
    const unsigned char message[2] = { 0, 1 };
    int low_changes;
    int high_changes;

    expect_int("digital_frequency_modulation", modulate_digital_frequency(cover, 128, message, 2), 128);

    low_changes = count_sign_changes(cover, 0, 64);
    high_changes = count_sign_changes(cover, 64, 128);
    expect_true("high_frequency_has_more_zero_crossings", high_changes > low_changes);
}

static void test_digital_amplitude_modulation(void)
{
    double cover[128];
    const unsigned char message[2] = { 0, 1 };

    expect_int("digital_amplitude_modulation", modulate_digital_amplitude(cover, 128, message, 2), 128);
    expect_true("digital_amplitude_differs", fabs(cover[5]) < fabs(cover[69]));
}

static void test_digital_phase_modulation(void)
{
    double cover[128];
    const unsigned char message[2] = { 0, 1 };

    expect_int("digital_phase_modulation", modulate_digital_phase(cover, 128, message, 2), 128);
    expect_true("digital_phase_inverts_waveform", fabs(cover[5] + cover[69]) < 1e-6);
}

static void test_analog_modulations(void)
{
    double message[128];
    double fm[128];
    double am[128];
    double pm[128];

    expect_int("analog_signal_for_modulation", simulate_analog_modulation_signal(message, 128), 128);
    expect_int("analog_frequency_modulation", modulate_analog_frequency(fm, 128, message, 128), 128);
    expect_int("analog_amplitude_modulation", modulate_analog_amplitude(am, 128, message, 128), 128);
    expect_int("analog_phase_modulation", modulate_analog_phase(pm, 128, message, 128), 128);

    expect_true("analog_frequency_changes_waveform", fabs(fm[10] - fm[11]) > 1e-4);
    expect_true("analog_amplitude_changes_waveform", fabs(am[8]) != fabs(am[72]));
    expect_true("analog_phase_changes_waveform", fabs(pm[16] - pm[17]) > 1e-4);
}

int main(void)
{
    test_generate_cover_signal();
    test_simulate_digital_signal();
    test_simulate_analog_signal();
    test_digital_frequency_modulation();
    test_digital_amplitude_modulation();
    test_digital_phase_modulation();
    test_analog_modulations();

    puts("All modulation tests passed.");
    return 0;
}
