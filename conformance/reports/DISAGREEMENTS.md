# Cross-client disagreements

Cases where at least two clients return different values for the same field. These are the inconsistencies a user sees when the same message is read on different apps, whatever the spec says. `n/a` = field not exposed.

## 6.1 Message Format: valid (18 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `env.no-codes` | `MECP/0/` | valid | false | false | false | false | true | false |
| `env.leading-space` | ` MECP/0/M01` | valid | false | false | false | true | true | false |
| `env.channel-prefix` | `Alice: MECP/0/M01` | valid | false | false | false | false | true | false |
| `env.no-prefix-compact` | `M01 P05 48.65,20.13` | valid | false | false | false | true | false | false |
| `env.four-char-code` | `MECP/0/M011` | valid | false | false | false | false | true | false |
| `env.trailing-space` | `MECP/1/T05 ` | valid | false | false | false | true | true | false |
| `env.trailing-space-after-text` | `MECP/1/T05 help ` | valid | false | false | false | true | true | false |
| `env.double-space-before-freetext` | `MECP/0/M01  help` | valid | false | false | false | true | true | false |
| `env.double-space-between-codes` | `MECP/0/M01  M07` | valid | false | false | false | true | true | false |
| `env.tab-after-codes` | `MECP/0/M01\tM07` | valid | false | false | false | true | true | false |
| `env.embedded-lf` | `MECP/0/M01\nM07` | valid | false | false | false | true | true | false |
| `env.embedded-cr` | `MECP/3/L01 a\rb` | valid | false | false | false | true | true | false |
| `env.line-separator` | `MECP/3/L01 a\u2028b` | valid | false | false | false | true | true | false |
| `env.nel` | `MECP/3/L01 a\u0085b` | valid | false | false | false | true | true | false |
| `env.two-trailing-lf` | `MECP/2/B03\n\n` | valid | false | false | false | true | true | false |
| `env.lfcr` | `MECP/2/B03\n\r` | valid | false | false | false | true | true | false |
| `env.two-crlf` | `MECP/2/B03\r\n\r\n` | valid | false | false | false | true | true | false |
| `env.nbsp-after-codes` | `MECP/0/M01\u00a0help` | valid | false | false | false | true | true | false |

## 6.1 Duration: duration (15 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `dur.eta-glued` | `MECP/2/R03 ETA45min` | duration | 45 | 45 | 45 | null | n/a | 45 |
| `dur.h` | `MECP/2/R03 2h` | duration | 120 | 120 | 120 | null | n/a | 120 |
| `dur.hm` | `MECP/2/R03 1h30min` | duration | 90 | 90 | 90 | null | n/a | 90 |
| `dur.h-space-m` | `MECP/2/R03 1h 30min` | duration | 90 | 90 | 90 | 30 | n/a | 90 |
| `dur.d` | `MECP/2/R03 1d` | duration | 1440 | 1440 | 1440 | null | n/a | 1440 |
| `dur.bare-not-first` | `MECP/2/C01 R03 1pax 45` | duration | null | null | null | 45 | n/a | null |
| `dur.bare-after-ts` | `MECP/2/R03 @1430 45` | duration | null | null | null | 45 | n/a | null |
| `dur.2d` | `MECP/2/R03 2d` | duration | 2880 | 2880 | 2880 | null | n/a | 2880 |
| `dur.48h` | `MECP/2/R03 48h` | duration | 2880 | 2880 | 2880 | null | n/a | 2880 |
| `dur.week` | `MECP/2/R03 7d` | duration | 10080 | 10080 | 10080 | null | n/a | 10080 |
| `dur.zero` | `MECP/2/R03 0min` | duration | null | null | null | 0 | n/a | null |
| `dur.same-position-list-order` | `MECP/2/R03 2 h` | duration | 120 | 120 | 120 | 2 | n/a | 120 |
| `dur.days-word` | `MECP/2/R03 in 5 days` | duration | null | null | null | 5 | n/a | null |
| `dur.with-pax` | `MECP/2/R03 4pax 2h` | duration | 120 | 120 | 120 | null | n/a | 120 |
| `dur.first-of-kind` | `MECP/2/R03 25h 3h` | duration | 1500 | 1500 | 1500 | null | n/a | 1500 |

