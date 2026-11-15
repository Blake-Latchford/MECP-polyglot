/// MECP (Mesh Emergency Communication Protocol) encoder/decoder.
///
/// Implements MECP-polyglot `spec/conformance.md`.
library mecp;

const int maxMessageBytes = 200;
const String prefix = 'MECP/';
const int _intFieldMax = 2147483647;

/// Warning and error identifiers.
abstract final class Warnings {
  static const missingPrefix = 'missing_prefix';
  static const invalidSeverity = 'invalid_severity';
  static const missingDelimiter = 'missing_delimiter';
  static const noCodes = 'no_codes';
  static const invalidCode = 'invalid_code';
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
  int? count;
  Gps? gps;
  int? eta;
  String? reference;
  String? language;
  String? timestamp;
  String? callsign;
}

class Decoded {
  final String raw;
  bool valid = false;
  int? severity;
  final List<String> codes = [];
  bool isDrill = false;
  String? freetext;
  final Extracted extracted = Extracted();
  final List<String> warnings = [];
  Decoded(this.raw);
}

class Encoded {
  final String message;
  final int byteLength;
  final bool overLimit;
  final List<String> warnings;
  const Encoded(this.message, this.byteLength, this.overLimit, this.warnings);
}

class Validation {
  final bool valid;
  final List<String> errors;
  final List<String> warnings;
  const Validation(this.valid, this.errors, this.warnings);
}

/// ECMAScript whitespace. All members are in the BMP, so a single UTF-16
/// code unit check is exact. (Dart's String.trim also strips U+0085.)
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

String _trimEnd(String s) {
  var e = s.length;
  while (e > 0 && _isWs(s.codeUnitAt(e - 1))) {
    e--;
  }
  return s.substring(0, e);
}

String _trim(String s) {
  var b = 0;
  while (b < s.length && _isWs(s.codeUnitAt(b))) {
    b++;
  }
  return _trimEnd(s.substring(b));
}

bool _isDigit(int c) => c >= 0x30 && c <= 0x39;

// Polyglot patterns: the same text in every implementation (spec "Patterns").
// _ws holds literal characters, written with host-language string escapes.
// Dart regexps match UTF-16 code units; every WS character is in the BMP.
const _ws = '[\t-\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]';
const _end = '(?:$_ws|\$)';
final _countRe = RegExp(r'([0-9]+)pax');
final _gpsRe = RegExp(r'(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)');
final _etaRe = RegExp(r'^([0-9]+)' + _end);
final _referenceRe = RegExp(r'#([A-Za-z0-9]{1,4})');
final _languageRe = RegExp(r'@([a-z]{2})' + _end);
final _timestampRe = RegExp(r'@([0-9]{4})' + _end);
final _callsignRe = RegExp(r'~([A-Za-z0-9]{1,9})' + _end);

/// Capture group 1 of the leftmost match of [re] in [s], or null.
String? _find(RegExp re, String s) => re.firstMatch(s)?.group(1);

int? _toInt(String digits) {
  final v = int.tryParse(digits);
  return v != null && v <= _intFieldMax ? v : null;
}

/// UTF-16 length of the code point at index i.
int _cpLen(String s, int i) {
  final c = s.codeUnitAt(i);
  if (c >= 0xD800 && c <= 0xDBFF && i + 1 < s.length) {
    final d = s.codeUnitAt(i + 1);
    if (d >= 0xDC00 && d <= 0xDFFF) return 2;
  }
  return 1;
}

int _utf8Length(String s) {
  var n = 0;
  for (final r in s.runes) {
    n += r < 0x80 ? 1 : r < 0x800 ? 2 : r < 0x10000 ? 3 : 4;
  }
  return n;
}

bool isMecp(String s) => s.startsWith(prefix);

bool isCode(String t) =>
    t.length == 3 &&
    t.codeUnitAt(0) >= 0x41 &&
    t.codeUnitAt(0) <= 0x5A &&
    _isDigit(t.codeUnitAt(1)) &&
    _isDigit(t.codeUnitAt(2));

