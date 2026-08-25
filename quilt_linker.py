"""
quilt-linker — A real linker-level 5-opcode linker for .qm modules.

Layer 3 of the polyformalism: the 5 opcodes (BIND, LINK, EFFECT, VIEW, TICK)
materialize as symbols with typed references at the module level.
The linker catches dangling LINKs and LINK cycles at compile time.

.qm file format (one declaration per line):
    BIND name value
    LINK from to relation
    EFFECT target forward_fn inverse_fn
    VIEW target viewer
    TICK dt
    # comments allowed
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional


# === Token kinds ===
BIND = "BIND"
LINK = "LINK"
EFFECT = "EFFECT"
VIEW = "VIEW"
TICK = "TICK"


# === Errors ===

class LinkError(Exception):
    pass


class DanglingLinkError(LinkError):
    pass


class CycleError(LinkError):
    pass


class ParseError(Exception):
    pass


# === Module ===

class Module:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.binds: dict[str, str] = {}
        self.links: list[tuple[str, str, str]] = []
        self.effects: list[tuple[str, str, str]] = []
        self.views: list[tuple[str, str]] = []
        self.ticks: list[float] = []
        self.imports: list[str] = []  # for future: IMPORT other.qm

    def __repr__(self):
        return f"Module({self.name}, binds={len(self.binds)}, links={len(self.links)})"


# === Parser ===

def parse_qm(path: Path) -> Module:
    """Parse a .qm file into a Module."""
    mod = Module(name=path.stem, path=path)
    with open(path) as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split(None, 3)  # max 4 tokens
            if len(tokens) < 2:
                raise ParseError(f"{path}:{lineno}: too few tokens: {raw!r}")
            op = tokens[0].upper()
            try:
                if op == BIND:
                    if len(tokens) < 2:
                        raise ParseError(f"BIND needs a name")
                    mod.binds[tokens[1]] = tokens[2] if len(tokens) >= 3 else ""
                elif op == LINK:
                    if len(tokens) < 4:
                        raise ParseError(f"LINK needs 3 args: from to relation")
                    mod.links.append((tokens[1], tokens[2], tokens[3]))
                elif op == EFFECT:
                    if len(tokens) < 4:
                        raise ParseError(f"EFFECT needs 3 args: target fwd inv")
                    mod.effects.append((tokens[1], tokens[2], tokens[3]))
                elif op == VIEW:
                    if len(tokens) < 3:
                        raise ParseError(f"VIEW needs 2 args: target viewer")
                    mod.views.append((tokens[1], tokens[2]))
                elif op == TICK:
                    if len(tokens) < 2:
                        raise ParseError(f"TICK needs a dt")
                    mod.ticks.append(float(tokens[1]))
                else:
                    raise ParseError(f"{path}:{lineno}: unknown op: {op}")
            except (ValueError, IndexError) as e:
                raise ParseError(f"{path}:{lineno}: {e}")
    return mod


# === Linker ===

def link(modules: list[Module], strict: bool = True) -> dict:
    """Link a set of modules. Returns the link report.

    Errors caught at link time (the polyformalism invariant):
      - DanglingLinkError: a LINK points to a name that no module BINDs
      - CycleError: a "depends_on" relation forms a cycle
    """
    report = {
        "modules": [],
        "all_binds": {},  # name -> (module, value)
        "all_links": [],  # (from_mod, to_mod, from, to, relation)
        "errors": [],
    }
    # First, register all BINDs
    for m in modules:
        report["modules"].append(m.name)
        for name, value in m.binds.items():
            if name in report["all_binds"]:
                # Same name in two modules: depends_on duplicate is OK if same module
                if strict and report["all_binds"][name][0] != m.name:
                    report["errors"].append(
                        f"DUPLICATE BIND: {name} in both {report['all_binds'][name][0]} and {m.name}"
                    )
            else:
                report["all_binds"][name] = (m.name, value)

    # Then check all LINKs
    for m in modules:
        for from_name, to_name, relation in m.links:
            if to_name not in report["all_binds"]:
                msg = f"DANGLING LINK in {m.name}: {from_name} --{relation}--> {to_name} (not BIND'd anywhere)"
                report["errors"].append(msg)
                if strict:
                    raise DanglingLinkError(msg)
            else:
                to_mod, _ = report["all_binds"][to_name]
                report["all_links"].append((m.name, to_mod, from_name, to_name, relation))

    # Check cycles in "depends_on" relations
    dep_graph = defaultdict(set)
    for from_mod, to_mod, from_name, to_name, relation in report["all_links"]:
        if relation == "depends_on":
            dep_graph[from_name].add(to_name)
    cycle = _find_cycle(dep_graph)
    if cycle:
        msg = f"DEPENDS_ON CYCLE: {' -> '.join(cycle)} -> {cycle[0]}"
        report["errors"].append(msg)
        if strict:
            raise CycleError(msg)
        report["cycle"] = cycle

    return report


def _find_cycle(graph: dict[str, set]) -> Optional[list[str]]:
    """Find a cycle in the dependency graph. Returns the cycle path or None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    parent = {}

    def dfs(u, path):
        color[u] = GRAY
        for v in graph.get(u, set()):
            if color[v] == GRAY:
                # Cycle: from v back to v through u
                cycle = path[path.index(v):] + [v]
                return cycle
            if color[v] == WHITE:
                parent[v] = u
                result = dfs(v, path + [v])
                if result:
                    return result
        color[u] = BLACK
        return None

    for node in list(graph.keys()):
        if color[node] == WHITE:
            result = dfs(node, [node])
            if result:
                return result
    return None


