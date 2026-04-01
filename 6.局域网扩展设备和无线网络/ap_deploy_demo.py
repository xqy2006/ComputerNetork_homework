from pathlib import Path

from ap_deploy import write_outputs


def main() -> None:
    base = Path(__file__).resolve().parent
    _, aps, coverages = write_outputs(base)
    print("AP deployment outputs generated from three floor matrices:")
    print(f"ap count: {len(aps)}")
    for floor, ratio in coverages.items():
        print(f"floor {floor}: {ratio:.1%}")
    print(f"layout: {base / 'building_layout.json'}")
    print(f"plan: {base / 'ap_plan.csv'}")
    print(f"heatmap: {base / 'ap_heatmap.png'}")


if __name__ == "__main__":
    main()
