#include <stdio.h>

#include "multiplex.h"

static void print_sequence(const char *name, const unsigned char *data, int size)
{
    int i;

    printf("%s:", name);
    for (i = 0; i < size; ++i) {
        printf(" %u", data[i]);
    }
    printf("\n");
}

int main(void)
{
    const unsigned char source_a[] = { 1, 0, 1, 1, 0, 1 };
    const unsigned char source_b[] = { 0, 1, 1, 0 };
    const multiplex_mode_t modes[] = {
        MULTIPLEX_MODE_STATISTICAL_TDM,
        MULTIPLEX_MODE_SYNCHRONOUS_TDM,
        MULTIPLEX_MODE_FDM,
        MULTIPLEX_MODE_CDM
    };
    unsigned char signal[128];
    unsigned char decoded_a[6];
    unsigned char decoded_b[4];
    int i;

    print_sequence("source_a", source_a, 6);
    print_sequence("source_b", source_b, 4);
    printf("\n");

    for (i = 0; i < (int) (sizeof(modes) / sizeof(modes[0])); ++i) {
        int written;
        int read;

        multiplex_set_mode(modes[i]);

        written = multiplex(signal, (int) sizeof(signal), source_a, 6, source_b, 4);
        read = demultiplex(decoded_a, 6, decoded_b, 4, signal, written);

        printf("== %s ==\n", multiplex_mode_name(modes[i]));
        printf("signal length: %d\n", written);
        print_sequence("signal", signal, written);
        printf("decoded items: %d\n", read);
        print_sequence("decoded_a", decoded_a, 6);
        print_sequence("decoded_b", decoded_b, 4);
        printf("\n");
    }

    return 0;
}
