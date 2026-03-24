from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    base = Path(__file__).resolve().parent
    csv_path = base / "modulation_samples.csv"
    png_path = base / "modulation_signals.png"

    df = pd.read_csv(csv_path)

    fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

    axes[0].plot(df["index"], df["cover"], label="cover")
    axes[0].plot(df["index"], df["analog_message"], label="analog_message")
    axes[0].set_title("Carrier And Analog Message")
    axes[0].legend(loc="upper right")

    axes[1].step(df["index"], df["digital_message"], where="mid", label="digital_message")
    axes[1].plot(df["index"], df["digital_fsk"], label="digital_fsk")
    axes[1].plot(df["index"], df["analog_fm"], label="analog_fm")
    axes[1].set_title("Frequency Modulation")
    axes[1].legend(loc="upper right")

    axes[2].plot(df["index"], df["digital_ask"], label="digital_ask")
    axes[2].plot(df["index"], df["analog_am"], label="analog_am")
    axes[2].set_title("Amplitude Modulation")
    axes[2].legend(loc="upper right")

    axes[3].plot(df["index"], df["digital_psk"], label="digital_psk")
    axes[3].plot(df["index"], df["analog_pm"], label="analog_pm")
    axes[3].set_title("Phase Modulation")
    axes[3].legend(loc="upper right")
    axes[3].set_xlabel("sample index")

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
