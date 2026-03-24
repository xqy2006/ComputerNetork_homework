#ifndef MULTIPLEX_H
#define MULTIPLEX_H

typedef enum {
    MULTIPLEX_MODE_STATISTICAL_TDM = 0,
    MULTIPLEX_MODE_SYNCHRONOUS_TDM = 1,
    MULTIPLEX_MODE_FDM = 2,
    MULTIPLEX_MODE_CDM = 3
} multiplex_mode_t;

void multiplex_set_mode(multiplex_mode_t mode);
multiplex_mode_t multiplex_get_mode(void);
const char *multiplex_mode_name(multiplex_mode_t mode);

int multiplex(
    unsigned char *c,
    const int c_size,
    const unsigned char *a,
    const int a_len,
    const unsigned char *b,
    const int b_len
);

int demultiplex(
    unsigned char *a,
    const int a_size,
    unsigned char *b,
    const int b_size,
    const unsigned char *c,
    const int c_len
);

#endif
