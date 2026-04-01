from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import math

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class AP:
    floor: int
    x: float
    y: float
    band: str
    channel: str


WIDTH = 100
HEIGHT = 80
FLOORS = 3
GRID = 2
THRESHOLD = -65.0
TX_POWER = -35.0


APS = [
    AP(1, 20, 20, "2.4GHz", "1"),
    AP(1, 50, 20, "5GHz", "36"),
    AP(1, 80, 20, "2.4GHz", "6"),
    AP(1, 20, 60, "5GHz", "40"),
    AP(1, 50, 60, "2.4GHz", "11"),
    AP(1, 80, 60, "5GHz", "44"),
    AP(2, 20, 20, "5GHz", "48"),
    AP(2, 50, 20, "2.4GHz", "1"),
    AP(2, 80, 20, "5GHz", "36"),
    AP(2, 20, 60, "2.4GHz", "6"),
    AP(2, 50, 60, "5GHz", "40"),
    AP(2, 80, 60, "2.4GHz", "11"),
    AP(3, 20, 20, "2.4GHz", "1"),
    AP(3, 50, 20, "5GHz", "44"),
    AP(3, 80, 20, "2.4GHz", "6"),
    AP(3, 20, 60, "5GHz", "48"),
    AP(3, 50, 60, "2.4GHz", "11"),
    AP(3, 80, 60, "5GHz", "36"),
]


def estimate_signal(ap: AP, x: float, y: float) -> float:
    distance = math.hypot(ap.x - x, ap.y - y)
    base_loss = distance * (1.1 if ap.band == "2.4GHz" else 1.5)
    corridor_loss = 0 if 39 <= y <= 41 else 6
    return TX_POWER - base_loss - corridor_loss


def build_floor_heatmap(floor: int) -> tuple[np.ndarray, float]:
    xs = np.arange(0, WIDTH + GRID, GRID)
    ys = np.arange(0, HEIGHT + GRID, GRID)
    heat = np.zeros((len(ys), len(xs)))
    covered = 0
    total = heat.size

    floor_aps = [ap for ap in APS if ap.floor == floor]

    for yi, y in enumerate(ys):
        for xi, x in enumerate(xs):
            strongest = max(estimate_signal(ap, float(x), float(y)) for ap in floor_aps)
            heat[yi, xi] = strongest
            if strongest >= THRESHOLD:
                covered += 1

    return heat, covered / total


def write_outputs(base: Path) -> None:
    csv_path = base / "ap_plan.csv"
    json_path = base / "ap_plan.json"
    png_path = base / "ap_heatmap.png"

    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["floor", "x", "y", "band", "channel"])
        for ap in APS:
            writer.writerow([ap.floor, ap.x, ap.y, ap.band, ap.channel])

    coverages = {}
    with json_path.open("w", encoding="utf-8") as fp:
        payload = {"aps": [ap.__dict__ for ap in APS], "coverage": {}}
        for floor in range(1, FLOORS + 1):
            _, ratio = build_floor_heatmap(floor)
            coverages[floor] = ratio
            payload["coverage"][str(floor)] = ratio
        json.dump(payload, fp, ensure_ascii=False, indent=2)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4), constrained_layout=True)
    for floor in range(1, FLOORS + 1):
        heat, ratio = build_floor_heatmap(floor)
        ax = axes[floor - 1]
        im = ax.imshow(heat, origin="lower", extent=[0, WIDTH, 0, HEIGHT], cmap="viridis", vmin=-90, vmax=-35)
        floor_aps = [ap for ap in APS if ap.floor == floor]
        ax.scatter([ap.x for ap in floor_aps], [ap.y for ap in floor_aps], c="red", s=24)
        ax.set_title(f"Floor {floor} coverage {ratio:.1%}")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
    fig.colorbar(im, ax=axes.ravel().tolist(), label="dBm")
    fig.savefig(png_path, dpi=160)


def summarize_coverages() -> dict[int, float]:
    return {floor: build_floor_heatmap(floor)[1] for floor in range(1, FLOORS + 1)}


if __name__ == "__main__":
    write_outputs(Path(__file__).resolve().parent)
