# meshcore-one: MECP 1.4.0 decode conformance

- Client: MeshCore One (MC1) iOS app, MECPDecode.decode() and MECPMessage's derived fields
- Repository: https://github.com/Avi0n/MeshCoreOne
- Commit tested: `5e980a53e0` (2026-11-16)
- Decoder: `MC1Services/Sources/MC1Services/MECP/MECPDecode.swift`
- Fields compared: valid, severity, codes, freetext, pax, timestamp, duration (others not exposed by this client)
- Vectors: `conformance/vectors/decode-1.4.0.json` plus mecp-org/MECP `freetext/tests.json` (249 cases), run 2026-11-18
- **Result: 154 pass, 95 fail, 0 error**

Cases marked *(proposed)* depend on spec changes not yet merged upstream; see the vector's `proposed` field.

Each row is one vector. *Expected* is written by hand from the protocol brief (clause in the heading); *Got* is what this client's decoder returned.

## 6.1 Message Format (21)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.freetext-inner-spaces` | `MECP/3/L01 see  you   there` | freetext | "see  you   there" | "see you there" |
| `env.trailing-lf` | `MECP/2/B03\n` | codes | ["B03"] | [] |
|  |  | freetext | null | "B03\n" |
| `env.trailing-cr` | `MECP/2/B03\r` | codes | ["B03"] | [] |
|  |  | freetext | null | "B03\r" |
| `env.trailing-crlf` | `MECP/2/B03\r\n` | codes | ["B03"] | [] |
|  |  | freetext | null | "B03\r\n" |
| `env.trailing-crlf-freetext` | `MECP/3/L01 see you\r\n` | freetext | "see you" | "see you\r\n" |
| `env.no-codes` | `MECP/0/` | valid | false | true |
| `env.no-codes-no-slash` | `MECP/0` | valid | false | true |
| `env.four-char-code` | `MECP/0/M011` | valid | false | true |
| `env.trailing-space` | `MECP/1/T05 ` | valid | false | true |
| `env.trailing-space-after-text` | `MECP/1/T05 help ` | valid | false | true |
| `env.double-space-before-freetext` | `MECP/0/M01  help` | valid | false | true |
| `env.double-space-between-codes` | `MECP/0/M01  M07` | valid | false | true |
| `env.tab-after-codes` | `MECP/0/M01\tM07` | valid | false | true |
| `env.embedded-lf` | `MECP/0/M01\nM07` | valid | false | true |
| `env.embedded-cr` | `MECP/3/L01 a\rb` | valid | false | true |
| `env.line-separator` | `MECP/3/L01 a\u2028b` | valid | false | true |
| `env.nel` | `MECP/3/L01 a\u0085b` | valid | false | true |
| `env.two-trailing-lf` | `MECP/2/B03\n\n` | valid | false | true |
| `env.lfcr` | `MECP/2/B03\n\r` | valid | false | true |
| `env.two-crlf` | `MECP/2/B03\r\n\r\n` | valid | false | true |
| `env.nbsp-after-codes` | `MECP/0/M01\u00a0help` | valid | false | true |

## 6.1 Duration (18)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `dur.min` | `MECP/2/R03 45min` | duration | 45 | null |
| `dur.eta-min` | `MECP/2/R03 ETA 45min` | duration | 45 | null |
| `dur.eta-glued` | `MECP/2/R03 ETA45min` | duration | 45 | null |
| `dur.eta-bare` | `MECP/2/R03 ETA 45` | duration | 45 | null |
| `dur.h` | `MECP/2/R03 2h` | duration | 120 | null |
| `dur.hm` | `MECP/2/R03 1h30min` | duration | 90 | null |
| `dur.h-space-m` | `MECP/2/R03 1h 30min` | duration | 90 | null |
| `dur.d` | `MECP/2/R03 1d` | duration | 1440 | null |
| `dur.with-codes-before` | `MECP/2/C01 R03 P05 47.3769,12.1048 45min` | duration | 45 | null |
| `dur.example` | `MECP/2/C01 R03 45min @en` | duration | 45 | null |
| `dur.2d` | `MECP/2/R03 2d` | duration | 2880 | null |
| `dur.48h` | `MECP/2/R03 48h` | duration | 2880 | null |
| `dur.2880min` | `MECP/2/R03 2880min` | duration | 2880 | null |
| `dur.week` | `MECP/2/R03 7d` | duration | 10080 | null |
| `dur.first-by-position` | `MECP/2/R03 30min or 1h` | duration | 30 | null |
| `dur.same-position-list-order` | `MECP/2/R03 2 h` | duration | 120 | 2 |
| `dur.with-pax` | `MECP/2/R03 4pax 2h` | duration | 120 | null |
| `dur.first-of-kind` | `MECP/2/R03 25h 3h` | duration | 1500 | null |

