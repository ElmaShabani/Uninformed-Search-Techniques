"""Search trees, solution paths, and DOT/HTML export using the standard library.

Run: python3 search_trees/solver.py
Default tree depths are 3 for 8-Puzzle, 11 for Missionaries and Cannibals,
and 6 for Workforce. The displayed trees are separate from full BFS paths.
Workforce uses an illustrative model with 3 employees, a 6-day cycle,
2 workers per day, 4 workdays per employee, a 2-day rotation offset,
and at most 2 consecutive workdays, including across the cycle boundary.
"""
import argparse
from collections import deque
from dataclasses import dataclass
from html import escape
import json
from pathlib import Path

PUZZLE_START = (1, 2, 3, 4, 0, 6, 7, 5, 8)
PUZZLE_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
MC_START = (3, 3, 0)  # Missionaries on the left, cannibals on the left, boat: 0 left / 1 right.
MC_GOAL = (0, 0, 1)


def puzzle_children(state):
    blank = state.index(0)
    r, c = divmod(blank, 3)
    for dr, dc, name in ((-1, 0, "lart"), (1, 0, "poshtë"),
                         (0, -1, "majtas"), (0, 1, "djathtas")):
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            target = nr * 3 + nc
            child = list(state)
            child[blank], child[target] = child[target], child[blank]
            yield "Bosh " + name, tuple(child)


def mc_safe(m, c):
    return (0 <= m <= 3 and 0 <= c <= 3 and (m == 0 or m >= c)
            and (3 - m == 0 or 3 - m >= 3 - c))


def mc_children(state):
    m, c, boat = state
    for dm, dc in ((1, 0), (2, 0), (0, 1), (0, 2), (1, 1)):
        sign = -1 if boat == 0 else 1
        nm, nc = m + sign * dm, c + sign * dc
        if mc_safe(nm, nc):
            yield f"{dm}M,{dc}C " + ("→" if boat == 0 else "←"), (nm, nc, 1 - boat)


@dataclass(frozen=True)
class Workforce:
    """Example model: a shared cyclic pattern shifted for each employee."""
    employees: int = 3
    days: int = 6
    offset: int = 2
    workdays: int = 4
    min_coverage: int = 2
    max_coverage: int = 2
    max_consecutive: int = 2

    def __post_init__(self):
        if (self.employees < 1 or self.days < 1 or not 0 <= self.workdays <= self.days
                or not 0 <= self.min_coverage <= self.max_coverage <= self.employees
                or self.max_consecutive < 1):
            raise ValueError("Parametra të pavlefshëm për Workforce.")

    def schedule(self, pattern):
        return [tuple(pattern[(d + worker * self.offset) % self.days]
                      for d in range(self.days)) for worker in range(self.employees)]

    def goal(self, pattern):
        if len(pattern) != self.days or sum(pattern) != self.workdays:
            return False
        if any(x not in (0, 1) for x in pattern):
            return False
        # Check cyclic runs, including the boundary between the last and first day.
        if all(pattern):
            return False  # An all-work cycle has no rest break.
        for start in range(self.days):
            if all(pattern[(start + k) % self.days]
                   for k in range(self.max_consecutive + 1)):
                return False
        return all(self.min_coverage <= sum(row[d] for row in self.schedule(pattern))
                   <= self.max_coverage for d in range(self.days))

    def children(self, pattern):
        if len(pattern) == self.days:
            return
        for value in (0, 1):
            child = pattern + (value,)
            remaining = self.days - len(child)
            if sum(child) > self.workdays or sum(child) + remaining < self.workdays:
                continue
            if len(child) > self.max_consecutive and all(child[-self.max_consecutive-1:]):
                continue
            if len(child) == self.days and not self.goal(child):
                continue
            yield f"Dita {len(child)}: " + ("punë" if value else "pushim"), child


