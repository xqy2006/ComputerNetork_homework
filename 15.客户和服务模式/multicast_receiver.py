import sys

from multicast_transfer import receive_file


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "received.bin"
    receive_file(output)
    print(f"saved to {output}")
