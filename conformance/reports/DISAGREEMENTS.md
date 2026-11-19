# Cross-client disagreements

Cases where at least two clients return different values for the same field. These are the inconsistencies a user sees when the same message is read on different apps, whatever the spec says. `n/a` = field not exposed.

## 6.1 Duration: duration (24 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `dur.min` | `MECP/2/R03 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `dur.eta-min` | `MECP/2/R03 ETA 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `dur.eta-glued` | `MECP/2/R03 ETA45min` | duration | 45 | 45 | null | 45 | null | n/a | null |
| `dur.eta-bare` | `MECP/2/R03 ETA 45` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `dur.h` | `MECP/2/R03 2h` | duration | 120 | 120 | null | 120 | null | n/a | null |
| `dur.hm` | `MECP/2/R03 1h30min` | duration | 90 | 90 | null | 90 | null | n/a | null |
| `dur.h-space-m` | `MECP/2/R03 1h 30min` | duration | 90 | 90 | null | 90 | 30 | n/a | null |
| `dur.d` | `MECP/2/R03 1d` | duration | 1440 | 1440 | null | 1440 | null | n/a | null |
| `dur.s` | `MECP/2/R03 120s` | duration | null | 2 | null | null | null | n/a | null |
| `dur.with-codes-before` | `MECP/2/C01 R03 P05 47.3769,12.1048 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `dur.example` | `MECP/2/C01 R03 45min @en` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `dur.bare-not-first` | `MECP/2/C01 R03 1pax 45` | duration | null | null | null | null | 45 | n/a | null |
| `dur.bare-latitude` | `MECP/2/R03 47.3769,12.1048` | duration | null | 47 | null | null | null | n/a | null |
| `dur.bare-after-ts` | `MECP/2/R03 @1430 45` | duration | null | null | null | null | 45 | n/a | null |
| `dur.2d` | `MECP/2/R03 2d` | duration | 2880 | 2880 | null | 2880 | null | n/a | null |
| `dur.48h` | `MECP/2/R03 48h` | duration | 2880 | 2880 | null | 2880 | null | n/a | null |
| `dur.2880min` | `MECP/2/R03 2880min` | duration | 2880 | 2880 | null | 2880 | 2880 | n/a | null |
| `dur.week` | `MECP/2/R03 7d` | duration | 10080 | 10080 | null | 10080 | null | n/a | null |
| `dur.zero` | `MECP/2/R03 0min` | duration | null | null | null | null | 0 | n/a | null |
| `dur.first-by-position` | `MECP/2/R03 30min or 1h` | duration | 30 | 60 | null | 30 | 30 | n/a | null |
| `dur.same-position-list-order` | `MECP/2/R03 2 h` | duration | 120 | 120 | 2 | 120 | 2 | n/a | 2 |
| `dur.days-word` | `MECP/2/R03 in 5 days` | duration | null | null | null | null | 5 | n/a | null |
| `dur.with-pax` | `MECP/2/R03 4pax 2h` | duration | 120 | 120 | null | 120 | null | n/a | null |
| `dur.first-of-kind` | `MECP/2/R03 25h 3h` | duration | 1500 | 1500 | null | 1500 | null | n/a | null |

## 6.1 Message Format: valid (19 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.no-codes` | `MECP/0/` | valid | false | false | true | false | false | true | true |
| `env.no-codes-no-slash` | `MECP/0` | valid | false | false | true | false | false | false | true |
| `env.leading-space` | ` MECP/0/M01` | valid | false | false | false | false | true | true | false |
| `env.channel-prefix` | `Alice: MECP/0/M01` | valid | false | false | false | false | false | true | false |
| `env.no-prefix-compact` | `M01 P05 48.65,20.13` | valid | false | false | false | false | true | false | false |
| `env.four-char-code` | `MECP/0/M011` | valid | false | false | true | false | false | true | true |
| `env.trailing-space` | `MECP/1/T05 ` | valid | false | false | true | false | true | true | true |
| `env.trailing-space-after-text` | `MECP/1/T05 help ` | valid | false | false | true | false | true | true | true |
| `env.double-space-before-freetext` | `MECP/0/M01  help` | valid | false | false | true | false | true | true | true |
| `env.double-space-between-codes` | `MECP/0/M01  M07` | valid | false | false | true | false | true | true | true |
| `env.tab-after-codes` | `MECP/0/M01\tM07` | valid | false | false | true | false | true | true | true |
| `env.embedded-lf` | `MECP/0/M01\nM07` | valid | false | false | true | false | true | true | true |
| `env.embedded-cr` | `MECP/3/L01 a\rb` | valid | false | false | true | false | true | true | true |
| `env.line-separator` | `MECP/3/L01 a\u2028b` | valid | false | false | true | false | true | true | true |
| `env.nel` | `MECP/3/L01 a\u0085b` | valid | false | false | true | false | true | true | true |
| `env.two-trailing-lf` | `MECP/2/B03\n\n` | valid | false | false | true | false | true | true | true |
| `env.lfcr` | `MECP/2/B03\n\r` | valid | false | false | true | false | true | true | true |
| `env.two-crlf` | `MECP/2/B03\r\n\r\n` | valid | false | false | true | false | true | true | true |
| `env.nbsp-after-codes` | `MECP/0/M01\u00a0help` | valid | false | false | true | false | true | true | true |