def bfs_path(start, goal, successors):
    queue = deque([start])
    parent = {start: None}
    while queue:
        state = queue.popleft()
        if goal(state):
            path = []
            while parent[state] is not None:
                previous, action = parent[state]
                path.append({"state": list(state), "action": action})
                state = previous
            path.append({"state": list(state), "action": "Fillimi"})
            return list(reversed(path))
        for action, child in successors(state):
            if child not in parent:
                parent[child] = (state, action)
                queue.append(child)
    return None


def build_tree(start, goal, successors, max_depth=3, max_nodes=200):
    """Repeated states are shown as leaves referencing their first occurrence."""
    if max_depth < 0 or max_nodes < 1:
        raise ValueError("Kërkohet depth >= 0 dhe max_nodes >= 1.")
    nodes = [{"id": 0, "state": start, "depth": 0, "parent": None,
              "action": "Fillimi", "goal": goal(start), "repeat": None}]
    seen = {start: 0}
    queue = deque([0])
    truncated = False
    while queue:
        index = queue.popleft()
        node = nodes[index]
        if node["goal"]:
            continue
        if node["depth"] == max_depth:
            if next(iter(successors(node["state"])), None) is not None:
                truncated = True
            continue
        for action, state in successors(node["state"]):
            if len(nodes) >= max_nodes:
                return nodes, True
            repeat = seen.get(state)
            new_id = len(nodes)
            nodes.append({"id": new_id, "state": state, "depth": node["depth"] + 1,
                          "parent": index, "action": action, "goal": goal(state),
                          "repeat": repeat})
            if repeat is None:
                seen[state] = new_id
                queue.append(new_id)
    return nodes, truncated


def state_label(state, kind):
    if kind == "8_puzzle":
        return "\n".join(" ".join(str(x) if x else "_" for x in state[i:i+3])
                         for i in (0, 3, 6))
    if kind == "missionaries":
        m, c, b = state
        return f"Majtas {m}M {c}C\nDjathtas {3-m}M {3-c}C\nVarka: {'M' if b == 0 else 'D'}"
    return "".join("P" if x else "O" for x in state) or "Model bosh"


