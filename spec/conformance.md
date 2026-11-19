# MECP-polyglot Conformance Rules

This document pins down the exact behaviour every MECP-polyglot codec must
implement. It follows MECP protocol **1.4.0**, brief §6.1
([MECP_Comprehensive_Brief.md](https://github.com/mecp-org/MECP/blob/main/MECP_Comprehensive_Brief.md)).
Where this document and the brief disagree, the brief wins and this document
has a bug.

Conformance is defined by two test sets, and a codec must pass both:

- [`../upstream/freetext/tests.json`](../upstream/freetext/tests.json): the
  upstream decode cases from mecp-org/MECP, copied unchanged.
- [`../vectors/mecp-vectors.json`](../vectors/mecp-vectors.json): our own
  hand-written cases for what upstream does not cover (the envelope fields,
  clamping, encode and validate).

## Where the regexes come from

The patterns are not retyped in any codec. [`tools/mecp_sync.py`](../tools/mecp_sync.py)
copies `freetext/{manifest,patterns,tests}.json` from a mecp-org/MECP commit
into [`upstream/`](../upstream/), reads the boundary class B from §6.1 rule 4
of the brief (`patterns.json` does not carry it), and generates one source file
per language:

| Language | Generated file |
|----------|----------------|
| Python | `python/src/mecp/_patterns.py` |
| Go | `go/patterns.go` |
| Rust | `rust/src/patterns.rs` |
| Dart | `dart/lib/src/patterns.dart` |
| C | `c/src/mecp_boundary.h` (B as code point ranges; C matches the patterns by hand) |

The generator rewrites each `\uXXXX` regex escape as the literal character,
written in the host language's string syntax: Go's RE2 has no `\u` escape and
Rust spells it `\u{..}`. Every other escape in the upstream patterns
(`\t`, `\.`, `\[`, …) means the same in Python `re`, Go `regexp`, Rust
`regex-lite` and Dart `RegExp`, so the regex text is otherwise unchanged.

To move to a newer MECP:

```sh
python3 tools/mecp_sync.py pull ../MECP   # a clean checkout of mecp-org/MECP
```

then run every test suite. `mecp_sync.py check` (CI) fails if a generated
file is stale, and `mecp_sync.py verify-remote` (CI) fails if `upstream/` is
not byte-identical to the recorded commit on GitHub.

## Definitions

- **B**: the boundary class from §6.1 rule 4 (`upstream/boundary.json`).
- **Code**: a token matching exactly `[A-Z][0-9][0-9]`.
- **Forbidden on the wire**: the line breaks `\n`, `\f`, `\r`, U+0085, U+2028,
  U+2029 (§6.1 Wire), plus the byte-order mark U+FEFF and the Unicode
  whitespace U+00A0, U+1680, U+2000–U+200A, U+202F, U+205F, U+3000 that
  encoders must not emit (rule 8).
- **ECMAScript whitespace (WS)**: U+0009–U+000D, U+0020, U+00A0, U+1680,
  U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000, U+FEFF. Only used to
  trim encoder input.
- **Clamp**: integer fields (`pax`, `duration`) are int32. A value above
  2147483647, including an intermediate such as `99999999h` in minutes,
  becomes 2147483647. Huge digit runs never fail.

## Decode

Input: a string. Output: a `Decoded` record:

| Field | Type | Default |
|-------|------|---------|
| `valid` | bool | false |
| `severity` | int 0–3 or null | null |
| `codes` | list of string | [] |
| `is_drill` | bool | false |
| `freetext` | string or null | null |
| `extracted.pax` | int or null | null |
| `extracted.gps` | `{lat, lon}` (float64) or null | null |
| `extracted.timestamp` | `"HH:MM"` or null | null |
| `extracted.language` | string or null | null |
| `extracted.callsign` | string or null | null |
| `extracted.reference` | string or null | null |
| `extracted.duration` | int (minutes) or null | null |

Steps:

1. **Strip** at most one trailing `\r\n`, `\n` or `\r`.
2. **Envelope.** Match the whole string against `message.decode`. With no
   match, return the defaults. (Python must use `fullmatch`: its `$` also
   matches before a final `\n`.)
3. Set `valid = true`, `severity` from group 1, `codes` from group 2 split on
   U+0020, and `freetext` from group 3 (null when absent). `is_drill` is true
   if `codes` contains `D01` or `D02`.
4. **Extract** from `freetext` if it is not null, each convention independently:
   - Wrap each decode pattern P as `(?:^|B)(?:P)(B|$)`. The right boundary is
     captured as the last group.
   - Search from position 0 for the leftmost match. If it fails Additional
     Validation, search again from the start of its right boundary (the end of
     the failed token), and so on. `^` keeps meaning the start of the freetext.
     Searching a suffix is equivalent, because that position always holds a
     B character and no pattern starts with one.
   - `pax`: group 1, clamped.
   - `gps`: groups 1 and 2 as float64. Valid only if −90 ≤ lat ≤ 90 and
     −180 ≤ lon ≤ 180.
   - `timestamp`: group 1 (hour) zero-padded to two digits, `:`, group 2.
   - `language`: group 1, ASCII-lowercased, `_` replaced with `-`.
   - `callsign`: group 1, ASCII-uppercased. Valid only if group 1 is at most
     12 characters.
   - `reference`: group 1, verbatim.
   - `duration`: only if `codes` contains `R03` (`duration.scope`). For each
     of decode patterns 1–4 in order (h+min, h, min, d), find the first valid
     match, where valid means the minutes are > 0. Keep the match with the
     lowest start; on a tie the earlier pattern wins. Only if none of 1–4
     matched, try pattern 5 (bare number), which is valid only if the minutes
     are > 0 **and** group 2 (a decimal part) did not take part. Minutes:
     h+min = g1·60 + g2, h = g1·60, min = g1, d = g1·1440, bare = g1, each
     clamped.

Case folding is ASCII-only, never locale-sensitive (rule 5).

Unknown but well-formed codes (e.g. `Z99`) are codes. Checking them against
the code table is a localisation concern.

Invalid UTF-8 is read as U+FFFD (C, Go). Python, Rust and Dart take
already-decoded strings.

## Encode

Input: `severity` (integer), `codes` (list of strings), `freetext` (string or
null). Output: `{message, byte_length, errors}`.

1. If `severity` is not 0–3: error `invalid_severity`. If `codes` is empty:
   error `no_codes`. For each code that is not a Code: error `invalid_code`,
   once per bad code, in order.
2. `message = "MECP/" + decimal(severity) + "/" + join(codes, " ")`. If
   `freetext` is non-null and not empty after trimming WS from both ends,
   append `" " + trimmed freetext`.
3. Add the `forbidden_character` and `over_limit` errors that
   [Validate](#validate) reports for `message`. (Its other errors would only
   repeat one from step 1.)
4. `byte_length` is the UTF-8 byte length of `message`. If there is any error,
   `message` is null: the encoder refuses (§6.1 Encoders). It never truncates.

## Validate

Whether a string may be transmitted. Input: a string `s`. Output:
`{valid, errors}`. Line endings are **not** stripped.

1. If `s` does not start with `MECP/`: errors `[missing_prefix]`, stop.
2. If the character at index 5 is not `0`–`3`: `invalid_severity`.
3. If the character at index 6 is not `/`: `missing_delimiter`.
4. If neither of those, and `s` has no forbidden character:
   - if `s[7..10]` is not a Code followed by a space or the end: `no_codes`;
   - otherwise, if `s` does not match `message.decode`: `invalid_freetext`.
5. If `s` contains a forbidden character: `forbidden_character`.
6. If the UTF-8 byte length of `s` is over 200: `over_limit`.
7. `valid = errors is empty`.

## Helpers

- `is_mecp(s)`: `s` starts with `MECP/`.
- `is_code(t)`: `t` is a Code.
- `is_beacon(codes)`, `is_beacon_ack(codes)`, `is_beacon_cancel(codes)`:
  `codes` contains `B01`, `B02` or `B03` respectively.
- `MAX_MESSAGE_BYTES = 200`; `MECP_VERSION`, the protocol version of the
  upstream pack.

## Error ids

| Id | Raised by |
|----|-----------|
| `missing_prefix` | validate |
| `invalid_severity` | encode, validate |
| `missing_delimiter` | validate |
| `no_codes` | encode, validate |
| `invalid_code` | encode |
| `invalid_freetext` | validate |
| `forbidden_character` | encode, validate |
| `over_limit` | encode, validate |

Errors are listed in the order of this table. Implementations may attach
human-readable messages, but conformance compares ids only.

## Choices the brief leaves open

| Area | Brief | MECP-polyglot |
|------|-------|---------------|
| Huge integers | Not covered (proposed: MUST NOT fail, SHOULD clamp); upstream's checker does not clamp | Clamp to 2147483647 |
| Oversize encode | Refuse, or truncate freetext at a grapheme boundary | Refuse; grapheme segmentation is not in every standard library |
| Oversize decode | MUST NOT reject | Accepted (C: up to `MECP_MAX_INPUT_BYTES`, default 256) |
| Extra boundary characters | Decoders MAY treat other non-ASCII space or punctuation as B | Exactly the B list, no more |
