# meshcore-one: MECP 1.4.0 decode conformance findings

**Tested:** `MECPDecode.decode()` and the fields `MECPMessage` derives from it (`personCount`,
`timestampHHMM`, `eta`) in `MC1Services/Sources/MC1Services/MECP/` (MeshCore One `5e980a53`,
2026-11-16), against the 179 hand-written vectors in [`decode-1.4.0.json`](../vectors/decode-1.4.0.json)
plus the 70 cases in mecp-org/MECP `freetext/tests.json`.
**Result:** 154 pass, 95 fail. MC1 does not decode GPS, language, callsign or reference, so those
are not scored. Full list: [reports/meshcore-one.md](../reports/meshcore-one.md).

The decoder follows the pre-1.2 `@mecp/engine` rules: it splits the body on spaces and looks for a
few fixed shapes. MECP 1.2 replaced those rules with the §6.1 message pattern and per-convention
decoding patterns wrapped in a boundary class B. Most failures below have the same fix: match the
§6.1 patterns from [`freetext/patterns.json`](https://github.com/mecp-org/MECP/blob/main/freetext/patterns.json).

## 1. The envelope is not the §6.1 message pattern (21 vectors, 7 upstream)

`decode()` checks the prefix and the severity digit, skips two characters, and splits the rest on
spaces, dropping empty tokens. As a result it accepts messages that are not MECP and changes the
freetext of ones that are:

| Input | Expected | MC1 |
|---|---|---|
| `MECP/0/` , `MECP/0` | not a message (no codes) | valid, no codes |
| `MECP/1/t05 x` | not a message (lowercase is not a code) | valid, freetext `t05 x` |
| `MECP/01/M01` | not a message | valid, codes `[M01]` |
| `MECP/1/T05 `, `MECP/0/M01  help`, `MECP/0/M01\tM07` | not a message (spacing) | valid |
| `MECP/3/L01 a\nb`, `a b`, `a\fb` | not a message (line break) | valid |
| `MECP/2/B03\n` | codes `[B03]` (one trailing CR/LF is stripped) | codes `[]`, freetext `B03\n` |
| `MECP/3/L01 see  you   there` | freetext kept verbatim | `see you there` |

The trailing-newline case matters in practice: a message read from a serial or text source with
its line ending loses all its codes.

## 2. No boundary class B (10 vectors, 5 upstream)

Person count is found wherever digits are followed by `pax`, with no boundary on either side, so
`x4pax`, `3paxmore`, `*4pax*`, `#4pax` and `4pax\u000bwater` all decode as a count. The other
direction fails too: `4Pax.` and `4 pax` and `4PAX` are not decoded, because the unit is matched
case-sensitively with no optional space and `.` is not treated as a boundary. `0pax 2pax` decodes
as 0; zero is not a valid count, so the decoder should move on to `2pax`.

## 3. Timestamp accepts only `@HHMM` followed by a space (7 vectors, 5 upstream)

`@630`, `@6:30`, `@06:30` and `@123` are not decoded; the §6.1 decoding pattern reads them as
06:30, 06:30, 06:30 and 01:23. `@1430,` is not decoded because `,` is not accepted after the
value. `@2460 @1400` gives no timestamp: an out-of-range value must be skipped and the next one
used (rule 6). In the other direction `meet@1430` decodes as 14:30, although `@` inside a word is
not a timestamp.

## 4. R03 duration reads only a bare leading number (18 vectors, 13 upstream)

`eta` is the first freetext token when it is all digits. None of the unit forms decode:
`45min`, `2h`, `1h30min`, `1h 30min`, `2d`, `ETA 45min`, `ETA45min`, `ETA 45` all give null. Where
a unit is present the bare number wins: `R03 2 h` gives 2 (expected 120) and `R03 45 2h` gives
45 (expected 120, since a value with a unit is preferred over a bare number).

## Adapter

[`adapters/meshcore-one/`](../adapters/meshcore-one/) compiles MC1's own `MECPDecode.swift` and
`MECPMessage.swift` from the checkout, together with a small `main.swift`, into one module. It uses
the official `swift` Docker image and links statically, so the host needs only Docker. No MC1 code
(GPLv3) is copied into this repository. The adapter changes representation only
(`timestampHHMM` `1430` becomes `14:30`).
