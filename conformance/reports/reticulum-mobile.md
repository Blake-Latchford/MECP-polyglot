# reticulum-mobile: MECP 1.4.1 decode conformance

- Client: decodeMecpMessage() in the mobile app
- Repository: https://github.com/FreeTAKTeam/reticulum_mobile_emergency_management
- Commit tested: `6cf3db0978` (2026-11-21)
- Decoder: `apps/mobile/src/utils/mecp.ts`
- Vectors: `conformance/vectors/decode-1.4.1.json` plus mecp-org/MECP `freetext/tests.json` (256 cases), run 2026-11-21
- **Result: 146 pass, 110 fail, 0 error**
- **Code table: 108/109 (+1 extra)**

## Code table (§7)

Compared with `conformance/vectors/codes-1.4.1.json`. A missing code still decodes (Codes rule 5) but has no label, so it reads as unknown.

- Missing (1): `M16`
- Not in §7 (1): `B04`

## Decode vectors

Cases marked *(proposed)* depend on spec changes not yet merged upstream; see the vector's `proposed` field.

Each row is one vector. *Expected* is written by hand from the protocol brief (clause in the heading); *Got* is what this client's decoder returned.

### 6.1 Message Format (17)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.freetext-inner-spaces` | `MECP/3/L01 see  you   there` | freetext | "see  you   there" | "see you there" |
| `env.freetext-tab-inside` | `MECP/3/L01 a\tb` | freetext | "a\tb" | "a b" |
| `env.leading-space` | ` MECP/0/M01` | valid | false | true |
| `env.no-prefix-compact` | `M01 P05 48.65,20.13` | valid | false | true |
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

### 6.1 Duration (15)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `dur.eta-glued` | `MECP/2/R03 ETA45min` | duration | 45 | null |
| `dur.h` | `MECP/2/R03 2h` | duration | 120 | null |
| `dur.hm` | `MECP/2/R03 1h30min` | duration | 90 | null |
| `dur.h-space-m` | `MECP/2/R03 1h 30min` | duration | 90 | 30 |
| `dur.d` | `MECP/2/R03 1d` | duration | 1440 | null |
| `dur.bare-not-first` | `MECP/2/C01 R03 1pax 45` | duration | null | 45 |
| `dur.bare-after-ts` | `MECP/2/R03 @1430 45` | duration | null | 45 |
| `dur.2d` | `MECP/2/R03 2d` | duration | 2880 | null |
| `dur.48h` | `MECP/2/R03 48h` | duration | 2880 | null |
| `dur.week` | `MECP/2/R03 7d` | duration | 10080 | null |
| `dur.zero` | `MECP/2/R03 0min` | duration | null | 0 |
| `dur.same-position-list-order` | `MECP/2/R03 2 h` | duration | 120 | 2 |
| `dur.days-word` | `MECP/2/R03 in 5 days` | duration | null | 5 |
| `dur.with-pax` | `MECP/2/R03 4pax 2h` | duration | 120 | null |
| `dur.first-of-kind` | `MECP/2/R03 25h 3h` | duration | 1500 | null |

### upstream: Duration (9)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.37` Duration: days are converted to minutes, with no upper bound | `MECP/2/R03 2d` | duration | 2880 | null |
| `up.38` Duration: hours are converted to minutes | `MECP/2/R03 48h` | duration | 2880 | null |
| `up.44` Duration: a bare number that is not the first freetext token is not decoded | `MECP/2/C01 R03 1pax 45` | duration | null | 45 |
| `up.48` Duration: a bare number followed by a period is minutes | `MECP/2/R03 45.` | duration | 45 | null |
| `up.50` Duration: a value with a unit is preferred over a bare number | `MECP/2/R03 45 2h` | duration | 120 | 45 |
| `up.51` Duration: the first value by position wins (days before minutes) | `MECP/2/R03 2d 45min` | duration | 2880 | 45 |
| `up.53` Duration: hours and minutes separated by a space are combined | `MECP/2/R03 1h 30min` | duration | 90 | 30 |
| `up.54` Duration: a space between the number and the unit is accepted | `MECP/2/R03 2 h` | duration | 120 | 2 |
| `up.61` Duration: a period after a letter still separates a value | `MECP/2/R03 hut.2h` | duration | 120 | null |

