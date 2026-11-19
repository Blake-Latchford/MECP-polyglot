# mesh-client: MECP 1.3.0 decode conformance findings

> **Status 2026-11-18:** re-run against MECP 1.4.0 (`decode-1.4.0.json` plus upstream `freetext/tests.json`) at `11aaa0a408` (2026-11-18): 249/249 pass. The findings below are from the 1.3.0 run; it now passes every case, so the issues below are fixed.

**Tested:** `tryParseMecp()` in `src/renderer/lib/mecp/mecpMessages.ts` at `f8d8132a` (2026-11-16), against
the 178 hand-written vectors in [MECP-polyglot `conformance/vectors/decode-1.3.0.json`](../vectors/decode-1.3.0.json).
**Result:** 155 pass, 23 fail (3 of them depend on a proposed spec change). Nearly every freetext
convention passes, including the 1.2.1 duration rules. Most failures are in envelope parsing. Full list:
[reports/mesh-client.md](../reports/mesh-client.md).

## 1. A trailing newline drops every code

§6.1 says to remove one trailing `\r?\n?` before matching. The decoder doesn't, so the codes section
becomes freetext:

| Input | Expected | Got |
|---|---|---|
| `MECP/2/B03\n` | codes `["B03"]`, freetext null | codes `[]`, freetext `"B03"` |
| `MECP/2/B03\r\n` | codes `["B03"]` | codes `[]` |

**Impact:** a beacon cancel (`B03`) or ack (`B02`) that arrives with a line ending, as it does from serial
or line-based transports, is not recognised. `isBeaconCancel(codes)` returns false.

## 2. The envelope is tokenised, not matched against the §6.1 message pattern

The `^MECP\/[0-3]\/` gate plus the engine's split-on-space tokeniser accepts strings that the §6.1
pattern rejects:

| Input | Expected `valid` |
|---|---|
| `MECP/0/` (no codes) | false |
| `MECP/1/T05 ` / `MECP/1/T05 help ` (trailing space) | false |
| `MECP/0/M01  help`, `MECP/0/M01  M07` (double space) | false |
| `MECP/0/M01\tM07`, `MECP/0/M01 help` | false |
| `MECP/0/M01\nM07`, `MECP/3/L01 a\u2028b`, `MECP/3/L01 a\u0085b` | false |
| `MECP/0/M011`, `MECP/1/t05 x` | false |

**Suggested fix:** the vendored `freetext/patterns.json` already contains the `message` pattern.
Strip `\r?\n?$` first, reject the remaining line if it contains `\r \n U+0085 U+2028 U+2029`, then
take severity, codes and freetext from that pattern's three groups. Using group 3 directly also keeps
freetext verbatim, which `env.freetext-inner-spaces` checks.

## 3. Duration patterns are tried in list order, not by position

`MECP/2/R03 30min or 1h` gives 60; expected 30. §6.1 rule 5 uses the first match by position, so
`30min` wins and `1h` is ignored. List order only breaks ties at the same position (`1h 30min` is 90).
The upstream `check-freetext.mjs` has the same bug, which is probably where this came from; a fix is
proposed alongside the spec wording.

## 4. Proposed: APRS/AX.25 SSIDs in callsigns

A pending spec change allows `-` in callsigns, so `~W1AW-9` decodes as `W1AW-9` (today: null), and
`~vk2/ok1abc-7` as `VK2/OK1ABC-7` (today: `VK2`). The vectors mark these cases *(proposed)*.

## Not covered by the vectors

`extractMecpCoords()` in `mecpMessages.ts` is a second GPS parser (`#?(-?\d+\.\d+),\s*(-?\d+\.\d+)`, used
for incident fingerprints). It has no boundary check and accepts any whitespace after the comma, so it
can disagree with the decoder's `gps` for the same message. Consider deriving it from `extracted.gps`.