## upstream: Duration: duration (16 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.36` | `MECP/2/R03 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `up.37` | `MECP/2/R03 2d` | duration | 2880 | 2880 | null | 2880 | null | n/a | null |
| `up.38` | `MECP/2/R03 48h` | duration | 2880 | 2880 | null | 2880 | null | n/a | null |
| `up.39` | `MECP/2/R03 2880min` | duration | 2880 | 2880 | null | 2880 | 2880 | n/a | null |
| `up.40` | `MECP/2/R03 ETA 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `up.42` | `MECP/2/C01 R03 P05 47.3769,12.1048 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `up.44` | `MECP/2/C01 R03 1pax 45` | duration | null | null | null | null | 45 | n/a | null |
| `up.45` | `MECP/2/R03 30s` | duration | null | 1 | null | null | null | n/a | null |
| `up.46` | `MECP/2/R03 30s 45min` | duration | 45 | 45 | null | 45 | 45 | n/a | null |
| `up.47` | `MECP/2/R03 47.3769,12.1048` | duration | null | 47 | null | null | null | n/a | null |
| `up.48` | `MECP/2/R03 45.` | duration | 45 | 45 | null | 45 | null | n/a | null |
| `up.50` | `MECP/2/R03 45 2h` | duration | 120 | 120 | 45 | 120 | 45 | n/a | 45 |
| `up.51` | `MECP/2/R03 2d 45min` | duration | 2880 | 45 | null | 2880 | 45 | n/a | null |
| `up.52` | `MECP/2/R03 45min 2h` | duration | 45 | 120 | null | 45 | 45 | n/a | null |
| `up.53` | `MECP/2/R03 1h 30min` | duration | 90 | 90 | null | 90 | 30 | n/a | null |
| `up.54` | `MECP/2/R03 2 h` | duration | 120 | 120 | 2 | 120 | 2 | n/a | 2 |

## 6.1 Optional Freetext 4: pax (13 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `b.paren` | `MECP/1/S01 (4pax)` | pax | 4 | 4 | 4 | 4 | null | null | 4 |
| `b.period` | `MECP/1/S01 4Pax.` | pax | 4 | 4 | null | 4 | null | null | null |
| `b.comma-run` | `MECP/1/S01 4pax,3pax` | pax | 4 | 4 | 4 | 4 | null | null | 4 |
| `b.asterisk` | `MECP/1/S01 *4pax*` | pax | null | 4 | 4 | null | null | null | 4 |
| `b.slash` | `MECP/1/S01 4pax/3` | pax | null | 4 | 4 | null | null | null | 4 |
| `b.ideographic-comma` | `MECP/1/S01 4pax、水` | pax | 4 | 4 | 4 | 4 | null | null | 4 |
| `b.corner-brackets` | `MECP/1/S01 「4pax」` | pax | 4 | 4 | 4 | 4 | null | null | 4 |
| `b.letter-left` | `MECP/1/S01 x4pax` | pax | null | null | 4 | null | null | null | 4 |
| `b.letter-right` | `MECP/1/S01 3paxmore` | pax | null | null | 3 | null | null | null | 3 |
| `b.hash-not-b` | `MECP/1/S01 #4pax` | pax | null | null | 4 | null | null | null | 4 |
| `b.hyphen-not-b` | `MECP/1/S01 -4pax` | pax | null | null | 4 | null | null | null | 4 |
| `b.underscore-not-b` | `MECP/1/S01 _4pax` | pax | null | null | 4 | null | null | null | 4 |
| `b.plus-not-b` | `MECP/1/S01 +4pax` | pax | null | null | 4 | null | null | null | 4 |

