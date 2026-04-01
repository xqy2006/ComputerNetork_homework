from pathlib import Path
import json

from ap_deploy import (
    BAND_SPECS,
    THRESHOLD_DBM,
    build_floor_heatmap,
    generate_default_building,
    load_building,
    optimize_ap_layout,
    write_outputs,
)


def main() -> None:
    building = generate_default_building()
    assert len(building.floors) == 3
    assert building.rows > 0 and building.cols > 0

    aps, coverages = optimize_ap_layout(building, coverage_target=0.92, max_aps=36)
    assert len(aps) >= 6
    for ratio in coverages.values():
        assert ratio >= 0.92

    for ap in aps:
        assert ap.channel_24 in BAND_SPECS["2.4GHz"]["channels"]
        assert ap.channel_5 in BAND_SPECS["5GHz"]["channels"]

    for floor in range(1, 4):
        heat, ratio = build_floor_heatmap(building, aps, floor)
        assert heat.size > 0
        assert ratio >= 0.92
        assert heat.max() >= THRESHOLD_DBM

    base = Path(__file__).resolve().parent
    written_building, written_aps, written_coverages = write_outputs(base, coverage_target=0.92, max_aps=36)
    payload = json.loads((base / "building_layout.json").read_text(encoding="utf-8"))
    assert len(payload["floors"]) == 3
    reloaded = load_building(base / "building_layout.json")
    assert reloaded.rows == written_building.rows
    assert len(written_aps) == len(aps)
    assert written_coverages[1] >= 0.92
    print("All AP deployment tests passed.")


if __name__ == "__main__":
    main()
