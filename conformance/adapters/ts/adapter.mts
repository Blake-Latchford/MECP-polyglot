// Conformance adapter for TypeScript MECP clients. Imports each client's own
// decoder from its checkout (nothing is copied here) and maps its output to the
// harness record. Mapping is representation-only: no protocol logic.
//
//   tsx adapter.mts <client> <checkout-dir>
//   stdin:  <id>\t<hex utf-8 input>     stdout: one JSON record per line
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

type Rec = Record<string, unknown>;
const [client, dir] = process.argv.slice(2);
const hhmm = (t: string | null | undefined) =>
  !t ? null : t.includes(':') ? t : `${t.slice(0, 2)}:${t.slice(2)}`;
const load = (rel: string) => import(pathToFileURL(join(dir, rel)).href);

// @mecp/engine's ParsedMessage, shared by mecp-app and mesh-client's vendored copy.
function fromEngine(p: any): Rec {
  if (!p || !p.valid) return { valid: false };
  const x = p.extracted;
  return {
    valid: true, severity: p.severity, codes: p.codes, freetext: p.freetext,
    pax: x.count, gps: x.gps, timestamp: hhmm(x.timestamp), language: x.language,
    callsign: x.callsign, reference: x.reference,
    duration: 'duration' in x ? x.duration : x.eta, // eta before 1.2
  };
}

const clients: Record<string, () => Promise<(s: string) => Rec>> = {
  async 'mecp-app'() {
    const m = await load('engine/src/decoder.ts');
    return (s) => fromEngine(m.decode(s));
  },
  async 'mesh-client'() {
    // tryParseMecp is what the app runs on inbound chat text.
    const m = await load('src/renderer/lib/mecp/mecpMessages.ts');
    return (s) => fromEngine(m.tryParseMecp(s));
  },
  async 'reticulum-mobile'() {
    const m = await load('apps/mobile/src/utils/mecp.ts');
    return (s) => {
      const d = m.decodeMecpMessage(s);
      if (!d.valid) return { valid: false };
      const x = d.extras;
      return {
        valid: true, severity: d.severity, codes: d.codes, freetext: d.details === '' ? null : d.details,
        pax: x.pax, gps: x.coordinates && { lat: x.coordinates.latitude, lon: x.coordinates.longitude },
        timestamp: hhmm(x.timestamp), language: x.language, callsign: x.callsign,
        reference: x.references[0]?.replace(/^#/, '') ?? null, duration: x.etaMinutes,
      };
    };
  },
};

const decode = await clients[client]();
const out: string[] = [];
for await (const line of createInterface({ input: process.stdin })) {
  if (!line) continue;
  const [id, hex] = line.split('\t');
  try {
    out.push(JSON.stringify({ id, result: decode(Buffer.from(hex, 'hex').toString('utf8')) }));
  } catch (e) {
    out.push(JSON.stringify({ id, error: String(e) }));
  }
}
process.stdout.write(out.join('\n') + '\n');
