# mesh-client: MECP 1.4.1 decode conformance

- Client: tryParseMecp() over its vendored @mecp/engine copy (inbound chat path)
- Repository: https://github.com/Colorado-Mesh/mesh-client
- Commit tested: `a9165a9906` (2026-11-21)
- Decoder: `src/renderer/lib/mecp/mecpMessages.ts`
- Vectors: `conformance/vectors/decode-1.4.1.json` plus mecp-org/MECP `freetext/tests.json` (256 cases), run 2026-11-22
- **Result: 256 pass, 0 fail, 0 error**
- **Code table: 109/109**

## Code table (§7)

All 109 codes from `conformance/vectors/codes-1.4.1.json` are present, and no others.

## Decode vectors

All cases pass.