## 6.1 GPS coordinates: gps (11 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `gps.plus-and-space` | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | {"lat": 48.8566, "lon": 2.3522} | null | {"lat": 48.8566, "lon": 2.3522} | null | null | n/a |
| `gps.limits` | `MECP/0/M04 90.0,180.0` | gps | {"lat": 90.0, "lon": 180.0} | {"lat": 90.0, "lon": 180.0} | {"lat": 90, "lon": 180} | {"lat": 90, "lon": 180} | {"lat": 90, "lon": 180} | {"lat": 90.0, "lon": 180.0} | n/a |
| `gps.neg-limits` | `MECP/0/M04 -90.0,-180.0` | gps | {"lat": -90.0, "lon": -180.0} | {"lat": -90.0, "lon": -180.0} | {"lat": -90, "lon": -180} | {"lat": -90, "lon": -180} | {"lat": -90, "lon": -180} | {"lat": -90.0, "lon": -180.0} | n/a |
| `gps.lat-out-of-range` | `MECP/0/M04 90.0001,0.0` | gps | null | null | null | null | null | {"lat": 90.0001, "lon": 0.0} | n/a |
| `gps.integers` | `MECP/0/M04 48,20` | gps | null | null | null | null | {"lat": 48, "lon": 20} | {"lat": 48, "lon": 20} | n/a |
| `gps.zero-zero` | `MECP/0/M04 0,0` | gps | null | null | null | null | {"lat": 0, "lon": 0} | {"lat": 0, "lon": 0} | n/a |
| `gps.decimal-comma` | `MECP/3/L02 2,5 km` | gps | null | null | null | null | {"lat": 2, "lon": 5} | {"lat": 2, "lon": 5} | n/a |
| `gps.colon-left` | `MECP/0/M01 at:48.65,20.13` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |
| `gps.trailing-period` | `MECP/0/M01 48.65,20.13.` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |
| `gps.letter-left` | `MECP/0/M01 x48.65,20.13` | gps | null | null | {"lat": 48.65, "lon": 20.13} | null | null | null | n/a |
| `gps.altitude-suffix` | `MECP/0/M01 48.65,20.13,1200` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |

## 6.1 Callsign: callsign (9 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `cs.portable` | `MECP/3/L20 ~VK2/OK1ABC/P` | callsign | "VK2/OK1ABC/P" | "VK2/OK1ABC/P" | null | "VK2/OK1ABC/P" | null | n/a | n/a |
| `cs.lower` | `MECP/3/L20 ~vk2/ok1abc/p` | callsign | "VK2/OK1ABC/P" | "VK2/OK1ABC/P" | null | "VK2/OK1ABC/P" | null | n/a | n/a |
| `cs.prefix` | `MECP/3/L20 ~DL/OK1ABC` | callsign | "DL/OK1ABC" | "DL/OK1ABC" | null | "DL/OK1ABC" | null | n/a | n/a |
| `cs.twelve` | `MECP/3/L20 ~ABCDEFGHIJKL` | callsign | "ABCDEFGHIJKL" | "ABCDEFGHIJKL" | null | "ABCDEFGHIJKL" | "ABCDEFGHIJKL" | n/a | n/a |
| `cs.comma` | `MECP/3/L20 ~OK1ABC, ok` | callsign | "OK1ABC" | "OK1ABC" | null | "OK1ABC" | null | n/a | n/a |
| `cs.ssid` | `MECP/3/L20 ~OK1ABC-7` | callsign | null | null | null | null | "OK1ABC-7" | n/a | n/a |
| `cs.aprs-ssid` | `MECP/3/L20 ~W1AW-9` | callsign | null | null | null | null | "W1AW-9" | n/a | n/a |
| `cs.portable-ssid` | `MECP/3/L20 ~vk2/ok1abc-7` | callsign | null | "VK2" | null | null | null | n/a | n/a |
| `cs.glued-left` | `MECP/3/L20 de~OK1ABC` | callsign | null | null | "OK1ABC" | null | null | n/a | n/a |

