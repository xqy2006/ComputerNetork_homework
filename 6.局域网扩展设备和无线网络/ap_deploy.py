from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import json
import math

import matplotlib.pyplot as plt
import numpy as np


WIDTH_M = 100.0
HEIGHT_M = 80.0
FLOOR_COUNT = 3
DEFAULT_CELL_SIZE_M = 2.5
DEFAULT_FLOOR_HEIGHT_M = 3.5
THRESHOLD_DBM = -65.0
TX_POWER_DBM = -35.0
FLOOR_PENALTY_DB = 18.0
OPEN_TILES = {"R", "C", "O", "."}
WALL_ATTENUATION_DB = {"B": 12.0, "P": 6.0, "G": 7.0}
BAND_ORDER = ("2.4GHz", "5GHz")
BAND_SPECS = {
    "2.4GHz": {"slope_db_per_meter": 1.2, "channels": ("1", "6", "11"), "reuse_distance_m": 18.0},
    "5GHz": {"slope_db_per_meter": 2.0, "channels": ("36", "40", "44", "48"), "reuse_distance_m": 10.0},
}


@dataclass(frozen=True)
class Candidate:
    floor: int
    row: int
    col: int


@dataclass
class AP:
    floor: int
    row: int
    col: int
    x: float
    y: float
    channel_24: str
    channel_5: str
    newly_covered: int
    score: float


@dataclass
class Building:
    floors: list[np.ndarray]
    cell_size_m: float = DEFAULT_CELL_SIZE_M
    floor_height_m: float = DEFAULT_FLOOR_HEIGHT_M

    @property
    def rows(self) -> int:
        return int(self.floors[0].shape[0])

    @property
    def cols(self) -> int:
        return int(self.floors[0].shape[1])


def _normalize_floor(matrix: list[str] | list[list[str]]) -> np.ndarray:
    if not matrix:
        raise ValueError("floor matrix cannot be empty")
    if isinstance(matrix[0], str):
        rows = [str(item) for item in matrix]
    else:
        rows = ["".join(str(cell) for cell in row) for row in matrix]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("all rows in a floor matrix must have equal width")
    return np.array([list(row) for row in rows], dtype="<U1")


def _floor_to_strings(floor: np.ndarray) -> list[str]:
    return ["".join(row.tolist()) for row in floor]


def load_building(layout_path: str | Path) -> Building:
    payload = json.loads(Path(layout_path).read_text(encoding="utf-8"))
    floors = [_normalize_floor(item) for item in payload["floors"]]
    if len(floors) != FLOOR_COUNT:
        raise ValueError(f"expected {FLOOR_COUNT} floor matrices")
    return Building(
        floors=floors,
        cell_size_m=float(payload.get("cell_size_m", DEFAULT_CELL_SIZE_M)),
        floor_height_m=float(payload.get("floor_height_m", DEFAULT_FLOOR_HEIGHT_M)),
    )


