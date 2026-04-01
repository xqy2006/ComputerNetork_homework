import sys

from multicast_transfer import send_file


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample.bin"
    send_file(path)
    print(f"sent {path}")