## 6.1 Reference: reference (9 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `ref.basecamp` | `MECP/2/C08 #basecamp` | reference | "basecamp" | "basecamp" | "base" | "basecamp" | "basecamp" | n/a | n/a |
| `ref.hyphen` | `MECP/2/C08 #base-camp,` | reference | "base-camp" | "base-camp" | "base" | "base-camp" | null | n/a | n/a |
| `ref.underscore` | `MECP/2/C08 #base_camp` | reference | "base-camp" | "base_camp" | "base" | "base_camp" | "base_camp" | n/a | n/a |
| `ref.upper` | `MECP/2/C08 #BaseCamp` | reference | "basecamp" | "BaseCamp" | "Base" | "BaseCamp" | "BaseCamp" | n/a | n/a |
| `ref.paren` | `MECP/2/C08 (#tag)` | reference | "tag" | "tag" | "tag" | "tag" | null | n/a | n/a |
| `ref.digits` | `MECP/2/C08 #2026a` | reference | "2026a" | "2026a" | "2026" | "2026a" | "2026a" | n/a | n/a |
| `ref.long` | `MECP/2/C08 #flood-sector-north-7` | reference | "flood-sector-north-7" | "flood-sector-north-7" | "floo" | "flood-sector-north-7" | "flood-sector-north-7" | n/a | n/a |
| `ref.accent` | `MECP/2/C08 #café` | reference | null | null | "caf" | null | null | n/a | n/a |
| `ref.glued-left` | `MECP/2/C08 issue#5` | reference | null | null | "5" | null | null | n/a | n/a |

## 6.1 Timestamp: timestamp (9 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `ts.three-digit` | `MECP/2/T01 @630` | timestamp | "06:30" | "06:30" | null | "06:30" | null | null | null |
| `ts.colon-one-digit` | `MECP/2/T01 @6:30` | timestamp | "06:30" | "06:30" | null | "06:30" | null | null | null |
| `ts.colon` | `MECP/2/T01 @06:30` | timestamp | "06:30" | "06:30" | null | "06:30" | null | null | null |
| `ts.hmm` | `MECP/3/L01 @123` | timestamp | "01:23" | "01:23" | null | "01:23" | null | null | null |
| `ts.skip-invalid` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "14:00" | null | "14:00" | "15:30" | "24:60" | null |
| `ts.2400` | `MECP/3/L06 @2400` | timestamp | null | null | null | null | null | "24:00" | null |
| `ts.9999` | `MECP/3/L06 @9999` | timestamp | null | null | null | null | null | "99:99" | null |
| `ts.trailing-comma` | `MECP/2/T05 @1430,` | timestamp | "14:30" | "14:30" | null | "14:30" | null | null | null |
| `ts.glued-left` | `MECP/2/T05 meet@1430` | timestamp | null | null | "14:30" | null | null | null | "14:30" |

## upstream: Reference: reference (9 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.06` | `MECP/2/C08 #base-camp,` | reference | "base-camp" | "base-camp" | "base" | "base-camp" | null | n/a | n/a |
| `up.07` | `MECP/2/C08 (#tag)` | reference | "tag" | "tag" | "tag" | "tag" | null | n/a | n/a |
| `up.08` | `MECP/2/C08 #basecamp` | reference | "basecamp" | "basecamp" | "base" | "basecamp" | "basecamp" | n/a | n/a |
| `up.10` | `MECP/2/C08 #hut،ok` | reference | "hut" | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.11` | `MECP/2/C08 #hut”ok` | reference | "hut" | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.12` | `MECP/2/C08 #hut、ok` | reference | "hut" | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.13` | `MECP/2/C08 #hut，ok` | reference | "hut" | "hut" | "hut" | "hut" | null | n/a | n/a |
| `up.14` | `MECP/2/C08 #hut2/basecamp` | reference | null | "hut2" | "hut2" | null | null | n/a | n/a |
| `up.15` | `MECP/3/L06 see https://example.org/#notes` | reference | null | "notes" | "note" | null | null | n/a | n/a |