def transitive_closure(report: dict) -> dict:
    """Compute the transitive closure of the dependency graph."""
    deps = defaultdict(set)
    for from_mod, to_mod, from_name, to_name, relation in report["all_links"]:
        if relation == "depends_on":
            deps[from_name].add(to_name)
    # Floyd-Warshall style
    nodes = list(deps.keys())
    for k in nodes:
        for i in list(deps.keys()):
            if k in deps[i]:
                deps[i] |= deps[k]
    return {k: sorted(v) for k, v in deps.items()}


def render_report(report: dict) -> str:
    """Render a human-readable link report."""
    lines = ["=" * 60, "Quilt Module Link Report", "=" * 60, ""]
    lines.append(f"Modules linked: {len(report['modules'])}")
    for m in report["modules"]:
        lines.append(f"  - {m}")
    lines.append("")
    lines.append(f"Total BINDs: {len(report['all_binds'])}")
    for name, (mod, value) in sorted(report["all_binds"].items()):
        lines.append(f"  {name:30} = {value!r:20}  in {mod}")
    lines.append("")
    lines.append(f"Total LINKs: {len(report['all_links'])}")
    for from_mod, to_mod, from_name, to_name, relation in report["all_links"]:
        lines.append(f"  {from_name:20} --{relation:15}--> {to_name:20}  ({from_mod} -> {to_mod})")
    lines.append("")
    if report.get("errors"):
        lines.append(f"ERRORS: {len(report['errors'])}")
        for e in report["errors"]:
            lines.append(f"  ! {e}")
    else:
        lines.append("No errors. Module graph is sound.")
    return "\n".join(lines)


# === CLI ===

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: quilt_linker.py <file1.qm> [file2.qm ...]", file=sys.stderr)
        return 1
    paths = [Path(p) for p in argv[1:]]
    try:
        modules = [parse_qm(p) for p in paths]
        report = link(modules, strict=True)
    except LinkError as e:
        print(f"LINK ERROR: {e}", file=sys.stderr)
        return 2
    except ParseError as e:
        print(f"PARSE ERROR: {e}", file=sys.stderr)
        return 3
    print(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
