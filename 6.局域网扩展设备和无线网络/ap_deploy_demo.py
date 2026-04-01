from pathlib import Path

from ap_deploy import summarize_coverages, write_outputs


def main() -> None:
    base = Path(__file__).resolve().parent
    write_outputs(base)
    coverages = summarize_coverages()
    print("AP deployment outputs generated:")
    for floor, ratio in coverages.items():
        print(f"floor {floor}: {ratio:.1%}")
    print(f"files: {base / 'ap_plan.csv'}, {base / 'ap_plan.json'}, {base / 'ap_heatmap.png'}")


if __name__ == "__main__":
    main()