### 6.1 GPS coordinates (8)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `gps.plus-and-space` | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | null |
| `gps.integers` | `MECP/0/M04 48,20` | gps | null | {"lat": 48, "lon": 20} |
| `gps.zero-zero` | `MECP/0/M04 0,0` | gps | null | {"lat": 0, "lon": 0} |
| `gps.decimal-comma` | `MECP/3/L02 2,5 km` | gps | null | {"lat": 2, "lon": 5} |
| `gps.colon-left` | `MECP/0/M01 at:48.65,20.13` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `gps.trailing-period` | `MECP/0/M01 48.65,20.13.` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `gps.altitude-suffix` | `MECP/0/M01 48.65,20.13,1200` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `gps.two-spaces-after-comma` | `MECP/0/M01 48.65,  20.13` | freetext | "48.65,  20.13" | "48.65, 20.13" |

### 6.1 Optional Freetext 4 (8)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `b.paren` | `MECP/1/S01 (4pax)` | pax | 4 | null |
| `b.period` | `MECP/1/S01 4Pax.` | pax | 4 | null |
| `b.comma-run` | `MECP/1/S01 4pax,3pax` | pax | 4 | null |
| `b.ideographic-comma` | `MECP/1/S01 4pax、水` | pax | 4 | null |
| `b.corner-brackets` | `MECP/1/S01 「4pax」` | pax | 4 | null |
| `b.nbsp` | `MECP/1/S01 4pax\u00a0water` | freetext | "4pax\u00a0water" | "4pax water" |
| `b.arabic-comma` | `MECP/0/M01 48.65,20.13،` | gps | {"lat": 48.65, "lon": 20.13} | null |
| `b.vt-not-b` | `MECP/1/S01 4pax\u000bwater` | freetext | "4pax\u000bwater" | "4pax water" |
|  |  | pax | null | 4 |

### upstream: Message (7)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.62` Message: a trailing space is invalid | `MECP/1/T05 ` | valid | false | true |
| `up.63` Message: a lowercase first code is not a code, so the message has no codes and is invalid | `MECP/1/t05 x` | valid | false | true |
| `up.65` Message: an unknown but well-formed code is still a valid message | `MECP/3/Z99 hello` | valid | true | false |
| `up.66` Message: a lowercase code ends the code section, so a lowercase r03 does not enable duration | `MECP/2/L01 r03 45min` | duration | null | 45 |
| `up.73` Message: an embedded LF is invalid | `MECP/1/T05 foo\nbar` | valid | false | true |
| `up.74` Message: an embedded line separator (U+2028) is invalid | `MECP/1/T05 foo\u2028bar` | valid | false | true |
| `up.75` Message: an embedded form feed is invalid | `MECP/1/T05 foo\fbar` | valid | false | true |

### 6.1 Callsign (6)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `cs.portable` | `MECP/3/L20 ~VK2/OK1ABC/P` | callsign | "VK2/OK1ABC/P" | null |
| `cs.lower` | `MECP/3/L20 ~vk2/ok1abc/p` | callsign | "VK2/OK1ABC/P" | null |
| `cs.prefix` | `MECP/3/L20 ~DL/OK1ABC` | callsign | "DL/OK1ABC" | null |
| `cs.comma` | `MECP/3/L20 ~OK1ABC, ok` | callsign | "OK1ABC" | null |
| `cs.ssid` | `MECP/3/L20 ~OK1ABC-7` | callsign | null | "OK1ABC-7" |
| `cs.aprs-ssid` | `MECP/3/L20 ~W1AW-9` | callsign | null | "W1AW-9" |

### 6.1 Timestamp (6)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `ts.three-digit` | `MECP/2/T01 @630` | timestamp | "06:30" | null |
| `ts.colon-one-digit` | `MECP/2/T01 @6:30` | timestamp | "06:30" | null |
| `ts.colon` | `MECP/2/T01 @06:30` | timestamp | "06:30" | null |
| `ts.hmm` | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `ts.skip-invalid` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "15:30" |
| `ts.trailing-comma` | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |

