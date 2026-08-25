"""Tests for the quilt-linker (using unittest)."""

import sys, os, tempfile, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quilt_linker import (
    parse_qm, link, DanglingLinkError, CycleError, ParseError,
    transitive_closure, _find_cycle, render_report
)


def write_qm(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".qm", delete=False)
    f.write(content)
    f.close()
    return Path(f.name)


class TestParser(unittest.TestCase):
    def test_parse_bind(self):
        p = write_qm("BIND bathy 4.2")
        m = parse_qm(p)
        self.assertEqual(m.binds, {"bathy": "4.2"})
        p.unlink()

    def test_parse_link(self):
        p = write_qm("BIND a 1\nBIND b 2\nLINK a b depends_on")
        m = parse_qm(p)
        self.assertEqual(m.links, [("a", "b", "depends_on")])
        p.unlink()

    def test_parse_view(self):
        p = write_qm("BIND x 1\nVIEW x anyone")
        m = parse_qm(p)
        self.assertEqual(m.views, [("x", "anyone")])
        p.unlink()

    def test_parse_effect(self):
        p = write_qm("BIND x 1\nEFFECT x inc dec")
        m = parse_qm(p)
        self.assertEqual(m.effects, [("x", "inc", "dec")])
        p.unlink()

    def test_parse_tick(self):
        p = write_qm("TICK 1.5")
        m = parse_qm(p)
        self.assertEqual(m.ticks, [1.5])
        p.unlink()

    def test_parse_comment(self):
        p = write_qm("# this is a comment\nBIND a 1\n# another\nBIND b 2")
        m = parse_qm(p)
        self.assertEqual(m.binds, {"a": "1", "b": "2"})
        p.unlink()

    def test_parse_error_garbage(self):
        p = write_qm("BOGUS a 1")
        with self.assertRaises(ParseError):
            parse_qm(p)
        p.unlink()


class TestLinker(unittest.TestCase):
    def test_link_happy_path(self):
        pa = write_qm("BIND a 1\nBIND b 2\nLINK a b depends_on")
        pb = write_qm("BIND c 3\nLINK c a depends_on")
        ma = parse_qm(pa); mb = parse_qm(pb)
        report = link([ma, mb])
        self.assertIn("a", report["all_binds"])
        self.assertIn("b", report["all_binds"])
        self.assertIn("c", report["all_binds"])
        self.assertEqual(len(report["errors"]), 0)
        pa.unlink(); pb.unlink()

    def test_link_dangling(self):
        pa = write_qm("BIND a 1\nLINK a missing depends_on")
        ma = parse_qm(pa)
        with self.assertRaises(DanglingLinkError):
            link([ma], strict=True)
        pa.unlink()

    def test_link_cycle(self):
        pa = write_qm("BIND a 1\nBIND b 2\nLINK a b depends_on\nLINK b a depends_on")
        ma = parse_qm(pa)
        with self.assertRaises(CycleError):
            link([ma], strict=True)
        # Verify the cycle is detected
        cycle = _find_cycle({"a": {"b"}, "b": {"a"}})
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle[0], cycle[-1])
        pa.unlink()

    def test_link_no_cycle_when_relation_differs(self):
        pa = write_qm("BIND a 1\nBIND b 2\nLINK a b depends_on\nLINK b a in")
        ma = parse_qm(pa)
        report = link([ma], strict=True)
        self.assertEqual(len(report["errors"]), 0)
        pa.unlink()

    def test_transitive_closure(self):
        pa = write_qm("BIND a 1\nBIND b 2\nBIND c 3\nLINK a b depends_on\nLINK b c depends_on")
        ma = parse_qm(pa)
        report = link([ma])
        tc = transitive_closure(report)
        self.assertIn("b", tc["a"])
        self.assertIn("c", tc["a"])
        self.assertIn("c", tc["b"])
        pa.unlink()

    def test_link_report(self):
        pa = write_qm("BIND a 1\nBIND b 2\nLINK a b depends_on\nVIEW a anyone")
        ma = parse_qm(pa)
        report = link([ma])
        text = render_report(report)
        self.assertIn("Modules linked: 1", text)
        self.assertIn("a", text)
        pa.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
