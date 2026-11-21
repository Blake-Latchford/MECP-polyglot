# wadamesh: MECP 1.4.1 decode conformance

- Client: MECP app decode() (renders text; structured fields recovered from the rendering)
- Repository: https://github.com/ALLFATHER-BV/wadamesh
- Commit tested: `3411a8fb3b` (2026-11-16)
- Decoder: `deploy/apps/mecp/1.0/mecp.lua`
- Fields compared: valid, severity, pax, gps, timestamp (others not exposed by this client)
- Vectors: `conformance/vectors/decode-1.4.1.json` plus mecp-org/MECP `freetext/tests.json` (256 cases), run 2026-11-21
- **Result: 187 pass, 69 fail, 0 error**
- **Code table: 108/109**

## Code table (§7)

Compared with `conformance/vectors/codes-1.4.1.json`. A missing code still decodes (Codes rule 5) but has no label, so it reads as unknown.

- Missing (1): `M16`

## Decode vectors

Cases marked *(proposed)* depend on spec changes not yet merged upstream; see the vector's `proposed` field.

Each row is one vector. *Expected* is written by hand from the protocol brief (clause in the heading); *Got* is what this client's decoder returned.

### 6.1 Message Format (17)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.no-codes` | `MECP/0/` | valid | false | true |
| `env.leading-space` | ` MECP/0/M01` | valid | false | true |
| `env.channel-prefix` | `Alice: MECP/0/M01` | valid | false | true |
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

### 6.1 GPS coordinates (8)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `gps.plus-and-space` | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | null |
| `gps.lat-out-of-range` | `MECP/0/M04 90.0001,0.0` | gps | null | {"lat": 90.0001, "lon": 0.0} |
| `gps.integers` | `MECP/0/M04 48,20` | gps | null | {"lat": 48, "lon": 20} |
| `gps.zero-zero` | `MECP/0/M04 0,0` | gps | null | {"lat": 0, "lon": 0} |
| `gps.decimal-comma` | `MECP/3/L02 2,5 km` | gps | null | {"lat": 2, "lon": 5} |
| `gps.colon-left` | `MECP/0/M01 at:48.65,20.13` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `gps.trailing-period` | `MECP/0/M01 48.65,20.13.` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `gps.altitude-suffix` | `MECP/0/M01 48.65,20.13,1200` | gps | {"lat": 48.65, "lon": 20.13} | null |

### 6.1 Optional Freetext 4 (8)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `b.paren` | `MECP/1/S01 (4pax)` | pax | 4 | null |
| `b.period` | `MECP/1/S01 4Pax.` | pax | 4 | null |
| `b.comma-run` | `MECP/1/S01 4pax,3pax` | pax | 4 | null |
| `b.ideographic-comma` | `MECP/1/S01 4pax、水` | pax | 4 | null |
| `b.corner-brackets` | `MECP/1/S01 「4pax」` | pax | 4 | null |
| `b.nbsp` | `MECP/1/S01 4pax\u00a0water` | pax | 4 | null |
| `b.arabic-comma` | `MECP/0/M01 48.65,20.13،` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `b.vt-not-b` | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |

### 6.1 Timestamp (8)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `ts.three-digit` | `MECP/2/T01 @630` | timestamp | "06:30" | null |
| `ts.colon-one-digit` | `MECP/2/T01 @6:30` | timestamp | "06:30" | null |
| `ts.colon` | `MECP/2/T01 @06:30` | timestamp | "06:30" | null |
| `ts.hmm` | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `ts.skip-invalid` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "24:60" |
| `ts.2400` | `MECP/3/L06 @2400` | timestamp | null | "24:00" |
| `ts.9999` | `MECP/3/L06 @9999` | timestamp | null | "99:99" |
| `ts.trailing-comma` | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |

### upstream: Message (7)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.62` Message: a trailing space is invalid | `MECP/1/T05 ` | valid | false | true |
| `up.63` Message: a lowercase first code is not a code, so the message has no codes and is invalid | `MECP/1/t05 x` | valid | false | true |
| `up.67` Message: no codes after the severity is invalid | `MECP/0/` | valid | false | true |
| `up.69` Message: severity above 3 is invalid | `MECP/4/M01` | valid | false | true |
| `up.73` Message: an embedded LF is invalid | `MECP/1/T05 foo\nbar` | valid | false | true |
| `up.74` Message: an embedded line separator (U+2028) is invalid | `MECP/1/T05 foo\u2028bar` | valid | false | true |
| `up.75` Message: an embedded form feed is invalid | `MECP/1/T05 foo\fbar` | valid | false | true |

### upstream: Pax (5)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.17` Pax: zero fails validation and the next value is used | `MECP/1/S01 0pax 2pax` | pax | 2 | 0 |
| `up.19` Pax: parentheses are boundaries | `MECP/1/S01 (4pax)` | pax | 4 | null |
| `up.20` Pax: the unit is case-insensitive and a trailing period is a boundary | `MECP/1/S01 4Pax.` | pax | 4 | null |
| `up.21` Pax: a no-break space (U+00A0) is a boundary | `MECP/1/S01 4pax\u00a0water` | pax | 4 | null |
| `up.22` Pax: a vertical tab (U+000B) is not a boundary | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |

### 6.1 Person count (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `pax.space` | `MECP/1/S01 4 pax` | pax | 4 | null |
| `pax.upper` | `MECP/1/S01 4PAX` | pax | 4 | null |
| `pax.zero-skipped` | `MECP/1/S01 0pax 2pax` | pax | 2 | 0 |
| `pax.after-decimal` | `MECP/1/S01 1.5pax` | pax | 5 | null |

### upstream: GPS (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.25` GPS: an out-of-range position is skipped and the next valid one is used | `MECP/3/L06 95.0,200.0 47.3,8.5` | gps | {"lat": 47.3, "lon": 8.5} | {"lat": 95.0, "lon": 200.0} |
| `up.26` GPS: integers with a decimal comma are not a position | `MECP/3/L02 2,5 km` | gps | null | {"lat": 2, "lon": 5} |
| `up.27` GPS: a plus sign and a space after the comma are accepted | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | null |
| `up.28` GPS: a latitude just above 90 is not decoded | `MECP/0/M04 90.0001,0.0` | gps | null | {"lat": 90.0001, "lon": 0.0} |

### upstream: Timestamp (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.00` Timestamp: out-of-range values are skipped and the first valid one is used | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "24:60" |
| `up.01` Timestamp: an out-of-range value is not decoded | `MECP/3/L06 @9999` | timestamp | null | "99:99" |
| `up.02` Timestamp: a three-digit value implies a leading zero hour | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `up.03` Timestamp: trailing punctuation is a boundary | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |

### 6.1 Severity (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.sev4` | `MECP/4/M01` | valid | false | true |
| `env.sev9` | `MECP/9/M01` | valid | false | true |

### 6.1 Codes 3 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.lowercase-first-code` | `MECP/1/t05 x` | valid | false | true |

### 6.1 Optional Freetext 6 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `gps.resume-after-invalid` | `MECP/3/L06 95.0,200.0 47.3,8.5` | gps | {"lat": 47.3, "lon": 8.5} | {"lat": 95.0, "lon": 200.0} |
