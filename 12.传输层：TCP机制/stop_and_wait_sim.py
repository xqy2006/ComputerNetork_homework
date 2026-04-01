from __future__ import annotations

import queue
import random
import threading
import time
from dataclasses import dataclass, field


@dataclass
class StopAndWaitResult:
    delivered: list[str] = field(default_factory=list)
    attempts: int = 0
    retransmissions: int = 0


def simulate_stop_and_wait(messages: list[str], loss_rate: float = 0.2, seed: int = 1) -> StopAndWaitResult:
    rng = random.Random(seed)
    data_queue: queue.Queue[tuple[int, str] | None] = queue.Queue()
    ack_queue: queue.Queue[int] = queue.Queue()
    result = StopAndWaitResult()

    def receiver() -> None:
        expected = 0
        while True:
            item = data_queue.get()
            if item is None:
                return
            seq, payload = item
            if rng.random() < loss_rate:
                continue
            if seq == expected:
                result.delivered.append(payload)
                expected ^= 1
            if rng.random() >= loss_rate:
                ack_queue.put(seq)

    thread = threading.Thread(target=receiver)
    thread.start()

    seq = 0
    for payload in messages:
        while True:
            result.attempts += 1
            data_queue.put((seq, payload))
            try:
                ack = ack_queue.get(timeout=0.05)
                if ack == seq:
                    seq ^= 1
                    break
            except queue.Empty:
                result.retransmissions += 1
    data_queue.put(None)
    thread.join()
    return result


if __name__ == "__main__":
    frames = ["pkt1", "pkt2", "pkt3", "pkt4"]
    outcome = simulate_stop_and_wait(frames, loss_rate=0.25, seed=7)
    print("delivered:", ",".join(outcome.delivered))
    print("attempts:", outcome.attempts)
    print("retransmissions:", outcome.retransmissions)
