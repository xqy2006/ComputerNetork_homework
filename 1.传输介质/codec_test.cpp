#include <iostream>

#include "bw_codec.hpp"
#include "octal_codec.hpp"

int main() {
    std::cout << "== BW file encode/decode test ==\n";
    for (int msg = 0; msg <= 1; ++msg) {
        bw::send(msg);
        int got = bw::receive();
        std::cout << "msg=" << msg << " -> recv=" << got << "\n";
    }

    std::cout << "\n== Octal file encode/decode test ==\n";
    for (int msg = 0; msg <= 7; ++msg) {
        octal::send(msg);
        int got = octal::receive();
        std::cout << "msg=" << msg << " -> recv=" << got << "\n";
    }

    std::cout << "\nOutput images saved to out/bw_msg.png and out/octal_msg.png\n";
    return 0;
}
