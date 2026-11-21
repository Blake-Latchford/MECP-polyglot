# MECP §6.1: spec questions and their status

Checked against mecp-org/MECP `main` at `76bcc1b` (protocol 1.4.0). Earlier tentative brief edits were
on `Blake-Latchford/MECP` branch `spec-clarifications`; vectors that still depend on text the 1.4.0
brief does not contain carry a `proposed` field.

Policy: upstream test cases are added only for real bugs or decided behaviour, not speculative
inputs. The upstream checker's structure will be reworked once the bug list is settled.

## Decided

| # | Topic | Decision | Where |
|---|---|---|---|
| A1 | Trailing line terminator | Remove at most one `\n`, `\r` or `\r\n` (1.4.0 "Decoder preprocessing") | vectors `env.trailing-*`, `env.lfcr`, `env.two-crlf`; upstream cases |
| A2 | Resume after a failed validation | Resume at the end of the failed *token*, so its trailing boundary can begin the next match | rule 6; `gps.resume-after-invalid`, `ts.skip-invalid` |
| A3 | Seconds | 1.4.0 dropped `s` as a unit: `30s` is not a duration, so rounding is moot | `dur.s`, `dur.zero-seconds`; upstream "seconds are not a unit" |
| A5 | VT (U+000B) | Not a boundary. 1.4.0 rule 4 lists the ASCII boundaries explicitly (mecp-org/MECP#38) | `b.vt-not-b`, `b.asterisk`, `b.slash` |
| A6 | Length limit | Encoders MUST NOT emit more than 200 bytes; decoders MUST NOT reject longer messages (1.4.0) | upstream 202-byte case |
| A8 | Bare-number duration | `R03 2 sleeping bags` = 2 min, `R03 5 days` = 5 min. Decode-only, never encoded. | `dur.bare-first-token-only`, `dur.bare-not-days` |
| N1 | Bare number against a GPS first token | 1.4.0: the bare number must not have a decimal part, so `R03 47.3769,12.1048` has no duration | `dur.bare-latitude`; upstream case |
| T3 | Duration with several matches | First match by position wins (`30min or 1h` = 30); list order only breaks ties at the same position (1.4.0) | `dur.first-by-position`, `dur.same-position-list-order` |
| T4 | `1.5pax` | Decodes as 5. Encoders cannot produce it, because encoded values follow a space (rule 3). | `pax.after-decimal` |
| T5 | `48.65,20.13,1200` | GPS 48.65,20.13; `,1200` stays in the freetext | `gps.altitude-suffix` |
| T6 | APRS/AX.25 SSIDs | 1.4.0 (mecp-org/MECP#36): `~W1AW-9` is not a callsign and is not read as `~W1AW` either. The `-` proposal was not adopted. | `cs.ssid`, `cs.aprs-ssid`, `cs.portable-ssid` |
| U1 | Checker's B class | The checker now reads B from rule 4 of the brief | `check-freetext.mjs` |

## Open

| # | Topic | Status |
|---|---|---|
| A4 | Is the structured `reference` value normalised? | The brief defines identity (case-insensitive, `_` = `-`) but not the exposed value. Upstream's checker returns it verbatim. The harness compares by identity. See `ref.underscore`, `ref.upper`. |
| A7 | Very large numbers | Not in the 1.4.0 brief. Proposed: decoders MUST handle any digit run without failing and SHOULD clamp. `pax.huge` and `dur.huge` are *(proposed)* and do not compare the value. MECP-polyglot clamps to 2147483647; upstream's checker does not clamp. |

## Upstream follow-ups

| # | Item |
|---|---|
| U3 | `check-freetext.mjs` slices the string between searches, so `^` can match mid-text after a fallback resume. It gives the same results today, because a resume always lands on a boundary character and no pattern starts with one. To be reworked once the bug list is settled. |
