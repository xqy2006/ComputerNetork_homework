from __future__ import annotations

import queue
import random
import threading
import time
from dataclasses import dataclass, field


@dataclass
class Snapshot:
    sent_and_acked: list[int]
    sent_unacked: list[int]
    allowed_unsent: list[int]
    disallowed: list[int]
    delivered: list[int]
    allowed_receive: list[int]
    disallowed_receive: list[int]
    advertised_window: int
    usable_window: int


@dataclass
class SlidingWindowResult:
    delivered: list[int] = field(default_factory=list)
    snapshots: list[Snapshot] = field(default_factory=list)


def simulate_sliding_window(total_frames: int = 8, window_size: int = 4, loss_rate: float = 0.2, seed: int = 5) -> SlidingWindowResult:
    rng = random.Random(seed)
    data_queue: queue.Queue[int | None] = queue.Queue()
    ack_queue: queue.Queue[int] = queue.Queue()
    result = SlidingWindowResult()
    lock = threading.Lock()

    sender_base = 0
    next_seq = 0
    acked: set[int] = set()
    receiver_base = 0
    received: set[int] = set()
    stop_flag = False

    def sender() -> None:
        nonlocal next_seq, stop_flag
        while not stop_flag:
            with lock:
                while next_seq < total_frames and next_seq < sender_base + window_size:
                    if rng.random() >= loss_rate:
                        data_queue.put(next_seq)
                    next_seq += 1
                # Simple timeout-retransmission model for frames still inside the sender window.
                for seq in range(sender_base, next_seq):
                    if seq not in acked and rng.random() >= loss_rate:
                        data_queue.put(seq)
            time.sleep(0.05)

    def receiver() -> None:
        nonlocal receiver_base
        while True:
            seq = data_queue.get()
            if seq is None:
                return
            if receiver_base <= seq < receiver_base + window_size:
                received.add(seq)
                while receiver_base in received:
                    result.delivered.append(receiver_base)
                    receiver_base += 1
                if rng.random() >= loss_rate:
                    ack_queue.put(seq)

    def ack_handler() -> None:
        nonlocal sender_base, stop_flag
        while not stop_flag:
            try:
                seq = ack_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            with lock:
                acked.add(seq)
                while sender_base in acked:
                    sender_base += 1
                if sender_base >= total_frames:
                    stop_flag = True

    sender_thread = threading.Thread(target=sender)
    receiver_thread = threading.Thread(target=receiver)
    ack_thread = threading.Thread(target=ack_handler)
    sender_thread.start()
    receiver_thread.start()
    ack_thread.start()

    while not stop_flag:
        with lock:
            sent_and_acked = list(range(sender_base))
            sent_unacked = [i for i in range(sender_base, next_seq) if i not in acked]
            allowed_unsent = list(range(next_seq, min(total_frames, sender_base + window_size)))
            disallowed = list(range(min(total_frames, sender_base + window_size), total_frames))
            allowed_receive = list(range(receiver_base, min(total_frames, receiver_base + window_size)))
            disallowed_receive = list(range(min(total_frames, receiver_base + window_size), total_frames))
            result.snapshots.append(
                Snapshot(
                    sent_and_acked=sent_and_acked,
                    sent_unacked=sent_unacked,
                    allowed_unsent=allowed_unsent,
                    disallowed=disallowed,
                    delivered=list(result.delivered),
                    allowed_receive=allowed_receive,
                    disallowed_receive=disallowed_receive,
                    advertised_window=window_size,
                    usable_window=max(0, sender_base + window_size - next_seq),
                )
            )
        time.sleep(1.0)

    data_queue.put(None)
    sender_thread.join()
    receiver_thread.join()
    ack_thread.join()
    result.snapshots.append(
        Snapshot(
            sent_and_acked=list(range(sender_base)),
            sent_unacked=[],
            allowed_unsent=[],
            disallowed=[],
            delivered=list(result.delivered),
            allowed_receive=[],
            disallowed_receive=[],
            advertised_window=window_size,
            usable_window=window_size,
        )
    )
    return result


if __name__ == "__main__":
    outcome = simulate_sliding_window(total_frames=8, window_size=4, loss_rate=0.15, seed=4)
    last = outcome.snapshots[-1]
    print("delivered:", outcome.delivered)
    print("sent_and_acked:", last.sent_and_acked)
    print("sent_unacked:", last.sent_unacked)
    print("allowed_unsent:", last.allowed_unsent)
    print("disallowed:", last.disallowed)
    print("allowed_receive:", last.allowed_receive)
    print("disallowed_receive:", last.disallowed_receive)
    print("advertised_window:", last.advertised_window)
    print("usable_window:", last.usable_window)
