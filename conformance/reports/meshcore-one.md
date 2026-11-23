# meshcore-one: MECP 1.4.1 decode conformance

- Client: MeshCore One (MC1) iOS app, MECPDecode.decode() and MECPMessage's derived fields
- Repository: https://github.com/Avi0n/MeshCoreOne
- Commit tested: `28a771d0e7` (2026-11-22)
- Decoder: `MC1Services/Sources/MC1Services/MECP/MECPDecode.swift`
- Fields compared: valid, severity, codes, freetext, pax, timestamp, duration (others not exposed by this client)
- Vectors: `conformance/vectors/decode-1.4.1.json` plus mecp-org/MECP `freetext/tests.json` (256 cases), run 2026-11-22
- **Result: 255 pass, 1 fail, 0 error**
- **Code table: 109/109**

## Code table (§7)

All 109 codes from `conformance/vectors/codes-1.4.1.json` are present, and no others.

## Decode vectors

Cases marked *(proposed)* depend on spec changes not yet merged upstream; see the vector's `proposed` field.

Each row is one vector. *Expected* is written by hand from the protocol brief (clause in the heading); *Got* is what this client's decoder returned.

### 6.1 Person count (1)

| Case | Input | Field | Expected | Got |
|---|---|---|---|---|
| `pax.after-decimal` | `MECP/1/S01 1.5pax` | pax | 5 | null |
