# quilt-linker

> Linker — substrate-to-substrate linking across the fleet

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-5+-brightgreen.svg)](tests/)
[![Brewed by](https://img.shields.io/badge/brewed_by-quilt--brewer-purple.svg)](https://github.com/SuperInstance/quilt-brewer)

## What is this?

Brewed by `quilt-brewer` from the `quilt-linker` recipe. Implements the
canonical substrate walker pattern (199 LOC wrapper + tests + demo).

## Polarity rules

| Polarity | Status |
|---|---|
| **ACCEPT** | `ok` |
| **DRIFT** | `ambiguous` |
| **REFUSE** | `fail` |

## Operations

- find_links
- resolve
- compose_chains

## Usage

```python
from quilt_linker import GraphSubstrate

substrate = GraphSubstrate()
receipt = substrate.step("cell-id", {"key": "value"}, status="ok")
print(receipt.polarity)  # ACCEPT
```

## Run tests

```bash
python3 -m unittest tests.test_graph -v
```

## Run demo

```bash
python3 examples/demo.py
```

## License

Apache-2.0
