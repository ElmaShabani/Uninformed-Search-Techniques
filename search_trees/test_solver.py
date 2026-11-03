"""Tests for legal solution paths, cyclic scheduling, and bounded trees."""
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from itertools import product
import xml.etree.ElementTree as ET
import solver as trees


class TreeTests(unittest.TestCase):
    def test_default_exports_include_solutions(self):
        with TemporaryDirectory() as directory:
            results = trees.generate(directory)
            for kind in trees.DEFAULT_DEPTHS:
                with self.subTest(kind=kind):
                    destination = Path(directory)
                    data = json.loads((destination / f"{kind}.json").read_text())
                    self.assertTrue(any(node["goal"] for node in data["nodes"]))
                    html = (destination / f"{kind}.html").read_text()
                    svg = html[html.index("<svg"):html.index("</svg>") + 6]
                    root = ET.fromstring(svg)
                    self.assertEqual(len(root.findall("{http://www.w3.org/2000/svg}rect")),
                                     len(data["nodes"]))
                    self.assertTrue((destination / f"{kind}.dot").is_file())
                    self.assertTrue((destination / f"{kind}.txt").is_file())
            saved = json.loads((Path(directory) / "solutions.json").read_text())
            self.assertEqual(saved, json.loads(json.dumps(results)))

    def test_workforce_cycle_boundary(self):
        model = trees.Workforce(min_coverage=0, max_coverage=3)
        # These patterns have four workdays but violate the cyclic run limit.
        self.assertFalse(model.goal((1, 1, 0, 0, 1, 1)))
        self.assertTrue(model.goal((1, 1, 0, 1, 1, 0)))

    def assert_legal_path(self, path, successors):
        self.assertIsNotNone(path)
        for before, after in zip(path, path[1:]):
            self.assertIn((after["action"], tuple(after["state"])), list(successors(tuple(before["state"]))))

    def test_puzzle_shortest_path(self):
        path = trees.bfs_path(trees.PUZZLE_START, lambda s: s == trees.PUZZLE_GOAL,
                              trees.puzzle_children)
        self.assert_legal_path(path, trees.puzzle_children)
        self.assertEqual(len(path) - 1, 2)

    def test_missionaries_shortest_path_and_safety(self):
        path = trees.bfs_path(trees.MC_START, lambda s: s == trees.MC_GOAL, trees.mc_children)
        self.assert_legal_path(path, trees.mc_children)
        self.assertEqual(len(path) - 1, 11)
        self.assertTrue(all(trees.mc_safe(*step["state"][:2]) for step in path))

    def test_workforce_against_exhaustive_oracle(self):
        model = trees.Workforce()
        valid_patterns = {p for p in product((0, 1), repeat=6) if model.goal(p)}
        queue, reachable = [()], set()
        while queue:
            state = queue.pop()
            if len(state) == 6:
                reachable.add(state)
            queue.extend(child for _, child in model.children(state))
        self.assertTrue(valid_patterns)
        self.assertEqual(reachable, valid_patterns)
        path = trees.bfs_path((), model.goal, model.children)
        self.assert_legal_path(path, model.children)
        schedule = model.schedule(path[-1]["state"])
        self.assertTrue(all(sum(row[d] for row in schedule) == 2 for d in range(6)))

    def test_repeats_and_truncation(self):
        nodes, limited = trees.build_tree(trees.PUZZLE_START, lambda s: s == trees.PUZZLE_GOAL,
                                          trees.puzzle_children, max_depth=2)
        self.assertTrue(limited)
        self.assertTrue(any(n["repeat"] is not None for n in nodes))
        self.assertTrue(any(n["goal"] for n in nodes))
        self.assertEqual(len(trees.build_tree(trees.MC_START, lambda _: False,
                                              trees.mc_children, max_nodes=1)[0]), 1)


if __name__ == "__main__":
    unittest.main()
