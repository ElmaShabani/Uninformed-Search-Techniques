"""Run the search demonstrations or their built-in tests."""
import argparse
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
SCRIPTS = {
    "golfers": ROOT / "1_social_golfers/social_golfers.py",
    "sudoku": ROOT / "2_sudoku/sudoku_bfs.py",
    "latin": ROOT / "3_latin_square/latin_square_iddfs.py",
}
TREE_PDFS = (
    ROOT / "4_search_trees/8_Puzzles.pdf",
    ROOT / "4_search_trees/Missionaries_and_Cannibals.pdf",
    ROOT / "4_search_trees/Rotating_Workforce_Scheduling.pdf",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("all", *SCRIPTS, "trees"), default="all")
    parser.add_argument("--test", action="store_true", help="Run the built-in solver tests.")
    args = parser.parse_args()
    selected = SCRIPTS if args.task == "all" else {
        key: path for key, path in SCRIPTS.items() if key == args.task}
    if args.test:
        for path in selected.values():
            subprocess.run([sys.executable, "-B", str(path), "--test"], check=True)
        return 0

    for name, path in selected.items():
        module = SimpleNamespace(**runpy.run_path(str(path)))
        if name == "golfers":
            result = module.solve(8, 4, 3)
            if result["status"] != "solved" or not module.valid(result["schedule"], 8, 4, 3):
                raise RuntimeError("Social Golfers demonstration did not produce a valid schedule.")
            print("Social Golfers DFS: solved")
            for week, groups in enumerate(result["schedule"], 1):
                print(f"Week {week}: " + " | ".join(",".join(map(str, group)) for group in groups))
            if not module.valid(module.REFERENCE_SCHEDULE, 8, 4, 10):
                raise RuntimeError("The ten-week reference schedule is invalid.")
            print("Ten-week reference: valid (separate from the DFS demonstration)")
            print("Landscape:", module.landscape(8, 4, 3))
        elif name == "sudoku":
            for level, rows in module.PUZZLES.items():
                initial = module.parse(rows)
                result = module.solve(initial)
                if result["status"] != "solved" or not module.solved(result["solution"]):
                    raise RuntimeError(f"Sudoku {level} was not solved.")
                if any(clue and clue != result["solution"][i] for i, clue in enumerate(initial)):
                    raise RuntimeError("A Sudoku clue was changed.")
                print(f"Sudoku BFS {level}: solved")
                module.show(result["solution"])
                print("Landscape:", module.landscape(initial))
        else:
            result = module.solve(5)
            if result["status"] != "solved" or not module.valid(result["grid"]):
                raise RuntimeError("Latin Square demonstration did not produce a valid grid.")
            print("Latin Square IDDFS 5x5: solved")
            for row in result["grid"]:
                print(*row)
            print("Landscape:", module.landscape(5))

    if args.task in ("all", "trees"):
        print("Hand-drawn search trees:")
        for path in TREE_PDFS:
            if not path.is_file():
                raise FileNotFoundError(path)
            print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