## upstream: Message: valid (8 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.55` | `MECP/1/T05 ` | valid | false | false | true | false | true | true | true |
| `up.56` | `MECP/1/t05 x` | valid | false | false | true | false | true | true | true |
| `up.60` | `MECP/0/` | valid | false | false | true | false | false | true | true |
| `up.61` | `MECP/0` | valid | false | false | true | false | false | false | true |
| `up.62` | `MECP/4/M01` | valid | false | false | false | false | false | true | false |
| `up.66` | `MECP/1/T05 foo\nbar` | valid | false | false | true | false | true | true | true |
| `up.67` | `MECP/1/T05 foo\u2028bar` | valid | false | false | true | false | true | true | true |
| `up.68` | `MECP/1/T05 foo\fbar` | valid | false | true | true | false | true | true | true |

## 6.1 Language hint: language (7 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `lang.upper` | `MECP/3/L04 @DE` | language | "de" | "de" | null | "de" | "de" | n/a | n/a |
| `lang.underscore` | `MECP/3/L04 @zh_CN` | language | "zh-cn" | "zh-cn" | null | "zh-cn" | null | n/a | n/a |
| `lang.region` | `MECP/3/L04 @zh-TW` | language | "zh-tw" | "zh-tw" | null | "zh-tw" | null | n/a | n/a |
| `lang.script-region` | `MECP/3/L04 @zh-Hans-CN` | language | "zh-hans-cn" | "zh-hans-cn" | null | "zh-hans-cn" | null | n/a | n/a |
| `lang.sr-latn` | `MECP/3/L04 @sr-Latn-RS` | language | "sr-latn-rs" | "sr-latn-rs" | null | "sr-latn-rs" | null | n/a | n/a |
| `lang.three-letter` | `MECP/3/L04 @fil` | language | "fil" | "fil" | null | "fil" | "fil" | n/a | n/a |
| `lang.period` | `MECP/3/L04 @en.` | language | "en" | "en" | null | "en" | null | n/a | n/a |

## upstream: Pax: pax (6 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.16` | `MECP/1/S01 3paxmore` | pax | null | null | 3 | null | null | null | 3 |
| `up.17` | `MECP/1/S01 0pax 2pax` | pax | 2 | 2 | 0 | 2 | 2 | 0 | 0 |
| `up.19` | `MECP/1/S01 (4pax)` | pax | 4 | 4 | 4 | 4 | null | null | 4 |
| `up.20` | `MECP/1/S01 4Pax.` | pax | 4 | 4 | null | 4 | null | null | null |
| `up.23` | `MECP/1/S01 2pax 5pax` | pax | 2 | 2 | 2 | 2 | 5 | 2 | 2 |
| `up.24` | `MECP/1/S01 3pax*` | pax | null | 3 | 3 | null | null | null | 3 |

## upstream: Timestamp: timestamp (6 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.00` | `MECP/3/L06 @2460 @1400 @1530` | timestamp | "14:00" | "14:00" | null | "14:00" | "15:30" | "24:60" | null |
| `up.01` | `MECP/3/L06 @9999` | timestamp | null | null | null | null | null | "99:99" | null |
| `up.02` | `MECP/3/L01 @123` | timestamp | "01:23" | "01:23" | null | "01:23" | null | null | null |
| `up.03` | `MECP/2/T05 @1430,` | timestamp | "14:30" | "14:30" | null | "14:30" | null | null | null |
| `up.04` | `MECP/2/T05 meet@1430` | timestamp | null | null | "14:30" | null | null | null | "14:30" |
| `up.05` | `MECP/3/L06 eta=@1430` | timestamp | null | "14:30" | "14:30" | null | null | null | "14:30" |

## 6.1 Person count: pax (5 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `pax.space` | `MECP/1/S01 4 pax` | pax | 4 | 4 | null | 4 | null | null | null |
| `pax.upper` | `MECP/1/S01 4PAX` | pax | 4 | 4 | null | 4 | 4 | null | null |
| `pax.zero-skipped` | `MECP/1/S01 0pax 2pax` | pax | 2 | 2 | 0 | 2 | 2 | 0 | 0 |
| `pax.first-wins` | `MECP/1/S01 2pax 5pax` | pax | 2 | 2 | 2 | 2 | 5 | 2 | 2 |
| `pax.after-decimal` | `MECP/1/S01 1.5pax` | pax | 5 | 5 | 5 | 5 | null | null | 5 |

