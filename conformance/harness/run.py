#!/usr/bin/env python3
"""Run the MECP decode conformance vectors against every client adapter.

  python3 conformance/harness/run.py                 # all clients in clients.json
  python3 conformance/harness/run.py --only a,b      # a subset
  python3 conformance/harness/run.py --build         # run each client's build step first

Writes conformance/reports/: SUMMARY.md, DISAGREEMENTS.md, one <client>.md each,
and results.json. Exit status is 0 even when clients fail; the reports are the output.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONF = ROOT / "conformance"
CLIENTS = Path(os.environ.get("MECP_CLIENTS_DIR", ROOT.parent)).resolve()
VECTORS = CONF / "vectors" / "decode-1.4.0.json"
UPSTREAM = ROOT / "upstream" / "freetext"
EXTRACTED = ["pax", "gps", "timestamp", "language", "callsign", "reference", "duration"]
REPORTS = CONF / "reports"
FIELDS = ["valid", "severity", "codes", "freetext",
          "pax", "gps", "timestamp", "language", "callsign", "reference", "duration"]
NA = "n/a"
# The field a clause is about, for marking clauses a client cannot be scored on.
CLAUSE_FIELD = {"6.1 Callsign": "callsign", "6.1 Language": "language",
                "6.1 Reference": "reference", "6.1 Duration": "duration",
                "6.1 Optional Freetext 9": "duration", "6.1 Codes": "codes"}


def expand(s: str) -> str:
    return s.replace("{root}", str(ROOT)).replace("{clients}", str(CLIENTS))


def git_info(repo: str | None) -> dict:
    if not repo:
        return {}
    path = expand(repo)

    def git(*args):
        r = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True)
        return r.stdout.strip()

    return {"sha": git("rev-parse", "HEAD"), "date": git("log", "-1", "--format=%cs"),
            "dirty": bool(git("status", "--porcelain", "--untracked-files=no"))}


def upstream_cases() -> list[dict]:
    """mecp-org/MECP freetext/tests.json as harness cases (validity and fields only)."""
    if json.loads((UPSTREAM / "manifest.json").read_text())["schemaVersion"] != 1:
        sys.exit("unsupported upstream schemaVersion")
    out = []
    for i, t in enumerate(json.loads((UPSTREAM / "tests.json").read_text(encoding="utf-8"))):
        exp = t["expect"]
        expect = ({"valid": False} if exp is None else
                  {"valid": True, **{f: exp.get(f) for f in EXTRACTED}})
        out.append({"id": f"up.{i:02d}", "clause": "upstream: " + t["title"].split(":")[0],
                    "input": t["input"], "expect": expect, "note": t["title"]})
    return out


def run_adapter(client: dict, cases: list[dict]) -> tuple[dict, str | None]:
    stdin = "".join(f"{c['id']}\t{c['input'].encode('utf-8').hex()}\n" for c in cases)
    try:
        p = subprocess.run([expand(a) for a in client["cmd"]], input=stdin, capture_output=True,
                           text=True, encoding="utf-8", timeout=600)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {}, f"adapter did not run: {e}"
    out = {}
    for line in p.stdout.split("\n"):  # not splitlines(): U+2028 can appear inside JSON
        if line.strip():
            rec = json.loads(line)
            out[rec["id"]] = rec
    err = None
    if p.returncode != 0 or len(out) != len(cases):
        err = f"exit {p.returncode}, {len(out)}/{len(cases)} records\n{p.stderr[-2000:]}"
    return out, err


def same(field, want, got) -> bool:
    if field == "gps" and want is not None and isinstance(got, dict):
        return (abs(want["lat"] - got.get("lat", 1e9)) < 1e-9
                and abs(want["lon"] - got.get("lon", 1e9)) < 1e-9)
    if field == "reference" and isinstance(want, str) and isinstance(got, str):
        return want.lower().replace("_", "-") == got.lower().replace("_", "-")
    return want == got


def compare(case: dict, rec: dict | None, fields: list[str]) -> tuple[str, list[tuple]]:
    """Return (status, diffs). status: pass | fail | error. diffs: (field, want, got)."""
    if rec is None:
        return "error", [("(adapter)", "a record", "no output")]
    if "error" in rec:
        return "error", [("(exception)", "a record", rec["error"])]
    got = rec["result"]
    want = case["expect"]
    keys = ["valid"] if want["valid"] is False else [k for k in want if k in fields]
    if want["valid"] is True and got.get("valid") is not True:
        return "fail", [("valid", True, got.get("valid"))]
    diffs = [(k, want[k], got.get(k)) for k in keys if not same(k, want[k], got.get(k))]
    return ("fail" if diffs else "pass"), diffs


def visible(s: str) -> str:
    """Escape control, format and non-ASCII-space characters so table cells show them."""
    return "".join(ch if ch == " " or unicodedata.category(ch)[0] not in "CZ"
                   else f"\\u{ord(ch):04x}" for ch in s)


def j(v) -> str:
    return visible(json.dumps(v, ensure_ascii=False)).replace("|", "\\|")


def show_input(s: str) -> str:
    # Make invisible characters visible in Markdown tables.
    esc = visible(json.dumps(s, ensure_ascii=False)[1:-1])
    return "`" + esc.replace("|", "\\|").replace("`", "\\`") + "`"


def client_report(client: dict, info: dict, results: dict, cases: list[dict], meta: dict) -> str:
    by_clause = defaultdict(list)
    counts = defaultdict(int)
    for c in cases:
        status, diffs = results[c["id"]]
        counts[status] += 1
        if status != "pass":
            by_clause[c["clause"]].append((c, status, diffs))
    lines = [f"# {client['name']}: MECP 1.4.0 decode conformance", ""]
    lines.append(f"- Client: {client.get('description', '')}")
    if client.get("upstream"):
        lines.append(f"- Repository: {client['upstream']}")
    if info.get("sha"):
        dirty = " (local changes)" if info["dirty"] else ""
        lines.append(f"- Commit tested: `{info['sha'][:10]}` ({info['date']}){dirty}")
    if client.get("source"):
        lines.append(f"- Decoder: `{client['source']}`")
    fields = client["_fields"]
    if len(fields) < len(FIELDS):
        lines.append(f"- Fields compared: {', '.join(fields)} (others not exposed by this client)")
    lines.append(f"- Vectors: `conformance/vectors/decode-1.4.0.json` plus mecp-org/MECP "
                 f"`freetext/tests.json` ({len(cases)} cases), run {meta['date']}")
    lines.append(f"- **Result: {counts['pass']} pass, {counts['fail']} fail, "
                 f"{counts['error']} error**")
    lines.append("")
    if not by_clause:
        lines.append("All cases pass.")
        return "\n".join(lines) + "\n"
    if any(c.get("proposed") for c in cases):
        lines.append("Cases marked *(proposed)* depend on spec changes not yet merged upstream; "
                     "see the vector's `proposed` field.")
        lines.append("")
    lines.append("Each row is one vector. *Expected* is written by hand from the protocol brief "
                 "(clause in the heading); *Got* is what this client's decoder returned.")
    for clause in sorted(by_clause, key=lambda k: (-len(by_clause[k]), k)):
        rows = by_clause[clause]
        lines += ["", f"## {clause} ({len(rows)})", "",
                  "| Case | Input | Field | Expected | Got |", "|---|---|---|---|---|"]
        for c, status, diffs in rows:
            for i, (field, want, got) in enumerate(diffs):
                tag = " (proposed)" if c.get("proposed") else ""
                title = f" {c['note']}" if c["id"].startswith("up.") else ""
                lead = (f"`{c['id']}`{tag}{title} | {show_input(c['input'])}" if i == 0
                        else " | ")
                lines.append(f"| {lead} | {field} | {j(want)} | {j(got)} |")
    return "\n".join(lines) + "\n"


def disagreements(cases, clients, raw) -> str:
    """Cases where real clients (not the reference) disagree with each other."""
    real = [c for c in clients if c["name"] != "reference" and not c.get("_failed")]
    lines = ["# Cross-client disagreements", "",
             "Cases where at least two clients return different values for the same field. "
             "These are the inconsistencies a user sees when the same message is read on "
             "different apps, whatever the spec says. `n/a` = field not exposed.", ""]
    groups = defaultdict(list)
    for case in cases:
        fields = ["valid"] if case["expect"]["valid"] is False else FIELDS
        diffs = {}
        for f in fields:
            vals = {}
            for c in real:
                rec = raw[c["name"]].get(case["id"], {})
                if "result" not in rec:
                    vals[c["name"]] = "ERROR"
                elif f not in c["_fields"]:
                    continue
                elif rec["result"].get("valid") is not True and f != "valid":
                    vals[c["name"]] = "(invalid)"
                else:
                    vals[c["name"]] = rec["result"].get(f)
            norm = {json.dumps(v, sort_keys=True) for v in vals.values()}
            if len(norm) > 1:
                diffs[f] = vals
        if diffs:
            groups[(case["clause"], tuple(diffs))].append((case, diffs))
    if not groups:
        return "\n".join(lines + ["No disagreements."]) + "\n"
    names = [c["name"] for c in real]
    for (clause, fields), items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines += [f"## {clause}: {', '.join(fields)} ({len(items)} cases)", "",
                  "| Case | Input | Field | Spec | " + " | ".join(names) + " |",
                  "|---|---|---|---|" + "---|" * len(names)]
        for case, diffs in items:
            for i, (f, vals) in enumerate(diffs.items()):
                lead = f"`{case['id']}` | {show_input(case['input'])}" if i == 0 else " | "
                exp = case["expect"]
                spec = (j(exp[f]) if f in exp else "(invalid)" if exp["valid"] is False
                        else "(any)")
                cells = [j(vals[n]) if n in vals else NA for n in names]
                lines.append(f"| {lead} | {f} | {spec} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()

    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    cases = doc["cases"] + upstream_cases()
    clients = json.loads((CONF / "clients.json").read_text())["clients"]
    if args.only:
        wanted = set(args.only.split(","))
        clients = [c for c in clients if c["name"] in wanted or c["name"] == "reference"]
    meta = {"date": date.today().isoformat(), "vectors": len(cases)}
    REPORTS.mkdir(exist_ok=True)

    raw, results, infos = {}, {}, {}
    for client in clients:
        name = client["name"]
        client["_fields"] = FIELDS if client["fields"] == "all" else ["valid", *client["fields"]]
        if args.build and client.get("build"):
            print(f"[{name}] building", file=sys.stderr)
            b = subprocess.run([expand(a) for a in client["build"]], cwd=expand(
                client.get("build_cwd", "{root}")))
            if b.returncode:
                print(f"[{name}] build failed", file=sys.stderr)
        infos[name] = git_info(client.get("repo"))
        raw[name], err = run_adapter(client, cases)
        if err:
            print(f"[{name}] {err}", file=sys.stderr)
            client["_failed"] = not raw[name]
        results[name] = {c["id"]: compare(c, raw[name].get(c["id"]), client["_fields"])
                         for c in cases}
        (REPORTS / f"{name}.md").write_text(
            client_report(client, infos[name], results[name], cases, meta), encoding="utf-8")
        n = sum(1 for s, _ in results[name].values() if s == "pass")
        print(f"[{name}] {n}/{len(cases)} pass", file=sys.stderr)

    # Summary: clients x clauses.
    clauses = sorted({c["clause"] for c in cases})
    lines = [f"# MECP 1.4.0 decode conformance summary ({meta['date']})", "",
             f"{len(cases)} cases: hand-written vectors from `conformance/vectors/decode-1.4.0.json` "
             "and the upstream mecp-org/MECP `freetext/tests.json` (clauses `upstream: …`). "
             "Cells are passing/total cases per clause; n/a means the client does not expose "
             "the field that clause is about.", "",
             "| Clause | " + " | ".join(c["name"] for c in clients) + " |",
             "|---|" + "---|" * len(clients)]
    for cl in clauses:
        ids = [c["id"] for c in cases if c["clause"] == cl]
        primary = next((f for key, f in CLAUSE_FIELD.items() if cl.startswith(key)), None)
        cells = ["n/a" if primary and primary not in c["_fields"] else
                 f"{sum(results[c['name']][i][0] == 'pass' for i in ids)}/{len(ids)}"
                 for c in clients]
        lines.append(f"| {cl} | " + " | ".join(cells) + " |")
    tot = [f"**{sum(s == 'pass' for s, _ in results[c['name']].values())}/{len(cases)}**"
           for c in clients]
    lines.append("| **Total** | " + " | ".join(tot) + " |")
    lines += ["", "| Client | Commit |", "|---|---|"]
    for c in clients:
        i = infos[c["name"]]
        lines.append(f"| [{c['name']}]({c['name']}.md) | "
                     + (f"`{i['sha'][:10]}` {i['date']}{' (dirty)' if i['dirty'] else ''}"
                        if i.get("sha") else "in-repo") + " |")
    (REPORTS / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTS / "DISAGREEMENTS.md").write_text(disagreements(cases, clients, raw), encoding="utf-8")
    (REPORTS / "results.json").write_text(json.dumps(
        {"meta": meta, "clients": {c["name"]: {"commit": infos[c["name"]], "results": raw[c["name"]]}
                                   for c in clients}}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    print(f"reports in {REPORTS.relative_to(ROOT)}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
