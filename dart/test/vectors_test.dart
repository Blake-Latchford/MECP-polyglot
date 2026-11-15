import 'dart:convert';
import 'dart:io';

import 'package:mecp/mecp.dart' as mecp;
import 'package:test/test.dart';

final Map<String, dynamic> vectors =
    jsonDecode(File('../vectors/mecp-vectors.json').readAsStringSync()) as Map<String, dynamic>;

Map<String, Object?> decodedJson(mecp.Decoded d) {
  final x = d.extracted;
  return {
    'valid': d.valid,
    'severity': d.severity,
    'codes': d.codes,
    'is_drill': d.isDrill,
    'freetext': d.freetext,
    'extracted': {
      'count': x.count,
      'gps': x.gps == null ? null : {'lat': x.gps!.lat, 'lon': x.gps!.lon},
      'eta': x.eta,
      'reference': x.reference,
      'language': x.language,
      'timestamp': x.timestamp,
      'callsign': x.callsign,
    },
    'warnings': d.warnings,
  };
}

void main() {
  group('decode', () {
    for (final c in vectors['decode'] as List) {
      test(c['name'], () {
        final got = mecp.decode(c['input'] as String);
        expect(got.raw, c['input']);
        expect(decodedJson(got), equals(c['expect']));
      });
    }
  });

  group('encode', () {
    for (final c in vectors['encode'] as List) {
      test(c['name'], () {
        final got = mecp.encode(
            c['severity'] as int, (c['codes'] as List).cast<String>(), c['freetext'] as String?);
        expect({
          'message': got.message,
          'byte_length': got.byteLength,
          'over_limit': got.overLimit,
          'warnings': got.warnings,
        }, equals(c['expect']));
      });
    }
  });

  group('validate', () {
    for (final c in vectors['validate'] as List) {
      test(c['name'], () {
        final got = mecp.validate(c['input'] as String);
        expect({'valid': got.valid, 'errors': got.errors, 'warnings': got.warnings},
            equals(c['expect']));
      });
    }
  });

  test('beacon helpers', () {
    final codes = mecp.decode('MECP/0/B01 B02 B03').codes;
    expect(mecp.isBeacon(codes), isTrue);
    expect(mecp.isBeaconAck(codes), isTrue);
    expect(mecp.isBeaconCancel(codes), isTrue);
    expect(mecp.isBeacon(['M01']), isFalse);
  });
}