## 6.1 GPS coordinates: gps (10 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `gps.plus-and-space` | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | {"lat": 48.8566, "lon": 2.3522} | {"lat": 48.8566, "lon": 2.3522} | null | null | n/a |
| `gps.limits` | `MECP/0/M04 90.0,180.0` | gps | {"lat": 90.0, "lon": 180.0} | {"lat": 90.0, "lon": 180.0} | {"lat": 90, "lon": 180} | {"lat": 90, "lon": 180} | {"lat": 90.0, "lon": 180.0} | n/a |
| `gps.neg-limits` | `MECP/0/M04 -90.0,-180.0` | gps | {"lat": -90.0, "lon": -180.0} | {"lat": -90.0, "lon": -180.0} | {"lat": -90, "lon": -180} | {"lat": -90, "lon": -180} | {"lat": -90.0, "lon": -180.0} | n/a |
| `gps.lat-out-of-range` | `MECP/0/M04 90.0001,0.0` | gps | null | null | null | null | {"lat": 90.0001, "lon": 0.0} | n/a |
| `gps.integers` | `MECP/0/M04 48,20` | gps | null | null | null | {"lat": 48, "lon": 20} | {"lat": 48, "lon": 20} | n/a |
| `gps.zero-zero` | `MECP/0/M04 0,0` | gps | null | null | null | {"lat": 0, "lon": 0} | {"lat": 0, "lon": 0} | n/a |
| `gps.decimal-comma` | `MECP/3/L02 2,5 km` | gps | null | null | null | {"lat": 2, "lon": 5} | {"lat": 2, "lon": 5} | n/a |
| `gps.colon-left` | `MECP/0/M01 at:48.65,20.13` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |
| `gps.trailing-period` | `MECP/0/M01 48.65,20.13.` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |
| `gps.altitude-suffix` | `MECP/0/M01 48.65,20.13,1200` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |

## upstream: Duration: duration (9 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.37` | `MECP/2/R03 2d` | duration | 2880 | 2880 | 2880 | null | n/a | 2880 |
| `up.38` | `MECP/2/R03 48h` | duration | 2880 | 2880 | 2880 | null | n/a | 2880 |
| `up.44` | `MECP/2/C01 R03 1pax 45` | duration | null | null | null | 45 | n/a | null |
| `up.48` | `MECP/2/R03 45.` | duration | 45 | 45 | 45 | null | n/a | 45 |
| `up.50` | `MECP/2/R03 45 2h` | duration | 120 | 120 | 120 | 45 | n/a | 120 |
| `up.51` | `MECP/2/R03 2d 45min` | duration | 2880 | 2880 | 2880 | 45 | n/a | 2880 |
| `up.53` | `MECP/2/R03 1h 30min` | duration | 90 | 90 | 90 | 30 | n/a | 90 |
| `up.54` | `MECP/2/R03 2 h` | duration | 120 | 120 | 120 | 2 | n/a | 120 |
| `up.61` | `MECP/2/R03 hut.2h` | duration | 120 | 120 | 120 | null | n/a | 120 |