## upstream: Duration (13)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.36` Duration: minutes | `MECP/2/R03 45min` | duration | 45 | null |
| `up.37` Duration: days are converted to minutes, with no upper bound | `MECP/2/R03 2d` | duration | 2880 | null |
| `up.38` Duration: hours are converted to minutes | `MECP/2/R03 48h` | duration | 2880 | null |
| `up.39` Duration: a large minute count is not capped | `MECP/2/R03 2880min` | duration | 2880 | null |
| `up.40` Duration: an ETA prefix is accepted | `MECP/2/R03 ETA 45min` | duration | 45 | null |
| `up.42` Duration: R03 applies when it is not the first code, alongside a position | `MECP/2/C01 R03 P05 47.3769,12.1048 45min` | duration | 45 | null |
| `up.46` Duration: a value in seconds is skipped and the next value is used | `MECP/2/R03 30s 45min` | duration | 45 | null |
| `up.48` Duration: a bare number followed by a period is minutes | `MECP/2/R03 45.` | duration | 45 | null |
| `up.50` Duration: a value with a unit is preferred over a bare number | `MECP/2/R03 45 2h` | duration | 120 | 45 |
| `up.51` Duration: the first value by position wins (days before minutes) | `MECP/2/R03 2d 45min` | duration | 2880 | null |
| `up.52` Duration: the first value by position wins (minutes before hours) | `MECP/2/R03 45min 2h` | duration | 45 | null |
| `up.53` Duration: hours and minutes separated by a space are combined | `MECP/2/R03 1h 30min` | duration | 90 | null |
| `up.54` Duration: a space between the number and the unit is accepted | `MECP/2/R03 2 h` | duration | 120 | 2 |

## 6.1 Optional Freetext 4 (10)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `b.period` | `MECP/1/S01 4Pax.` | pax | 4 | null |
| `b.asterisk` | `MECP/1/S01 *4pax*` | pax | null | 4 |
| `b.slash` | `MECP/1/S01 4pax/3` | pax | null | 4 |
| `b.letter-left` | `MECP/1/S01 x4pax` | pax | null | 4 |
| `b.letter-right` | `MECP/1/S01 3paxmore` | pax | null | 3 |
| `b.hash-not-b` | `MECP/1/S01 #4pax` | pax | null | 4 |
| `b.hyphen-not-b` | `MECP/1/S01 -4pax` | pax | null | 4 |
| `b.underscore-not-b` | `MECP/1/S01 _4pax` | pax | null | 4 |
| `b.plus-not-b` | `MECP/1/S01 +4pax` | pax | null | 4 |
| `b.vt-not-b` | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |

## 6.1 Timestamp (7)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `ts.three-digit` | `MECP/2/T01 @630` | timestamp | "06:30" | null |
| `ts.colon-one-digit` | `MECP/2/T01 @6:30` | timestamp | "06:30" | null |
| `ts.colon` | `MECP/2/T01 @06:30` | timestamp | "06:30" | null |
| `ts.hmm` | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `ts.skip-invalid` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | null |
| `ts.trailing-comma` | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |
| `ts.glued-left` | `MECP/2/T05 meet@1430` | timestamp | null | "14:30" |

## upstream: Message (7)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.55` Message: a trailing space is invalid | `MECP/1/T05 ` | valid | false | true |
| `up.56` Message: a lowercase first code is not a code, so the message has no codes and is invalid | `MECP/1/t05 x` | valid | false | true |
| `up.60` Message: no codes after the severity is invalid | `MECP/0/` | valid | false | true |
| `up.61` Message: a missing code section is invalid | `MECP/0` | valid | false | true |
| `up.66` Message: an embedded LF is invalid | `MECP/1/T05 foo\nbar` | valid | false | true |
| `up.67` Message: an embedded line separator (U+2028) is invalid | `MECP/1/T05 foo\u2028bar` | valid | false | true |
| `up.68` Message: an embedded form feed is invalid | `MECP/1/T05 foo\fbar` | valid | false | true |

## upstream: Pax (5)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.16` Pax: letters after the unit prevent a match | `MECP/1/S01 3paxmore` | pax | null | 3 |
| `up.17` Pax: zero fails validation and the next value is used | `MECP/1/S01 0pax 2pax` | pax | 2 | 0 |
| `up.20` Pax: the unit is case-insensitive and a trailing period is a boundary | `MECP/1/S01 4Pax.` | pax | 4 | null |
| `up.22` Pax: a vertical tab (U+000B) is not a boundary | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |
| `up.24` Pax: an asterisk is not a boundary | `MECP/1/S01 3pax*` | pax | null | 3 |

## upstream: Timestamp (5)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.00` Timestamp: out-of-range values are skipped and the first valid one is used | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | null |
| `up.02` Timestamp: a three-digit value implies a leading zero hour | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `up.03` Timestamp: trailing punctuation is a boundary | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |
| `up.04` Timestamp: a sigil inside a word is not decoded | `MECP/2/T05 meet@1430` | timestamp | null | "14:30" |
| `up.05` Timestamp: an equals sign is not a boundary | `MECP/3/L06 eta=@1430` | timestamp | null | "14:30" |

## 6.1 Person count (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `pax.space` | `MECP/1/S01 4 pax` | pax | 4 | null |
| `pax.upper` | `MECP/1/S01 4PAX` | pax | 4 | null |
| `pax.zero-skipped` | `MECP/1/S01 0pax 2pax` | pax | 2 | 0 |
| `pax.two-spaces` | `MECP/1/S01 4  pax` | freetext | "4  pax" | "4 pax" |

## 6.1 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `mix.everything` | `MECP/0/M01 M07 R03 3pax 48.8566,2.3522 @1430 @en ~OK1ABC #base 20min` | duration | 20 | null |

## 6.1 Codes 3 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.lowercase-first-code` | `MECP/1/t05 x` | valid | false | true |

## 6.1 GPS coordinates (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `gps.two-spaces-after-comma` | `MECP/0/M01 48.65,  20.13` | freetext | "48.65,  20.13" | "48.65, 20.13" |

## 6.1 Optional Freetext 6 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `dur.zero-then-ok` | `MECP/2/R03 0min 5min` | duration | 5 | null |

## 6.1 Severity (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.sev-two-digits` | `MECP/01/M01` | valid | false | true |