## upstream: GPS: gps (5 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.25` | `MECP/3/L06 95.0,200.0 47.3,8.5` | gps | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | null | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 95.0, "lon": 200.0} | n/a |
| `up.26` | `MECP/3/L02 2,5 km` | gps | null | null | null | null | {"lat": 2, "lon": 5} | {"lat": 2, "lon": 5} | n/a |
| `up.27` | `MECP/0/M04 +48.8566, 2.3522` | gps | {"lat": 48.8566, "lon": 2.3522} | {"lat": 48.8566, "lon": 2.3522} | null | {"lat": 48.8566, "lon": 2.3522} | null | null | n/a |
| `up.28` | `MECP/0/M04 90.0001,0.0` | gps | null | null | null | null | null | {"lat": 90.0001, "lon": 0.0} | n/a |
| `up.29` | `MECP/0/M01 x48.65,20.13` | gps | null | null | {"lat": 48.65, "lon": 20.13} | null | null | null | n/a |

## 6.1 Message Format: codes, freetext (3 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.trailing-lf` | `MECP/2/B03\n` | codes | ["B03"] | ["B03"] | [] | ["B03"] | ["B03"] | n/a | [] |
|  |  | freetext | null | null | "B03\n" | null | null | n/a | "B03\n" |
| `env.trailing-cr` | `MECP/2/B03\r` | codes | ["B03"] | ["B03"] | [] | ["B03"] | ["B03"] | n/a | [] |
|  |  | freetext | null | null | "B03\r" | null | null | n/a | "B03\r" |
| `env.trailing-crlf` | `MECP/2/B03\r\n` | codes | ["B03"] | ["B03"] | [] | ["B03"] | ["B03"] | n/a | [] |
|  |  | freetext | null | null | "B03\r\n" | null | null | n/a | "B03\r\n" |

## 6.1 Message Format: freetext (3 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.freetext-inner-spaces` | `MECP/3/L01 see  you   there` | freetext | "see  you   there" | "see  you   there" | "see you there" | "see  you   there" | "see you there" | n/a | "see you there" |
| `env.freetext-tab-inside` | `MECP/3/L01 a\tb` | freetext | "a\tb" | "a\tb" | "a\tb" | "a\tb" | "a b" | n/a | "a\tb" |
| `env.trailing-crlf-freetext` | `MECP/3/L01 see you\r\n` | freetext | "see you" | "see you" | "see you\r\n" | "see you" | "see you" | n/a | "see you\r\n" |

## 6.1 Severity: valid (3 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.sev4` | `MECP/4/M01` | valid | false | false | false | false | false | true | false |
| `env.sev9` | `MECP/9/M01` | valid | false | false | false | false | false | true | false |
| `env.sev-two-digits` | `MECP/01/M01` | valid | false | false | true | false | false | false | true |

## upstream: Callsign: callsign (3 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.30` | `MECP/3/L20 ~DL/OK1ABC` | callsign | "DL/OK1ABC" | "DL/OK1ABC" | null | "DL/OK1ABC" | null | n/a | n/a |
| `up.32` | `MECP/3/L20 ~ABCDEFGHIJKL` | callsign | "ABCDEFGHIJKL" | "ABCDEFGHIJKL" | null | "ABCDEFGHIJKL" | "ABCDEFGHIJKL" | n/a | n/a |
| `up.33` | `MECP/3/L20 ~W1AW-9` | callsign | null | null | null | null | "W1AW-9" | n/a | n/a |

## upstream: Message: freetext (3 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.63` | `MECP/1/T05 T05 damaged\n` | freetext | (any) | "damaged" | "damaged\n" | "damaged" | "damaged" | n/a | "damaged\n" |
| `up.64` | `MECP/1/T05 T05 damaged\r\n` | freetext | (any) | "damaged" | "damaged\r\n" | "damaged" | "damaged" | n/a | "damaged\r\n" |
| `up.65` | `MECP/1/T05 T05 damaged\r` | freetext | (any) | "damaged" | "damaged\r" | "damaged" | "damaged" | n/a | "damaged\r" |

