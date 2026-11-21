# meshcore-tak-bridge: MECP 1.4.1 decode conformance

- Client: Kotlin decoder Mecp.parse()
- Repository: https://github.com/Colorado-Mesh/meshcore-tak-bridge
- Commit tested: `08a3a4d17c` (2026-11-20)
- Decoder: `meshcore-kotlin/protocol/src/main/kotlin/org/coloradomesh/meshcore/protocol/Mecp.kt`
- Vectors: `conformance/vectors/decode-1.4.1.json` plus mecp-org/MECP `freetext/tests.json` (256 cases), run 2026-11-21
- **Result: 256 pass, 0 fail, 0 error**
- **Code table: 109/109**

## Code table (§7)

All 109 codes from `conformance/vectors/codes-1.4.1.json` are present, and no others.

## Decode vectors

All cases pass.
