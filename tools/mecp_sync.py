#!/usr/bin/env python3
"""Pull the MECP freetext conformance pack and generate per-language patterns.

The regexes and decode cases come from mecp-org/MECP, unchanged:

  upstream/freetext/{manifest,patterns,tests}.json   byte-for-byte copies
  upstream/boundary.json   the boundary class B, read from brief §6.1 rule 4
                           (patterns.json does not carry it)
  upstream/source.json     the MECP commit they were taken from

From those files this script writes the pattern constants for every codec,
so no implementation retypes a regex:

  python/src/mecp/_patterns.py, go/patterns.go, rust/src/patterns.rs,
  dart/lib/src/patterns.dart, c/src/mecp_boundary.h (C matches by hand and
  only takes the boundary table).

Usage:
  python3 tools/mecp_sync.py pull ../MECP   # copy from a MECP checkout, then generate
  python3 tools/mecp_sync.py generate       # regenerate code from upstream/
  python3 tools/mecp_sync.py check          # exit 1 if generated code is stale
  python3 tools/mecp_sync.py verify-remote  # exit 1 if upstream/ differs from GitHub
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "upstream"
FREETEXT_FILES = ("manifest.json", "patterns.json", "tests.json")
REPO = "mecp-org/MECP"
BRIEF = "MECP_Comprehensive_Brief.md"

# Convention order in generated code. Decode output uses the same order.
CONVENTIONS = ("pax", "gps", "timestamp", "language", "callsign", "reference")


# --------------------------------------------------------------------- pull

def boundary_from_brief(brief: str) -> dict:
    """Read B from §6.1 rule 4, the way MECP scripts/check-freetext.mjs does."""
    rule = next((l for l in brief.split("\n") if l.startswith("4. Decoding patterns")), None)
    if rule is None or ", a space" not in rule or not re.search(r"one of `[^`]+`", rule):
        sys.exit("cannot read the boundary list B from §6.1 rule 4; update boundary_from_brief()")
    head = rule[: rule.index(", a space")]
    controls = re.findall(r"`(\\[tnfr])`", head)
    ascii_chars = re.search(r"one of `([^`]+)`", rule).group(1).split(" ")
    spans = re.findall(r"U\+([0-9A-F]{4})(?:–U\+([0-9A-F]{4}))?", rule)

    escape = {"\\t": 0x09, "\\n": 0x0A, "\\f": 0x0C, "\\r": 0x0D}
    ranges = [[escape[c], escape[c]] for c in controls] + [[0x20, 0x20]]
    ranges += [[ord(c), ord(c)] for c in ascii_chars]
    ranges += [[int(lo, 16), int(hi or lo, 16)] for lo, hi in spans]
    ranges.sort()

    # Same text as check-freetext.mjs builds, so the class is portable as-is.
    js = "[" + "".join(controls) + " "
    js += "".join(re.sub(r"([\\\[\]^-])", r"\\\1", c) for c in ascii_chars)
    js += "".join(f"\\u{lo}-\\u{hi}" if hi else f"\\u{lo}" for lo, hi in spans) + "]"
    return {"class": js, "ranges": ranges}


def git(mecp: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(mecp), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def pull(mecp: Path) -> None:
    if git(mecp, "status", "--porcelain", "--", "freetext", BRIEF):
        sys.exit(f"{mecp}: freetext/ or the brief has uncommitted changes; commit or stash first")
    commit = git(mecp, "rev-parse", "HEAD")
    (UP / "freetext").mkdir(parents=True, exist_ok=True)
    for name in FREETEXT_FILES:
        shutil.copyfile(mecp / "freetext" / name, UP / "freetext" / name)
    boundary = boundary_from_brief((mecp / BRIEF).read_text(encoding="utf-8"))
    manifest = json.loads((UP / "freetext/manifest.json").read_text(encoding="utf-8"))
    source = {
        "repository": f"https://github.com/{REPO}",
        "commit": commit,
        "protocolVersion": manifest["protocolVersion"],
        "schemaVersion": manifest["schemaVersion"],
    }
    write_json(UP / "boundary.json", {"source": f"{BRIEF} §6.1 rule 4", **boundary})
    write_json(UP / "source.json", source)
    print(f"pulled {REPO}@{commit[:12]} (protocol {source['protocolVersion']})")


def write_json(path: Path, data) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    # Keep each [lo, hi] range on one line.
    text = re.sub(r"\[\s+(\d+),\s+(\d+)\s+\]", r"[\1, \2]", text)
    path.write_text(text + "\n", encoding="utf-8")


def verify_remote() -> None:
    src = load("source.json")
    base = f"https://raw.githubusercontent.com/{REPO}/{src['commit']}"
    bad = []
    for name in FREETEXT_FILES:
        with urllib.request.urlopen(f"{base}/freetext/{name}") as r:
            if r.read() != (UP / "freetext" / name).read_bytes():
                bad.append(f"freetext/{name}")
    with urllib.request.urlopen(f"{base}/{BRIEF}") as r:
        b = boundary_from_brief(r.read().decode("utf-8"))
    if {k: load("boundary.json")[k] for k in b} != b:
        bad.append("boundary.json")
    if bad:
        sys.exit(f"upstream/ differs from {REPO}@{src['commit']}: {', '.join(bad)}")
    print(f"upstream/ matches {REPO}@{src['commit'][:12]}")


# ----------------------------------------------------------------- generate

def load(name: str):
    return json.loads((UP / name).read_text(encoding="utf-8"))


def literal_regex(pattern: str) -> str:
    r"""Replace each \uXXXX regex escape with the character itself.

    `\u` is ECMAScript syntax; Go RE2 rejects it and Rust spells it `\u{..}`.
    A literal character means the same in every engine. The other escapes
    (`\t`, `\.`, `\[`, ...) are portable and stay as they are.
    """
    out, i = [], 0
    while i < len(pattern):
        if pattern[i] == "\\":
            m = re.match(r"u([0-9A-Fa-f]{4})", pattern[i + 1:])
            if m:
                cp = int(m.group(1), 16)
                assert cp >= 0x80, f"\\u{m.group(1)} would need escaping: {pattern}"
                out.append(chr(cp))
                i += 6
                continue
            out.append(pattern[i:i + 2])
            i += 2
            continue
        out.append(pattern[i])
        i += 1
    return "".join(out)


def model() -> dict:
    pats = load("freetext/patterns.json")
    src = load("source.json")
    expected = {"message", "duration", *CONVENTIONS}
    if set(pats) != expected:
        sys.exit(f"patterns.json conventions changed: {sorted(set(pats) ^ expected)}; "
                 "update tools/mecp_sync.py and every codec")
    dur = pats["duration"]
    if dur.get("scope") != "R03" or len(dur["decode"]) != 5:
        sys.exit("duration shape changed; update tools/mecp_sync.py and every codec")
    validate = {n: pats[n].get("validate") for n in CONVENTIONS if pats[n].get("validate")}
    if validate != {"gps": "gps", "callsign": "callsign"}:
        sys.exit(f"Additional Validation set changed: {validate}")
    consts = [("MESSAGE", pats["message"]["decode"]), ("BOUNDARY", load("boundary.json")["class"])]
    consts += [(n.upper(), pats[n]["decode"]) for n in CONVENTIONS]
    return {
        "version": src["protocolVersion"],
        "commit": src["commit"],
        "consts": [(k, literal_regex(v)) for k, v in consts],
        "duration": [literal_regex(p) for p in dur["decode"]],
        "scope": dur["scope"],
        "ranges": load("boundary.json")["ranges"],
    }


def esc(s: str, style: str) -> str:
    """A double-quoted string literal in the host language."""
    out = []
    for ch in s:
        cp = ord(ch)
        if ch in '"\\':
            out.append("\\" + ch)
        elif ch == "$" and style == "dart":
            out.append("\\$")
        elif 0x20 <= cp < 0x7F:
            out.append(ch)
        elif style == "rust":
            out.append(f"\\u{{{cp:x}}}")
        else:
            out.append(f"\\u{cp:04x}")
    return '"' + "".join(out) + '"'


HEADER = ("Generated by tools/mecp_sync.py from upstream/ (mecp-org/MECP {commit:.12},"
          " protocol {version}). Do not edit.")


def gen_python(m) -> str:
    lines = [f'"""{HEADER.format(**m)}"""', "", f'MECP_VERSION = "{m["version"]}"',
             f'MECP_COMMIT = "{m["commit"]}"', f'DURATION_SCOPE = "{m["scope"]}"', ""]
    lines += [f"{k} = {esc(v, 'py')}" for k, v in m["consts"]]
    lines += ["", "# Duration decode patterns, in spec order: h+min, h, min, d, bare number.",
              "DURATION = ("] + [f"    {esc(p, 'py')}," for p in m["duration"]] + [")", ""]
    return "\n".join(lines)


def gen_go(m) -> str:
    def block(pairs):  # gofmt aligns the = of consecutive const lines
        w = max(len(k) for k, _ in pairs)
        return [f"\t{k.ljust(w)} = {v}" for k, v in pairs]
    lines = [f"// {HEADER.format(**m)}", "", "package mecp", "", "const ("]
    lines += block([("MecpVersion", f'"{m["version"]}"'), ("durationScope", f'"{m["scope"]}"')])
    lines += [""] + block([(f"pat{k.title()}", esc(v, "go")) for k, v in m["consts"]])
    lines += [")", "", "// Duration decode patterns, in spec order: h+min, h, min, d, bare number.",
              "var patDuration = [...]string{"] + [f"\t{esc(p, 'go')}," for p in m["duration"]]
    lines += ["}", ""]
    return "\n".join(lines)


def gen_rust(m) -> str:
    lines = [f"//! {HEADER.format(**m)}", "",
             f'pub const MECP_VERSION: &str = "{m["version"]}";',
             f'pub(crate) const DURATION_SCOPE: &str = "{m["scope"]}";', ""]
    lines += [f"pub(crate) const {k}: &str = {esc(v, 'rust')};" for k, v in m["consts"]]
    lines += ["", "/// Duration decode patterns, in spec order: h+min, h, min, d, bare number.",
              "pub(crate) const DURATION: [&str; 5] = ["]
    lines += [f"    {esc(p, 'rust')}," for p in m["duration"]] + ["];", ""]
    return "\n".join(lines)


def gen_dart(m) -> str:
    def camel(k):
        a, *b = k.lower().split("_")
        return a + "".join(x.title() for x in b)
    lines = [f"// {HEADER.format(**m)}", "",
             f"const String mecpVersion = '{m['version']}';",
             f"const String durationScope = '{m['scope']}';", ""]
    lines += [f"const String {camel(k)}Pattern = {esc(v, 'dart')};" for k, v in m["consts"]]
    lines += ["", "/// Duration decode patterns, in spec order: h+min, h, min, d, bare number.",
              "const List<String> durationPatterns = ["]
    lines += [f"  {esc(p, 'dart')}," for p in m["duration"]] + ["];", ""]
    return "\n".join(lines)


def gen_c(m) -> str:
    rows = [f"    {{0x{lo:04X}, 0x{hi:04X}}}," for lo, hi in m["ranges"]]
    return "\n".join([
        f"/* {HEADER.format(**m)} */",
        "#ifndef MECP_BOUNDARY_H",
        "#define MECP_BOUNDARY_H",
        "",
        f'#define MECP_PROTOCOL_VERSION "{m["version"]}"',
        "",
        "/* Boundary class B (brief §6.1 rule 4) as sorted code point ranges. */",
        "static const struct { unsigned long lo, hi; } mecp_boundary[] = {",
        *rows,
        "};",
        "",
        "#endif",
        "",
    ])


OUTPUTS = {
    "python/src/mecp/_patterns.py": gen_python,
    "go/patterns.go": gen_go,
    "rust/src/patterns.rs": gen_rust,
    "dart/lib/src/patterns.dart": gen_dart,
    "c/src/mecp_boundary.h": gen_c,
}


def generate(check: bool) -> None:
    m = model()
    stale = []
    for rel, fn in OUTPUTS.items():
        path, text = ROOT / rel, fn(m)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if stale:
        sys.exit("stale generated files (run python3 tools/mecp_sync.py generate): "
                 + ", ".join(stale))
    print("generated files are up to date" if check else f"wrote {len(OUTPUTS)} files")


def main(argv: list[str]) -> None:
    match argv:
        case ["pull", path]:
            pull(Path(path).resolve())
            generate(check=False)
        case ["generate"]:
            generate(check=False)
        case ["check"]:
            generate(check=True)
        case ["verify-remote"]:
            verify_remote()
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
