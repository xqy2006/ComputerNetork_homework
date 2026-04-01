#include "simple_http_server.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#define close_socket closesocket
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#define close_socket close
typedef int SOCKET;
#define INVALID_SOCKET (-1)
#define SOCKET_ERROR (-1)
#endif

static void send_text(SOCKET client, const char *status, const char *content_type, const char *body)
{
    char header[512];
    const int body_len = (int)strlen(body);
    snprintf(
        header,
        sizeof(header),
        "HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",
        status,
        content_type,
        body_len
    );
    send(client, header, (int)strlen(header), 0);
    send(client, body, body_len, 0);
}

int sanitize_path(const char *request_path, char *output, size_t output_size)
{
    if (strstr(request_path, "..") != NULL) {
        return 0;
    }
    if (strcmp(request_path, "/") == 0) {
        request_path = "/index.html";
    }
    snprintf(output, output_size, ".%s", request_path);
    return 1;
}

static void handle_client(SOCKET client)
{
    char request[2048];
    int received = recv(client, request, sizeof(request) - 1, 0);
    char method[16];
    char path[512];
    char local_path[600];
    FILE *fp;
    long size;
    char *buffer;
    char header[512];

    if (received <= 0) {
        close_socket(client);
        return;
    }
    request[received] = '\0';

    if (sscanf(request, "%15s %511s", method, path) != 2) {
        send_text(client, "400 Bad Request", "text/plain; charset=utf-8", "Bad Request");
        close_socket(client);
        return;
    }
    if (strcmp(method, "GET") != 0) {
        send_text(client, "405 Method Not Allowed", "text/plain; charset=utf-8", "Method Not Allowed");
        close_socket(client);
        return;
    }
    if (!sanitize_path(path, local_path, sizeof(local_path))) {
        send_text(client, "403 Forbidden", "text/plain; charset=utf-8", "Forbidden");
        close_socket(client);
        return;
    }

    fp = fopen(local_path, "rb");
    if (fp == NULL) {
        send_text(client, "404 Not Found", "text/plain; charset=utf-8", "Not Found");
        close_socket(client);
        return;
    }
    fseek(fp, 0, SEEK_END);
    size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    buffer = (char *)malloc((size_t)size);
    if (buffer == NULL) {
        fclose(fp);
        send_text(client, "500 Internal Server Error", "text/plain; charset=utf-8", "Internal Server Error");
        close_socket(client);
        return;
    }
    fread(buffer, 1, (size_t)size, fp);
    fclose(fp);

    snprintf(
        header,
        sizeof(header),
        "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %ld\r\nConnection: close\r\n\r\n",
        size
    );
    send(client, header, (int)strlen(header), 0);
    send(client, buffer, (int)size, 0);
    free(buffer);
    close_socket(client);
}

#ifndef HTTP_SERVER_NO_MAIN
int main(int argc, char **argv)
{
    unsigned short port = 8080;
    SOCKET server_fd;
    struct sockaddr_in addr;

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return 1;
    }
#endif

    if (argc > 1) {
        port = (unsigned short)atoi(argv[1]);
    }

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == INVALID_SOCKET) {
        fprintf(stderr, "socket failed\n");
        return 1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) == SOCKET_ERROR) {
        fprintf(stderr, "bind failed\n");
        close_socket(server_fd);
        return 1;
    }
    if (listen(server_fd, 8) == SOCKET_ERROR) {
        fprintf(stderr, "listen failed\n");
        close_socket(server_fd);
        return 1;
    }

    printf("HTTP server listening on http://127.0.0.1:%u\n", port);
    while (1) {
        SOCKET client = accept(server_fd, NULL, NULL);
        if (client == INVALID_SOCKET) {
            continue;
        }
        handle_client(client);
    }

    close_socket(server_fd);
    return 0;
}
#endif
