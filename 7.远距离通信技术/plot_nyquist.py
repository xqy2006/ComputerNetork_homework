from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_csv(csv_name: str, title: str, target: str) -> None:
    base = Path(__file__).resolve().parent
    frame = pd.read_csv(base / csv_name)
    plt.figure(figsize=(10, 4))
    plt.plot(frame["time"], frame["original"], label="original", linewidth=1.6)
    plt.plot(frame["time"], frame["reconstructed"], label="reconstructed", linewidth=1.2)
    plt.title(title)
    plt.xlabel("time (s)")
    plt.ylabel("amplitude")
    plt.legend()
    plt.tight_layout()
    plt.savefig(base / target, dpi=160)
    plt.close()


if __name__ == "__main__":
    plot_csv("nyquist_good.csv", "Sample rate 150 Hz (> 2*fmax)", "nyquist_good.png")
    plot_csv("nyquist_bad.csv", "Sample rate 80 Hz (< 2*fmax)", "nyquist_bad.png")
