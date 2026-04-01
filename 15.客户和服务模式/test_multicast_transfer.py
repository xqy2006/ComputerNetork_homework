from multicast_transfer import decode_chunk, encode_chunk


def main() -> None:
    packet = encode_chunk(3, b"hello", False)
    seq, eof, payload = decode_chunk(packet)
    assert seq == 3
    assert eof is False
    assert payload == b"hello"

    eof_packet = encode_chunk(9, b"", True)
    seq, eof, payload = decode_chunk(eof_packet)
    assert seq == 9
    assert eof is True
    assert payload == b""
    print("All multicast transfer tests passed.")


if __name__ == "__main__":
    main()
