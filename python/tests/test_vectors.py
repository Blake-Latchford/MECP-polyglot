import dataclasses
import json
import unittest
from pathlib import Path

import mecp

VECTORS = json.loads(
    (Path(__file__).resolve().parents[2] / "vectors" / "mecp-vectors.json").read_text(encoding="utf-8")
)


def as_dict(decoded: mecp.Decoded) -> dict:
    d = dataclasses.asdict(decoded)
    del d["raw"]
    return d


class DecodeVectors(unittest.TestCase):
    def test_decode(self):
        for case in VECTORS["decode"]:
            with self.subTest(case["name"]):
                got = mecp.decode(case["input"])
                self.assertEqual(got.raw, case["input"])
                self.assertEqual(as_dict(got), case["expect"])


class EncodeVectors(unittest.TestCase):
    def test_encode(self):
        for case in VECTORS["encode"]:
            with self.subTest(case["name"]):
                got = mecp.encode(case["severity"], case["codes"], case["freetext"])
                self.assertEqual(dataclasses.asdict(got), case["expect"])


class ValidateVectors(unittest.TestCase):
    def test_validate(self):
        for case in VECTORS["validate"]:
            with self.subTest(case["name"]):
                got = mecp.validate(case["input"])
                self.assertEqual(dataclasses.asdict(got), case["expect"])


class RoundTrip(unittest.TestCase):
    def test_encode_then_decode(self):
        enc = mecp.encode(0, ["M01", "M07", "P05"], "2pax 48.6520,20.1305")
        dec = mecp.decode(enc.message)
        self.assertTrue(dec.valid)
        self.assertEqual(dec.codes, ["M01", "M07", "P05"])
        self.assertEqual(dec.extracted.count, 2)
        self.assertEqual(dec.extracted.gps, mecp.Gps(48.652, 20.1305))

    def test_beacon_helpers(self):
        codes = mecp.decode("MECP/0/B01 B02 B03").codes
        self.assertTrue(mecp.is_beacon(codes))
        self.assertTrue(mecp.is_beacon_ack(codes))
        self.assertTrue(mecp.is_beacon_cancel(codes))
        self.assertFalse(mecp.is_beacon(["M01"]))


if __name__ == "__main__":
    unittest.main()