bool isBeacon(List<String> codes) => codes.contains('B01');
bool isBeaconAck(List<String> codes) => codes.contains('B02');
bool isBeaconCancel(List<String> codes) => codes.contains('B03');

class _Header {
  int? severity;
  bool hasDelimiter = false;
  String body = '';
}

/// [s] must start with [prefix]. Indexing is by code point.
_Header _parseHeader(String s) {
  final h = _Header();
  var i = prefix.length;
  if (i < s.length) {
    final c = s.codeUnitAt(i);
    if (c >= 0x30 && c <= 0x33) h.severity = c - 0x30;
    i += _cpLen(s, i);
  }
  if (i < s.length) {
    h.hasDelimiter = s.codeUnitAt(i) == 0x2F;
    i += _cpLen(s, i);
  }
  h.body = s.substring(i);
  return h;
}

void _extract(String t, List<String> codes, Extracted x) {
  final count = _find(_countRe, t);
  if (count != null) x.count = _toInt(count);

  final gps = _gpsRe.firstMatch(t);
  if (gps != null) {
    final lat = double.parse(gps.group(1)!);
    final lon = double.parse(gps.group(2)!);
    if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) x.gps = Gps(lat, lon);
  }

  if (codes.contains('R03')) {
    final eta = _find(_etaRe, t);
    if (eta != null) x.eta = _toInt(eta);
  }

  x.reference = _find(_referenceRe, t);
  x.language = _find(_languageRe, t);

  final ts = _find(_timestampRe, t);
  if (ts != null && int.parse(ts.substring(0, 2)) <= 23 && int.parse(ts.substring(2)) <= 59) {
    x.timestamp = ts;
  }

  x.callsign = _find(_callsignRe, t);
}

Decoded decode(String s) {
  final d = Decoded(s);
  if (!isMecp(s)) return d;

  final h = _parseHeader(s);
  d.severity = h.severity;
  if (h.severity == null) d.warnings.add(Warnings.invalidSeverity);
  if (!h.hasDelimiter) d.warnings.add(Warnings.missingDelimiter);

  if (_trim(h.body).isEmpty) {
    d.valid = h.severity != null;
    if (d.valid) d.warnings.add(Warnings.noCodes);
    return d;
  }

  final tokens = h.body.split(' ').where((t) => t.isNotEmpty).toList();
  var i = 0;
  while (i < tokens.length && isCode(tokens[i])) {
    d.codes.add(tokens[i]);
    i++;
  }
  if (i < tokens.length) {
    final ft = d.freetext = tokens.sublist(i).join(' ');
    _extract(ft, d.codes, d.extracted);
  }

  d.isDrill = d.codes.contains('D01') || d.codes.contains('D02');
  d.valid = h.severity != null;
  return d;
}

Encoded encode(int severity, List<String> codes, [String? freetext]) {
  final warnings = <String>[];
  if (severity < 0 || severity > 3) warnings.add(Warnings.invalidSeverity);
  for (final c in codes) {
    if (!isCode(c)) warnings.add(Warnings.invalidCode);
  }

  var message = '$prefix$severity/${codes.join(' ')}';
  if (freetext != null) {
    final ft = _trim(freetext);
    if (ft.isNotEmpty) message += ' $ft';
  }
  message = _trimEnd(message);

  final byteLength = _utf8Length(message);
  final over = byteLength > maxMessageBytes;
  if (over) warnings.add(Warnings.overLimit);
  return Encoded(message, byteLength, over, warnings);
}

Validation validate(String s) {
  if (!isMecp(s)) return const Validation(false, [Warnings.missingPrefix], []);
  final h = _parseHeader(s);
  final errors = <String>[];
  final warnings = <String>[];
  if (h.severity == null) errors.add(Warnings.invalidSeverity);
  if (!h.hasDelimiter) errors.add(Warnings.missingDelimiter);
  if (_trim(h.body).isEmpty) warnings.add(Warnings.noCodes);
  if (_utf8Length(s) > maxMessageBytes) warnings.add(Warnings.overLimit);
  return Validation(errors.isEmpty, errors, warnings);
}
