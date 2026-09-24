"""quilt-linker — Linker — substrate-to-substrate linking across the fleet.

Brewed by quilt-brewer from recipe 'quilt-linker'.

Polarity rules:
  - ACCEPT: ok
  - DRIFT: ambiguous
  - REFUSE: fail
"""
from .graph import GraphSubstrate

__version__ = "0.1.0"
__all__ = ["GraphSubstrate"]
