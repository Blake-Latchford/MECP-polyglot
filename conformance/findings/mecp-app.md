# mecp-app (`@mecp/engine`): MECP 1.3.0 decode conformance findings

> **Status 2026-11-18:** re-run against MECP 1.4.0 (`decode-1.4.0.json` plus upstream `freetext/tests.json`) at `80139af8e6` (2026-11-11): 118/249 pass. The findings below are from the 1.3.0 run; This write-up has not been re-checked against 1.4.0.

**Tested:** `engine/src/decoder.ts` `decode()` at `80139af8` (2026-11-11), against the 178 hand-written
vectors in [`decode-1.3.0.json`](../vectors/decode-1.3.0.json).
**Result:** 86 pass, 92 fail (3 depend on a proposed spec change). The engine still implements the 1.1 freetext rules, while the MECP
README calls it the reference implementation. Full list: [reports/mecp-app.md](../reports/mecp-app.md).

**Fastest path to conformance:** mesh-client vendors this engine and has already ported it to 1.2.1
(Colorado-Mesh/mesh-client#1472: `engine/freetextExtract.ts`, `freetext/patterns.json`, a conformance
test). It passes every freetext vector except duration ordering (`30min or 1h`). Upstreaming that
port, with that fix, would fix causes 3–5 below. This is the planned PR.

## 1. A trailing newline drops every code

`MECP/2/B03\n` decodes as codes `[]` and freetext `"B03\n"`. §6.1 removes one trailing `\r?\n?`
before matching. Beacon cancel/ack messages with a line ending are not recognised.

## 2. The envelope is tokenised, not matched against the §6.1 message pattern

Accepted although §6.1 rejects them: `MECP/0/`, `MECP/0`, `MECP/01/M01`, `MECP/0/M011`, `MECP/1/t05 x`,
trailing or double spaces, tabs, embedded `\r` `\n` U+0085 U+2028, and NBSP after the codes. Inner
runs of spaces in freetext are collapsed (`see  you   there` → `see you there`). Freetext is §6.1
group 3, verbatim.

## 3. Freetext conventions use the 1.1 patterns

| Convention | Example | Expected | Got |
|---|---|---|---|
| Reference | `#basecamp`, `#flood-sector-north-7` | `basecamp`, `flood-sector-north-7` | `base`, `floo` (truncated to 4) |
| Language | `@DE`, `@zh_CN`, `@zh-Hans-CN`, `@fil` | `de`, `zh-cn`, `zh-hans-cn`, `fil` | null |
| Timestamp | `@630`, `@6:30`, `@123`, `@1430,` | `06:30`, `06:30`, `01:23`, `14:30` | null |
| Callsign | `~VK2/OK1ABC/P`, `~ABCDEFGHIJKL` | `VK2/OK1ABC/P`, `ABCDEFGHIJKL` | null (no `/`, max 9) |
| Pax | `4 pax`, `4PAX`, `4Pax.` | 4 | null |
| GPS | `+48.8566, 2.3522` | 48.8566, 2.3522 | null |

## 4. No boundary class B

Matches are found inside words: `x4pax` → 4, `3paxmore` → 3, `meet@1430` → 14:30, `issue#5` → `5`,
`de~OK1ABC` → `OK1ABC`, `x48.65,20.13` → GPS. Punctuation after a value prevents a match:
`4Pax.`, `@1430,`, `@en.`.

## 5. No validate-and-resume, and no R03 duration convention

- When the first match fails validation, the decoder does not search on. `95.0,200.0 47.3,8.5` gives
  no GPS, `@2460 @1400` gives no timestamp, and `0pax 2pax` gives 0.
- Duration only reads a bare leading number into `extracted.eta`. `45min`, `2h`, `1h30min`, `1d`,
  `120s` and `ETA 45min` are not decoded.
