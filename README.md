# quilt-linker

A real linker-level 5-opcode linker for `.qm` modules. **Layer 3 of
the polyformalism**: the 5 opcodes (BIND, LINK, EFFECT, VIEW, TICK)
materialize as **symbols with typed references** at the module level.

The linker catches errors **at link time, not runtime:**

- **Dangling LINKs** — a LINK points to a name that no module BINDs
- **Cycles** in `depends_on` relations (transitive dependency analysis)
- **Duplicate BINDs** across modules

## The .qm file format

One declaration per line:

```
BIND name value
LINK from to relation
EFFECT target forward_fn inverse_fn
VIEW target viewer
TICK dt
# comments allowed
```

## Run

```bash
python3 quilt_linker.py file1.qm file2.qm ...
```

## Tests

```bash
python3 tests/test_linker.py
```

13 tests, all passing. The 5-opcode invariant holds: the substrate
is one, the form is many.

## Example

```bash
python3 quilt_linker.py examples/01-bathy.qm examples/02-spreadsheet.qm examples/03-bus.qm
```

Output: a link report showing all BINDs, all LINKs, all dependencies,
and a transitive-closure report of the dependency graph.

## The polyformalism

This is the same 5-opcode substrate expressed as a linker. In
language-level syntax (Python decorators, Rust proc-macros) the
substrate is decorators and traits. In the linker, the substrate is
typed references and dependency graphs. In the runtime, the substrate
is allocations and reachability. **The substrate is one. The
forms are many.**

## Version

0.1.0 — first public release.
