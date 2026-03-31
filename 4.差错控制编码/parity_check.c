#include "parity_check.h"

int parity_check(const unsigned char *msg, const int msg_length)
{
    int i;
    int ones = 0;

    if (msg == 0 || msg_length <= 0) {
        return 0;
    }

    for (i = 0; i < msg_length; ++i) {
        if (msg[i] != 0) {
            ++ones;
        }
    }

    return (ones % 2 == 0) ? 1 : 0;
}