### upstream: Reference (6)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.06` Reference: trailing punctuation is a boundary | `MECP/2/C08 #base-camp,` | reference | "base-camp" | null |
| `up.07` Reference: parentheses are boundaries | `MECP/2/C08 (#tag)` | reference | "tag" | null |
| `up.10` Reference: an Arabic comma (U+060C) is a boundary | `MECP/2/C08 #hut،ok` | reference | "hut" | null |
| `up.11` Reference: a right double quotation mark (U+201D) is a boundary | `MECP/2/C08 #hut”ok` | reference | "hut" | null |
| `up.12` Reference: an ideographic comma (U+3001) is a boundary | `MECP/2/C08 #hut、ok` | reference | "hut" | null |
| `up.13` Reference: a fullwidth comma (U+FF0C) is a boundary | `MECP/2/C08 #hut，ok` | reference | "hut" | null |

### 6.1 Language hint (5)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `lang.underscore` | `MECP/3/L04 @zh_CN` | language | "zh-cn" | null |
| `lang.region` | `MECP/3/L04 @zh-TW` | language | "zh-tw" | null |
| `lang.script-region` | `MECP/3/L04 @zh-Hans-CN` | language | "zh-hans-cn" | null |
| `lang.sr-latn` | `MECP/3/L04 @sr-Latn-RS` | language | "sr-latn-rs" | null |
| `lang.period` | `MECP/3/L04 @en.` | language | "en" | null |

### 6.1 Person count (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `pax.space` | `MECP/1/S01 4 pax` | pax | 4 | null |
| `pax.first-wins` | `MECP/1/S01 2pax 5pax` | pax | 2 | 5 |
| `pax.two-spaces` | `MECP/1/S01 4  pax` | freetext | "4  pax" | "4 pax" |
| `pax.after-decimal` | `MECP/1/S01 1.5pax` | pax | 5 | null |

### upstream: Pax (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.19` Pax: parentheses are boundaries | `MECP/1/S01 (4pax)` | pax | 4 | null |
| `up.20` Pax: the unit is case-insensitive and a trailing period is a boundary | `MECP/1/S01 4Pax.` | pax | 4 | null |
| `up.22` Pax: a vertical tab (U+000B) is not a boundary | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |
| `up.23` Pax: the first value wins | `MECP/1/S01 2pax 5pax` | pax | 2 | 5 |

### upstream: Timestamp (3)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.00` Timestamp: out-of-range values are skipped and the first valid one is used | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "15:30" |
| `up.02` Timestamp: a three-digit value implies a leading zero hour | `MECP/3/L01 @123` | timestamp | "01:23" | null |
| `up.03` Timestamp: trailing punctuation is a boundary | `MECP/2/T05 @1430,` | timestamp | "14:30" | null |

### 6.1 Codes 3 (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.lowercase-ends-codes` | `MECP/3/L01 l06 late` | codes | ["L01"] | ["L01", "L06"] |
|  |  | freetext | "l06 late" | "late" |
| `env.lowercase-first-code` | `MECP/1/t05 x` | valid | false | true |

### 6.1 Codes 5 (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `env.unknown-code` | `MECP/3/Z99 hello` | valid | true | false |
| `env.unknown-category-only` | `MECP/1/Q42` | valid | true | false |

### 6.1 Reference (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `ref.hyphen` | `MECP/2/C08 #base-camp,` | reference | "base-camp" | null |
| `ref.paren` | `MECP/2/C08 (#tag)` | reference | "tag" | null |

### upstream: Callsign (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.30` Callsign: a prefix separated by a slash is kept | `MECP/3/L20 ~DL/OK1ABC` | callsign | "DL/OK1ABC" | null |
| `up.33` Callsign: an APRS/AX.25 SSID is not decoded, and the message is still valid | `MECP/3/L20 ~W1AW-9` | callsign | null | "W1AW-9" |

### upstream: GPS (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.26` GPS: integers with a decimal comma are not a position | `MECP/3/L02 2,5 km` | gps | null | {"lat": 2, "lon": 5} |
| `up.27` GPS: a plus sign and a space after the comma are accepted | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | null |

### 6.1 Optional Freetext 6 (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `dur.zero-then-ok` | `MECP/2/R03 0min 5min` | duration | 5 | 0 |

### upstream: Language (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.34` Language: an underscore region tag is normalised to lowercase with a hyphen | `MECP/3/L04 @zh_CN` | language | "zh-cn" | null |
