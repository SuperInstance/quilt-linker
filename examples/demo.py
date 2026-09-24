"""quilt-linker demo — substrate walker at the graph layer."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quilt_linker import GraphSubstrate


def main():
    print("\n" + "=" * 60)
    print("🌱 quilt-linker demo")
    print("=" * 60)

    substrate = GraphSubstrate()

    for i, status in enumerate(["ok", "warn", "ok", "fail", "ok"]):
        receipt = substrate.step(f"c{i}", {"i": i, "value": i * 10}, status)
        print(f"  Step {i+1}: {receipt.polarity:6}  cell_id={receipt.cell_id}  witness={receipt.witness_id[:8]}")

    print(f"\n  Chain intact: {substrate.chain_intact()}")
    print(f"  Total receipts: {len(substrate.receipts)}")
    counts = substrate.by_polarity()
    print(f"  By polarity: ACCEPT={counts['ACCEPT']} DRIFT={counts['DRIFT']} REFUSE={counts['REFUSE']}")

    print("\n" + "=" * 60)
    print("✅ Demo complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