## 6.1 Timestamp: timestamp (8 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `ts.three-digit` | `MECP/2/T01 @630` | timestamp | "06:30" | "06:30" | "06:30" | null | null | "06:30" |
| `ts.colon-one-digit` | `MECP/2/T01 @6:30` | timestamp | "06:30" | "06:30" | "06:30" | null | null | "06:30" |
| `ts.colon` | `MECP/2/T01 @06:30` | timestamp | "06:30" | "06:30" | "06:30" | null | null | "06:30" |
| `ts.hmm` | `MECP/3/L01 @123` | timestamp | "01:23" | "01:23" | "01:23" | null | null | "01:23" |
| `ts.skip-invalid` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "14:00" | "14:00" | "15:30" | "24:60" | "14:00" |
| `ts.2400` | `MECP/3/L06 @2400` | timestamp | null | null | null | null | "24:00" | null |
| `ts.9999` | `MECP/3/L06 @9999` | timestamp | null | null | null | null | "99:99" | null |
| `ts.trailing-comma` | `MECP/2/T05 @1430,` | timestamp | "14:30" | "14:30" | "14:30" | null | null | "14:30" |

## upstream: Message: valid (7 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.62` | `MECP/1/T05 ` | valid | false | false | false | true | true | false |
| `up.63` | `MECP/1/t05 x` | valid | false | false | false | true | true | false |
| `up.67` | `MECP/0/` | valid | false | false | false | false | true | false |
| `up.69` | `MECP/4/M01` | valid | false | false | false | false | true | false |
| `up.73` | `MECP/1/T05 foo\nbar` | valid | false | false | false | true | true | false |
| `up.74` | `MECP/1/T05 foo\u2028bar` | valid | false | false | false | true | true | false |
| `up.75` | `MECP/1/T05 foo\fbar` | valid | false | false | false | true | true | false |

## 6.1 Callsign: callsign (6 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `cs.portable` | `MECP/3/L20 ~VK2/OK1ABC/P` | callsign | "VK2/OK1ABC/P" | "VK2/OK1ABC/P" | "VK2/OK1ABC/P" | null | n/a | n/a |
| `cs.lower` | `MECP/3/L20 ~vk2/ok1abc/p` | callsign | "VK2/OK1ABC/P" | "VK2/OK1ABC/P" | "VK2/OK1ABC/P" | null | n/a | n/a |
| `cs.prefix` | `MECP/3/L20 ~DL/OK1ABC` | callsign | "DL/OK1ABC" | "DL/OK1ABC" | "DL/OK1ABC" | null | n/a | n/a |
| `cs.comma` | `MECP/3/L20 ~OK1ABC, ok` | callsign | "OK1ABC" | "OK1ABC" | "OK1ABC" | null | n/a | n/a |
| `cs.ssid` | `MECP/3/L20 ~OK1ABC-7` | callsign | null | null | null | "OK1ABC-7" | n/a | n/a |
| `cs.aprs-ssid` | `MECP/3/L20 ~W1AW-9` | callsign | null | null | null | "W1AW-9" | n/a | n/a |

## upstream: Reference: reference (6 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.06` | `MECP/2/C08 #base-camp,` | reference | "base-camp" | "base-camp" | "base-camp" | null | n/a | n/a |
| `up.07` | `MECP/2/C08 (#tag)` | reference | "tag" | "tag" | "tag" | null | n/a | n/a |
| `up.10` | `MECP/2/C08 #hut،ok` | reference | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.11` | `MECP/2/C08 #hut”ok` | reference | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.12` | `MECP/2/C08 #hut、ok` | reference | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.13` | `MECP/2/C08 #hut，ok` | reference | "hut" | "hut" | "hut" | null | n/a | n/a |

## 6.1 Language hint: language (5 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `lang.underscore` | `MECP/3/L04 @zh_CN` | language | "zh-cn" | "zh-cn" | "zh-cn" | null | n/a | n/a |
| `lang.region` | `MECP/3/L04 @zh-TW` | language | "zh-tw" | "zh-tw" | "zh-tw" | null | n/a | n/a |
| `lang.script-region` | `MECP/3/L04 @zh-Hans-CN` | language | "zh-hans-cn" | "zh-hans-cn" | "zh-hans-cn" | null | n/a | n/a |
| `lang.sr-latn` | `MECP/3/L04 @sr-Latn-RS` | language | "sr-latn-rs" | "sr-latn-rs" | "sr-latn-rs" | null | n/a | n/a |
| `lang.period` | `MECP/3/L04 @en.` | language | "en" | "en" | "en" | null | n/a | n/a |

