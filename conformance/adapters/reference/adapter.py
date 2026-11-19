"""Adapter for the in-repo §6.1 reference decoder (sanity check for the harness)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "reference"))
import record  # noqa: E402

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    case_id, hexed = line.split("\t", 1)
    try:
        out = {"id": case_id, "result": record.decode(bytes.fromhex(hexed).decode("utf-8"))}
    except Exception as e:  # report, don't crash the run
        out = {"id": case_id, "error": f"{type(e).__name__}: {e}"}
    print(json.dumps(out, ensure_ascii=False), flush=False)
