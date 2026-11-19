# meshcore-tak-bridge: MECP 1.4.0 decode conformance

- Client: Kotlin decoder Mecp.parse()
- Repository: https://github.com/Colorado-Mesh/meshcore-tak-bridge
- Commit tested: `d808585f01` (2026-11-18)
- Decoder: `meshcore-kotlin/protocol/src/main/kotlin/org/coloradomesh/meshcore/protocol/Mecp.kt`
- Vectors: `conformance/vectors/decode-1.4.0.json` plus mecp-org/MECP `freetext/tests.json` (249 cases), run 2026-11-18
- **Result: 231 pass, 18 fail, 0 error**

Cases marked *(proposed)* depend on spec changes not yet merged upstream; see the vector's `proposed` field.

Each row is one vector. *Expected* is written by hand from the protocol brief (clause in the heading); *Got* is what this client's decoder returned.

## upstream: Duration (4)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.45` Duration: seconds are not a unit | `MECP/2/R03 30s` | duration | null | 1 |
| `up.47` Duration: a position as the first freetext token is not a bare number | `MECP/2/R03 47.3769,12.1048` | duration | null | 47 |
| `up.51` Duration: the first value by position wins (days before minutes) | `MECP/2/R03 2d 45min` | duration | 2880 | 45 |
| `up.52` Duration: the first value by position wins (minutes before hours) | `MECP/2/R03 45min 2h` | duration | 45 | 120 |

## 6.1 Duration (3)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `dur.s` | `MECP/2/R03 120s` | duration | null | 2 |
| `dur.bare-latitude` | `MECP/2/R03 47.3769,12.1048` | duration | null | 47 |
| `dur.first-by-position` | `MECP/2/R03 30min or 1h` | duration | 30 | 60 |

## 6.1 Optional Freetext 4 (3)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `b.asterisk` | `MECP/1/S01 *4pax*` | pax | null | 4 |
| `b.slash` | `MECP/1/S01 4pax/3` | pax | null | 4 |
| `b.vt-not-b` | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |

## upstream: Message (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.68` Message: an embedded form feed is invalid | `MECP/1/T05 foo\fbar` | valid | false | true |
| `up.69` Message: decoders accept a message longer than 200 bytes (202 bytes) | `MECP/0/M01 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | valid | true | false |

## upstream: Pax (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.22` Pax: a vertical tab (U+000B) is not a boundary | `MECP/1/S01 4pax\u000bwater` | pax | null | 4 |
| `up.24` Pax: an asterisk is not a boundary | `MECP/1/S01 3pax*` | pax | null | 3 |

## upstream: Reference (2)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.14` Reference: a slash is not a boundary | `MECP/2/C08 #hut2/basecamp` | reference | null | "hut2" |
| `up.15` Reference: a fragment inside a URL is not decoded | `MECP/3/L06 see https://example.org/#notes` | reference | null | "notes" |

## 6.1 Callsign (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `cs.portable-ssid` | `MECP/3/L20 ~vk2/ok1abc-7` | callsign | null | "VK2" |

## upstream: Timestamp (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `up.05` Timestamp: an equals sign is not a boundary | `MECP/3/L06 eta=@1430` | timestamp | null | "14:30" |
