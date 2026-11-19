import 'dart:convert';
import 'dart:io';

import 'package:mecp/mecp.dart' as mecp;
import 'package:test/test.dart';

dynamic readJson(String rel) => jsonDecode(File('../$rel').readAsStringSync());

final Map<String, dynamic> vectors = readJson('vectors/mecp-vectors.json') as Map<String, dynamic>;
const fields = ['pax', 'gps', 'timestamp', 'language', 'callsign', 'reference', 'duration'];

Map<String, Object?> extractedJson(mecp.Extracted x) => {
      'pax': x.pax,
      'gps': x.gps == null ? null : {'lat': x.gps!.lat, 'lon': x.gps!.lon},
      'timestamp': x.timestamp,
      'language': x.language,
      'callsign': x.callsign,
      'reference': x.reference,
      'duration': x.duration,
    };

Map<String, Object?> decodedJson(mecp.Decoded d) => {
      'valid': d.valid,
      'severity': d.severity,
      'codes': d.codes,
      'is_drill': d.isDrill,
      'freetext': d.freetext,
      'extracted': extractedJson(d.extracted),
    };

void main() {
  group('decode', () {
    for (final c in vectors['decode'] as List) {
      test(c['name'], () => expect(decodedJson(mecp.decode(c['input'] as String)), c['expect']));
    }
  });

  group('encode', () {
    for (final c in vectors['encode'] as List) {
      test(c['name'], () {
        final e = mecp.encode(
            c['severity'] as int, (c['codes'] as List).cast<String>(), c['freetext'] as String?);
        expect({'message': e.message, 'byte_length': e.byteLength, 'errors': e.errors},
            c['expect']);
      });
    }
  });

  group('validate', () {
    for (final c in vectors['validate'] as List) {
      test(c['name'], () {
        final v = mecp.validate(c['input'] as String);
        expect({'valid': v.valid, 'errors': v.errors}, c['expect']);
      });
    }
  });

  group('upstream freetext', () {
    test('schemaVersion', () {
      expect(readJson('upstream/freetext/manifest.json')['schemaVersion'], 1);
    });
    for (final t in readJson('upstream/freetext/tests.json') as List) {
      test(t['title'], () {
        final d = mecp.decode(t['input'] as String);
        final exp = t['expect'] as Map<String, dynamic>?;
        if (exp == null) {
          expect(d.valid, isFalse);
          return;
        }
        expect(d.valid, isTrue);
        expect(extractedJson(d.extracted), {for (final f in fields) f: exp[f]});
      });
    }
  });

  test('beacon helpers', () {
    final codes = mecp.decode('MECP/0/B01 B02 B03').codes;
    expect(mecp.isBeacon(codes), isTrue);
    expect(mecp.isBeaconAck(codes), isTrue);
    expect(mecp.isBeaconCancel(codes), isTrue);
    expect(mecp.isBeacon(['M01']), isFalse);
    expect(mecp.mecpVersion, '1.4.0');
  });
}
