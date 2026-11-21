# MECP work tracker

Open work across MECP clients and the spec. Last updated 2026-11-21.

Polyglot and the harness follow MECP [v1.4.1](https://github.com/mecp-org/MECP/releases/tag/v1.4.1)
(`eab9510`, 2026-11-20). Its only decode change is that R03 durations are not read from a decimal
fraction (`R03 1.5h`). Unreleased on `main`: rule 5 claim order
([mecp-org/MECP#53](https://github.com/mecp-org/MECP/pull/53), 2026-11-21) and the app designator.
Nothing below depends on them yet.

## TODO

- [ ] **M16 is missing from three clients' code tables.** M16 "Medical supply drop needed" was added
  in MECP 1.2.0 (brief §7). M16 messages still decode, but these apps can't label the code.
  Found by the code-table check in [conformance/](conformance/README.md#code-table). No issue or PR
  exists yet in any of the three repos (checked 2026-11-20).
  - [ ] MeshCore One ([Avi0n/MeshCoreOne](https://github.com/Avi0n/MeshCoreOne)): missing from all
    11 packs in `MC1Services/Sources/MC1Services/MECP/Languages/`; shown as "M16: Unknown code".
    Add a test to `MECPCatalogTests.swift` that checks every pack against the §7 list.
  - [ ] reticulum-mobile
    ([FreeTAKTeam/reticulum_mobile_emergency_management](https://github.com/FreeTAKTeam/reticulum_mobile_emergency_management)):
    missing from `MECP_EVENT_CODES` in `apps/mobile/src/utils/mecp.ts`; shown as a bare "M16".
    Could go in the code-table check in the conformance test from #360.
  - [ ] wadamesh ([ALLFATHER-BV/wadamesh](https://github.com/ALLFATHER-BV/wadamesh)): missing
    from `CODES` in `deploy/apps/mecp/1.0/mecp.lua`; shown as a bare "M16" and can't be picked when
    composing. There are no Lua app tests to add a check to.

## Fixes by client

Everything below is a failing vector from the [conformance harness](conformance/reports/SUMMARY.md)
run on 2026-11-21 (each client at its upstream default branch), grouped by root cause the way
[MeshCoreOne#494](https://github.com/Avi0n/MeshCoreOne/issues/494) is. Each top-level checkbox
is meant to be one small PR. The spec links are pinned to the commit #494 uses; the lines they
cite read the same in v1.4.1. Every item is something the 1.4.1 brief decides. Nothing here depends on the proposed
`spec-clarifications` changes.

### MeshCore One (Avi0n/MeshCoreOne): 209/256, see [#494](https://github.com/Avi0n/MeshCoreOne/issues/494)

The owner has agreed to take one PR per section of #494.

Both PRs so far are merged to `dev`, not yet released (`main` is v1.7.1). Tested at `dev`
`26460496fe`. All 47 remaining failures are in the timestamp and R03 sections.

- [x] Messages that aren't MECP are accepted: [#495](https://github.com/Avi0n/MeshCoreOne/pull/495) (merged 2026-11-19)
- [x] Trailing line endings: #495
- [x] Free text is changed: #495
- [x] Person count has no boundaries: [#496](https://github.com/Avi0n/MeshCoreOne/pull/496) (merged 2026-11-20)
- [ ] Timestamp accepts only `@HHMM` followed by a space (12 vectors):
  [#497](https://github.com/Avi0n/MeshCoreOne/pull/497) (open; all 12 pass, 216/249). Changes
  requested 2026-11-21: `@6:30 pax` makes MC1's token removal trap. The owner is reworking the
  removal code and will ping to merge it in. Only the unreleased claim order (#53) settles the
  `@6:30 pax` overlap; under v1.4.1 it is 06:30 and 30 people.
- [ ] R03 duration reads only a bare leading number (35 vectors, incl. 1.4.1 `R03 1.5h 45min`, `R03 hut.2h`)
- [ ] Language packs are a stale copy: byte-identical to mecp-org/MECP `languages/` at `ee17ef3`
  (2026-02-27). They were copied on 2026-11-10, one day before M16 merged upstream. Not in #494
  yet. Gaps that MC1 reads:
  - M16 missing from all 11 packs (see TODO above)
  - R03 text is now `ETA [time]` (was `[minutes]`). MC1 uses the bracket word as the unit, so
    copying the new packs gives "ETA 15 time"; `fillingSlots` and `MECPCatalogTests` need
    changing too. Best done with the R03 duration PR.
  - `@HHMM` is the sender's local time in 1.4.0, but `MECPCatalog.clockLine` hard-codes " UTC"

### reticulum-mobile (FreeTAKTeam/reticulum_mobile_emergency_management): 146/256

Tested at `6cf3db0978`. All fields are compared. [#360](https://github.com/FreeTAKTeam/reticulum_mobile_emergency_management/pull/360)
(merged 2026-11-21) adds the upstream vectors as a test, with the current failures in `KNOWN_FAILURES`.

- [ ] **Unknown codes make the message invalid.** `MECP/3/Z99 hello` and `MECP/1/Q42` are rejected
  because the category isn't known. [A well-formed unknown code is still a code](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L331).
- [ ] **Messages that aren't MECP are accepted** ([message pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L296-L303),
  [single line](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L305), [one trailing line ending](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L307)):
  - a leading space ` MECP/0/M01`, or no prefix at all: `M01 P05 48.65,20.13`
  - a lowercase first code: `MECP/1/t05 x`
  - a trailing space: `MECP/1/T05 `, `MECP/1/T05 help `
  - two spaces, a tab or an NBSP after the codes: `MECP/0/M01  M07`, `MECP/0/M01\tM07`
  - a line break inside: `\n`, `\r`, `\f`, U+0085, U+2028
  - more than one trailing line ending: `MECP/2/B03\n\n`, `\n\r`, `\r\n\r\n`
- [ ] **Lowercase codes are uppercased.** `MECP/3/L01 l06 late` gives codes `L01 L06` and free text
  `late`. [Codes are case-sensitive](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L329), so `l06` starts the free text.
- [ ] **Free text is changed.** Runs of spaces are collapsed, and tab, VT and NBSP become a space
  (`see  you   there` → `see you there`). [Free text is group 3, verbatim](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L299-L303).
- [ ] **Conventions are matched as whole tokens, not with the [boundary class B](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L337).**
  - Not decoded: `(4pax)`, `4Pax.`, `4pax,3pax`, `「4pax」`, `48.65,20.13،`, `at:48.65,20.13`,
    `48.65,20.13.`, `48.65,20.13,1200`, `@en.`, `~OK1ABC, ok`, `#base-camp,`, `(#tag)`, `1.5pax` (5).
  - Decoded but shouldn't be: `4pax\vwater` (VT is not in B).
- [ ] **The last match wins, and invalid matches aren't skipped.** `2pax 5pax` gives 5 (should be 2).
  `@2460 @1400 @1530` gives 15:30 (should be 14:00; timestamp only:
  [#368](https://github.com/FreeTAKTeam/reticulum_mobile_emergency_management/pull/368), open). [The first match by position wins, and a failed
  match is skipped](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L338-L339).
- [ ] **Person count:** `4 pax` isn't decoded ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L344-L351)).
- [ ] **GPS needs decimal points:** `48,20`, `0,0` and `2,5 km` are decoded as positions;
  `+48.8566, 2.3522` isn't ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L353-L362)).
- [ ] **Timestamp:** `@630`, `@6:30`, `@06:30`, `@123` and `@1430,` aren't decoded
  ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L364-L371)).
- [ ] **Language hint:** `@zh_CN`, `@zh-TW`, `@zh-Hans-CN` and `@sr-Latn-RS` aren't decoded
  ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L373-L380)).
- [ ] **Callsign:**
  - Not decoded: `~VK2/OK1ABC/P`, `~vk2/ok1abc/p`, `~DL/OK1ABC`.
  - Decoded but shouldn't be: `~OK1ABC-7`, `~W1AW-9` ([an SSID is not a callsign](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L382-L390)).
- [ ] **R03 duration** ([patterns](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L401-L418)):
  - Not decoded: `2h`, `1d`, `2d`, `48h`, `7d`, `1h30min`, `ETA45min`, `hut.2h`, and `2h` after `4pax`.
  - Wrong value: `1h 30min` gives 30 (should be 90), `2 h` gives 2 (120), `25h 3h` gives nothing (1500).
  - A bare number counts only as the first token, but `R03 1pax 45`, `R03 @1430 45` and `in 5 days`
    are read as minutes.
  - Zero isn't a duration: `0min` gives 0, and `0min 5min` gives 0 (should be 5).
- [ ] **Code table:** M16 is missing (TODO above). B04 isn't an MECP code:
  [mecp-org/MECP#50](https://github.com/mecp-org/MECP/issues/50) closed 2026-11-20, rejected in ADR 0006.

### wadamesh (ALLFATHER-BV/wadamesh): 187/256

Tested at `main` `3411a8fb3b`; [#894](https://github.com/ALLFATHER-BV/wadamesh/pull/894) is not merged.
The app only returns rendered text, so only validity, severity, pax, GPS and timestamp could be checked.

- [ ] **Messages that aren't MECP are accepted** ([message pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L296-L303),
  [single line](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L305), [one trailing line ending](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L307)):
  - `MECP/` is found anywhere in the line: ` MECP/0/M01`, `Alice: MECP/0/M01`
  - no codes `MECP/0/`; severity 4–9 `MECP/4/M01`; bad codes `MECP/1/t05 x`, `MECP/0/M011`
  - trailing spaces, two spaces, a tab or an NBSP after the codes
  - a line break inside (`\n`, `\r`, `\f`, U+0085, U+2028), or more than one trailing line ending
- [ ] **No [boundary class B](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L337).** Values must be whole space-separated tokens.
  - Not decoded: `(4pax)`, `4Pax.`, `4pax,3pax`, `4pax、水`, `「4pax」`, `4pax` followed by an NBSP,
    `48.65,20.13،`, `at:48.65,20.13`, `48.65,20.13.`, `48.65,20.13,1200`.
  - Decoded but shouldn't be: `4pax\vwater` (VT is not in B).
- [ ] **Person count** ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L344-L351)): `4 pax`, `4PAX` and `1.5pax` (5) aren't decoded.
  `0pax 2pax` gives 0 (should be 2: [skip invalid matches](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L339)).
- [ ] **GPS** ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L353-L362)):
  - No range check: `90.0001,0.0` is shown, and `95.0,200.0 47.3,8.5` gives the first pair.
  - No decimal point needed: `48,20`, `0,0` and `2,5 km` are shown as positions.
  - `+48.8566, 2.3522` isn't decoded.
- [ ] **Timestamp** ([pattern](https://github.com/mecp-org/MECP/blob/76bcc1b6cbb442cd3c0dc6c60e60e8549d4028ba/MECP_Comprehensive_Brief.md?plain=1#L364-L371)):
  - No range check: `@2400` and `@9999` are shown, and `@2460 @1400` gives 24:60 (should be 14:00).
  - `@630`, `@6:30`, `@06:30`, `@123` and `@1430,` aren't decoded.
- [ ] **Code table:** M16 is missing (TODO above).

### Nothing to fix

- **mesh-client** (Colorado-Mesh/mesh-client, `a9165a9906`, re-run 2026-11-21): 256/256, and all 109 codes.
- **meshcore-tak-bridge** (Colorado-Mesh/meshcore-tak-bridge `08a3a4d`, meshcore-kotlin `0207e42`,
  re-run 2026-11-21): 256/256, and all 109 codes. The maintainer moved `Mecp.kt` to MECP 1.4.1
  (meshcore-kotlin#17), which fixed all 18 earlier failures.
- **Meshcore-Solo:** the decoder is your own PR
  [#64](https://github.com/MarekZegare4/MeshCore-Solo/pull/64) (merged 2026-11-20); it isn't in the harness.
- **meshcore-open:** has no MECP support yet; see [#659](https://github.com/zjs81/meshcore-open/issues/659).

## Open pull requests

| Repo | PR | Title |
|---|---|---|
| Avi0n/MeshCoreOne | [#497](https://github.com/Avi0n/MeshCoreOne/pull/497) | fix: Decode MECP timestamps per MECPv1.4.1 |
| FreeTAKTeam/reticulum_mobile_emergency_management | [#368](https://github.com/FreeTAKTeam/reticulum_mobile_emergency_management/pull/368) | fix(mecp): keep the first timestamp in a message |
| ALLFATHER-BV/wadamesh | [#894](https://github.com/ALLFATHER-BV/wadamesh/pull/894) | apps: MECP sends P05 with the codes, not after the head count |

## Open issues

| Repo | Issue | Title |
|---|---|---|
| mecp-org/MECP | [#55](https://github.com/mecp-org/MECP/issues/55) | Documentation Structure |
| mecp-org/MECP | [#14](https://github.com/mecp-org/MECP/issues/14) | [Sug] Centralised Coordination Conversations |
| Avi0n/MeshCoreOne | [#494](https://github.com/Avi0n/MeshCoreOne/issues/494) | MECP 1.4.0 Support |
| MarekZegare4/MeshCore-Solo | [#63](https://github.com/MarekZegare4/MeshCore-Solo/issues/63) | [Feature Request] MECP Support |
| zjs81/meshcore-open | [#659](https://github.com/zjs81/meshcore-open/issues/659) | Feature Request: Add MECP Support |
