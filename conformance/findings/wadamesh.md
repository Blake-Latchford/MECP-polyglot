# Wadamesh MECP app: MECP 1.3.0 decode conformance findings

> **Status 2026-11-18:** re-run against MECP 1.4.0 (`decode-1.4.0.json` plus upstream `freetext/tests.json`) at `3411a8fb3b` (2026-11-16): 180/249 pass. The findings below are from the 1.3.0 run; This write-up has not been re-checked against 1.4.0.

**Tested:** `decode()` in `deploy/apps/mecp/1.0/mecp.lua` at `3411a8fb` (2026-11-16), loaded unmodified
under Lua 5.4 with a stub SDK, against the 178 hand-written vectors in
[`decode-1.3.0.json`](../vectors/decode-1.3.0.json). The app returns rendered text, so only validity,
severity, pax, GPS and timestamp could be compared. Codes, freetext, language, callsign, reference and
duration are untested.
**Result:** 127 pass, 51 fail. Full list: [reports/wadamesh.md](../reports/wadamesh.md).

## 1. Timestamp has no range check

`@2460` renders "at 24:60", `@2400` "at 24:00" and `@9999` "at 99:99". In `@2460 @1400 @1530` the
first valid timestamp is 14:00. (The MECP 1.2.0 changelog names this as non-conformant.) `@630`, `@6:30`,
`@06:30`, `@123` and `@1430,` aren't decoded.

## 2. GPS has no range check and accepts integers

`95.0,200.0 47.3,8.5` renders "at 95.0,200.0" (expected 47.3,8.5). `90.0001,0.0` is shown. `48,20`,
`0,0` and `2,5 km` render as positions. §6.1 requires a decimal point in both numbers and
−90…90 / −180…180. `+48.8566, 2.3522` (sign and space allowed) isn't decoded.

## 3. Severity 4–9 is accepted

`MECP/9/M01` renders as "Severity 9: …". Severity is a single digit 0–3.

## 4. "MECP/" is found anywhere in the line

`Alice: MECP/0/M01` and ` MECP/0/M01` decode. This is deliberate, so that channel lines decode. The
§6.1 pattern is anchored, though, so the sender framing should be stripped first (`^[^:]+: `), then the
rest matched from its first character. Otherwise `see MECP/0/M01 in the docs` raises a MAYDAY.

## 5. The envelope is tokenised on whitespace

`MECP/0/` (no codes), trailing or doubled spaces, tabs, NBSP, embedded `\r`/`\n`/U+2028, `MECP/0/M011`
and `MECP/1/t05 x` are all accepted.

## 6. Pax and boundaries

Values must be whole tokens: `(4pax)`, `4Pax.`, `4pax,3pax`, `*4pax*`, `「4pax」` and `48.65,20.13،`
aren't decoded, and neither are `4 pax` or `4PAX`. `0pax` is shown as "0 people" (expected: skipped, then
`2pax`).
