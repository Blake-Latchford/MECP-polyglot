"""MECP (Mesh Emergency Communication Protocol) encoder/decoder.

Implements spec/conformance.md of MECP-polyglot (MECP protocol 1.4.0). The
regexes come from the upstream pack via the generated module _patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from . import _patterns as P

__all__ = [
    "MAX_MESSAGE_BYTES",
    "MECP_VERSION",
    "PREFIX",
    "Gps",
    "Extracted",
    "Decoded",
    "Encoded",
    "Validation",
    "decode",
    "encode",
    "validate",
    "is_mecp",
    "is_code",
    "is_beacon",
    "is_beacon_ack",
    "is_beacon_cancel",
]

MAX_MESSAGE_BYTES = 200
MECP_VERSION = P.MECP_VERSION
PREFIX = "MECP/"
_INT_MAX = 2147483647

# ECMAScript whitespace: what encode() trims from freetext.
_WS_CHARS = (
    "\t\n\x0b\x0c\r   "
    + "".join(chr(c) for c in range(0x2000, 0x200B))
    + "    　﻿"
)
# Never on the wire: line breaks (§6.1 Wire), BOM and Unicode whitespace (rule 8).
_FORBIDDEN = re.compile(
    "[\n\x0c\r\u0085  ﻿   -   　]"
)

_MESSAGE = re.compile(P.MESSAGE)
_CODE = re.compile(r"[A-Z][0-9]{2}")


def _wrap(pattern: str) -> re.Pattern:
    # Rule 4: (?:^|B)(?:pattern)(?:B|$). The right boundary is captured as the
    # last group so a failed match can resume where its token ends (rule 6).
    return re.compile(f"(?:^|{P.BOUNDARY})(?:{pattern})({P.BOUNDARY}|$)")


_PAX = _wrap(P.PAX)
_GPS = _wrap(P.GPS)
_TIMESTAMP = _wrap(P.TIMESTAMP)
_LANGUAGE = _wrap(P.LANGUAGE)
_CALLSIGN = _wrap(P.CALLSIGN)
_REFERENCE = _wrap(P.REFERENCE)
_DURATION = tuple(_wrap(p) for p in P.DURATION)


def _clamp_int(digits: str) -> int:
    # Huge digit runs must not fail; they clamp to the int32 maximum.
    return min(int(digits), _INT_MAX) if len(digits) <= 12 else _INT_MAX


@dataclass(frozen=True)
class Gps:
    lat: float
    lon: float


@dataclass
class Extracted:
    pax: Optional[int] = None
    gps: Optional[Gps] = None
    timestamp: Optional[str] = None
    language: Optional[str] = None
    callsign: Optional[str] = None
    reference: Optional[str] = None
    duration: Optional[int] = None


@dataclass
class Decoded:
    raw: str
    valid: bool = False
    severity: Optional[int] = None
    codes: list[str] = field(default_factory=list)
    is_drill: bool = False
    freetext: Optional[str] = None
    extracted: Extracted = field(default_factory=Extracted)


@dataclass
class Encoded:
    message: Optional[str]
    byte_length: int
    errors: list[str]


@dataclass
class Validation:
    valid: bool
    errors: list[str]


def is_mecp(s: str) -> bool:
    return s.startswith(PREFIX)


def is_code(token: str) -> bool:
    return _CODE.fullmatch(token) is not None


def is_beacon(codes: Sequence[str]) -> bool:
    return "B01" in codes


def is_beacon_ack(codes: Sequence[str]) -> bool:
    return "B02" in codes


def is_beacon_cancel(codes: Sequence[str]) -> bool:
    return "B03" in codes


def _first_valid(rx: re.Pattern, text: str,
                 ok: Callable[[re.Match], bool] = lambda m: True) -> Optional[re.Match]:
    """Rules 5 and 6: the first match by position that passes validation."""
    pos = 0
    while (m := rx.search(text, pos)) is not None:
        if ok(m):
            return m
        pos = max(m.start(m.lastindex), m.start() + 1)
    return None


def _gps_ok(m: re.Match) -> bool:
    return -90 <= float(m[1]) <= 90 and -180 <= float(m[2]) <= 180


# Duration kinds, in the order of P.DURATION.
_KINDS = ("hm", "h", "min", "d", "bare")


def _minutes(kind: str, m: re.Match) -> int:
    a = _clamp_int(m[1])
    if kind == "hm":
        return min(a * 60 + _clamp_int(m[2]), _INT_MAX)
    if kind == "h":
        return min(a * 60, _INT_MAX)
    if kind == "d":
        return min(a * 1440, _INT_MAX)
    return a  # min, bare


_DIGITS = "0123456789"


def _decimal_mark(text: str, i: int) -> bool:
    """True if text[i] is `.` or `,` between two ASCII digits."""
    return (0 < i < len(text) - 1 and text[i] in ".,"
            and text[i - 1] in _DIGITS and text[i + 1] in _DIGITS)


def _duration_ok(kind: str, m: re.Match) -> bool:
    if _minutes(kind, m) <= 0:
        return False
    if kind == "bare":
        # Group 2 absent, and a decimal mark taken as the boundary also fails.
        return m[2] is None and not _decimal_mark(m.string, m.end(1))
    # Not the fractional part of a decimal.
    return not _decimal_mark(m.string, m.start(1) - 1)


def _duration(text: str) -> Optional[int]:
    best: Optional[tuple[int, int]] = None  # (match start, minutes)
    for kind, rx in zip(_KINDS, _DURATION):
        if kind == "bare" and best:
            break  # the bare number is only a fallback
        m = _first_valid(rx, text, lambda m, k=kind: _duration_ok(k, m))
        # First by position; on a tie the earlier pattern (already in best) wins.
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), _minutes(kind, m))
    return best[1] if best else None


def _extract(text: str, codes: list[str]) -> Extracted:
    x = Extracted()
    if m := _first_valid(_PAX, text):
        x.pax = _clamp_int(m[1])
    if m := _first_valid(_GPS, text, _gps_ok):
        x.gps = Gps(float(m[1]), float(m[2]))
    if m := _first_valid(_TIMESTAMP, text):
        x.timestamp = f"{int(m[1]):02d}:{m[2]}"
    if m := _first_valid(_LANGUAGE, text):
        x.language = m[1].lower().replace("_", "-")
    if m := _first_valid(_CALLSIGN, text, lambda m: len(m[1]) <= 12):
        x.callsign = m[1].upper()
    if m := _first_valid(_REFERENCE, text):
        x.reference = m[1]
    if P.DURATION_SCOPE in codes:
        x.duration = _duration(text)
    return x


def _strip_line_ending(s: str) -> str:
    if s.endswith("\r\n"):
        return s[:-2]
    if s.endswith(("\n", "\r")):
        return s[:-1]
    return s


def decode(s: str) -> Decoded:
    r = Decoded(raw=s)
    env = _MESSAGE.fullmatch(_strip_line_ending(s))
    if env is None:
        return r
    r.valid = True
    r.severity = int(env[1])
    r.codes = env[2].split(" ")
    r.is_drill = "D01" in r.codes or "D02" in r.codes
    r.freetext = env[3]
    if r.freetext is not None:
        r.extracted = _extract(r.freetext, r.codes)
    return r


def validate(s: str) -> Validation:
    if not is_mecp(s):
        return Validation(False, ["missing_prefix"])
    errors = []
    severity_ok = s[5:6] in ("0", "1", "2", "3")
    if not severity_ok:
        errors.append("invalid_severity")
    if s[6:7] != "/":
        errors.append("missing_delimiter")
    forbidden = _FORBIDDEN.search(s) is not None
    if severity_ok and s[6:7] == "/" and not forbidden:
        if not (is_code(s[7:10]) and s[10:11] in ("", " ")):
            errors.append("no_codes")
        elif not _MESSAGE.fullmatch(s):
            errors.append("invalid_freetext")
    if forbidden:
        errors.append("forbidden_character")
    if len(s.encode("utf-8")) > MAX_MESSAGE_BYTES:
        errors.append("over_limit")
    return Validation(not errors, errors)


# validate() errors that encode() adds to its own input checks. The others
# (no_codes, invalid_freetext, ...) only repeat an input error already reported.
_WIRE_ERRORS = ("forbidden_character", "over_limit")


def encode(severity: int, codes: Sequence[str], freetext: Optional[str] = None) -> Encoded:
    """Build a message. If there is any error, `message` is None: the encoder refuses."""
    errors = []
    if severity not in (0, 1, 2, 3):
        errors.append("invalid_severity")
    if not codes:
        errors.append("no_codes")
    errors.extend("invalid_code" for c in codes if not is_code(c))

    message = f"{PREFIX}{severity}/{' '.join(codes)}"
    if freetext is not None and (ft := freetext.strip(_WS_CHARS)):
        message += " " + ft
    errors += [e for e in validate(message).errors if e in _WIRE_ERRORS]
    return Encoded(None if errors else message, len(message.encode("utf-8")), errors)
