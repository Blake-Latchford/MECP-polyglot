# meshcore-one: MECP 1.4.1 decode conformance

- Client: MeshCore One (MC1) iOS app, MECPDecode.decode() and MECPMessage's derived fields
- Repository: https://github.com/Avi0n/MeshCoreOne
- Commit tested: `26460496fe` (2026-11-20)
- Decoder: `MC1Services/Sources/MC1Services/MECP/MECPDecode.swift`
- Fields compared: valid, severity, codes, freetext, pax, timestamp, duration (others not exposed by this client)
- Vectors: `conformance/vectors/decode-1.4.1.json` plus mecp-org/MECP `freetext/tests.json` (256 cases), run 2026-11-21
- **Result: 209 pass, 47 fail, 0 error**
- **Code table: 108/109**

## Code table (§7)

Compared with `conformance/vectors/codes-1.4.1.json`. A missing code still decodes (Codes rule 5) but has no label, so it reads as unknown.

- Missing (1): `M16`

## Decode vectors

Cases marked *(proposed)* depend on spec changes not yet merged upstream; see the vector's `proposed` field.

Each row is one vector. *Expected* is written by hand from the protocol brief (clause in the heading); *Got* is what this client's decoder returned.

### 6.1 Duration (18)

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

### upstream: Duration (15)

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
| `up.60` Duration: a skipped decimal value lets the next value be used | `MECP/2/R03 1.5h 45min` | duration | 45 | null |
| `up.61` Duration: a period after a letter still separates a value | `MECP/2/R03 hut.2h` | duration | 120 | null |

### 6.1 Timestamp (7)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `ts.three-digit` | `MECP/2/T01 @630` | timestamp | "06:30" | null |
| `ts.colon-one-digit` | `MECP/2/T01 @6:30` | timestamp | "06:30" | null |
| `ts.colon` | `MECP/2/T01 @06:30` | timestamp | "06:30" | null |
| `ts.hmm` | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `ts.skip-invalid` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | null |
| `ts.trailing-comma` | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |
| `ts.glued-left` | `MECP/2/T05 meet@1430` | timestamp | null | "14:30" |

### upstream: Timestamp (5)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.00` Timestamp: out-of-range values are skipped and the first valid one is used | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | null |
| `up.02` Timestamp: a three-digit value implies a leading zero hour | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `up.03` Timestamp: trailing punctuation is a boundary | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |
| `up.04` Timestamp: a sigil inside a word is not decoded | `MECP/2/T05 meet@1430` | timestamp | null | "14:30" |
| `up.05` Timestamp: an equals sign is not a boundary | `MECP/3/L06 eta=@1430` | timestamp | null | "14:30" |

### 6.1 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `mix.everything` | `MECP/0/M01 M07 R03 3pax 48.8566,2.3522 @1430 @en ~OK1ABC #base 20min` | duration | 20 | null |

### 6.1 Optional Freetext 6 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `dur.zero-then-ok` | `MECP/2/R03 0min 5min` | duration | 5 | null |
