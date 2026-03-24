#include "multiplex.h"

static multiplex_mode_t g_mode = MULTIPLEX_MODE_STATISTICAL_TDM;

static int normalize_bit(unsigned char value)
{
    return value ? 1 : 0;
}

static int max_int(int left, int right)
{
    return left > right ? left : right;
}

void multiplex_set_mode(multiplex_mode_t mode)
{
    g_mode = mode;
}

multiplex_mode_t multiplex_get_mode(void)
{
    return g_mode;
}

const char *multiplex_mode_name(multiplex_mode_t mode)
{
    switch (mode) {
    case MULTIPLEX_MODE_STATISTICAL_TDM:
        return "Statistical TDM";
    case MULTIPLEX_MODE_SYNCHRONOUS_TDM:
        return "Synchronous TDM";
    case MULTIPLEX_MODE_FDM:
        return "Frequency Division Multiplexing";
    case MULTIPLEX_MODE_CDM:
        return "Code Division Multiplexing";
    default:
        return "Unknown";
    }
}

int multiplex(
    unsigned char *c,
    const int c_size,
    const unsigned char *a,
    const int a_len,
    const unsigned char *b,
    const int b_len
)
{
    int i;

    if (c_size < 0 || a_len < 0 || b_len < 0) {
        return -1;
    }
    if ((a_len > 0 && a == 0) || (b_len > 0 && b == 0) || (c_size > 0 && c == 0)) {
        return -1;
    }

    switch (g_mode) {
    case MULTIPLEX_MODE_STATISTICAL_TDM: {
        int a_index = 0;
        int b_index = 0;
        int written = 0;
        int required = 2 * (a_len + b_len);

        if (c_size < required) {
            return -1;
        }

        while (a_index < a_len || b_index < b_len) {
            if (a_index < a_len) {
                c[written++] = 0;
                c[written++] = (unsigned char) normalize_bit(a[a_index++]);
            }
            if (b_index < b_len) {
                c[written++] = 1;
                c[written++] = (unsigned char) normalize_bit(b[b_index++]);
            }
        }

        return written;
    }

    case MULTIPLEX_MODE_SYNCHRONOUS_TDM: {
        int slot_count = max_int(a_len, b_len);
        int required = slot_count * 2;

        if (c_size < required) {
            return -1;
        }

        for (i = 0; i < slot_count; ++i) {
            c[2 * i] = (unsigned char) (i < a_len ? normalize_bit(a[i]) : 0);
            c[2 * i + 1] = (unsigned char) (i < b_len ? normalize_bit(b[i]) : 0);
        }

        return required;
    }

    case MULTIPLEX_MODE_FDM: {
        int slot_count = max_int(a_len, b_len);

        if (c_size < slot_count) {
            return -1;
        }

        for (i = 0; i < slot_count; ++i) {
            int a_bit = i < a_len ? normalize_bit(a[i]) : 0;
            int b_bit = i < b_len ? normalize_bit(b[i]) : 0;

            c[i] = (unsigned char) (a_bit | (b_bit << 1));
        }

        return slot_count;
    }

    case MULTIPLEX_MODE_CDM: {
        int slot_count = max_int(a_len, b_len);
        int required = slot_count * 2;

        if (c_size < required) {
            return -1;
        }

        for (i = 0; i < slot_count; ++i) {
            int a_level = 0;
            int b_level = 0;
            int chip_1;
            int chip_2;

            if (i < a_len) {
                a_level = normalize_bit(a[i]) ? 1 : -1;
            }
            if (i < b_len) {
                b_level = normalize_bit(b[i]) ? 1 : -1;
            }

            chip_1 = a_level + b_level;
            chip_2 = a_level - b_level;

            c[2 * i] = (unsigned char) (chip_1 + 2);
            c[2 * i + 1] = (unsigned char) (chip_2 + 2);
        }

        return required;
    }

    default:
        return -1;
    }
}

int demultiplex(
    unsigned char *a,
    const int a_size,
    unsigned char *b,
    const int b_size,
    const unsigned char *c,
    const int c_len
)
{
    int i;

    if (a_size < 0 || b_size < 0 || c_len < 0) {
        return -1;
    }
    if ((a_size > 0 && a == 0) || (b_size > 0 && b == 0) || (c_len > 0 && c == 0)) {
        return -1;
    }

    switch (g_mode) {
    case MULTIPLEX_MODE_STATISTICAL_TDM: {
        int a_index = 0;
        int b_index = 0;

        if (c_len % 2 != 0) {
            return -1;
        }

        for (i = 0; i < c_len; i += 2) {
            int source = c[i];
            unsigned char bit = (unsigned char) normalize_bit(c[i + 1]);

            if (source == 0) {
                if (a_index >= a_size) {
                    return -1;
                }
                a[a_index++] = bit;
            } else if (source == 1) {
                if (b_index >= b_size) {
                    return -1;
                }
                b[b_index++] = bit;
            } else {
                return -1;
            }
        }

        if (a_index != a_size || b_index != b_size) {
            return -1;
        }

        return a_index + b_index;
    }

    case MULTIPLEX_MODE_SYNCHRONOUS_TDM: {
        int slot_count;

        if (c_len % 2 != 0) {
            return -1;
        }

        slot_count = c_len / 2;
        if (slot_count < max_int(a_size, b_size)) {
            return -1;
        }

        for (i = 0; i < a_size; ++i) {
            a[i] = (unsigned char) normalize_bit(c[2 * i]);
        }
        for (i = 0; i < b_size; ++i) {
            b[i] = (unsigned char) normalize_bit(c[2 * i + 1]);
        }

        return a_size + b_size;
    }

    case MULTIPLEX_MODE_FDM: {
        int slot_count = max_int(a_size, b_size);

        if (c_len < slot_count) {
            return -1;
        }

        for (i = 0; i < slot_count; ++i) {
            unsigned char symbol = c[i];

            if ((symbol & 0xfc) != 0) {
                return -1;
            }
            if (i < a_size) {
                a[i] = (unsigned char) (symbol & 0x01);
            }
            if (i < b_size) {
                b[i] = (unsigned char) ((symbol >> 1) & 0x01);
            }
        }

        return a_size + b_size;
    }

    case MULTIPLEX_MODE_CDM: {
        int slot_count;

        if (c_len % 2 != 0) {
            return -1;
        }

        slot_count = c_len / 2;
        if (slot_count < max_int(a_size, b_size)) {
            return -1;
        }

        for (i = 0; i < slot_count; ++i) {
            int chip_1 = (int) c[2 * i] - 2;
            int chip_2 = (int) c[2 * i + 1] - 2;
            int projection_a;
            int projection_b;

            if (chip_1 < -2 || chip_1 > 2 || chip_2 < -2 || chip_2 > 2) {
                return -1;
            }

            projection_a = chip_1 + chip_2;
            projection_b = chip_1 - chip_2;

            if (i < a_size) {
                if (projection_a == 0) {
                    return -1;
                }
                a[i] = (unsigned char) (projection_a > 0 ? 1 : 0);
            }
            if (i < b_size) {
                if (projection_b == 0) {
                    return -1;
                }
                b[i] = (unsigned char) (projection_b > 0 ? 1 : 0);
            }
        }

        return a_size + b_size;
    }

    default:
        return -1;
    }
}
