# meshcore-tak-bridge: MECP 1.3.0 decode conformance findings

> **Status 2026-11-18:** re-run against MECP 1.4.0 (`decode-1.4.0.json` plus upstream `freetext/tests.json`) at `d808585f01` (2026-11-18): 231/249 pass. The findings below are from the 1.3.0 run; the remaining failures are 1.4.0 changes (seconds unit dropped, bare-number latitude, first-by-position, explicit ASCII boundary list, form feed).

**Tested:** `Mecp.parse()` in `meshcore-kotlin/protocol/.../Mecp.kt` (meshcore-kotlin `4d890e1`, via
tak-bridge `100eeb68`, 2026-11-15), against the 178 hand-written vectors in
[`decode-1.3.0.json`](../vectors/decode-1.3.0.json).
**Result:** 173 pass, 5 fail, 3 of which depend on a proposed spec change. This is the most
conformant decoder tested. Full list: [reports/meshcore-tak-bridge.md](../reports/meshcore-tak-bridge.md).

## 1. Duration patterns are tried in list order, not by position

`MECP/2/R03 30min or 1h` gives 60; expected 30. §6.1 rule 5 uses the first match by position, so
`30min` wins and `1h` is ignored. List order only breaks ties at the same position (`1h 30min` is 90).
The upstream `check-freetext.mjs` has the same bug; a fix is proposed alongside the spec wording.

## 2. VT (U+000B) is treated as a boundary

`MECP/1/S01 4pax\u000bwater` gives pax 4; expected null. The ASCII whitespace in B is TAB, LF, FF, CR and
SPACE, the same set as in the §6.1 message pattern. VT is not included. Java/Kotlin `\s` and
`Char.isWhitespace()` include it, so build B from an explicit class.

## 3. Proposed: APRS/AX.25 SSIDs in callsigns

A pending spec change allows `-` in callsigns, so `~W1AW-9` decodes as `W1AW-9` (today: null),
`~OK1ABC-7` as `OK1ABC-7`, and `~vk2/ok1abc-7` as `VK2/OK1ABC-7` (today: `VK2`). The vectors mark these
cases *(proposed)*.
