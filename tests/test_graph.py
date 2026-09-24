"""Tests for quilt-linker."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quilt_linker import GraphSubstrate


class TestGraphSubstrate(unittest.TestCase):

    def test_find_links(self):
        """test_find_links"""
        substrate = GraphSubstrate()
        receipt = substrate.step(
            cell_id="c0",
            payload={"k": "v0"},
            status="ok",
        )
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.polarity, "ACCEPT")

    def test_resolve_known_link(self):
        """test_resolve_known_link"""
        substrate = GraphSubstrate()
        receipt = substrate.step(
            cell_id="c1",
            payload={"k": "v1"},
            status="ambiguous",
        )
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.polarity, "DRIFT")

    def test_resolve_ambiguous_link(self):
        """test_resolve_ambiguous_link"""
        substrate = GraphSubstrate()
        receipt = substrate.step(
            cell_id="c2",
            payload={"k": "v2"},
            status="fail",
        )
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.polarity, "REFUSE")

    def test_compose_chains(self):
        """test_compose_chains"""
        substrate = GraphSubstrate()
        receipt = substrate.step(
            cell_id="c3",
            payload={"k": "v3"},
            status="ok",
        )
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.polarity, "ACCEPT")

    def test_schema_mismatch_refusal(self):
        """test_schema_mismatch_refusal"""
        substrate = GraphSubstrate()
        receipt = substrate.step(
            cell_id="c4",
            payload={"k": "v4"},
            status="ambiguous",
        )
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.polarity, "DRIFT")


    def test_chain_intact(self):
        substrate = GraphSubstrate()
        for i in range(5):
            substrate.step(f"c{i}", {"i": i})
        self.assertTrue(substrate.chain_intact())

    def test_chain_broken_detected(self):
        substrate = GraphSubstrate()
        substrate.step("c0", {})
        substrate.last_witness_id = ""  # break the chain
        substrate.step("c1", {})
        self.assertFalse(substrate.chain_intact())

    def test_by_polarity(self):
        substrate = GraphSubstrate()
        substrate.step("c0", {}, "ok")
        substrate.step("c1", {}, "ambiguous")
        substrate.step("c2", {}, "fail")
        counts = substrate.by_polarity()
        self.assertEqual(counts["ACCEPT"], 1)
        self.assertEqual(counts["DRIFT"], 1)
        self.assertEqual(counts["REFUSE"], 1)


if __name__ == "__main__":
    unittest.main()
