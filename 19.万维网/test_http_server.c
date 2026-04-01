#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "simple_http_server.h"

static void expect_true(const char *name, int condition)
{
    if (!condition) {
        fprintf(stderr, "%s failed\n", name);
        exit(1);
    }
}

int main(void)
{
    char path[256];
    expect_true("root_maps_index", sanitize_path("/", path, sizeof(path)) && strcmp(path, "./index.html") == 0);
    expect_true("normal_path", sanitize_path("/hello.html", path, sizeof(path)) && strcmp(path, "./hello.html") == 0);
    expect_true("reject_parent", !sanitize_path("/../../secret.txt", path, sizeof(path)));
    printf("All HTTP server tests passed.\n");
    return 0;
}
