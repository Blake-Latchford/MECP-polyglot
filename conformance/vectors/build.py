#!/usr/bin/env python3
"""Build decode-1.4.1.json (MECP 1.4.1 §6.1 decode conformance vectors) and
codes-1.4.1.json (the §7 code table every client's catalog should match).

Every expectation here is written by hand from the protocol brief
(MECP_Comprehensive_Brief.md §6.1, release 1.4.1) -- never copied from a
client's output. `--check` also runs each case through
../reference/record.py; a disagreement is a typo here or a spec ambiguity.

Usage:
  python3 conformance/vectors/build.py           # rewrite both JSON files
  python3 conformance/vectors/build.py --check   # verify; exit 1 on drift
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "decode-1.4.1.json"
CODES_OUT = HERE / "codes-1.4.1.json"
sys.path.insert(0, str(HERE.parent / "reference"))

FIELDS = ("pax", "gps", "timestamp", "language", "callsign", "reference", "duration")
CASES: list[dict] = []


def ok(id, clause, input, codes, freetext=None, severity=None, note=None, skip=(), proposed=False,
       **fields):
    """A valid message. Unlisted extracted fields are expected to be null.

    `skip` names fields the spec leaves to the implementation; they are left out
    of `expect` and not compared (e.g. a SHOULD-clamp value). `proposed` marks a
    case that depends on spec text not yet merged upstream (see PROPOSED).
    """
    unknown = set(fields) - set(FIELDS)
    assert not unknown, f"{id}: unknown fields {unknown}"
    if severity is None:
        severity = int(input[5])
    expect = {"valid": True, "severity": severity, "codes": codes, "freetext": freetext}
    expect.update({f: fields.get(f) for f in FIELDS if f not in skip})
    _add(id, clause, input, expect, note, proposed)


def bad(id, clause, input, note=None):
    """Not an MECP 1.4.1 message: only `valid` is compared."""
    _add(id, clause, input, {"valid": False}, note)


# Proposed spec changes that some vectors depend on.
PROPOSED = "Not in the 1.4.1 brief: proposed on Blake-Latchford/MECP branch spec-clarifications (2026-11-16)"


def _add(id, clause, input, expect, note, proposed=False):
    assert all(c["id"] != id for c in CASES), f"duplicate id {id}"
    case = {"id": id, "clause": clause, "input": input, "expect": expect}
    if proposed:
        case["proposed"] = PROPOSED
    if note:
        case["note"] = note
    CASES.append(case)


def gps(lat, lon):
    return {"lat": lat, "lon": lon}


# ---------------------------------------------------------------- envelope
E = "6.1 Message Format"
ok("env.readme", E, "MECP/0/M01 M07 2pax P05 48.6520,20.1305", ["M01", "M07"],
   "2pax P05 48.6520,20.1305", pax=2, gps=gps(48.652, 20.1305),
   note="README example. P05 after freetext starts is freetext (Codes rule 3).")
ok("env.codes-only", E, "MECP/2/B03", ["B03"])
ok("env.sev0", E, "MECP/0/B01", ["B01"])
ok("env.sev3", E, "MECP/3/L04", ["L04"])
ok("env.repeat-code", "6.1 Codes 4", "MECP/1/T05 T05 damaged", ["T05", "T05"], "damaged")
ok("env.unknown-code", "6.1 Codes 5", "MECP/3/Z99 hello", ["Z99"], "hello",
   note="Unknown but well-formed codes MUST be preserved, not treated as freetext.")
ok("env.unknown-category-only", "6.1 Codes 5", "MECP/1/Q42", ["Q42"])
ok("env.lowercase-ends-codes", "6.1 Codes 3", "MECP/3/L01 l06 late", ["L01"], "l06 late")
ok("env.code-after-freetext", "6.1 Codes 3", "MECP/0/M01 2pax M07", ["M01"], "2pax M07", pax=2)
ok("env.freetext-inner-spaces", "6.1 Message Format", "MECP/3/L01 see  you   there", ["L01"],
   "see  you   there", note="Freetext is regex group 3 verbatim; inner runs of spaces are kept.")
ok("env.freetext-tab-inside", E, "MECP/3/L01 a\tb", ["L01"], "a\tb")
ok("env.trailing-lf", E, "MECP/2/B03\n", ["B03"],
   note="Remove at most one trailing CR/LF before matching.")
ok("env.trailing-cr", E, "MECP/2/B03\r", ["B03"])
ok("env.trailing-crlf", E, "MECP/2/B03\r\n", ["B03"],
   note="One trailing CR/LF means the regex \\r?\\n? at the end, so CRLF counts as one.")
ok("env.trailing-crlf-freetext", E, "MECP/3/L01 see you\r\n", ["L01"], "see you")
ok("env.utf8-freetext", E, "MECP/3/L04 Gipfel erreicht 山頂", ["L04"], "Gipfel erreicht 山頂")
bad("env.no-codes", E, "MECP/0/", note="The envelope regex needs at least one code.")
bad("env.no-codes-no-slash", E, "MECP/0")
bad("env.prefix-only", E, "MECP/")
bad("env.empty", E, "")
bad("env.not-mecp", E, "hello world")
bad("env.sev4", "6.1 Severity", "MECP/4/M01")
bad("env.sev9", "6.1 Severity", "MECP/9/M01")
bad("env.sev-letter", "6.1 Severity", "MECP/X/M01")
bad("env.sev-two-digits", "6.1 Severity", "MECP/01/M01")
bad("env.sev-arabic-indic", "6.1 Severity", "MECP/٣/M01")
bad("env.lowercase-prefix", E, "mecp/0/M01")
bad("env.leading-space", E, " MECP/0/M01")
bad("env.channel-prefix", E, "Alice: MECP/0/M01",
    note="A sender prefix is transport framing; strip it before decoding, not in the decoder.")
bad("env.no-prefix-compact", E, "M01 P05 48.65,20.13")
bad("env.lowercase-first-code", "6.1 Codes 3", "MECP/1/t05 x")
bad("env.four-char-code", E, "MECP/0/M011")
bad("env.trailing-space", E, "MECP/1/T05 ",
    note="Freetext MUST NOT begin or end with a space.")
bad("env.trailing-space-after-text", E, "MECP/1/T05 help ")
bad("env.double-space-before-freetext", E, "MECP/0/M01  help")
bad("env.double-space-between-codes", E, "MECP/0/M01  M07")
bad("env.tab-after-codes", E, "MECP/0/M01\tM07")
bad("env.embedded-lf", E, "MECP/0/M01\nM07")
bad("env.embedded-cr", E, "MECP/3/L01 a\rb")
bad("env.line-separator", E, "MECP/3/L01 a\u2028b")
bad("env.nel", E, "MECP/3/L01 a\u0085b")
bad("env.two-trailing-lf", E, "MECP/2/B03\n\n")
bad("env.lfcr", E, "MECP/2/B03\n\r", note="\\r?\\n? removes only the final CR; the LF remains.")
bad("env.two-crlf", E, "MECP/2/B03\r\n\r\n")
bad("env.nbsp-after-codes", E, "MECP/0/M01 help")

# ---------------------------------------------------------------- boundaries
BD = "6.1 Optional Freetext 4"
ok("b.paren", BD, "MECP/1/S01 (4pax)", ["S01"], "(4pax)", pax=4)
ok("b.period", BD, "MECP/1/S01 4Pax.", ["S01"], "4Pax.", pax=4)
ok("b.comma-run", BD, "MECP/1/S01 4pax,3pax", ["S01"], "4pax,3pax", pax=4)
ok("b.asterisk", BD, "MECP/1/S01 *4pax*", ["S01"], "*4pax*",
   note="1.4.0 lists the ASCII boundaries explicitly; '*' is not one of them.")
ok("b.slash", BD, "MECP/1/S01 4pax/3", ["S01"], "4pax/3",
   note="1.4.0 lists the ASCII boundaries explicitly; '/' is not one of them.")
ok("b.ideographic-comma", BD, "MECP/1/S01 4pax、水", ["S01"], "4pax、水", pax=4)
ok("b.corner-brackets", BD, "MECP/1/S01 「4pax」", ["S01"], "「4pax」", pax=4)
ok("b.nbsp", BD, "MECP/1/S01 4pax water", ["S01"], "4pax water", pax=4)
ok("b.arabic-comma", BD, "MECP/0/M01 48.65,20.13،", ["M01"], "48.65,20.13،",
   gps=gps(48.65, 20.13))
ok("b.letter-left", BD, "MECP/1/S01 x4pax", ["S01"], "x4pax")
ok("b.letter-right", BD, "MECP/1/S01 3paxmore", ["S01"], "3paxmore")
ok("b.hash-not-b", BD, "MECP/1/S01 #4pax", ["S01"], "#4pax",
   note="'#' is a sigil, so it is not a boundary; '4pax' is not decoded (but '#4pax' is a reference).",
   reference="4pax")
ok("b.hyphen-not-b", BD, "MECP/1/S01 -4pax", ["S01"], "-4pax")
ok("b.underscore-not-b", BD, "MECP/1/S01 _4pax", ["S01"], "_4pax")
ok("b.plus-not-b", BD, "MECP/1/S01 +4pax", ["S01"], "+4pax")
ok("b.vt-not-b", BD, "MECP/1/S01 4pax\u000bwater", ["S01"], "4pax\u000bwater",
   note="ASCII whitespace in B is TAB, LF, FF, CR and SPACE; VT is not a boundary.")

# ---------------------------------------------------------------- pax
PX = "6.1 Person count"
ok("pax.canonical", PX, "MECP/1/S01 4pax", ["S01"], "4pax", pax=4)
ok("pax.space", PX, "MECP/1/S01 4 pax", ["S01"], "4 pax", pax=4)
ok("pax.upper", PX, "MECP/1/S01 4PAX", ["S01"], "4PAX", pax=4)
ok("pax.leading-zero", PX, "MECP/1/S01 04pax", ["S01"], "04pax", pax=4)
ok("pax.zero-skipped", PX, "MECP/1/S01 0pax 2pax", ["S01"], "0pax 2pax", pax=2)
ok("pax.first-wins", PX, "MECP/1/S01 2pax 5pax", ["S01"], "2pax 5pax", pax=2)
ok("pax.multi-digit", PX, "MECP/2/H07 120pax", ["H07"], "120pax", pax=120)
ok("pax.localised-word", PX, "MECP/1/S01 4人", ["S01"], "4人")
ok("pax.german-word", PX, "MECP/1/S01 4 Personen", ["S01"], "4 Personen")
ok("pax.arabic-indic-digit", "6.1 Optional Freetext 5", "MECP/1/S01 ٤pax", ["S01"], "٤pax")
ok("pax.fullwidth-digit", "6.1 Optional Freetext 5", "MECP/1/S01 ４pax", ["S01"], "４pax")
ok("pax.two-spaces", PX, "MECP/1/S01 4  pax", ["S01"], "4  pax")
ok("pax.after-decimal", PX, "MECP/1/S01 1.5pax", ["S01"], "1.5pax", pax=5,
   note="'.' is in B, so this decodes as 5. Encoders cannot produce it: encoded values follow a space (rule 3).")
ok("pax.huge", "6.1 Optional Freetext 10", "MECP/1/S01 99999999999999999999999pax", ["S01"],
   "99999999999999999999999pax", skip=("pax",), proposed=True,
   note="Must decode without failing; the value SHOULD be clamped, so it is not compared.")

# ---------------------------------------------------------------- gps
G = "6.1 GPS coordinates"
ok("gps.canonical", G, "MECP/0/M04 P05 -41.2865,174.7762", ["M04", "P05"],
   "-41.2865,174.7762", gps=gps(-41.2865, 174.7762))
ok("gps.plus-and-space", G, "MECP/0/M04 +48.8566, 2.3522", ["M04"], "+48.8566, 2.3522",
   gps=gps(48.8566, 2.3522))
ok("gps.high-precision", G, "MECP/0/M04 48.85661234,2.35221234", ["M04"],
   "48.85661234,2.35221234", gps=gps(48.85661234, 2.35221234))
ok("gps.limits", G, "MECP/0/M04 90.0,180.0", ["M04"], "90.0,180.0", gps=gps(90.0, 180.0))
ok("gps.neg-limits", G, "MECP/0/M04 -90.0,-180.0", ["M04"], "-90.0,-180.0",
   gps=gps(-90.0, -180.0))
ok("gps.lat-out-of-range", G, "MECP/0/M04 90.0001,0.0", ["M04"], "90.0001,0.0")
ok("gps.resume-after-invalid", "6.1 Optional Freetext 6", "MECP/3/L06 95.0,200.0 47.3,8.5",
   ["L06"], "95.0,200.0 47.3,8.5", gps=gps(47.3, 8.5))
ok("gps.integers", G, "MECP/0/M04 48,20", ["M04"], "48,20")
ok("gps.zero-zero", G, "MECP/0/M04 0,0", ["M04"], "0,0")
ok("gps.decimal-comma", G, "MECP/3/L02 2,5 km", ["L02"], "2,5 km")
ok("gps.colon-left", G, "MECP/0/M01 at:48.65,20.13", ["M01"], "at:48.65,20.13",
   gps=gps(48.65, 20.13))
ok("gps.trailing-period", G, "MECP/0/M01 48.65,20.13.", ["M01"], "48.65,20.13.",
   gps=gps(48.65, 20.13))
ok("gps.letter-left", G, "MECP/0/M01 x48.65,20.13", ["M01"], "x48.65,20.13")
ok("gps.space-before-comma", G, "MECP/0/M01 48.65 ,20.13", ["M01"], "48.65 ,20.13")
ok("gps.altitude-suffix", G, "MECP/0/M01 48.65,20.13,1200", ["M01"], "48.65,20.13,1200",
   gps=gps(48.65, 20.13), note="',' is in B, so a trailing altitude stays in the freetext.")
ok("gps.two-spaces-after-comma", G, "MECP/0/M01 48.65,  20.13", ["M01"], "48.65,  20.13")
ok("gps.after-codes-later", G, "MECP/0/M01 M07 2pax P05 48.65,20.13 @1430", ["M01", "M07"],
   "2pax P05 48.65,20.13 @1430", pax=2, gps=gps(48.65, 20.13), timestamp="14:30")

# ---------------------------------------------------------------- timestamp
T = "6.1 Timestamp"
ok("ts.canonical", T, "MECP/2/T01 @0630", ["T01"], "@0630", timestamp="06:30")
ok("ts.three-digit", T, "MECP/2/T01 @630", ["T01"], "@630", timestamp="06:30")
ok("ts.colon-one-digit", T, "MECP/2/T01 @6:30", ["T01"], "@6:30", timestamp="06:30")
ok("ts.colon", T, "MECP/2/T01 @06:30", ["T01"], "@06:30", timestamp="06:30")
ok("ts.hmm", T, "MECP/3/L01 @123", ["L01"], "@123", timestamp="01:23")
ok("ts.midnight", T, "MECP/3/L01 @0000", ["L01"], "@0000", timestamp="00:00")
ok("ts.2359", T, "MECP/3/L01 @2359", ["L01"], "@2359", timestamp="23:59")
ok("ts.skip-invalid", T, "MECP/3/L06 @2460 @1400 @1530", ["L06"], "@2460 @1400 @1530",
   timestamp="14:00")
ok("ts.2400", T, "MECP/3/L06 @2400", ["L06"], "@2400")
ok("ts.9999", T, "MECP/3/L06 @9999", ["L06"], "@9999")
ok("ts.trailing-comma", T, "MECP/2/T05 @1430,", ["T05"], "@1430,", timestamp="14:30")
ok("ts.glued-left", T, "MECP/2/T05 meet@1430", ["T05"], "meet@1430")
ok("ts.zulu-suffix", T, "MECP/2/T05 @1430Z", ["T05"], "@1430Z")
ok("ts.five-digits", T, "MECP/2/T05 @14300", ["T05"], "@14300")
ok("ts.with-language", T, "MECP/0/M01 @1430 @en", ["M01"], "@1430 @en",
   timestamp="14:30", language="en")
ok("ts.arabic-indic", "6.1 Optional Freetext 5", "MECP/2/T05 @١٤٣٠", ["T05"], "@١٤٣٠")

# ---------------------------------------------------------------- language
L = "6.1 Language hint"
ok("lang.canonical", L, "MECP/3/L04 Gipfel erreicht @de", ["L04"], "Gipfel erreicht @de",
   language="de")
ok("lang.upper", L, "MECP/3/L04 @DE", ["L04"], "@DE", language="de")
ok("lang.underscore", L, "MECP/3/L04 @zh_CN", ["L04"], "@zh_CN", language="zh-cn")
ok("lang.region", L, "MECP/3/L04 @zh-TW", ["L04"], "@zh-TW", language="zh-tw")
ok("lang.script-region", L, "MECP/3/L04 @zh-Hans-CN", ["L04"], "@zh-Hans-CN",
   language="zh-hans-cn")
ok("lang.sr-latn", L, "MECP/3/L04 @sr-Latn-RS", ["L04"], "@sr-Latn-RS", language="sr-latn-rs")
ok("lang.three-letter", L, "MECP/3/L04 @fil", ["L04"], "@fil", language="fil")
ok("lang.four-letter", L, "MECP/3/L04 @abcd", ["L04"], "@abcd")
ok("lang.email", L, "MECP/3/L04 mail me@example.com", ["L04"], "mail me@example.com")
ok("lang.period", L, "MECP/3/L04 @en.", ["L04"], "@en.", language="en")
ok("lang.turkish-i", "6.1 Optional Freetext 5", "MECP/3/L04 @TR", ["L04"], "@TR", language="tr",
   note="ASCII-only, locale-independent case folding.")

# ---------------------------------------------------------------- callsign
C = "6.1 Callsign"
ok("cs.portable", C, "MECP/3/L20 ~VK2/OK1ABC/P", ["L20"], "~VK2/OK1ABC/P",
   callsign="VK2/OK1ABC/P")
ok("cs.lower", C, "MECP/3/L20 ~vk2/ok1abc/p", ["L20"], "~vk2/ok1abc/p", callsign="VK2/OK1ABC/P")
ok("cs.prefix", C, "MECP/3/L20 ~DL/OK1ABC", ["L20"], "~DL/OK1ABC", callsign="DL/OK1ABC")
ok("cs.simple", C, "MECP/3/L20 ~OK1ABC", ["L20"], "~OK1ABC", callsign="OK1ABC")
ok("cs.twelve", C, "MECP/3/L20 ~ABCDEFGHIJKL", ["L20"], "~ABCDEFGHIJKL",
   callsign="ABCDEFGHIJKL")
ok("cs.thirteen-skipped", C, "MECP/3/L20 ~ABCDEFGHIJKLM ~OK1ABC", ["L20"],
   "~ABCDEFGHIJKLM ~OK1ABC", callsign="OK1ABC")
ok("cs.comma", C, "MECP/3/L20 ~OK1ABC, ok", ["L20"], "~OK1ABC, ok", callsign="OK1ABC")
ok("cs.ssid", C, "MECP/3/L20 ~OK1ABC-7", ["L20"], "~OK1ABC-7",
   note="An APRS/AX.25 SSID is outside the alphabet and '-' is not in B, so this is not a "
        "callsign and is not read as ~OK1ABC either (1.4.0, mecp-org/MECP#36).")
ok("cs.aprs-ssid", C, "MECP/3/L20 ~W1AW-9", ["L20"], "~W1AW-9")
ok("cs.portable-ssid", C, "MECP/3/L20 ~vk2/ok1abc-7", ["L20"], "~vk2/ok1abc-7")
ok("cs.glued-left", C, "MECP/3/L20 de~OK1ABC", ["L20"], "de~OK1ABC")

# ---------------------------------------------------------------- reference
R = "6.1 Reference"
ok("ref.basecamp", R, "MECP/2/C08 #basecamp", ["C08"], "#basecamp", reference="basecamp")
ok("ref.hyphen", R, "MECP/2/C08 #base-camp,", ["C08"], "#base-camp,", reference="base-camp")
ok("ref.underscore", R, "MECP/2/C08 #base_camp", ["C08"], "#base_camp", reference="base-camp",
   note="Compared by identity: case-insensitive, '_' equals '-'.")
ok("ref.upper", R, "MECP/2/C08 #BaseCamp", ["C08"], "#BaseCamp", reference="basecamp")
ok("ref.paren", R, "MECP/2/C08 (#tag)", ["C08"], "(#tag)", reference="tag")
ok("ref.digits", R, "MECP/2/C08 #2026a", ["C08"], "#2026a", reference="2026a")
ok("ref.long", R, "MECP/2/C08 #flood-sector-north-7", ["C08"], "#flood-sector-north-7",
   reference="flood-sector-north-7")
ok("ref.cjk", R, "MECP/2/C08 #避難所", ["C08"], "#避難所")
ok("ref.cyrillic", R, "MECP/2/C08 #база", ["C08"], "#база")
ok("ref.accent", R, "MECP/2/C08 #café", ["C08"], "#café")
ok("ref.glued-left", R, "MECP/2/C08 issue#5", ["C08"], "issue#5")

# ---------------------------------------------------------------- duration
D = "6.1 Duration"
ok("dur.min", D, "MECP/2/R03 45min", ["R03"], "45min", duration=45)
ok("dur.eta-min", D, "MECP/2/R03 ETA 45min", ["R03"], "ETA 45min", duration=45)
ok("dur.eta-glued", D, "MECP/2/R03 ETA45min", ["R03"], "ETA45min", duration=45)
ok("dur.space-min", D, "MECP/2/R03 45 min", ["R03"], "45 min", duration=45)
ok("dur.bare", D, "MECP/2/R03 45", ["R03"], "45", duration=45)
ok("dur.eta-bare", D, "MECP/2/R03 ETA 45", ["R03"], "ETA 45", duration=45)
ok("dur.h", D, "MECP/2/R03 2h", ["R03"], "2h", duration=120)
ok("dur.hm", D, "MECP/2/R03 1h30min", ["R03"], "1h30min", duration=90)
ok("dur.h-space-m", D, "MECP/2/R03 1h 30min", ["R03"], "1h 30min", duration=90)
ok("dur.d", D, "MECP/2/R03 1d", ["R03"], "1d", duration=1440)
ok("dur.s", D, "MECP/2/R03 120s", ["R03"], "120s",
   note="1.4.0 dropped seconds: s is not a unit of this convention.")
ok("dur.with-codes-before", D, "MECP/2/C01 R03 P05 47.3769,12.1048 45min", ["C01", "R03", "P05"],
   "47.3769,12.1048 45min", gps=gps(47.3769, 12.1048), duration=45)
ok("dur.example", D, "MECP/2/C01 R03 45min @en", ["C01", "R03"], "45min @en", duration=45,
   language="en")
ok("dur.unscoped-min", "6.1 Optional Freetext 9", "MECP/3/L06 45min", ["L06"], "45min")
ok("dur.unscoped-bare", "6.1 Optional Freetext 9", "MECP/3/L06 45", ["L06"], "45")
ok("dur.bare-not-first", D, "MECP/2/C01 R03 1pax 45", ["C01", "R03"], "1pax 45", pax=1)
ok("dur.bare-latitude", D, "MECP/2/R03 47.3769,12.1048", ["R03"], "47.3769,12.1048",
   gps=gps(47.3769, 12.1048), note="The bare number must not have a decimal part (1.4.0).")
ok("dur.bare-after-ts", D, "MECP/2/R03 @1430 45", ["R03"], "@1430 45", timestamp="14:30")
ok("dur.2d", D, "MECP/2/R03 2d", ["R03"], "2d", duration=2880,
   note="1.2.1 removed the 1440-minute upper bound.")
ok("dur.48h", D, "MECP/2/R03 48h", ["R03"], "48h", duration=2880)
ok("dur.2880min", D, "MECP/2/R03 2880min", ["R03"], "2880min", duration=2880)
ok("dur.week", D, "MECP/2/R03 7d", ["R03"], "7d", duration=10080)
ok("dur.zero", D, "MECP/2/R03 0min", ["R03"], "0min")
ok("dur.first-by-position", D, "MECP/2/R03 30min or 1h", ["R03"], "30min or 1h", duration=30,
   note="The first match by position wins (rule 5); 1h is ignored.")
ok("dur.same-position-list-order", D, "MECP/2/R03 2 h", ["R03"], "2 h", duration=120,
   note="h (pattern 2) and the bare number both start at 0; the bare number is only a fallback.")
ok("dur.zero-seconds", D, "MECP/2/R03 0s", ["R03"], "0s", note="s is not a unit (1.4.0).")
ok("dur.huge", "6.1 Optional Freetext 10", "MECP/2/R03 99999999999999999999999min", ["R03"],
   "99999999999999999999999min", skip=("duration",), proposed=True,
   note="Must decode without failing; the value SHOULD be clamped, so it is not compared.")
ok("dur.h-then-digits", D, "MECP/2/R03 1h30", ["R03"], "1h30")
ok("dur.days-word", D, "MECP/2/R03 in 5 days", ["R03"], "in 5 days")
ok("dur.with-pax", D, "MECP/2/R03 4pax 2h", ["R03"], "4pax 2h", pax=4, duration=120)
ok("dur.localised", D, "MECP/2/R03 45分", ["R03"], "45分")
ok("dur.first-of-kind", D, "MECP/2/R03 25h 3h", ["R03"], "25h 3h", duration=1500)
ok("dur.zero-then-ok", "6.1 Optional Freetext 6", "MECP/2/R03 0min 5min", ["R03"], "0min 5min",
   duration=5)
ok("dur.bare-first-token-only", D, "MECP/2/R03 2 sleeping bags", ["R03"], "2 sleeping bags",
   duration=2, note="Decode-only form: a bare first-token number is minutes. Encoders must not emit it.")
ok("dur.bare-not-days", D, "MECP/2/R03 5 days", ["R03"], "5 days", duration=5,
   note="'5 days' is not the day form '5d'; the bare first token 5 is read as minutes. Decode-only.")

# ---------------------------------------------------------------- mixed
MX = "6.1"
ok("mix.everything", MX, "MECP/0/M01 M07 R03 3pax 48.8566,2.3522 @1430 @en ~OK1ABC #base 20min",
   ["M01", "M07", "R03"], "3pax 48.8566,2.3522 @1430 @en ~OK1ABC #base 20min",
   pax=3, gps=gps(48.8566, 2.3522), timestamp="14:30", language="en", callsign="OK1ABC",
   reference="base", duration=20)
ok("mix.beacon", MX, "MECP/0/B01 M01 P05 48.65,20.13 @1430", ["B01", "M01", "P05"],
   "48.65,20.13 @1430", gps=gps(48.65, 20.13), timestamp="14:30")
ok("mix.drill", MX, "MECP/0/D01 M01 M07 2pax P05 48.65,20.13", ["D01", "M01", "M07"],
   "2pax P05 48.65,20.13", pax=2, gps=gps(48.65, 20.13))


# ------------------------------------------------------------ code table
# Brief §7 "The Full Code Table": category letter and number of codes, numbered
# from 01 with no gaps. Unknown codes still decode (Codes rule 5), so a client
# missing one only shows it as unknown; vectors cannot catch that, this table can.
CODE_TABLE = [("M", 16), ("T", 17), ("W", 6), ("S", 6), ("P", 7), ("C", 8), ("R", 7),
              ("D", 4), ("L", 20), ("X", 7), ("H", 8), ("B", 3)]
CODES = [f"{cat}{n:02d}" for cat, count in CODE_TABLE for n in range(1, count + 1)]
assert len(CODES) == 109, "§7: MECP defines 109 codes"


def codes_document() -> dict:
    return {
        "spec": "MECP 1.4.1, MECP_Comprehensive_Brief.md §7",
        "kind": "code-table",
        "generated_by": "conformance/vectors/build.py (hand-written; do not edit the JSON)",
        "codes": CODES,
    }


def document() -> dict:
    return {
        "spec": "MECP 1.4.1, MECP_Comprehensive_Brief.md §6.1",
        "kind": "decode",
        "generated_by": "conformance/vectors/build.py (hand-written; do not edit the JSON)",
        "fields": ["valid", "severity", "codes", "freetext", *FIELDS],
        "cases": CASES,
    }


def _same(a, b, field):
    if field == "reference" and a is not None and b is not None:
        return a.lower().replace("_", "-") == b.lower().replace("_", "-")
    return a == b


def check_against_reference() -> list[str]:
    import record

    problems = []
    for c in CASES:
        got = record.decode(c["input"])
        for k, want in c["expect"].items():
            if not _same(got.get(k), want, k):
                problems.append(f"{c['id']}: {k} hand-written {want!r}, reference {got.get(k)!r}")
    return problems


def main() -> int:
    outputs = {OUT: document(), CODES_OUT: codes_document()}
    texts = {path: json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
             for path, doc in outputs.items()}
    problems = check_against_reference()
    for p in problems:
        print("MISMATCH", p, file=sys.stderr)
    if "--check" in sys.argv:
        stale = [p for p, t in texts.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        for p in stale:
            print(f"{p.name} is out of date; run build.py", file=sys.stderr)
        return 1 if stale or problems else 0
    for path, text in texts.items():
        path.write_text(text, encoding="utf-8")
    print(f"wrote {len(CASES)} cases to {OUT.name}, {len(CODES)} codes to {CODES_OUT.name}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
