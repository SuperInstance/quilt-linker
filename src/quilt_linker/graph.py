"""graph.py — the quilt-linker substrate walker."""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


# Polarity rules (filled in from recipe)
_POLARITY_RULES = {
        "ok": "ACCEPT",
        "ambiguous": "DRIFT",
        "fail": "REFUSE",
    "unknown": "DRIFT",  # default
}

DEFAULT_POLARITY = "DRIFT"


def status_to_polarity(status: str) -> str:
    """Map a substrate-specific status to ACCEPT/DRIFT/REFUSE."""
    return _POLARITY_RULES.get(status.lower(), DEFAULT_POLARITY)


@dataclass
class GraphReceipt:
    """One walker step's witness — canonical envelope (8 fields)."""
    witness_id: str
    prev_witness_id: str
    cell_id: str
    substrate: str = "quilt-linker"
    polarity: str = "DRIFT"
    status: str = ""
    timestamp: float = field(default_factory=time.time)
    payload: dict = field(default_factory=dict)


def _witness_id(cell_id: str, payload: dict) -> str:
    """sha256-of-canonical: hash the cell_id + payload."""
    h = hashlib.sha256()
    h.update(cell_id.encode("utf-8"))
    h.update(json.dumps(payload, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()[:16]


class GraphSubstrate:
    """The quilt-linker walker — handles graph inputs."""

    def __init__(self):
        self.last_witness_id = ""
        self.receipts: list = []

    def step(self, cell_id: str, payload: dict, status: str = "ok"):
        """One step of the walker — emits one receipt."""
        pol = status_to_polarity(status)
        wid = _witness_id(cell_id, payload)
        receipt = GraphReceipt(
            witness_id=wid,
            prev_witness_id=self.last_witness_id,
            cell_id=cell_id,
            polarity=pol,
            status=status,
            payload=payload,
        )
        self.last_witness_id = wid
        self.receipts.append(receipt)
        return receipt

    def chain_intact(self) -> bool:
        """Verify all receipts chain properly."""
        prev = ""
        for r in self.receipts:
            if r.prev_witness_id != prev:
                return False
            prev = r.witness_id
        return True

    def reset(self):
        """Reset the substrate to genesis state."""
        self.last_witness_id = ""
        self.receipts = []

    def by_polarity(self) -> dict:
        """Count receipts by polarity."""
        counts = {"ACCEPT": 0, "DRIFT": 0, "REFUSE": 0}
        for r in self.receipts:
            counts[r.polarity] = counts.get(r.polarity, 0) + 1
        return counts
