#ifndef RS232C_H
#define RS232C_H

int rs232c_encode(double *volts, int volts_size, const char *msg, int size);
int rs232c_decode(char *msg, int size, const double *volts, int volts_size);

#endif