## 6.1 Optional Freetext 4: pax (5 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `b.paren` | `MECP/1/S01 (4pax)` | pax | 4 | 4 | 4 | null | null | 4 |
| `b.period` | `MECP/1/S01 4Pax.` | pax | 4 | 4 | 4 | null | null | 4 |
| `b.comma-run` | `MECP/1/S01 4pax,3pax` | pax | 4 | 4 | 4 | null | null | 4 |
| `b.ideographic-comma` | `MECP/1/S01 4pax、水` | pax | 4 | 4 | 4 | null | null | 4 |
| `b.corner-brackets` | `MECP/1/S01 「4pax」` | pax | 4 | 4 | 4 | null | null | 4 |

## 6.1 Person count: pax (5 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `pax.space` | `MECP/1/S01 4 pax` | pax | 4 | 4 | 4 | null | null | 4 |
| `pax.upper` | `MECP/1/S01 4PAX` | pax | 4 | 4 | 4 | 4 | null | 4 |
| `pax.zero-skipped` | `MECP/1/S01 0pax 2pax` | pax | 2 | 2 | 2 | 2 | 0 | 2 |
| `pax.first-wins` | `MECP/1/S01 2pax 5pax` | pax | 2 | 2 | 2 | 5 | 2 | 2 |
| `pax.after-decimal` | `MECP/1/S01 1.5pax` | pax | 5 | 5 | 5 | null | null | null |

## upstream: GPS: gps (4 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.25` | `MECP/3/L06 95.0,200.0 47.3,8.5` | gps | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 95.0, "lon": 200.0} | n/a |
| `up.26` | `MECP/3/L02 2,5 km` | gps | null | null | null | {"lat": 2, "lon": 5} | {"lat": 2, "lon": 5} | n/a |
| `up.27` | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | {"lat": 48.8566, "lon": 2.3522} | {"lat": 48.8566, "lon": 2.3522} | null | null | n/a |
| `up.28` | `MECP/0/M04 90.0001,0.0` | gps | null | null | null | null | {"lat": 90.0001, "lon": 0.0} | n/a |

## upstream: Pax: pax (4 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.17` | `MECP/1/S01 0pax 2pax` | pax | 2 | 2 | 2 | 2 | 0 | 2 |
| `up.19` | `MECP/1/S01 (4pax)` | pax | 4 | 4 | 4 | null | null | 4 |
| `up.20` | `MECP/1/S01 4Pax.` | pax | 4 | 4 | 4 | null | null | 4 |
| `up.23` | `MECP/1/S01 2pax 5pax` | pax | 2 | 2 | 2 | 5 | 2 | 2 |

## upstream: Timestamp: timestamp (4 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.00` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "14:00" | "14:00" | "15:30" | "24:60" | "14:00" |
| `up.01` | `MECP/3/L06 @9999` | timestamp | null | null | null | null | "99:99" | null |
| `up.02` | `MECP/3/L01 @123` | timestamp | "01:23" | "01:23" | "01:23" | null | null | "01:23" |
| `up.03` | `MECP/2/T05 @1430,` | timestamp | "14:30" | "14:30" | "14:30" | null | null | "14:30" |