## 6.1 Codes 5: valid, severity, codes, freetext, pax, gps, timestamp, language, callsign, reference, duration (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.unknown-code` | `MECP/3/Z99 hello` | valid | true | true | true | true | false | true | true |
|  |  | severity | 3 | 3 | 3 | 3 | "(invalid)" | 3 | 3 |
|  |  | codes | ["Z99"] | ["Z99"] | ["Z99"] | ["Z99"] | "(invalid)" | n/a | ["Z99"] |
|  |  | freetext | "hello" | "hello" | "hello" | "hello" | "(invalid)" | n/a | "hello" |
|  |  | pax | null | null | null | null | "(invalid)" | null | null |
|  |  | gps | null | null | null | null | "(invalid)" | null | n/a |
|  |  | timestamp | null | null | null | null | "(invalid)" | null | null |
|  |  | language | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | callsign | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | reference | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | duration | null | null | null | null | "(invalid)" | n/a | null |
| `env.unknown-category-only` | `MECP/1/Q42` | valid | true | true | true | true | false | true | true |
|  |  | severity | 1 | 1 | 1 | 1 | "(invalid)" | 1 | 1 |
|  |  | codes | ["Q42"] | ["Q42"] | ["Q42"] | ["Q42"] | "(invalid)" | n/a | ["Q42"] |
|  |  | freetext | null | null | null | null | "(invalid)" | n/a | null |
|  |  | pax | null | null | null | null | "(invalid)" | null | null |
|  |  | gps | null | null | null | null | "(invalid)" | null | n/a |
|  |  | timestamp | null | null | null | null | "(invalid)" | null | null |
|  |  | language | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | callsign | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | reference | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | duration | null | null | null | null | "(invalid)" | n/a | null |

## 6.1 Optional Freetext 4: freetext, pax (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `b.nbsp` | `MECP/1/S01 4pax\u00a0water` | freetext | "4pax\u00a0water" | "4pax\u00a0water" | "4pax\u00a0water" | "4pax\u00a0water" | "4pax water" | n/a | "4pax\u00a0water" |
|  |  | pax | 4 | 4 | 4 | 4 | 4 | null | 4 |
| `b.vt-not-b` | `MECP/1/S01 4pax\u000bwater` | freetext | "4pax\u000bwater" | "4pax\u000bwater" | "4pax\u000bwater" | "4pax\u000bwater" | "4pax water" | n/a | "4pax\u000bwater" |
|  |  | pax | null | 4 | 4 | null | 4 | 4 | 4 |

## upstream: Language: language (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.34` | `MECP/3/L04 @zh_CN` | language | "zh-cn" | "zh-cn" | null | "zh-cn" | null | n/a | n/a |
| `up.35` | `MECP/3/L04 @DE` | language | "de" | "de" | null | "de" | "de" | n/a | n/a |

## upstream: Message: valid, severity, codes, freetext, pax, gps, timestamp, language, callsign, reference, duration (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.58` | `MECP/3/Z99 hello` | valid | true | true | true | true | false | true | true |
|  |  | severity | (any) | 3 | 3 | 3 | "(invalid)" | 3 | 3 |
|  |  | codes | (any) | ["Z99"] | ["Z99"] | ["Z99"] | "(invalid)" | n/a | ["Z99"] |
|  |  | freetext | (any) | "hello" | "hello" | "hello" | "(invalid)" | n/a | "hello" |
|  |  | pax | null | null | null | null | "(invalid)" | null | null |
|  |  | gps | null | null | null | null | "(invalid)" | null | n/a |
|  |  | timestamp | null | null | null | null | "(invalid)" | null | null |
|  |  | language | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | callsign | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | reference | null | null | null | null | "(invalid)" | n/a | n/a |
|  |  | duration | null | null | null | null | "(invalid)" | n/a | null |
| `up.69` | `MECP/0/M01 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | valid | true | false | true | true | true | true | true |
|  |  | severity | (any) | "(invalid)" | 0 | 0 | 0 | 0 | 0 |
|  |  | codes | (any) | "(invalid)" | ["M01"] | ["M01"] | ["M01"] | n/a | ["M01"] |
|  |  | freetext | (any) | "(invalid)" | "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" | "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" | "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" | n/a | "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" |
|  |  | pax | null | "(invalid)" | null | null | null | null | null |
|  |  | gps | null | "(invalid)" | null | null | null | null | n/a |
|  |  | timestamp | null | "(invalid)" | null | null | null | null | null |
|  |  | language | null | "(invalid)" | null | null | null | n/a | n/a |
|  |  | callsign | null | "(invalid)" | null | null | null | n/a | n/a |
|  |  | reference | null | "(invalid)" | null | null | null | n/a | n/a |
|  |  | duration | null | "(invalid)" | null | null | null | n/a | null |

## upstream: Pax: freetext, pax (2 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.21` | `MECP/1/S01 4pax\u00a0water` | freetext | (any) | "4pax\u00a0water" | "4pax\u00a0water" | "4pax\u00a0water" | "4pax water" | n/a | "4pax\u00a0water" |
|  |  | pax | 4 | 4 | 4 | 4 | 4 | null | 4 |
| `up.22` | `MECP/1/S01 4pax\u000bwater` | freetext | (any) | "4pax\u000bwater" | "4pax\u000bwater" | "4pax\u000bwater" | "4pax water" | n/a | "4pax\u000bwater" |
|  |  | pax | null | 4 | 4 | null | 4 | 4 | 4 |