def export(nodes, truncated, kind, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    dot = ["digraph search {", "rankdir=TB;", 'node [shape=box, fontname="Arial"];']
    children = {node["id"]: [] for node in nodes}
    labels = {}
    for node in nodes:
        idx = node["id"]
        label = f"#{idx}\n" + state_label(node["state"], kind)
        if node["goal"]:
            label += "\nZGJIDHJE"
        if node["repeat"] is not None:
            label += f"\nPërsëritje e #{node['repeat']}"
        labels[idx] = label
        dot.append(f"n{idx} [label={json.dumps(label, ensure_ascii=False)}];")
        if node["parent"] is not None:
            parent = node["parent"]
            children[parent].append(idx)
            dot.append(f"n{parent} -> n{idx} [label={json.dumps(node['action'], ensure_ascii=False)}];")
    dot.append("}")
    (destination / f"{kind}.dot").write_text("\n".join(dot), encoding="utf-8")
    # Lay out SVG nodes from the leaves upward; Graphviz is not required.
    positions, leaf = {}, [0]

    def layout(idx):
        if not children[idx]:
            x = 110 + leaf[0] * 210
            leaf[0] += 1
        else:
            xs = [layout(child) for child in children[idx]]
            x = sum(xs) / len(xs)
        positions[idx] = (x, 70 + nodes[idx]["depth"] * 180)
        return x

    layout(0)
    width, height = max(400, leaf[0] * 210), 160 + max(n["depth"] for n in nodes) * 180
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    for node in nodes[1:]:
        x, y = positions[node["id"]]
        px, py = positions[node["parent"]]
        svg.append(f'<path d="M {px} {py+55} L {x} {y-55}" stroke="#94a3b8" fill="none"/>')
        svg.append(f'<text x="{(x+px)/2}" y="{(y+py)/2}" text-anchor="middle" font-size="11">'
                   + escape(node["action"]) + '</text>')
    for node in nodes:
        x, y = positions[node["id"]]
        fill = "#dcfce7" if node["goal"] else ("#fef3c7" if node["repeat"] is not None else "#eff6ff")
        svg.append(f'<rect x="{x-95}" y="{y-55}" width="190" height="110" rx="10" '
                   f'fill="{fill}" stroke="#475569"/>')
        for line, text in enumerate(labels[node["id"]].splitlines()):
            svg.append(f'<text x="{x}" y="{y-32+line*17}" text-anchor="middle" '
                       'font-family="monospace" font-size="12">' + escape(text) + '</text>')
    svg.append('</svg>')
    note = "Pamje e kufizuar nga thellësia/nyjat." if truncated else "Të gjitha degët e arritshme u trajtuan (përsëritjet nuk zgjerohen)."
    html = ('<!doctype html><html lang="sq"><meta charset="utf-8"><title>' + kind + '</title>'
            '<style>body{font-family:system-ui;margin:28px;color:#172033}main{overflow:auto;'
            'border:1px solid #ddd;border-radius:12px}h1{font-size:24px}</style>'
            f'<h1>Pema e kërkimit: {kind}</h1><p>{note} Jeshile = zgjidhje; '
            'verdhë = gjendje e vizituar. P = punë, O = pushim. Lëviz horizontalisht për degët.</p>'
            '<main>' + ''.join(svg) + '</main></html>')
    (destination / f"{kind}.html").write_text(html, encoding="utf-8")
    (destination / f"{kind}.json").write_text(json.dumps(
        {"truncated": truncated, "nodes": nodes}, ensure_ascii=False, indent=2), encoding="utf-8")
    text_tree = [f"Pema: {kind}", note, ""]

    def describe(idx, prefix="", tail=True):
        node = nodes[idx]
        annotation = " [ZGJIDHJE]" if node["goal"] else ""
        if node["repeat"] is not None:
            annotation += f" [përsëritje e #{node['repeat']}]"
        text_tree.append(prefix + ("└── " if tail else "├── ") + f"#{idx} "
                         + node["action"] + ": " + str(node["state"]) + annotation)
        for pos, child in enumerate(children[idx]):
            describe(child, prefix + ("    " if tail else "│   "), pos == len(children[idx])-1)

    describe(0)
    (destination / f"{kind}.txt").write_text("\n".join(text_tree), encoding="utf-8")


DEFAULT_DEPTHS = {"8_puzzle": 3, "missionaries": 11, "workforce": 6}


def generate(destination=None, depth=None):
    if destination is None:
        destination = Path(__file__).parent / "examples"
    if depth is None:
        depth = DEFAULT_DEPTHS
    workforce = Workforce()
    problems = {
        "8_puzzle": (PUZZLE_START, lambda s: s == PUZZLE_GOAL, puzzle_children),
        "missionaries": (MC_START, lambda s: s == MC_GOAL, mc_children),
        "workforce": ((), workforce.goal, workforce.children),
    }
    results = {}
    for kind, (start, goal, successors) in problems.items():
        limit = depth[kind] if isinstance(depth, dict) else depth
        nodes, truncated = build_tree(start, goal, successors, max_depth=limit)
        export(nodes, truncated, kind, destination)
        path = bfs_path(start, goal, successors)
        results[kind] = {"path": path, "moves": len(path) - 1 if path else None,
                         "tree_nodes": len(nodes), "tree_truncated": truncated}
        print(kind, "hapa:", results[kind]["moves"], "nyja në pamje:", len(nodes))
    results["workforce"]["schedule"] = workforce.schedule(tuple(results["workforce"]["path"][-1]["state"]))
    (Path(destination) / "solutions.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=None,
                        help="Override the default depth for all three trees.")
    parser.add_argument("--output", default=str(Path(__file__).parent / "examples"))
    args = parser.parse_args()
    generate(args.output, args.depth)
