# MECP 1.4.1 decode conformance summary (2026-11-22)

256 cases: hand-written vectors from `conformance/vectors/decode-1.4.1.json` and the upstream mecp-org/MECP `freetext/tests.json` (clauses `upstream: …`). Cells are passing/total cases per clause; n/a means the client does not expose the field that clause is about.

| Clause | reference | meshcore-tak-bridge | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|
| 6.1 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| 6.1 Callsign | 11/11 | 11/11 | 11/11 | 5/11 | n/a | n/a |
| 6.1 Codes 3 | 3/3 | 3/3 | 3/3 | 1/3 | n/a | 3/3 |
| 6.1 Codes 4 | 1/1 | 1/1 | 1/1 | 1/1 | n/a | 1/1 |
| 6.1 Codes 5 | 2/2 | 2/2 | 2/2 | 0/2 | n/a | 2/2 |
| 6.1 Duration | 31/31 | 31/31 | 31/31 | 16/31 | n/a | 31/31 |
| 6.1 GPS coordinates | 16/16 | 16/16 | 16/16 | 8/16 | 8/16 | 16/16 |
| 6.1 Language hint | 10/10 | 10/10 | 10/10 | 5/10 | n/a | n/a |
| 6.1 Message Format | 34/34 | 34/34 | 34/34 | 17/34 | 17/34 | 34/34 |
| 6.1 Optional Freetext 10 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| 6.1 Optional Freetext 4 | 16/16 | 16/16 | 16/16 | 8/16 | 8/16 | 16/16 |
| 6.1 Optional Freetext 5 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| 6.1 Optional Freetext 6 | 2/2 | 2/2 | 2/2 | 1/2 | 1/2 | 2/2 |
| 6.1 Optional Freetext 9 | 2/2 | 2/2 | 2/2 | 2/2 | n/a | 2/2 |
| 6.1 Person count | 11/11 | 11/11 | 11/11 | 7/11 | 7/11 | 10/11 |
| 6.1 Reference | 11/11 | 11/11 | 11/11 | 9/11 | n/a | n/a |
| 6.1 Severity | 5/5 | 5/5 | 5/5 | 5/5 | 3/5 | 5/5 |
| 6.1 Timestamp | 15/15 | 15/15 | 15/15 | 9/15 | 7/15 | 15/15 |
| upstream: Callsign | 4/4 | 4/4 | 4/4 | 2/4 | 4/4 | 4/4 |
| upstream: Duration | 26/26 | 26/26 | 26/26 | 17/26 | 26/26 | 26/26 |
| upstream: GPS | 5/5 | 5/5 | 5/5 | 3/5 | 1/5 | 5/5 |
| upstream: Language | 2/2 | 2/2 | 2/2 | 1/2 | 2/2 | 2/2 |
| upstream: Message | 15/15 | 15/15 | 15/15 | 8/15 | 8/15 | 15/15 |
| upstream: Pax | 9/9 | 9/9 | 9/9 | 5/9 | 4/9 | 9/9 |
| upstream: Reference | 10/10 | 10/10 | 10/10 | 4/10 | 10/10 | 10/10 |
| upstream: Timestamp | 6/6 | 6/6 | 6/6 | 3/6 | 2/6 | 6/6 |
| **Total** | **256/256** | **256/256** | **256/256** | **146/256** | **187/256** | **255/256** |

## Code table (§7, 109 codes)

Each client's own code table against `conformance/vectors/codes-1.4.1.json`. Unknown codes still decode, so the vectors above cannot catch a missing code; the app just cannot label it.

| Client | Codes | Missing | Not in §7 |
|---|---|---|---|
| reference | n/a |  |  |
| meshcore-tak-bridge | 109/109 | none | none |
| mesh-client | 109/109 | none | none |
| reticulum-mobile | 108/109 (+1 extra) | M16 | B04 |
| wadamesh | 108/109 | M16 | none |
| meshcore-one | 109/109 | none | none |

| Client | Commit |
|---|---|
| [reference](reference.md) | in-repo |
| [meshcore-tak-bridge](meshcore-tak-bridge.md) | `08a3a4d17c` 2026-11-20 |
| [mesh-client](mesh-client.md) | `a9165a9906` 2026-11-21 |
| [reticulum-mobile](reticulum-mobile.md) | `6cf3db0978` 2026-11-21 |
| [wadamesh](wadamesh.md) | `3411a8fb3b` 2026-11-16 |
| [meshcore-one](meshcore-one.md) | `28a771d0e7` 2026-11-22 |