## 6.1 Codes 5: valid, severity, codes, freetext, pax, gps, timestamp, language, callsign, reference, duration (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `env.unknown-code` | `MECP/3/Z99 hello` | valid | true | true | true | false | true | true |
|  |  | severity | 3 | 3 | 3 | "(invalid)" | 3 | 3 |
|  |  | codes | ["Z99"] | ["Z99"] | ["Z99"] | "(invalid)" | n/a | ["Z99"] |
|  |  | freetext | "hello" | "hello" | "hello" | "(invalid)" | n/a | "hello" |
|  |  | pax | null | null | null | "(invalid)" | null | null |
|  |  | gps | null | null | null | "(invalid)" | null | n/a |
|  |  | timestamp | null | null | null | "(invalid)" | null | null |
|  |  | language | null | null | null | "(invalid)" | n/a | n/a |
|  |  | callsign | null | null | null | "(invalid)" | n/a | n/a |
|  |  | reference | null | null | null | "(invalid)" | n/a | n/a |
|  |  | duration | null | null | null | "(invalid)" | n/a | null |
| `env.unknown-category-only` | `MECP/1/Q42` | valid | true | true | true | false | true | true |
|  |  | severity | 1 | 1 | 1 | "(invalid)" | 1 | 1 |
|  |  | codes | ["Q42"] | ["Q42"] | ["Q42"] | "(invalid)" | n/a | ["Q42"] |
|  |  | freetext | null | null | null | "(invalid)" | n/a | null |
|  |  | pax | null | null | null | "(invalid)" | null | null |
|  |  | gps | null | null | null | "(invalid)" | null | n/a |
|  |  | timestamp | null | null | null | "(invalid)" | null | null |
|  |  | language | null | null | null | "(invalid)" | n/a | n/a |
|  |  | callsign | null | null | null | "(invalid)" | n/a | n/a |
|  |  | reference | null | null | null | "(invalid)" | n/a | n/a |
|  |  | duration | null | null | null | "(invalid)" | n/a | null |

## 6.1 Message Format: freetext (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `env.freetext-inner-spaces` | `MECP/3/L01 see  you   there` | freetext | "see  you   there" | "see  you   there" | "see  you   there" | "see you there" | n/a | "see  you   there" |
| `env.freetext-tab-inside` | `MECP/3/L01 a\tb` | freetext | "a\tb" | "a\tb" | "a\tb" | "a b" | n/a | "a\tb" |

## 6.1 Optional Freetext 4: freetext, pax (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `b.nbsp` | `MECP/1/S01 4pax\u00a0water` | freetext | "4pax\u00a0water" | "4pax\u00a0water" | "4pax\u00a0water" | "4pax water" | n/a | "4pax\u00a0water" |
|  |  | pax | 4 | 4 | 4 | 4 | null | 4 |
| `b.vt-not-b` | `MECP/1/S01 4pax\u000bwater` | freetext | "4pax\u000bwater" | "4pax\u000bwater" | "4pax\u000bwater" | "4pax water" | n/a | "4pax\u000bwater" |
|  |  | pax | null | null | null | 4 | 4 | null |

## 6.1 Reference: reference (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `ref.hyphen` | `MECP/2/C08 #base-camp,` | reference | "base-camp" | "base-camp" | "base-camp" | null | n/a | n/a |
| `ref.paren` | `MECP/2/C08 (#tag)` | reference | "tag" | "tag" | "tag" | null | n/a | n/a |

## 6.1 Severity: valid (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `env.sev4` | `MECP/4/M01` | valid | false | false | false | false | true | false |
| `env.sev9` | `MECP/9/M01` | valid | false | false | false | false | true | false |

## upstream: Callsign: callsign (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.30` | `MECP/3/L20 ~DL/OK1ABC` | callsign | "DL/OK1ABC" | "DL/OK1ABC" | "DL/OK1ABC" | null | n/a | n/a |
| `up.33` | `MECP/3/L20 ~W1AW-9` | callsign | null | null | null | "W1AW-9" | n/a | n/a |

## upstream: Pax: freetext, pax (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.21` | `MECP/1/S01 4pax\u00a0water` | freetext | (any) | "4pax\u00a0water" | "4pax\u00a0water" | "4pax water" | n/a | "4pax\u00a0water" |
|  |  | pax | 4 | 4 | 4 | 4 | null | 4 |
| `up.22` | `MECP/1/S01 4pax\u000bwater` | freetext | (any) | "4pax\u000bwater" | "4pax\u000bwater" | "4pax water" | n/a | "4pax\u000bwater" |
|  |  | pax | null | null | null | 4 | 4 | null |

