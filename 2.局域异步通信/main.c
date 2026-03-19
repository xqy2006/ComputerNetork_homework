#include <stdio.h>

#include "rs232c.h"

int main(void)
{
    char input[16];
    double volts[10];
    int written;
    int i;

    printf("Input one character: ");
    if (scanf("%15s", input) != 1) {
        fprintf(stderr, "Failed to read input.\n");
        return 1;
    }

    written = rs232c_encode(volts, 10, input, 1);
    if (written != 10) {
        fprintf(stderr, "Encoding failed. Please enter a 7-bit ASCII character.\n");
        return 1;
    }

    printf("Voltage sequence:");
    for (i = 0; i < written; ++i) {
        printf(" %.1f", volts[i]);
    }
    printf("\n");

    return 0;
}
