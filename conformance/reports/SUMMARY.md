# MECP 1.4.0 decode conformance summary (2026-11-18)

249 cases: hand-written vectors from `conformance/vectors/decode-1.4.0.json` and the upstream mecp-org/MECP `freetext/tests.json` (clauses `upstream: …`). Cells are passing/total cases per clause; n/a means the client does not expose the field that clause is about.

| Clause | reference | meshcore-tak-bridge | mecp-app | mesh-client | reticulum-mobile | wadamesh | meshcore-one |
|---|---|---|---|---|---|---|---|
| 6.1 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 2/3 |
| 6.1 Callsign | 11/11 | 10/11 | 5/11 | 11/11 | 5/11 | n/a | n/a |
| 6.1 Codes 3 | 3/3 | 3/3 | 2/3 | 3/3 | 1/3 | n/a | 2/3 |
| 6.1 Codes 4 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | n/a | 1/1 |
| 6.1 Codes 5 | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | n/a | 2/2 |
| 6.1 Duration | 31/31 | 28/31 | 13/31 | 31/31 | 16/31 | n/a | 13/31 |
| 6.1 GPS coordinates | 16/16 | 16/16 | 13/16 | 16/16 | 8/16 | 8/16 | 15/16 |
| 6.1 Language hint | 10/10 | 10/10 | 3/10 | 10/10 | 5/10 | n/a | n/a |
| 6.1 Message Format | 34/34 | 34/34 | 13/34 | 34/34 | 17/34 | 17/34 | 13/34 |
| 6.1 Optional Freetext 10 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| 6.1 Optional Freetext 4 | 16/16 | 13/16 | 6/16 | 16/16 | 8/16 | 8/16 | 6/16 |
| 6.1 Optional Freetext 5 | 4/4 | 4/4 | 3/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| 6.1 Optional Freetext 6 | 2/2 | 2/2 | 0/2 | 2/2 | 1/2 | 1/2 | 1/2 |
| 6.1 Optional Freetext 9 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | n/a | 2/2 |
| 6.1 Person count | 11/11 | 11/11 | 7/11 | 11/11 | 7/11 | 7/11 | 7/11 |
| 6.1 Reference | 11/11 | 11/11 | 3/11 | 11/11 | 9/11 | n/a | n/a |
| 6.1 Severity | 5/5 | 5/5 | 4/5 | 5/5 | 5/5 | 3/5 | 4/5 |
| 6.1 Timestamp | 15/15 | 15/15 | 8/15 | 15/15 | 9/15 | 7/15 | 8/15 |
| upstream: Callsign | 4/4 | 4/4 | 2/4 | 4/4 | 2/4 | 4/4 | 4/4 |
| upstream: Duration | 19/19 | 15/19 | 6/19 | 19/19 | 11/19 | 19/19 | 6/19 |
| upstream: GPS | 5/5 | 5/5 | 2/5 | 5/5 | 3/5 | 1/5 | 5/5 |
| upstream: Language | 2/2 | 2/2 | 0/2 | 2/2 | 1/2 | 2/2 | 2/2 |
| upstream: Message | 15/15 | 13/15 | 8/15 | 15/15 | 8/15 | 8/15 | 8/15 |
| upstream: Pax | 9/9 | 7/9 | 4/9 | 9/9 | 5/9 | 4/9 | 4/9 |
| upstream: Reference | 10/10 | 8/10 | 6/10 | 10/10 | 4/10 | 10/10 | 10/10 |
| upstream: Timestamp | 6/6 | 5/6 | 1/6 | 6/6 | 3/6 | 2/6 | 1/6 |
| **Total** | **249/249** | **231/249** | **118/249** | **249/249** | **140/249** | **180/249** | **154/249** |

| Client | Commit |
|---|---|
| [reference](reference.md) | in-repo |
| [meshcore-tak-bridge](meshcore-tak-bridge.md) | `d808585f01` 2026-11-18 |
| [mecp-app](mecp-app.md) | `80139af8e6` 2026-11-11 |
| [mesh-client](mesh-client.md) | `11aaa0a408` 2026-11-18 |
| [reticulum-mobile](reticulum-mobile.md) | `42cdc3276e` 2026-11-18 |
| [wadamesh](wadamesh.md) | `3411a8fb3b` 2026-11-16 |
| [meshcore-one](meshcore-one.md) | `5e980a53e0` 2026-11-16 |
