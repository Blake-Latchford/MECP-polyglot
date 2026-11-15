# MECP-polyglot

Encoders and decoders for [MECP](https://github.com/mecp-org/MECP) (Mesh
Emergency Communication Protocol) in several programming languages. All of
them pass one shared set of conformance vectors.

```
MECP/0/M01 M07 2pax P05 48.6520,20.1305
→ severity 0 (MAYDAY), codes [M01, M07], count 2, gps 48.652,20.1305
```

| Language | Directory | Dependencies | Test command |
|----------|-----------|--------------|--------------|
| Python ≥ 3.10 | [python/](python/) | none | `cd python && PYTHONPATH=src python3 -m unittest discover -s tests` |
| C99 / C++ | [c/](c/) | none; no heap | `cd c && make test` |
| Rust | [rust/](rust/) | regex-lite (serde_json for tests) | `cd rust && cargo test` |
| Go | [go/](go/) | standard library | `cd go && go test ./...` |
| Dart ≥ 3.0 | [dart/](dart/) | none (test for tests) | `cd dart && dart pub get && dart test` |

## How it fits together

- [spec/conformance.md](spec/conformance.md) gives exact decode, encode and
  validate rules. It follows the wire format in the MECP brief and matches the
  TypeScript reference engine
  [`@mecp/engine`](https://github.com/mecp-org/mecp-app/tree/main/engine),
  apart from a few documented divergences.
- [vectors/mecp-vectors.json](vectors/mecp-vectors.json) holds the shared test
  cases. It is generated from [vectors/build_vectors.py](vectors/build_vectors.py),
  where every expectation is written by hand. To change the vectors, edit that
  file and run `python3 vectors/build_vectors.py`.
- [oracle/check-engine.mts](oracle/check-engine.mts) runs the vectors against
  `@mecp/engine` in CI, so the vectors cannot drift from the reference
  behaviour without someone noticing.

## API shape

Every implementation provides the same operations, named in each language's
usual style:

- `decode(s)` returns a record with `valid`, `severity`, `codes`, `is_drill`,
  `freetext`, `extracted` (`count`, `gps`, `eta`, `reference`, `language`,
  `timestamp`, `callsign`) and `warnings`.
- `encode(severity, codes, freetext?)` returns `message`, `byte_length`,
  `over_limit` and `warnings`.
- `validate(s)` returns `valid`, `errors` and `warnings`.
- Helpers: `is_mecp`, `is_code`, `is_beacon`, `is_beacon_ack`,
  `is_beacon_cancel`, and `MAX_MESSAGE_BYTES = 200`.

The C version takes `(pointer, length)` inputs, fills caller-owned structs,
and reports warnings as bit flags. `MECP_MAX_INPUT_BYTES` (default 256)
controls the buffer sizes.

## Adding a language

1. Implement the rules in `spec/conformance.md`. Copy the regexes from its
   Patterns section unchanged; the portability notes there cover the platform
   differences. Also watch the header: indexing is by code point.
2. Write a test that loads `vectors/mecp-vectors.json` and compares each
   `expect` object field by field.
3. Add a CI job in `.github/workflows/ci.yml`.

## Scope

This repository covers the wire format only. Turning codes into localised text
uses the language packs in
[mecp-org/MECP `languages/`](https://github.com/mecp-org/MECP/tree/main/languages)
and is not implemented here yet.

## License

[MIT](LICENSE).