def generate_default_building(cell_size_m: float = DEFAULT_CELL_SIZE_M) -> Building:
    rows = int(round(HEIGHT_M / cell_size_m))
    cols = int(round(WIDTH_M / cell_size_m))
    corridor_row = rows // 2

    def base_floor(variant: int) -> np.ndarray:
        grid = np.full((rows, cols), "R", dtype="<U1")

        grid[:, 0] = "B"
        grid[:, -1] = "B"
        grid[0, :] = "G"
        grid[-1, :] = "G"

        grid[corridor_row, 1:-1] = "C"
        grid[corridor_row - 1, 1:-1] = "P"
        grid[corridor_row + 1, 1:-1] = "P"

        for col in range(6, cols - 1, 6):
            for row in range(1, corridor_row - 1):
                grid[row, col] = "P"
            for row in range(corridor_row + 2, rows - 1):
                grid[row, col] = "P"
            if corridor_row - 2 > 0:
                grid[corridor_row - 2, col] = "R"
            if corridor_row + 2 < rows - 1:
                grid[corridor_row + 2, col] = "R"

        for row in range(5, corridor_row - 1, 4):
            grid[row, 1:-1] = "P"
            for col in range(3, cols - 1, 6):
                grid[row, col] = "R"
        for row in range(corridor_row + 5, rows - 1, 4):
            grid[row, 1:-1] = "P"
            for col in range(3, cols - 1, 6):
                grid[row, col] = "R"

        if variant == 1:
            grid[1:4, cols // 2 - 2 : cols // 2 + 2] = "O"
            grid[0, cols // 2 - 2 : cols // 2 + 2] = "G"
        elif variant == 2:
            shaft_col = cols // 2
            grid[4 : rows - 4, shaft_col] = "B"
            grid[corridor_row, shaft_col] = "C"
            grid[corridor_row - 1, shaft_col] = "P"
            grid[corridor_row + 1, shaft_col] = "P"
        else:
            grid[2:6, 2:8] = "O"
            grid[1, 2:8] = "G"
            grid[2:6, cols - 8 : cols - 2] = "O"
            grid[1, cols - 8 : cols - 2] = "G"

        return grid

    floors = [base_floor(variant) for variant in (1, 2, 3)]
    return Building(floors=floors, cell_size_m=cell_size_m, floor_height_m=DEFAULT_FLOOR_HEIGHT_M)


def _cell_center(building: Building, row: int, col: int) -> tuple[float, float]:
    return ((col + 0.5) * building.cell_size_m, (row + 0.5) * building.cell_size_m)


def _iter_open_cells(building: Building) -> list[tuple[int, int, int]]:
    cells: list[tuple[int, int, int]] = []
    for floor_index, floor in enumerate(building.floors):
        for row in range(building.rows):
            for col in range(building.cols):
                if floor[row, col] in OPEN_TILES:
                    cells.append((floor_index, row, col))
    return cells


def _iter_candidates(building: Building) -> list[Candidate]:
    candidates: list[Candidate] = []
    for floor_index, floor in enumerate(building.floors):
        for row in range(building.rows):
            for col in range(building.cols):
                tile = floor[row, col]
                if tile not in OPEN_TILES:
                    continue
                if tile == "C" or (row % 2 == 1 and col % 2 == 1):
                    candidates.append(Candidate(floor=floor_index, row=row, col=col))
    return candidates


def _bresenham(row0: int, col0: int, row1: int, col1: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    d_row = abs(row1 - row0)
    d_col = abs(col1 - col0)
    step_row = 1 if row0 < row1 else -1
    step_col = 1 if col0 < col1 else -1
    err = d_col - d_row
    row = row0
    col = col0
    while True:
        points.append((row, col))
        if row == row1 and col == col1:
            break
        twice_err = 2 * err
        if twice_err > -d_row:
            err -= d_row
            col += step_col
        if twice_err < d_col:
            err += d_col
            row += step_row
    return points


def _wall_loss(
    building: Building,
    floor_index: int,
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    cache: dict[tuple[int, int, int, int, int], float],
) -> float:
    key = (floor_index, start_row, start_col, end_row, end_col)
    if key in cache:
        return cache[key]

    seen: set[tuple[int, int]] = set()
    loss = 0.0
    for row, col in _bresenham(start_row, start_col, end_row, end_col):
        if (row, col) == (start_row, start_col) or (row, col) == (end_row, end_col):
            continue
        tile = building.floors[floor_index][row, col]
        if tile in WALL_ATTENUATION_DB and (row, col) not in seen:
            loss += WALL_ATTENUATION_DB[tile]
            seen.add((row, col))

    cache[key] = loss
    cache[(floor_index, end_row, end_col, start_row, start_col)] = loss
    return loss


def _signal_strength(
    building: Building,
    candidate: Candidate,
    band: str,
    target: tuple[int, int, int],
    wall_cache: dict[tuple[int, int, int, int, int], float],
) -> float:
    target_floor, target_row, target_col = target
    x0, y0 = _cell_center(building, candidate.row, candidate.col)
    x1, y1 = _cell_center(building, target_row, target_col)
    planar_distance = math.hypot(x1 - x0, y1 - y0)
    signal = TX_POWER_DBM - BAND_SPECS[band]["slope_db_per_meter"] * planar_distance

    if candidate.floor == target_floor:
        signal -= _wall_loss(building, candidate.floor, candidate.row, candidate.col, target_row, target_col, wall_cache)
    else:
        signal -= FLOOR_PENALTY_DB * abs(candidate.floor - target_floor)
        signal -= 0.5 * planar_distance

    return signal


def _precompute_candidate_maps(
    building: Building,
) -> tuple[list[tuple[int, int, int]], list[Candidate], dict[Candidate, dict[str, dict[int, float]]]]:
    open_cells = _iter_open_cells(building)
    candidates = _iter_candidates(building)
    wall_cache: dict[tuple[int, int, int, int, int], float] = {}
    coverage_maps: dict[Candidate, dict[str, dict[int, float]]] = {}

    for candidate in candidates:
        band_maps: dict[str, dict[int, float]] = {band: {} for band in BAND_ORDER}
        combined: dict[int, float] = {}
        for idx, target in enumerate(open_cells):
            best = -1e9
            for band in BAND_ORDER:
                signal = _signal_strength(building, candidate, band, target, wall_cache)
                if signal >= THRESHOLD_DBM:
                    band_maps[band][idx] = signal
                    best = max(best, signal)
            if best >= THRESHOLD_DBM:
                combined[idx] = best
        band_maps["combined"] = combined
        coverage_maps[candidate] = band_maps

    return open_cells, candidates, coverage_maps


def _coverage_summary(
    building: Building,
    open_cells: list[tuple[int, int, int]],
    best_signal: list[float],
) -> dict[int, float]:
    total = {floor: 0 for floor in range(1, len(building.floors) + 1)}
    covered = {floor: 0 for floor in range(1, len(building.floors) + 1)}
    for idx, (floor_index, _, _) in enumerate(open_cells):
        floor = floor_index + 1
        total[floor] += 1
        if best_signal[idx] >= THRESHOLD_DBM:
            covered[floor] += 1
    return {floor: covered[floor] / total[floor] for floor in total}


def _candidate_score(
    candidate: Candidate,
    existing: list[Candidate],
    band_maps: dict[str, dict[int, float]],
    open_cells: list[tuple[int, int, int]],
    best_signal: list[float],
    building: Building,
) -> tuple[float, int]:
    combined = band_maps["combined"]
    if not combined:
        return (-1e9, 0)

    newly_covered = 0
    overlap = 0
    own_floor_bonus = 0.0
    for idx in combined:
        if best_signal[idx] < THRESHOLD_DBM:
            newly_covered += 1
            if open_cells[idx][0] == candidate.floor:
                own_floor_bonus += 0.5
        else:
            overlap += 1

    penalty = 0.0
    x0, y0 = _cell_center(building, candidate.row, candidate.col)
    for other in existing:
        if other.floor != candidate.floor:
            continue
        x1, y1 = _cell_center(building, other.row, other.col)
        distance = math.hypot(x0 - x1, y0 - y1)
        if distance < 8.0:
            penalty += 15.0
        elif distance < 14.0:
            penalty += 6.0

    score = newly_covered * 3.5 + own_floor_bonus - overlap * 0.8 - penalty
    return (score, newly_covered)


def optimize_ap_layout(
    building: Building,
    coverage_target: float = 0.95,
    max_aps: int = 36,
) -> tuple[list[AP], dict[int, float]]:
    open_cells, candidates, coverage_maps = _precompute_candidate_maps(building)
    best_signal = [-1e9] * len(open_cells)
    selected: list[Candidate] = []
    selected_aps: list[AP] = []
    used_positions: set[tuple[int, int, int]] = set()

    while True:
        current_coverages = _coverage_summary(building, open_cells, best_signal)
        if all(ratio >= coverage_target for ratio in current_coverages.values()):
            break
        if len(selected) >= max_aps:
            break

        best_candidate: Candidate | None = None
        best_score = -1e9
        best_newly_covered = 0

        for candidate in candidates:
            if (candidate.floor, candidate.row, candidate.col) in used_positions:
                continue
            score, newly_covered = _candidate_score(
                candidate,
                selected,
                coverage_maps[candidate],
                open_cells,
                best_signal,
                building,
            )
            if score > best_score:
                best_candidate = candidate
                best_score = score
                best_newly_covered = newly_covered

        if best_candidate is None or best_score <= 0:
            break

        selected.append(best_candidate)
        used_positions.add((best_candidate.floor, best_candidate.row, best_candidate.col))
        for idx, signal in coverage_maps[best_candidate]["combined"].items():
            best_signal[idx] = max(best_signal[idx], signal)
        x, y = _cell_center(building, best_candidate.row, best_candidate.col)
        selected_aps.append(
            AP(
                floor=best_candidate.floor + 1,
                row=best_candidate.row,
                col=best_candidate.col,
                x=x,
                y=y,
                channel_24="",
                channel_5="",
                newly_covered=best_newly_covered,
                score=best_score,
            )
        )

    _assign_channels(building, selected, selected_aps, coverage_maps)
    return selected_aps, _coverage_summary(building, open_cells, best_signal)


def _conflict_weight(
    building: Building,
    left: Candidate,
    right: Candidate,
    band: str,
    coverage_maps: dict[Candidate, dict[str, dict[int, float]]],
) -> float:
    overlap = len(set(coverage_maps[left][band]).intersection(coverage_maps[right][band]))
    if overlap == 0:
        return 0.0
    x0, y0 = _cell_center(building, left.row, left.col)
    x1, y1 = _cell_center(building, right.row, right.col)
    distance = math.hypot(x0 - x1, y0 - y1)
    reuse_distance = BAND_SPECS[band]["reuse_distance_m"]
    distance_penalty = max(0.0, reuse_distance - distance)
    return overlap + distance_penalty * 6.0


def _assign_channels(
    building: Building,
    selected: list[Candidate],
    selected_aps: list[AP],
    coverage_maps: dict[Candidate, dict[str, dict[int, float]]],
) -> None:
    for band in BAND_ORDER:
        channels = BAND_SPECS[band]["channels"]
        assignments: dict[Candidate, str] = {}
        ordered = sorted(selected, key=lambda item: len(coverage_maps[item][band]), reverse=True)
        for candidate in ordered:
            channel_scores = {}
            for channel in channels:
                score = 0.0
                for other, other_channel in assignments.items():
                    if other_channel != channel:
                        continue
                    score += _conflict_weight(building, candidate, other, band, coverage_maps)
                channel_scores[channel] = score
            assignments[candidate] = min(channel_scores, key=channel_scores.get)

        for candidate, ap in zip(selected, selected_aps):
            if band == "2.4GHz":
                ap.channel_24 = assignments[candidate]
            else:
                ap.channel_5 = assignments[candidate]


def build_floor_heatmap(
    building: Building,
    aps: list[AP],
    floor: int,
) -> tuple[np.ndarray, float]:
    floor_index = floor - 1
    heat = np.full((building.rows, building.cols), -95.0, dtype=float)
    wall_cache: dict[tuple[int, int, int, int, int], float] = {}
    covered = 0
    total = 0

    for row in range(building.rows):
        for col in range(building.cols):
            tile = building.floors[floor_index][row, col]
            if tile not in OPEN_TILES:
                continue
            total += 1
            strongest = -95.0
            target = (floor_index, row, col)
            for ap in aps:
                candidate = Candidate(ap.floor - 1, ap.row, ap.col)
                for band in BAND_ORDER:
                    strongest = max(strongest, _signal_strength(building, candidate, band, target, wall_cache))
            heat[row, col] = strongest
            if strongest >= THRESHOLD_DBM:
                covered += 1

    ratio = covered / total if total else 0.0
    return heat, ratio


def write_outputs(
    base: Path,
    layout_path: str | Path | None = None,
    coverage_target: float = 0.95,
    max_aps: int = 36,
) -> tuple[Building, list[AP], dict[int, float]]:
    base.mkdir(parents=True, exist_ok=True)
    building = load_building(layout_path) if layout_path else generate_default_building()
    aps, coverages = optimize_ap_layout(building, coverage_target=coverage_target, max_aps=max_aps)

    layout_json = base / "building_layout.json"
    plan_csv = base / "ap_plan.csv"
    plan_json = base / "ap_plan.json"
    heatmap_png = base / "ap_heatmap.png"

    layout_payload = {
        "cell_size_m": building.cell_size_m,
        "floor_height_m": building.floor_height_m,
        "floors": [_floor_to_strings(floor) for floor in building.floors],
    }
    layout_json.write_text(json.dumps(layout_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with plan_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["floor", "x_m", "y_m", "row", "col", "channel_24", "channel_5", "newly_covered", "score"])
        for ap in aps:
            writer.writerow([ap.floor, f"{ap.x:.2f}", f"{ap.y:.2f}", ap.row, ap.col, ap.channel_24, ap.channel_5, ap.newly_covered, f"{ap.score:.2f}"])

    payload = {
        "aps": [asdict(ap) for ap in aps],
        "coverage": {str(floor): ratio for floor, ratio in coverages.items()},
        "threshold_dbm": THRESHOLD_DBM,
        "cell_size_m": building.cell_size_m,
    }
    plan_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fig, axes = plt.subplots(1, len(building.floors), figsize=(16, 4), constrained_layout=True)
    if len(building.floors) == 1:
        axes = [axes]
    for floor in range(1, len(building.floors) + 1):
        heat, ratio = build_floor_heatmap(building, aps, floor)
        ax = axes[floor - 1]
        im = ax.imshow(heat, origin="lower", extent=[0, WIDTH_M, 0, HEIGHT_M], cmap="viridis", vmin=-90, vmax=-35)
        floor_aps = [ap for ap in aps if ap.floor == floor]
        ax.scatter([ap.x for ap in floor_aps], [ap.y for ap in floor_aps], c="red", s=20)
        ax.set_title(f"Floor {floor} coverage {ratio:.1%}")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
    fig.colorbar(im, ax=axes, label="Best signal (dBm)")
    fig.savefig(heatmap_png, dpi=160)

    return building, aps, coverages


def summarize_coverages(layout_path: str | Path | None = None) -> dict[int, float]:
    building = load_building(layout_path) if layout_path else generate_default_building()
    _, coverages = optimize_ap_layout(building)
    return coverages


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deploy APs from three floor matrices and generate a heatmap.")
    parser.add_argument("--layout", help="JSON file containing three floor matrices.")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--target", type=float, default=0.95)
    parser.add_argument("--max-aps", type=int, default=36)
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    building, aps, coverages = write_outputs(output_dir, layout_path=args.layout, coverage_target=args.target, max_aps=args.max_aps)
    print(f"layout saved to: {output_dir / 'building_layout.json'}")
    print(f"AP plan saved to: {output_dir / 'ap_plan.csv'}")
    print(f"heatmap saved to: {output_dir / 'ap_heatmap.png'}")
    print(f"AP count: {len(aps)}")
    for floor, ratio in coverages.items():
        print(f"floor {floor}: {ratio:.1%}")
