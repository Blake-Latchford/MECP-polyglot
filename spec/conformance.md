# MECP-polyglot Conformance Rules

This document pins down the exact behaviour every MECP-polyglot codec must
implement. The wire format comes from the
[MECP protocol brief](https://github.com/mecp-org/MECP/blob/main/MECP_Comprehensive_Brief.md)
(§6.1). Where the brief is loose, behaviour follows the TypeScript reference
engine [`@mecp/engine`](https://github.com/mecp-org/mecp-app/tree/main/engine).
Deliberate divergences from that engine are listed in
[Divergences from @mecp/engine](#divergences-from-mecpengine).

The shared test vectors in [`../vectors/mecp-vectors.json`](../vectors/mecp-vectors.json)
are normative: an implementation conforms when it passes every vector.

## Definitions

- **String**: a sequence of Unicode code points. On the wire it is UTF-8.
  All indexing in this document counts **code points**, not bytes or UTF-16
  code units.
- **Digit**: ASCII `0`–`9` only. Unicode digits do not count. (Python's and
  Rust's `\d` are Unicode-aware by default, so use `[0-9]`.)
- **Alnum**: ASCII `A`–`Z`, `a`–`z`, `0`–`9`.
- **Whitespace (WS)**: the ECMAScript whitespace set:
  U+0009 TAB, U+000A LF, U+000B VT, U+000C FF, U+000D CR, U+0020 SPACE,
  U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000,
  U+FEFF. This differs from Python `str.strip()`, Go RE2's `\s` and C
  `isspace()`, so define it explicitly.
- **trim(s)**: `s` with leading and trailing WS removed.
- **Boundary**: a position followed by a WS code point or by the end of the
  string. (In regex form: `(?:WS|$)`; see [Patterns](#patterns).)
- **Code**: a token matching exactly `[A-Z][0-9][0-9]`.
- **Integer field limit**: `count` and `eta` are integers in
  `0..2147483647`. A digit run whose value exceeds 2147483647 yields `null`.

Patterns below are given as regexes with leftmost-first semantics. "Search"
means find the match with the **lowest start index**. Only that first match is
considered: if it later fails a range check, the field is `null` and no
further matches are tried.

## Decode

Input: a string `s`. Output: a `Decoded` record:

| Field | Type | Default |
|-------|------|---------|
| `valid` | bool | false |
| `severity` | int 0–3 or null | null |
| `codes` | list of string | [] |
| `is_drill` | bool | false |
| `freetext` | string or null | null |
| `extracted.count` | int or null | null |
| `extracted.gps` | `{lat, lon}` (float64) or null | null |
| `extracted.eta` | int or null | null |
| `extracted.reference` | string or null | null |
| `extracted.language` | string or null | null |
| `extracted.timestamp` | string or null | null |
| `extracted.callsign` | string or null | null |
| `warnings` | list of warning ids | [] |

Steps:

1. **Prefix.** If `s` does not start with `MECP/` (case-sensitive), return the
   defaults.
2. **Severity.** Let `c5` be the code point at index 5 (none if `s` is too
   short). If `c5` is one of `0 1 2 3`, set `severity` to its value. Otherwise
   add warning `invalid_severity` and continue.
3. **Delimiter.** If the code point at index 6 is not `/` (or does not exist),
   add warning `missing_delimiter` and continue.
4. **Body.** `body` is `s` from code point index 7 to the end (empty if `s` is
   shorter). If `trim(body)` is empty: set `valid = (severity != null)`; if
   `valid`, add warning `no_codes`; return.
5. **Tokenise.** Split `body` on U+0020 SPACE **only** and drop empty tokens.
   Other WS stays inside tokens. Walk the tokens left to right: while a token is
   a Code, append it to `codes`. The first non-Code token and every token after
   it, joined with a single U+0020, form `freetext`. Code-like tokens after
   that point stay in `freetext`. If every token is a Code, `freetext` stays
   null.
6. **Extract** from `freetext` (use `""` when it is null):
   - `count`: search `([0-9]+)pax`. The value is the decimal integer of group 1
     (subject to the integer field limit).
   - `gps`: search `(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)`. Parse both groups as
     float64 (round to nearest). If `-90 ≤ lat ≤ 90` and `-180 ≤ lon ≤ 180`,
     set `gps`; otherwise it stays null.
   - `eta`: only if `codes` contains `R03` and `freetext` is non-null: match
     `^([0-9]+)Boundary` anchored at index 0 of `freetext`. The value is the
     integer of group 1 (subject to the limit).
   - `reference`: search `#([A-Za-z0-9]{1,4})`. Greedy, with **no** boundary,
     so `#basecamp` yields `base`.
   - `language`: search `@([a-z]{2})Boundary`.
   - `timestamp`: search `@([0-9]{4})Boundary`. Let `hh` be the first two digits
     and `mm` the last two. If `hh ≤ 23` and `mm ≤ 59`, set `timestamp` to the
     four-digit string.
   - `callsign`: search `~([A-Za-z0-9]{1,9})Boundary`. The alnum run after `~`
     must be 1–9 long and end at a Boundary.
7. **Drill.** `is_drill` is true if `codes` contains `D01` or `D02`. (`D03` and
   `D04` do not set it.)
8. **Valid.** `valid = (severity != null)`.

Unknown but well-formed codes (e.g. `Z99`) are accepted as codes. Checking
codes against the code table is a localisation concern, not a decode concern.

## Patterns

The extraction rules in Decode step 6 are written so that the same regex text
works in Python `re`, Go `regexp`, Rust `regex`/`regex-lite` and ECMAScript
(Dart `RegExp`). Implementations with a regex engine should use these exact
patterns. Implementations without one (C) match them by hand.

```text
WS        = [\t-\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]
END       = (?:WS|$)
COUNT     = ([0-9]+)pax
GPS       = (-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)
ETA       = ^([0-9]+)END
REFERENCE = #([A-Za-z0-9]{1,4})
LANGUAGE  = @([a-z]{2})END
TIMESTAMP = @([0-9]{4})END
CALLSIGN  = ~([A-Za-z0-9]{1,9})END
```

Portability rules:

- **Build `WS` from literal characters.** The `\t`, `\r` and `\uXXXX` in `WS`
  are host-language *string* escapes, not regex escapes. Each language writes
  them in its own string-literal syntax (Rust: `\u{a0}`), so the regex engine
  sees the characters themselves. Regex escape syntax for code points differs
  between engines (`\x{a0}` in Go, `\u00a0` in ECMAScript), and `\s` means
  something different in each one.
- **Use `$` without multiline mode.** In Go, Rust and ECMAScript it matches only
  at the end of the text. Python's `$` also matches just before a final `\n`,
  but `\n` is in `WS`, so `END` matches there anyway and the result is the same.
- **Use ASCII ranges, never `\d` or `\w`.** They are Unicode-aware in some
  engines.
- **Match code units or code points.** Every character a pattern can match is
  in the BMP, so engines that work on UTF-16 code units (Dart, ECMAScript) give
  the same results as those that work on code points.
- **Search for the leftmost match** (Python `re.search`, Go
  `FindStringSubmatch`, Rust `captures`, Dart `firstMatch`) and use capture
  group 1. Only the first match is considered (see above).

## Encode

Input: `severity` (integer), `codes` (list of strings), `freetext` (string or
null). Output: `{message, byte_length, over_limit, warnings}`.

1. If `severity` is not 0–3, add warning `invalid_severity`. Encoding still
   proceeds using the decimal form of the integer.
2. For each code that is not a Code, add warning `invalid_code`, once per bad
   code and in order. The code is still emitted.
3. `message = "MECP/" + decimal(severity) + "/" + join(codes, " ")`.
4. If `freetext` is non-null and `trim(freetext)` is non-empty, append
   `" " + trim(freetext)`.
5. Strip trailing WS from `message`.
6. `byte_length` is the UTF-8 byte length of `message`.
   `over_limit = byte_length > 200`. If over the limit, add warning
   `over_limit`.

## Validate

Input: a string `s`. Output: `{valid, errors, warnings}`.

1. If `s` does not start with `MECP/`: errors `[missing_prefix]`, return.
2. If the code point at index 5 is not `0`–`3`: error `invalid_severity`.
3. If the code point at index 6 is not `/`: error `missing_delimiter`.
4. If `trim(body)` is empty (body as in Decode step 4): warning `no_codes`.
5. If the UTF-8 byte length of `s` > 200: warning `over_limit`.
6. `valid = errors is empty`.

## Helpers

- `is_mecp(s)`: `s` starts with `MECP/`.
- `is_beacon(codes)`, `is_beacon_ack(codes)`, `is_beacon_cancel(codes)`:
  `codes` contains `B01`, `B02` or `B03` respectively.
- `MAX_MESSAGE_BYTES = 200`.

## Warning and error ids

| Id | Raised by |
|----|-----------|
| `invalid_severity` | decode (warning), encode (warning), validate (error) |
| `missing_delimiter` | decode (warning), validate (error) |
| `missing_prefix` | validate (error) |
| `no_codes` | decode (warning), validate (warning) |
| `invalid_code` | encode (warning) |
| `over_limit` | encode (warning), validate (warning) |

Implementations may attach human-readable messages, but conformance compares
ids only, in order.

## Divergences from @mecp/engine

| Area | @mecp/engine | MECP-polyglot | Why |
|------|--------------|---------------|-----|
| Indexing | UTF-16 code units | Code points | Same for everything except astral-plane characters at index 5 or 6. Code points are portable to C, Rust and Go. |
| Integer overflow | `parseInt` → float, loses precision | `null` above 2147483647 | Deterministic and safe on firmware. |
| Warnings | Free-text strings | Stable ids | Comparable across languages. |
