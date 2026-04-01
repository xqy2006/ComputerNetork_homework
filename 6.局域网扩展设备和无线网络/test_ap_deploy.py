from pathlib import Path
import json

from ap_deploy import APS, FLOORS, THRESHOLD, build_floor_heatmap, write_outputs


def main() -> None:
    assert len(APS) == 18
    for floor in range(1, FLOORS + 1):
        heat, ratio = build_floor_heatmap(floor)
        assert heat.size > 0
        assert ratio > 0.60

    base = Path(__file__).resolve().parent
    write_outputs(base)
    payload = json.loads((base / "ap_plan.json").read_text(encoding="utf-8"))
    assert payload["coverage"]["1"] > 0.60
    assert payload["coverage"]["2"] > 0.60
    assert payload["coverage"]["3"] > 0.60
    print("All AP deployment tests passed.")


if __name__ == "__main__":
    main()
