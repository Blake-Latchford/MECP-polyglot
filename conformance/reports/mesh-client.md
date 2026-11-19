# mesh-client: MECP 1.4.0 decode conformance

- Client: tryParseMecp() over its vendored @mecp/engine copy (inbound chat path)
- Repository: https://github.com/Colorado-Mesh/mesh-client
- Commit tested: `11aaa0a408` (2026-11-18)
- Decoder: `src/renderer/lib/mecp/mecpMessages.ts`
- Vectors: `conformance/vectors/decode-1.4.0.json` plus mecp-org/MECP `freetext/tests.json` (249 cases), run 2026-11-18
- **Result: 249 pass, 0 fail, 0 error**

All cases pass.
