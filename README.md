# MECP-polyglot

Encoders and decoders for [MECP](https://github.com/mecp-org/MECP) (Mesh
Emergency Communication Protocol) **1.4.0** in several programming languages.
All of them use the regexes from MECP's own `freetext/patterns.json` and pass
both MECP's `freetext/tests.json` and a shared set of hand-written vectors.

```
MECP/0/M01 M07 2pax P05 48.6520,20.1305
→ severity 0 (MAYDAY), codes [M01, M07], pax 2, gps 48.652,20.1305
```

| Language | Directory | Dependencies | Test command |
|----------|-----------|--------------|--------------|
| Python ≥ 3.10 | [python/](python/) | none | `cd python && PYTHONPATH=src python3 -m unittest discover -s tests` |
| C99 / C++ | [c/](c/) | none; no heap | `cd c && make test` |
| Rust | [rust/](rust/) | regex-lite (serde_json for tests) | `cd rust && cargo test` |
| Go | [go/](go/) | standard library | `cd go && go test ./...` |
| Dart ≥ 3.0 | [dart/](dart/) | none (test for tests) | `cd dart && dart pub get && dart test` |

## How it fits together

- [upstream/](upstream/) holds MECP's freetext conformance pack
  (`manifest.json`, `patterns.json`, `tests.json`), copied unchanged from the
  mecp-org/MECP commit recorded in `upstream/source.json`, plus the boundary
  class B read from brief §6.1 rule 4.
- [tools/mecp_sync.py](tools/mecp_sync.py) pulls that pack and generates each
  codec's pattern constants from it, so no implementation retypes a regex.
  To update: `python3 tools/mecp_sync.py pull ../MECP`, then run every test
  suite. CI fails if a generated file is stale or `upstream/` differs from
  the recorded commit.
- [spec/conformance.md](spec/conformance.md) gives exact decode, encode and
  validate rules, following brief §6.1, and lists the choices the brief
  leaves open.
- [vectors/mecp-vectors.json](vectors/mecp-vectors.json) holds our own test
  cases for what upstream does not cover: envelope fields, clamping, encode
  and validate. It is generated from [vectors/build_vectors.py](vectors/build_vectors.py),
  where every expectation is written by hand. To change the vectors, edit that
  file and run `python3 vectors/build_vectors.py`.
- [oracle/check_vectors.py](oracle/check_vectors.py) runs our decode vectors
  through MECP's normative `scripts/check-freetext.mjs` in CI, so the vectors
  cannot drift from the reference behaviour.
- [conformance/](conformance/) runs decode vectors against third-party MECP
  clients and reports where they disagree with the spec and with each other.

## API shape

Every implementation provides the same operations, named in each language's
usual style:

- `decode(s)` returns a record with `valid`, `severity`, `codes`, `is_drill`,
  `freetext` and `extracted` (`pax`, `gps`, `timestamp` as `HH:MM`,
  `language`, `callsign`, `reference`, `duration` in minutes).
- `encode(severity, codes, freetext?)` returns `message`, `byte_length` and
  `errors`. With any error, `message` is null: the encoder refuses to build
  a message that is not conforming, including one over 200 bytes.
- `validate(s)` returns `valid` and `errors`: whether `s` may be transmitted.
- Helpers: `is_mecp`, `is_code`, `is_beacon`, `is_beacon_ack`,
  `is_beacon_cancel`, `MAX_MESSAGE_BYTES = 200` and `MECP_VERSION`.

The C version takes `(pointer, length)` inputs, fills caller-owned structs,
and reports errors as bit flags. `MECP_MAX_INPUT_BYTES` (default 256)
controls the buffer sizes.

## Adding a language

1. Add a generator for the language's pattern constants to
   `tools/mecp_sync.py` (`OUTPUTS`), and implement the rules in
   `spec/conformance.md` on top of them.
2. Write tests that load `vectors/mecp-vectors.json` (compare each `expect`
   record field by field) and `upstream/freetext/tests.json` (check
   `manifest.json` has `schemaVersion` 1 first).
3. Add a CI job in `.github/workflows/ci.yml`.

## Scope

This repository covers the wire format only. Turning codes into localised text
uses the language packs in
[mecp-org/MECP `languages/`](https://github.com/mecp-org/MECP/tree/main/languages)
and is not implemented here yet.

## License

[MIT](LICENSE).