## 6.1 Codes 3: codes, freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `env.lowercase-ends-codes` | `MECP/3/L01 l06 late` | codes | ["L01"] | ["L01"] | ["L01"] | ["L01", "L06"] | n/a | ["L01"] |
|  |  | freetext | "l06 late" | "l06 late" | "l06 late" | "late" | n/a | "l06 late" |

## 6.1 Codes 3: valid (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `env.lowercase-first-code` | `MECP/1/t05 x` | valid | false | false | false | true | true | false |

## 6.1 GPS coordinates: freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `gps.two-spaces-after-comma` | `MECP/0/M01 48.65,  20.13` | freetext | "48.65,  20.13" | "48.65,  20.13" | "48.65,  20.13" | "48.65, 20.13" | n/a | "48.65,  20.13" |

## 6.1 Optional Freetext 10: duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `dur.huge` | `MECP/2/R03 99999999999999999999999min` | duration | (any) | null | 1e+23 | null | n/a | null |

## 6.1 Optional Freetext 10: pax (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `pax.huge` | `MECP/1/S01 99999999999999999999999pax` | pax | (any) | null | 1e+23 | null | 1e+23 | null |

## 6.1 Optional Freetext 4: gps (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `b.arabic-comma` | `MECP/0/M01 48.65,20.13،` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |

## 6.1 Optional Freetext 6: duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `dur.zero-then-ok` | `MECP/2/R03 0min 5min` | duration | 5 | 5 | 5 | 0 | n/a | 5 |

## 6.1 Optional Freetext 6: gps (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `gps.resume-after-invalid` | `MECP/3/L06 95.0,200.0 47.3,8.5` | gps | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 95.0, "lon": 200.0} | n/a |

## 6.1 Person count: freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `pax.two-spaces` | `MECP/1/S01 4  pax` | freetext | "4  pax" | "4  pax" | "4  pax" | "4 pax" | n/a | "4  pax" |

## upstream: Language: language (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.34` | `MECP/3/L04 @zh_CN` | language | "zh-cn" | "zh-cn" | "zh-cn" | null | n/a | n/a |

## upstream: Message: codes, freetext, duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.66` | `MECP/2/L01 r03 45min` | codes | (any) | ["L01"] | ["L01"] | ["L01", "R03"] | n/a | ["L01"] |
|  |  | freetext | (any) | "r03 45min" | "r03 45min" | "45min" | n/a | "r03 45min" |
|  |  | duration | null | null | null | 45 | n/a | null |

## upstream: Message: valid, severity, codes, freetext, pax, gps, timestamp, language, callsign, reference, duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.65` | `MECP/3/Z99 hello` | valid | true | true | true | false | true | true |
|  |  | severity | (any) | 3 | 3 | "(invalid)" | 3 | 3 |
|  |  | codes | (any) | ["Z99"] | ["Z99"] | "(invalid)" | n/a | ["Z99"] |
|  |  | freetext | (any) | "hello" | "hello" | "(invalid)" | n/a | "hello" |
|  |  | pax | null | null | null | "(invalid)" | null | null |
|  |  | gps | null | null | null | "(invalid)" | null | n/a |
|  |  | timestamp | null | null | null | "(invalid)" | null | null |
|  |  | language | null | null | null | "(invalid)" | n/a | n/a |
|  |  | callsign | null | null | null | "(invalid)" | n/a | n/a |
|  |  | reference | null | null | null | "(invalid)" | n/a | n/a |
|  |  | duration | null | null | null | "(invalid)" | n/a | null |

## upstream: Reference: freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|
| `up.09` | `MECP/2/C08 #hut\u3000ok` | freetext | (any) | "#hut\u3000ok" | "#hut\u3000ok" | "#hut ok" | n/a | "#hut\u3000ok" |

