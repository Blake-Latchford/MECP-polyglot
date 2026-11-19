import dataclasses
import json
import unittest
from pathlib import Path

import mecp

ROOT = Path(__file__).resolve().parents[2]
VECTORS = json.loads((ROOT / "vectors/mecp-vectors.json").read_text(encoding="utf-8"))
UPSTREAM = ROOT / "upstream/freetext"
FIELDS = ("pax", "gps", "timestamp", "language", "callsign", "reference", "duration")


def decoded_json(d: mecp.Decoded) -> dict:
    out = dataclasses.asdict(d)
    del out["raw"]
    return out


class Vectors(unittest.TestCase):
    def test_decode(self):
        for c in VECTORS["decode"]:
            with self.subTest(c["name"]):
                self.assertEqual(decoded_json(mecp.decode(c["input"])), c["expect"])

    def test_encode(self):
        for c in VECTORS["encode"]:
            with self.subTest(c["name"]):
                got = mecp.encode(c["severity"], c["codes"], c["freetext"])
                self.assertEqual(dataclasses.asdict(got), c["expect"])

    def test_validate(self):
        for c in VECTORS["validate"]:
            with self.subTest(c["name"]):
                self.assertEqual(dataclasses.asdict(mecp.validate(c["input"])), c["expect"])


class UpstreamFreetext(unittest.TestCase):
    """mecp-org/MECP freetext/tests.json, run unchanged."""

    def test_cases(self):
        manifest = json.loads((UPSTREAM / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schemaVersion"], 1)
        tests = json.loads((UPSTREAM / "tests.json").read_text(encoding="utf-8"))
        for t in tests:
            with self.subTest(t["title"]):
                d = mecp.decode(t["input"])
                if t["expect"] is None:
                    self.assertFalse(d.valid)
                    continue
                self.assertTrue(d.valid)
                got = dataclasses.asdict(d.extracted)
                self.assertEqual(got, {f: t["expect"].get(f) for f in FIELDS})


class Helpers(unittest.TestCase):
    def test_beacon(self):
        codes = mecp.decode("MECP/0/B01 B02 B03").codes
        self.assertTrue(mecp.is_beacon(codes))
        self.assertTrue(mecp.is_beacon_ack(codes))
        self.assertTrue(mecp.is_beacon_cancel(codes))
        self.assertFalse(mecp.is_beacon(["M01"]))

    def test_version(self):
        self.assertEqual(mecp.MECP_VERSION, "1.4.0")


if __name__ == "__main__":
    unittest.main()
