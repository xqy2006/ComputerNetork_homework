#include "modulation.h"

#include <math.h>

enum {
    DIGITAL_PATTERN_SIZE = 8
};

static const double PI_VALUE = 3.14159265358979323846;
static const double CARRIER_CYCLES = 16.0;
static const double DIGITAL_LOW_CYCLES = 12.0;
static const double DIGITAL_HIGH_CYCLES = 20.0;
static const double ANALOG_MESSAGE_CYCLES = 2.0;

static int normalize_bit(unsigned char value)
{
    return value ? 1 : 0;
}

static int message_index_for_sample(int sample_index, int sample_count, int message_size)
{
    return (int) (((long long) sample_index * (long long) message_size) / sample_count);
}

static double clamp_unit(double value)
{
    if (value > 1.0) {
        return 1.0;
    }
    if (value < -1.0) {
        return -1.0;
    }
    return value;
}

static double carrier_sample(int index, int size, double cycles, double phase_shift)
{
    return sin((2.0 * PI_VALUE * cycles * index) / size + phase_shift);
}

int generate_cover_signal(double *cover, const int size)
{
    int i;

    if (cover == 0 || size <= 0) {
        return -1;
    }

    for (i = 0; i < size; ++i) {
        cover[i] = carrier_sample(i, size, CARRIER_CYCLES, 0.0);
    }

    return size;
}

int simulate_digital_modulation_signal(unsigned char *message, const int size)
{
    static const unsigned char pattern[DIGITAL_PATTERN_SIZE] = { 1, 0, 1, 1, 0, 0, 1, 0 };
    int i;

    if (message == 0 || size <= 0) {
        return -1;
    }

    for (i = 0; i < size; ++i) {
        message[i] = pattern[i % DIGITAL_PATTERN_SIZE];
    }

    return size;
}

int simulate_analog_modulation_signal(double *message, const int size)
{
    int i;

    if (message == 0 || size <= 0) {
        return -1;
    }

    for (i = 0; i < size; ++i) {
        message[i] = 0.8 * sin((2.0 * PI_VALUE * ANALOG_MESSAGE_CYCLES * i) / size);
    }

    return size;
}

int modulate_digital_frequency(double *cover, const int cover_len, const unsigned char *message, const int msg_len)
{
    int i;

    if (cover == 0 || message == 0 || cover_len <= 0 || msg_len <= 0) {
        return -1;
    }

    for (i = 0; i < cover_len; ++i) {
        int msg_index = message_index_for_sample(i, cover_len, msg_len);
        double cycles = normalize_bit(message[msg_index]) ? DIGITAL_HIGH_CYCLES : DIGITAL_LOW_CYCLES;

        cover[i] = carrier_sample(i, cover_len, cycles, 0.0);
    }

    return cover_len;
}

int modulate_analog_frequency(double *cover, const int cover_len, const double *message, const int msg_len)
{
    double phase = 0.0;
    int i;

    if (cover == 0 || message == 0 || cover_len <= 0 || msg_len <= 0) {
        return -1;
    }

    for (i = 0; i < cover_len; ++i) {
        int msg_index = message_index_for_sample(i, cover_len, msg_len);
        double offset = 4.0 * clamp_unit(message[msg_index]);

        phase += (2.0 * PI_VALUE * (CARRIER_CYCLES + offset)) / cover_len;
        cover[i] = sin(phase);
    }

    return cover_len;
}

int modulate_digital_amplitude(double *cover, const int cover_len, const unsigned char *message, const int msg_len)
{
    int i;

    if (cover == 0 || message == 0 || cover_len <= 0 || msg_len <= 0) {
        return -1;
    }

    for (i = 0; i < cover_len; ++i) {
        int msg_index = message_index_for_sample(i, cover_len, msg_len);
        double amplitude = normalize_bit(message[msg_index]) ? 1.0 : 0.35;

        cover[i] = amplitude * carrier_sample(i, cover_len, CARRIER_CYCLES, 0.0);
    }

    return cover_len;
}

int modulate_analog_amplitude(double *cover, const int cover_len, const double *message, const int msg_len)
{
    int i;

    if (cover == 0 || message == 0 || cover_len <= 0 || msg_len <= 0) {
        return -1;
    }

    for (i = 0; i < cover_len; ++i) {
        int msg_index = message_index_for_sample(i, cover_len, msg_len);
        double amplitude = 1.0 + 0.5 * clamp_unit(message[msg_index]);

        cover[i] = amplitude * carrier_sample(i, cover_len, CARRIER_CYCLES, 0.0);
    }

    return cover_len;
}

int modulate_digital_phase(double *cover, const int cover_len, const unsigned char *message, const int msg_len)
{
    int i;

    if (cover == 0 || message == 0 || cover_len <= 0 || msg_len <= 0) {
        return -1;
    }

    for (i = 0; i < cover_len; ++i) {
        int msg_index = message_index_for_sample(i, cover_len, msg_len);
        double phase_shift = normalize_bit(message[msg_index]) ? PI_VALUE : 0.0;

        cover[i] = carrier_sample(i, cover_len, CARRIER_CYCLES, phase_shift);
    }

    return cover_len;
}

int modulate_analog_phase(double *cover, const int cover_len, const double *message, const int msg_len)
{
    int i;

    if (cover == 0 || message == 0 || cover_len <= 0 || msg_len <= 0) {
        return -1;
    }

    for (i = 0; i < cover_len; ++i) {
        int msg_index = message_index_for_sample(i, cover_len, msg_len);
        double phase_shift = (PI_VALUE / 2.0) * clamp_unit(message[msg_index]);

        cover[i] = carrier_sample(i, cover_len, CARRIER_CYCLES, phase_shift);
    }

    return cover_len;
}