## 6.1: duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `mix.everything` | `MECP/0/M01 M07 R03 3pax 48.8566,2.3522 @1430 @en ~OK1ABC #base 20min` | duration | 20 | 20 | null | 20 | 20 | n/a | null |

## 6.1 Codes 3: codes, freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.lowercase-ends-codes` | `MECP/3/L01 l06 late` | codes | ["L01"] | ["L01"] | ["L01"] | ["L01"] | ["L01", "L06"] | n/a | ["L01"] |
|  |  | freetext | "l06 late" | "l06 late" | "l06 late" | "l06 late" | "late" | n/a | "l06 late" |

## 6.1 Codes 3: valid (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `env.lowercase-first-code` | `MECP/1/t05 x` | valid | false | false | true | false | true | true | true |

## 6.1 GPS coordinates: freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `gps.two-spaces-after-comma` | `MECP/0/M01 48.65,  20.13` | freetext | "48.65,  20.13" | "48.65,  20.13" | "48.65, 20.13" | "48.65,  20.13" | "48.65, 20.13" | n/a | "48.65, 20.13" |

## 6.1 Optional Freetext 10: duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `dur.huge` | `MECP/2/R03 99999999999999999999999min` | duration | (any) | null | null | 1e+23 | null | n/a | null |

## 6.1 Optional Freetext 10: pax (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `pax.huge` | `MECP/1/S01 99999999999999999999999pax` | pax | (any) | null | 1e+23 | 1e+23 | null | 1e+23 | null |

## 6.1 Optional Freetext 4: gps (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `b.arabic-comma` | `MECP/0/M01 48.65,20.13،` | gps | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | {"lat": 48.65, "lon": 20.13} | null | null | n/a |

## 6.1 Optional Freetext 5: language (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `lang.turkish-i` | `MECP/3/L04 @TR` | language | "tr" | "tr" | null | "tr" | "tr" | n/a | n/a |

## 6.1 Optional Freetext 6: duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `dur.zero-then-ok` | `MECP/2/R03 0min 5min` | duration | 5 | 5 | null | 5 | 0 | n/a | null |

## 6.1 Optional Freetext 6: gps (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `gps.resume-after-invalid` | `MECP/3/L06 95.0,200.0 47.3,8.5` | gps | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | null | {"lat": 47.3, "lon": 8.5} | {"lat": 47.3, "lon": 8.5} | {"lat": 95.0, "lon": 200.0} | n/a |

## 6.1 Person count: freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `pax.two-spaces` | `MECP/1/S01 4  pax` | freetext | "4  pax" | "4  pax" | "4 pax" | "4  pax" | "4 pax" | n/a | "4 pax" |

## upstream: Message: codes, freetext, duration (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.59` | `MECP/2/L01 r03 45min` | codes | (any) | ["L01"] | ["L01"] | ["L01"] | ["L01", "R03"] | n/a | ["L01"] |
|  |  | freetext | (any) | "r03 45min" | "r03 45min" | "r03 45min" | "45min" | n/a | "r03 45min" |
|  |  | duration | null | null | null | null | 45 | n/a | null |

## upstream: Reference: freetext (1 cases)

| Case | Input | Field | Spec | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|---|---|
| `up.09` | `MECP/2/C08 #hut\u3000ok` | freetext | (any) | "#hut\u3000ok" | "#hut\u3000ok" | "#hut\u3000ok" | "#hut ok" | n/a | "#hut\u3000ok" |

