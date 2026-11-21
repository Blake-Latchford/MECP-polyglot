/// MECP (Mesh Emergency Communication Protocol) 1.4.0 encoder/decoder.
///
/// Implements MECP-polyglot `spec/conformance.md`. The regexes come from the
/// upstream pack via the generated `src/patterns.dart`.
library mecp;

import 'dart:convert' show utf8;

import 'src/patterns.dart' as p;

export 'src/patterns.dart' show mecpVersion;

const int maxMessageBytes = 200;
const String prefix = 'MECP/';
const int _intMax = 2147483647;

/// Error identifiers.
abstract final class Errors {
  static const missingPrefix = 'missing_prefix';
  static const invalidSeverity = 'invalid_severity';
  static const missingDelimiter = 'missing_delimiter';
  static const noCodes = 'no_codes';
  static const invalidCode = 'invalid_code';
  static const invalidFreetext = 'invalid_freetext';
  static const forbiddenCharacter = 'forbidden_character';
  static const overLimit = 'over_limit';
}

class Gps {
  final double lat;
  final double lon;
  const Gps(this.lat, this.lon);

  @override
  bool operator ==(Object other) => other is Gps && other.lat == lat && other.lon == lon;
  @override
  int get hashCode => Object.hash(lat, lon);
  @override
  String toString() => 'Gps($lat, $lon)';
}

class Extracted {
  int? pax;
  Gps? gps;

  /// `HH:MM`.
  String? timestamp;
  String? language;
  String? callsign;
  String? reference;

  /// Minutes.
  int? duration;
}

class Decoded {
  final String raw;
  bool valid = false;
  int? severity;
  final List<String> codes = [];
  bool isDrill = false;
  String? freetext;
  Extracted extracted = Extracted();
  Decoded(this.raw);
}

/// [message] is null when the encoder refused (there are errors).
class Encoded {
  final String? message;
  final int byteLength;
  final List<String> errors;
  const Encoded(this.message, this.byteLength, this.errors);
}

class Validation {
  final bool valid;
  final List<String> errors;
  const Validation(this.valid, this.errors);
}

/// ECMAScript whitespace: what [encode] trims from freetext.
bool _isWs(int c) =>
    (c >= 0x09 && c <= 0x0D) ||
    c == 0x20 ||
    c == 0xA0 ||
    c == 0x1680 ||
    (c >= 0x2000 && c <= 0x200A) ||
    c == 0x2028 ||
    c == 0x2029 ||
    c == 0x202F ||
    c == 0x205F ||
    c == 0x3000 ||
    c == 0xFEFF;

/// Never on the wire: line breaks (§6.1 Wire), BOM and Unicode whitespace (rule 8).
bool _isForbidden(int c) =>
    c == 0x0A ||
    c == 0x0C ||
    c == 0x0D ||
    c == 0x85 ||
    c == 0x2028 ||
    c == 0x2029 ||
    c == 0xFEFF ||
    c == 0xA0 ||
    c == 0x1680 ||
    (c >= 0x2000 && c <= 0x200A) ||
    c == 0x202F ||
    c == 0x205F ||
    c == 0x3000;

/// Rule 4: `(?:^|B)(?:pattern)(B|$)`. The right boundary is the last group so
/// a failed match can resume where its token ends (rule 6).
RegExp _wrap(String pattern) =>
    RegExp('(?:^|${p.boundaryPattern})(?:$pattern)(${p.boundaryPattern}|\$)');

final _message = RegExp(p.messagePattern);
final _pax = _wrap(p.paxPattern);
final _gps = _wrap(p.gpsPattern);
final _timestamp = _wrap(p.timestampPattern);
final _language = _wrap(p.languagePattern);
final _callsign = _wrap(p.callsignPattern);
final _reference = _wrap(p.referencePattern);
final _duration = [for (final d in p.durationPatterns) _wrap(d)];
final _code = RegExp(r'^[A-Z][0-9]{2}$');

bool _always(RegExpMatch m) => true;

