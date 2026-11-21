# REM (reticulum_mobile_emergency_management): MECP 1.3.0 decode conformance findings

> **Status 2026-11-18:** re-run against MECP 1.4.0 (`decode-1.4.0.json` plus upstream `freetext/tests.json`) at `42cdc3276e` (2026-11-18): 140/249 pass. The findings below are from the 1.3.0 run; This write-up has not been re-checked against 1.4.0.

**Tested:** `decodeMecpMessage()` in `apps/mobile/src/utils/mecp.ts` at `be25a210` (2026-11-16), against the
178 hand-written vectors in [`decode-1.3.0.json`](../vectors/decode-1.3.0.json).
**Result:** 100 pass, 78 fail (1 depends on a proposed spec change). Full list: [reports/reticulum-mobile.md](../reports/reticulum-mobile.md).

## 1. Unknown codes make the whole message invalid

`MECP/3/Z99 hello` and `MECP/1/Q42` are rejected ("Invalid MECP category"). §6.1 Codes rule 5: a
well-formed code not in the table "is still a code. Decoders MUST preserve and display it". A message
using a code added in a later MECP release is dropped instead of shown.

## 2. Codes are uppercased

`MECP/3/L01 l06 late` gives codes `["L01", "L06"]` (expected `["L01"]`, freetext `l06 late`), and
`MECP/1/t05 x` is accepted. Codes are case-sensitive, and a lowercase token ends the code section.

## 3. Conventions are matched against whole tokens, not searched for with boundaries

Each whitespace-separated token must be exactly one value, so punctuation or a space next to it hides it:

| Input | Expected | Got |
|---|---|---|
| `(4pax)`, `4Pax.`, `4pax,3pax`, `4pax、水`, `「4pax」` | pax 4 | null |
| `4 pax` | pax 4 | null |
| `+48.8566, 2.3522`, `at:48.65,20.13`, `48.65,20.13.` | GPS | null |
| `@1430,` | 14:30 | null |
| `~OK1ABC, ok` | `OK1ABC` | null |
| `#base-camp,`, `(#tag)` | reference | null |

The §6.1 approach searches the freetext with each decoding pattern wrapped in `(?:^|B)…(?:B|$)`.

## 4. The last match wins, and invalid matches are not skipped

`2pax 5pax` gives 5 (expected 2), and `@2460 @1400 @1530` gives 15:30 (expected 14:00: the first
*valid* match). `0min 5min` with R03 gives 0 (expected 5).

## 5. GPS accepts integers

`MECP/3/L02 2,5 km` gives GPS 2, 5, and `48,20` and `0,0` also decode. §6.1: both groups must contain a
decimal point. **Impact:** a European decimal comma ("2,5 km") puts a map pin in the Gulf of Guinea.

## 6. Duration (R03)

- Any token of 1–4 digits counts, not only the first freetext token: `R03 1pax 45` and `R03 @1430 45`
  give 45. Expected null.
- `h`, `d`, `s` units and combined `1h30min` aren't decoded: `2h`, `1d`, `2d`, `48h`, `7d`, `120s`
  and `1h30min` give null. `1h 30min` gives 30.
- `0min` gives 0. A total must be ≥ 1.

## 7. Other conventions

- Timestamp: only `@HHMM`. `@630`, `@6:30`, `@06:30` and `@123` aren't decoded.
- Language: only 2–3 letters. `@zh_CN`, `@zh-TW`, `@zh-Hans-CN` and `@sr-Latn-RS` aren't decoded,
  and neither is `@en.`.
- Callsign: `/` isn't allowed, so `~VK2/OK1ABC/P` and `~DL/OK1ABC` give null. `-` and `_` are allowed and
  length is unbounded. `~OK1ABC-7` gives `OK1ABC-7`, which matches a proposed spec change that
  allows APRS/AX.25 SSIDs (pending upstream). `~vk2/ok1abc-7` still gives null because of the `/`.

## 8. Envelope

The input is trimmed and split on `/\s+/`, so a leading space, tabs, NBSP, embedded `\r`/`\n`/U+2028,
trailing spaces and doubled spaces are all accepted. Freetext whitespace is collapsed (NBSP becomes a
space). A body without the `MECP/` prefix (`M01 P05 48.65,20.13`) is decoded as severity 2. If that is
REM's compact wire format, consider a separate entry point so `MECP/` text is decoded strictly.

## 9. Code table (checked 2026-11-20 at `6ccf01a958`)

`MECP_EVENT_CODES` has no `M16` ("Medical supply drop needed", brief §7), so `MECP/1/M16` decodes
with the label "M16" and a warning that the code is unknown. It also has `B04` ("Household / community
status"), which is not in the MECP code table. The Events view offers B04 when composing, so REM can send
a code that other clients show as unknown.
