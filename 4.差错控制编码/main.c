#include <stdio.h>
#include <string.h>

#include "parity_check.h"

static int parse_bits(unsigned char *buffer, int buffer_size, const char *text)
{
    int i;
    int length = (int) strlen(text);

    if (length <= 0 || length > buffer_size) {
        return -1;
    }

    for (i = 0; i < length; ++i) {
        if (text[i] == '0') {
            buffer[i] = 0;
        } else if (text[i] == '1') {
            buffer[i] = 1;
        } else {
            return -1;
        }
    }

    return length;
}

int main(void)
{
    char input[256];
    unsigned char bits[256];
    int length;

    printf("Input parity code bits (for example 101010101): ");
    if (scanf("%255s", input) != 1) {
        fprintf(stderr, "Failed to read input.\n");
        return 1;
    }

    length = parse_bits(bits, (int) sizeof(bits), input);
    if (length < 0) {
        fprintf(stderr, "Input must contain only 0 and 1.\n");
        return 1;
    }

    if (parity_check(bits, length) == 1) {
        printf("Parity check passed.\n");
    } else {
        printf("Parity check failed.\n");
    }

    return 0;
}