/// Rules 5 and 6: the first match by position that passes [ok].
RegExpMatch? _firstValid(RegExp re, String text, [bool Function(RegExpMatch) ok = _always]) {
  var pos = 0;
  while (pos <= text.length) {
    // Searching from pos keeps ^ anchored at the start of the freetext.
    final m = re.allMatches(text, pos).firstOrNull;
    if (m == null) return null;
    if (ok(m)) return m;
    // Resume at the right boundary: B is one UTF-16 unit, or empty at $.
    pos = m.end - m.group(m.groupCount)!.length;
  }
  return null;
}

/// Parse an ASCII digit run, clamping huge values to the int32 maximum.
int _clampInt(String digits) {
  var v = 0;
  for (final c in digits.codeUnits) {
    v = v * 10 + (c - 0x30);
    if (v > _intMax) return _intMax;
  }
  return v;
}

int _clamp(int v) => v > _intMax ? _intMax : v;

// Duration kinds, in the order of p.durationPatterns.
const _hm = 0, _h = 1, _d = 3, _bare = 4;

int _minutes(int kind, RegExpMatch m) {
  final a = _clampInt(m.group(1)!);
  switch (kind) {
    case _hm:
      return _clamp(a * 60 + _clampInt(m.group(2)!));
    case _h:
      return _clamp(a * 60);
    case _d:
      return _clamp(a * 1440);
    default:
      return a; // min, bare
  }
}

bool _isDigit(int c) => c >= 0x30 && c <= 0x39;

/// Whether text[i] is `.` or `,` between two ASCII digits.
bool _decimalMark(String text, int i) =>
    i > 0 &&
    i < text.length - 1 &&
    (text[i] == '.' || text[i] == ',') &&
    _isDigit(text.codeUnitAt(i - 1)) &&
    _isDigit(text.codeUnitAt(i + 1));

bool _durationOk(String text, int kind, RegExpMatch m) {
  if (_minutes(kind, m) <= 0) return false;
  // Dart has no group offsets. The bare number's group 1 ends where the right
  // boundary group starts; group 2 must be absent, and a decimal mark taken
  // as that boundary also fails.
  if (kind == _bare) {
    return m.group(2) == null && !_decimalMark(text, m.end - m.group(m.groupCount)!.length);
  }
  // Not the fractional part of a decimal. Group 1 directly follows the left
  // boundary only when that boundary is `.` or `,` and no ETA prefix is used,
  // which is exactly when the boundary at m.start is a decimal mark.
  return !_decimalMark(text, m.start);
}

int? _durationOf(String text) {
  RegExpMatch? best;
  var bestMinutes = 0;
  for (var kind = 0; kind < _duration.length; kind++) {
    if (kind == _bare && best != null) break; // the bare number is only a fallback
    final m = _firstValid(_duration[kind], text, (m) => _durationOk(text, kind, m));
    // First by position; on a tie the earlier pattern (already in best) wins.
    if (m != null && (best == null || m.start < best.start)) {
      best = m;
      bestMinutes = _minutes(kind, m);
    }
  }
  return best == null ? null : bestMinutes;
}

bool _gpsOk(RegExpMatch m) {
  final lat = double.parse(m.group(1)!), lon = double.parse(m.group(2)!);
  return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
}

// ASCII-only case folding (rule 5): never locale-sensitive.
String _asciiLower(String s) =>
    String.fromCharCodes(s.codeUnits.map((c) => c >= 0x41 && c <= 0x5A ? c + 32 : c));
String _asciiUpper(String s) =>
    String.fromCharCodes(s.codeUnits.map((c) => c >= 0x61 && c <= 0x7A ? c - 32 : c));

