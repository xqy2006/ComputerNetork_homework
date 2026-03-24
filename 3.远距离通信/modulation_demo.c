#include <stdio.h>

#include "modulation.h"

static int message_index_for_sample(int sample_index, int sample_count, int message_size)
{
    return (int) (((long long) sample_index * (long long) message_size) / sample_count);
}

static int write_csv(
    const char *path,
    const double *cover,
    const unsigned char *digital_message,
    const double *analog_message,
    const double *digital_fsk,
    const double *analog_fm,
    const double *digital_ask,
    const double *analog_am,
    const double *digital_psk,
    const double *analog_pm,
    int sample_count,
    int digital_size,
    int analog_size
)
{
    FILE *fp = fopen(path, "w");
    int i;

    if (fp == 0) {
        return -1;
    }

    fprintf(
        fp,
        "index,cover,digital_message,analog_message,digital_fsk,analog_fm,digital_ask,analog_am,digital_psk,analog_pm\n"
    );

    for (i = 0; i < sample_count; ++i) {
        int digital_index = message_index_for_sample(i, sample_count, digital_size);
        int analog_index = message_index_for_sample(i, sample_count, analog_size);

        fprintf(
            fp,
            "%d,%.10f,%u,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f\n",
            i,
            cover[i],
            digital_message[digital_index],
            analog_message[analog_index],
            digital_fsk[i],
            analog_fm[i],
            digital_ask[i],
            analog_am[i],
            digital_psk[i],
            analog_pm[i]
        );
    }

    fclose(fp);
    return 0;
}

int main(void)
{
    enum {
        SAMPLE_COUNT = 256,
        DIGITAL_SIZE = 16,
        ANALOG_SIZE = 256
    };
    double cover[SAMPLE_COUNT];
    unsigned char digital_message[DIGITAL_SIZE];
    double analog_message[ANALOG_SIZE];
    double digital_fsk[SAMPLE_COUNT];
    double analog_fm[SAMPLE_COUNT];
    double digital_ask[SAMPLE_COUNT];
    double analog_am[SAMPLE_COUNT];
    double digital_psk[SAMPLE_COUNT];
    double analog_pm[SAMPLE_COUNT];
    int i;

    if (generate_cover_signal(cover, SAMPLE_COUNT) < 0 ||
        simulate_digital_modulation_signal(digital_message, DIGITAL_SIZE) < 0 ||
        simulate_analog_modulation_signal(analog_message, ANALOG_SIZE) < 0 ||
        modulate_digital_frequency(digital_fsk, SAMPLE_COUNT, digital_message, DIGITAL_SIZE) < 0 ||
        modulate_analog_frequency(analog_fm, SAMPLE_COUNT, analog_message, ANALOG_SIZE) < 0 ||
        modulate_digital_amplitude(digital_ask, SAMPLE_COUNT, digital_message, DIGITAL_SIZE) < 0 ||
        modulate_analog_amplitude(analog_am, SAMPLE_COUNT, analog_message, ANALOG_SIZE) < 0 ||
        modulate_digital_phase(digital_psk, SAMPLE_COUNT, digital_message, DIGITAL_SIZE) < 0 ||
        modulate_analog_phase(analog_pm, SAMPLE_COUNT, analog_message, ANALOG_SIZE) < 0) {
        fprintf(stderr, "Failed to generate signals.\n");
        return 1;
    }

    if (write_csv(
            "modulation_samples.csv",
            cover,
            digital_message,
            analog_message,
            digital_fsk,
            analog_fm,
            digital_ask,
            analog_am,
            digital_psk,
            analog_pm,
            SAMPLE_COUNT,
            DIGITAL_SIZE,
            ANALOG_SIZE
        ) != 0) {
        fprintf(stderr, "Failed to write modulation_samples.csv.\n");
        return 1;
    }

    printf("Digital message:");
    for (i = 0; i < DIGITAL_SIZE; ++i) {
        printf(" %u", digital_message[i]);
    }
    printf("\n");

    printf("First 8 cover samples:");
    for (i = 0; i < 8; ++i) {
        printf(" %.4f", cover[i]);
    }
    printf("\n");

    puts("Generated carrier, digital signal, analog signal, and six modulated waveforms.");
    puts("Output file: modulation_samples.csv");
    return 0;
}
