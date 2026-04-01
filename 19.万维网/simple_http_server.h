#ifndef SIMPLE_HTTP_SERVER_H
#define SIMPLE_HTTP_SERVER_H

#include <stddef.h>

int sanitize_path(const char *request_path, char *output, size_t output_size);

#endif