Extracted _extract(String text, List<String> codes) {
  final x = Extracted();
  RegExpMatch? m;
  if ((m = _firstValid(_pax, text)) != null) x.pax = _clampInt(m!.group(1)!);
  if ((m = _firstValid(_gps, text, _gpsOk)) != null) {
    x.gps = Gps(double.parse(m!.group(1)!), double.parse(m.group(2)!));
  }
  if ((m = _firstValid(_timestamp, text)) != null) {
    x.timestamp = '${_clampInt(m!.group(1)!).toString().padLeft(2, '0')}:${m.group(2)}';
  }
  if ((m = _firstValid(_language, text)) != null) {
    x.language = _asciiLower(m!.group(1)!).replaceAll('_', '-');
  }
  if ((m = _firstValid(_callsign, text, (m) => m.group(1)!.length <= 12)) != null) {
    x.callsign = _asciiUpper(m!.group(1)!);
  }
  if ((m = _firstValid(_reference, text)) != null) x.reference = m!.group(1);
  if (codes.contains(p.durationScope)) x.duration = _durationOf(text);
  return x;
}

bool isMecp(String s) => s.startsWith(prefix);
bool isCode(String token) => _code.hasMatch(token);
bool isBeacon(List<String> codes) => codes.contains('B01');
bool isBeaconAck(List<String> codes) => codes.contains('B02');
bool isBeaconCancel(List<String> codes) => codes.contains('B03');

String _stripLineEnding(String s) {
  if (s.endsWith('\r\n')) return s.substring(0, s.length - 2);
  if (s.endsWith('\n') || s.endsWith('\r')) return s.substring(0, s.length - 1);
  return s;
}

Decoded decode(String s) {
  final r = Decoded(s);
  final env = _message.firstMatch(_stripLineEnding(s));
  if (env == null) return r;
  r.valid = true;
  r.severity = int.parse(env.group(1)!);
  r.codes.addAll(env.group(2)!.split(' '));
  r.isDrill = r.codes.contains('D01') || r.codes.contains('D02');
  r.freetext = env.group(3);
  if (r.freetext != null) r.extracted = _extract(r.freetext!, r.codes);
  return r;
}

/// Whether [s] may be transmitted as an MECP 1.4.0 message.
Validation validate(String s) {
  if (!isMecp(s)) return const Validation(false, [Errors.missingPrefix]);
  final errors = <String>[];
  final severityOk = s.length > 5 && '0123'.contains(s[5]);
  final delimOk = s.length > 6 && s[6] == '/';
  if (!severityOk) errors.add(Errors.invalidSeverity);
  if (!delimOk) errors.add(Errors.missingDelimiter);
  final forbidden = s.runes.any(_isForbidden);
  if (severityOk && delimOk && !forbidden) {
    if (s.length < 10 || !isCode(s.substring(7, 10)) || (s.length > 10 && s[10] != ' ')) {
      errors.add(Errors.noCodes);
    } else if (!_message.hasMatch(s)) {
      errors.add(Errors.invalidFreetext);
    }
  }
  if (forbidden) errors.add(Errors.forbiddenCharacter);
  if (utf8.encode(s).length > maxMessageBytes) errors.add(Errors.overLimit);
  return Validation(errors.isEmpty, errors);
}

String _trim(String s) {
  final r = s.runes.toList();
  var a = 0, b = r.length;
  while (a < b && _isWs(r[a])) {
    a++;
  }
  while (b > a && _isWs(r[b - 1])) {
    b--;
  }
  return String.fromCharCodes(r.sublist(a, b));
}

/// Build a message. With any error, [Encoded.message] is null: the encoder refuses.
Encoded encode(int severity, List<String> codes, [String? freetext]) {
  final errors = <String>[];
  if (severity < 0 || severity > 3) errors.add(Errors.invalidSeverity);
  if (codes.isEmpty) errors.add(Errors.noCodes);
  for (final c in codes) {
    if (!isCode(c)) errors.add(Errors.invalidCode);
  }
  var message = '$prefix$severity/${codes.join(' ')}';
  final ft = freetext == null ? '' : _trim(freetext);
  if (ft.isNotEmpty) message += ' $ft';
  // Wire errors; the other validate errors only repeat an input error.
  errors.addAll(validate(message)
      .errors
      .where((e) => e == Errors.forbiddenCharacter || e == Errors.overLimit));
  return Encoded(errors.isEmpty ? message : null, utf8.encode(message).length, errors);
}
