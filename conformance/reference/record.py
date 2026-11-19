"""§6.1 reference decoder for the harness: MECP-polyglot's Python codec.

The codec is built on the upstream patterns (upstream/freetext/patterns.json)
and is checked against mecp-org/MECP scripts/check-freetext.mjs in CI. This
module only reshapes its output into the harness record (../README.md).

It is NOT the source of truth for the conformance vectors: every expectation
in vectors/build.py is written by hand from the spec text. build.py --check
uses this to cross-check them; a disagreement is a vector typo or a spec
ambiguity.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python" / "src"))
import mecp  # noqa: E402

FIELDS = ("pax", "gps", "timestamp", "language", "callsign", "reference", "duration")


def decode(raw: str) -> dict:
    d = mecp.decode(raw)
    if not d.valid:
        return {"valid": False}
    x = d.extracted
    rec = {"valid": True, "severity": d.severity, "codes": d.codes, "freetext": d.freetext}
    rec.update({f: getattr(x, f) for f in FIELDS})
    if x.gps is not None:
        rec["gps"] = {"lat": x.gps.lat, "lon": x.gps.lon}
    return rec
