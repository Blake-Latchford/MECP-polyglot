# MECP 1.4.1 decode conformance

Test vectors for the MECP 1.4.1 message format (protocol brief §6.1), plus a
harness that runs them against several MECP clients and reports where each
client departs from the spec, and where clients disagree with each other.

## For implementors

Use [`vectors/decode-1.4.1.json`](vectors/decode-1.4.1.json) in your own test
suite. Each case has an `id`, the spec `clause` it tests, an `input` string and
an `expect` record:

| Field | Type | Meaning |
|---|---|---|
| `valid` | bool | The input matches the §6.1 message pattern, after removing a trailing `\r?\n?` (so CRLF, CR or LF) |
| `severity` | 0–3 | |
| `codes` | string[] | The code section, in order. Unknown well-formed codes are kept. |
| `freetext` | string or null | Regex group 3, verbatim (inner spaces are kept) |
| `pax` | int or null | Person count |
| `gps` | `{lat, lon}` or null | Compare with a tolerance of 1e-9 |
| `timestamp` | `"HH:MM"` or null | |
| `language` | string or null | Lowercase, `_` normalised to `-` |
| `callsign` | string or null | Uppercase |
| `reference` | string or null | Compare by identity: case-insensitive, `_` equals `-` |
| `duration` | int (minutes) or null | Only when `R03` is a code |

When `expect.valid` is false, compare only `valid`. Otherwise compare every
field you expose. `null` means "not present" and is tested as deliberately as
the values are. How you represent a field is up to you (`1430` vs `14:30`).
What it means is not.

Every expectation is written by hand from the brief, never generated from a
client. If you think a vector is wrong, open an issue and cite the clause.
Inputs where the brief is ambiguous are left out and listed in
[SPEC-ISSUES.md](SPEC-ISSUES.md).

## Code table

[`vectors/codes-1.4.1.json`](vectors/codes-1.4.1.json) lists the 109 codes of brief §7, in order.
Unknown well-formed codes still decode (Codes rule 5), so the decode vectors cannot tell whether a
client knows a code. A client that is missing one shows it unlabelled. Check your code table, in every
language you ship, against this list.

## Running the harness

```sh
python3 conformance/vectors/build.py --check   # vectors match build.py and the reference
python3 conformance/harness/run.py --build     # build adapters, run all clients
```

The client checkouts are expected next to this repository (override with
`MECP_CLIENTS_DIR`). Requirements: Python ≥ 3.10, Node + npm (TypeScript
clients, via tsx), Lua 5.4 (wadamesh), a JDK, which Gradle fetches if
missing (meshcore-tak-bridge), and Docker (meshcore-one, built with the
official `swift` image). After pulling meshcore-tak-bridge, run
`git submodule update`: its decoder lives in the `meshcore-kotlin` submodule.

Besides the hand-written vectors, every run includes the 70 upstream cases
from mecp-org/MECP `freetext/tests.json` (copied unchanged into
[`../upstream/`](../upstream/)). They appear as `up.NN` with clause
`upstream: …` and compare only validity and the extracted fields.

Reports go to [`reports/`](reports/):

- `SUMMARY.md`: pass counts, clients × clauses, with the commit of each client tested.
- `<client>.md`: every failing vector for that client, grouped by clause. This is
  the file to hand to that client's maintainers.
- `DISAGREEMENTS.md`: cases where clients give each other different answers.
  This is what users experience as "the same message reads differently on
  different apps".
- `results.json`: raw adapter output.

[`findings/`](findings/) holds a hand-written summary per non-conformant client. Each groups the
failures into root causes, with representative inputs and the user-visible impact. These are the files
to hand to maintainers; the generated `reports/` hold the full evidence.

## How clients are driven

[`clients.json`](clients.json) lists each client: its checkout, an optional
build step, the adapter command, and which record fields it exposes. An
adapter reads `id<TAB>hex(utf-8 input)` lines on stdin and writes one JSON
object per line: `{"id": …, "result": {record}}`, or `{"id": …, "error": "…"}`.
A client's optional `codes_cmd` prints the codes in the client's own code table as a JSON
array. The harness compares that with `vectors/codes-1.4.1.json` and reports missing codes and
codes that are not in §7.

Adapters import each client's own decoder from its checkout, so no client code
is copied into this MIT-licensed repository. An adapter may convert
representation (field names, `HHMM` → `HH:MM`). It must never apply protocol
logic, because then the harness would be testing the adapter.

| Client | Adapter | Entry point |
|---|---|---|
| mesh-client | [ts/adapter.mts](adapters/ts/adapter.mts) | `mecpMessages.ts` `tryParseMecp()` |
| reticulum-mobile | [ts/adapter.mts](adapters/ts/adapter.mts) | `apps/mobile/src/utils/mecp.ts` `decodeMecpMessage()` |
| meshcore-tak-bridge | [meshcore-tak-bridge/](adapters/meshcore-tak-bridge/) | `Mecp.parse()` |
| wadamesh | [wadamesh/adapter.lua](adapters/wadamesh/adapter.lua) | `mecp.lua` local `decode()`, recovered from rendered text |
| meshcore-one | [meshcore-one/](adapters/meshcore-one/) | `MECPDecode.decode()` and `MECPMessage`'s derived fields, compiled from the checkout in the `swift` Docker image |
| reference | [reference/adapter.py](adapters/reference/adapter.py) | [`reference/record.py`](reference/record.py): MECP-polyglot's Python codec, built on the upstream patterns and checked against upstream's `check-freetext.mjs`, used to cross-check the vectors |
