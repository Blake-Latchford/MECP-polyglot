#!/usr/bin/env python3
"""Run vectors/mecp-vectors.json decode cases through upstream's reference checker.

mecp-org/MECP scripts/check-freetext.mjs is the normative §6.1 decoder. It
reads its cases from freetext/tests.json next to the brief, so this script
builds a scratch tree with the brief, patterns and checker from a MECP
checkout and our decode vectors in upstream's case shape, then runs it.

Cases whose expectation relies on clamping (2147483647) are skipped: the
brief says SHOULD clamp, and the checker does not.

Usage: python3 oracle/check_vectors.py <path/to/MECP checkout>
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAMP = 2147483647


def main(mecp: Path) -> int:
    commit = json.loads((ROOT / "upstream/source.json").read_text())["commit"]
    head = subprocess.run(["git", "-C", str(mecp), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    if head and head != commit:
        print(f"warning: {mecp} is at {head[:12]}, upstream/ is from {commit[:12]}")

    vectors = json.loads((ROOT / "vectors/mecp-vectors.json").read_text(encoding="utf-8"))
    cases, skipped = [], 0
    for c in vectors["decode"]:
        x = c["expect"]
        fields = {k: v for k, v in x["extracted"].items() if v is not None}
        if CLAMP in fields.values():
            skipped += 1
            continue
        cases.append({"title": c["name"], "input": c["input"],
                      "expect": fields if x["valid"] else None})

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "scripts").mkdir()
        (t / "freetext").mkdir()
        shutil.copy(mecp / "MECP_Comprehensive_Brief.md", t)
        shutil.copy(mecp / "scripts/check-freetext.mjs", t / "scripts")
        shutil.copy(mecp / "freetext/patterns.json", t / "freetext")
        (t / "freetext/tests.json").write_text(json.dumps(cases, ensure_ascii=False),
                                               encoding="utf-8")
        r = subprocess.run(["node", str(t / "scripts/check-freetext.mjs")])
    print(f"({skipped} clamping cases skipped)")
    return r.returncode


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1])))
