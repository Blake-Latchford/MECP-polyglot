"""MECP (Mesh Emergency Communication Protocol) encoder/decoder.

Implements spec/conformance.md of MECP-polyglot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

__all__ = [
    "MAX_MESSAGE_BYTES",
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
PREFIX = "MECP/"
_INT_MAX = 2147483647

# ECMAScript whitespace, for str.strip(). Python's own strip()/\s differ.
_WS_CHARS = (
    "\t\n\x0b\x0c\r \u00a0\u1680"
    + "".join(chr(c) for c in range(0x2000, 0x200B))
    + "\u2028\u2029\u202f\u205f\u3000\ufeff"
)

# Polyglot patterns: the same text in every implementation (spec "Patterns").
# _WS holds literal characters, written with host-language string escapes.
_WS = "[\t-\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]"
_END = "(?:" + _WS + "|$)"
_COUNT_RE = re.compile(r"([0-9]+)pax")
_GPS_RE = re.compile(r"(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)")
_ETA_RE = re.compile(r"^([0-9]+)" + _END)
_REF_RE = re.compile(r"#([A-Za-z0-9]{1,4})")
_LANG_RE = re.compile(r"@([a-z]{2})" + _END)
_TS_RE = re.compile(r"@([0-9]{4})" + _END)
_CALLSIGN_RE = re.compile(r"~([A-Za-z0-9]{1,9})" + _END)

_CODE_RE = re.compile(r"[A-Z][0-9]{2}\Z")


def _trim(s: str) -> str:
    return s.strip(_WS_CHARS)


def _to_int(digits: str) -> Optional[int]:
    value = int(digits)
    return value if value <= _INT_MAX else None


@dataclass(frozen=True)
class Gps:
    lat: float
    lon: float


@dataclass
class Extracted:
    count: Optional[int] = None
    gps: Optional[Gps] = None
    eta: Optional[int] = None
    reference: Optional[str] = None
    language: Optional[str] = None
    timestamp: Optional[str] = None
    callsign: Optional[str] = None


@dataclass
class Decoded:
    raw: str
    valid: bool = False
    severity: Optional[int] = None
    codes: list[str] = field(default_factory=list)
    is_drill: bool = False
    freetext: Optional[str] = None
    extracted: Extracted = field(default_factory=Extracted)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Encoded:
    message: str
    byte_length: int
    over_limit: bool
    warnings: list[str]


@dataclass
class Validation:
    valid: bool
    errors: list[str]
    warnings: list[str]


def is_mecp(s: str) -> bool:
    return s.startswith(PREFIX)


def is_code(token: str) -> bool:
    return _CODE_RE.match(token) is not None


def is_beacon(codes: Sequence[str]) -> bool:
    return "B01" in codes


def is_beacon_ack(codes: Sequence[str]) -> bool:
    return "B02" in codes


def is_beacon_cancel(codes: Sequence[str]) -> bool:
    return "B03" in codes


def _severity_at(s: str) -> Optional[int]:
    c = s[5:6]
    return int(c) if c in ("0", "1", "2", "3") else None


def _extract(text: str, codes: list[str], x: Extracted) -> None:
    if m := _COUNT_RE.search(text):
        x.count = _to_int(m[1])
    if m := _GPS_RE.search(text):
        lat, lon = float(m[1]), float(m[2])
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            x.gps = Gps(lat, lon)
    if "R03" in codes and (m := _ETA_RE.search(text)):
        x.eta = _to_int(m[1])
    if m := _REF_RE.search(text):
        x.reference = m[1]
    if m := _LANG_RE.search(text):
        x.language = m[1]
    if m := _TS_RE.search(text):
        if int(m[1][:2]) <= 23 and int(m[1][2:]) <= 59:
            x.timestamp = m[1]
    if m := _CALLSIGN_RE.search(text):
        x.callsign = m[1]


def decode(s: str) -> Decoded:
    r = Decoded(raw=s)
    if not is_mecp(s):
        return r

    r.severity = _severity_at(s)
    if r.severity is None:
        r.warnings.append("invalid_severity")
    if s[6:7] != "/":
        r.warnings.append("missing_delimiter")

    body = s[7:]
    if not _trim(body):
        r.valid = r.severity is not None
        if r.valid:
            r.warnings.append("no_codes")
        return r

    tokens = [t for t in body.split(" ") if t]
    i = 0
    while i < len(tokens) and is_code(tokens[i]):
        r.codes.append(tokens[i])
        i += 1
    if i < len(tokens):
        r.freetext = " ".join(tokens[i:])
        _extract(r.freetext, r.codes, r.extracted)

    r.is_drill = "D01" in r.codes or "D02" in r.codes
    r.valid = r.severity is not None
    return r


def encode(severity: int, codes: Sequence[str], freetext: Optional[str] = None) -> Encoded:
    warnings = []
    if severity not in (0, 1, 2, 3):
        warnings.append("invalid_severity")
    warnings.extend("invalid_code" for c in codes if not is_code(c))

    message = f"{PREFIX}{severity}/{' '.join(codes)}"
    if freetext is not None and (ft := _trim(freetext)):
        message += " " + ft
    message = message.rstrip(_WS_CHARS)

    byte_length = len(message.encode("utf-8"))
    over_limit = byte_length > MAX_MESSAGE_BYTES
    if over_limit:
        warnings.append("over_limit")
    return Encoded(message, byte_length, over_limit, warnings)


def validate(s: str) -> Validation:
    if not is_mecp(s):
        return Validation(False, ["missing_prefix"], [])
    errors, warnings = [], []
    if _severity_at(s) is None:
        errors.append("invalid_severity")
    if s[6:7] != "/":
        errors.append("missing_delimiter")
    if not _trim(s[7:]):
        warnings.append("no_codes")
    if len(s.encode("utf-8")) > MAX_MESSAGE_BYTES:
        warnings.append("over_limit")
    return Validation(not errors, errors, warnings)
