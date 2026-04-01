import datetime as dt

from ntp_server import NTPPacket, build_ntp_reply, parse_time_string


def make_request() -> bytes:
    packet = NTPPacket(
        li_vn_mode=(0 << 6) | (4 << 3) | 3,
        stratum=0,
        poll=4,
        precision=0,
        root_delay=0,
        root_dispersion=0,
        ref_id=0,
        ref_ts_sec=0,
        ref_ts_frac=0,
        orig_ts_sec=0,
        orig_ts_frac=0,
        recv_ts_sec=0,
        recv_ts_frac=0,
        tx_ts_sec=100,
        tx_ts_frac=200,
    )
    return packet.to_bytes()


def main() -> None:
    fixed_time = parse_time_string("2019-05-01 10:41:00")
    reply = NTPPacket.from_bytes(build_ntp_reply(make_request(), fixed_time))
    assert reply.stratum == 1
    assert reply.orig_ts_sec == 100
    assert reply.orig_ts_frac == 200
    assert reply.tx_ts_sec == reply.recv_ts_sec
    assert fixed_time == dt.datetime(2019, 5, 1, 10, 41, 0, tzinfo=dt.timezone.utc)
    print("All NTP server tests passed.")


if __name__ == "__main__":
    main()
