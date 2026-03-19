#include "rs232c.h"

enum {
    RS232C_DATA_BITS = 7,
    RS232C_FRAME_BITS = 10
};

static const double RS232C_MARK_VOLT = -5.0;
static const double RS232C_SPACE_VOLT = 5.0;
static const double RS232C_MARK_THRESHOLD = -3.0;
static const double RS232C_SPACE_THRESHOLD = 3.0;

static double bit_to_voltage(int bit)
{
    return bit ? RS232C_MARK_VOLT : RS232C_SPACE_VOLT;
}

static int voltage_to_bit(double volt)
{
    if (volt <= RS232C_MARK_THRESHOLD) {
        return 1;
    }
    if (volt >= RS232C_SPACE_THRESHOLD) {
        return 0;
    }
    return -1;
}

int rs232c_encode(double *volts, int volts_size, const char *msg, int size)
{
    int i;
    int frame_offset;
    int required;

    if (size < 0 || volts_size < 0) {
        return -1;
    }
    if (size > 0 && (volts == 0 || msg == 0)) {
        return -1;
    }

    required = size * RS232C_FRAME_BITS;
    if (volts_size < required) {
        return -1;
    }

    for (i = 0; i < size; ++i) {
        unsigned char ch = (unsigned char) msg[i];
        int bit;

        if (ch > 0x7f) {
            return -1;
        }

        frame_offset = i * RS232C_FRAME_BITS;
        volts[frame_offset] = bit_to_voltage(1);
        volts[frame_offset + 1] = bit_to_voltage(0);

        for (bit = 0; bit < RS232C_DATA_BITS; ++bit) {
            volts[frame_offset + 2 + bit] = bit_to_voltage((ch >> bit) & 0x01);
        }

        volts[frame_offset + RS232C_FRAME_BITS - 1] = bit_to_voltage(1);
    }

    return required;
}

int rs232c_decode(char *msg, int size, const double *volts, int volts_size)
{
    int frame_count;
    int i;

    if (size < 0 || volts_size < 0) {
        return -1;
    }
    if (volts_size == 0) {
        if (msg != 0 && size > 0) {
            msg[0] = '\0';
        }
        return 0;
    }
    if (msg == 0 || volts == 0) {
        return -1;
    }
    if (volts_size % RS232C_FRAME_BITS != 0) {
        return -1;
    }

    frame_count = volts_size / RS232C_FRAME_BITS;
    if (size < frame_count) {
        return -1;
    }

    for (i = 0; i < frame_count; ++i) {
        int frame_offset = i * RS232C_FRAME_BITS;
        int idle_bit = voltage_to_bit(volts[frame_offset]);
        int start_bit = voltage_to_bit(volts[frame_offset + 1]);
        int stop_bit = voltage_to_bit(volts[frame_offset + RS232C_FRAME_BITS - 1]);
        unsigned char ch = 0;
        int bit;

        if (idle_bit != 1 || start_bit != 0 || stop_bit != 1) {
            return -1;
        }

        for (bit = 0; bit < RS232C_DATA_BITS; ++bit) {
            int value = voltage_to_bit(volts[frame_offset + 2 + bit]);

            if (value < 0) {
                return -1;
            }

            ch |= (unsigned char) (value << bit);
        }

        msg[i] = (char) ch;
    }

    if (size > frame_count) {
        msg[frame_count] = '\0';
    }

    return frame_count;
}
