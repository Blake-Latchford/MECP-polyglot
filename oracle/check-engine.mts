// Runs vectors/mecp-vectors.json against the TypeScript reference engine
// (@mecp/engine from mecp-org/mecp-app) to keep the vectors honest.
//
// Usage: npx tsx oracle/check-engine.mts <path/to/mecp-app/engine/src/index.ts>
//
// Vectors marked `engine_divergence` are skipped. Engine warning strings are
// mapped to MECP-polyglot ids before comparison.
import { readFileSync } from 'node:fs';
import { isDeepStrictEqual } from 'node:util';
import { pathToFileURL } from 'node:url';

const enginePath = process.argv[2];
if (!enginePath) {
  console.error('usage: check-engine.mts <engine/src/index.ts>');
  process.exit(2);
}
const engine = await import(pathToFileURL(enginePath).href);
const vectors = JSON.parse(
  readFileSync(new URL('../vectors/mecp-vectors.json', import.meta.url), 'utf8'),
);

const ID_PATTERNS: Array<[RegExp, string]> = [
  [/does not start with/, 'missing_prefix'],
  [/^Invalid severity/, 'invalid_severity'],
  [/^Missing "\/" delimiter/, 'missing_delimiter'],
  [/^No codes present/, 'no_codes'],
  [/^Invalid code format/, 'invalid_code'],
  [/exceeds \d+ byte limit/, 'over_limit'],
];

function toIds(messages: string[]): string[] {
  return messages.map((m) => {
    const hit = ID_PATTERNS.find(([re]) => re.test(m));
    if (!hit) throw new Error(`unmapped engine message: ${m}`);
    return hit[1];
  });
}

let failures = 0;
let skipped = 0;
function check(section: string, name: string, got: unknown, want: unknown) {
  if (!isDeepStrictEqual(got, want)) {
    failures++;
    console.log(`FAIL ${section}/${name}\n  got  ${JSON.stringify(got)}\n  want ${JSON.stringify(want)}`);
  }
}

for (const c of vectors.decode) {
  if (c.engine_divergence) {
    skipped++;
    continue;
  }
  const r = engine.decode(c.input);
  check('decode', c.name, {
    valid: r.valid,
    severity: r.severity,
    codes: r.codes,
    is_drill: r.isDrill,
    freetext: r.freetext,
    extracted: r.extracted,
    warnings: toIds(r.warnings),
  }, c.expect);
}

for (const c of vectors.encode) {
  const r = engine.encode(c.severity, c.codes, c.freetext ?? undefined);
  check('encode', c.name, {
    message: r.message,
    byte_length: r.byteLength,
    over_limit: r.overLimit,
    warnings: toIds(r.warnings),
  }, c.expect);
}

for (const c of vectors.validate) {
  const r = engine.validate(c.input);
  check('validate', c.name, {
    valid: r.valid,
    errors: toIds(r.errors),
    warnings: toIds(r.warnings),
  }, c.expect);
}

console.log(`@mecp/engine: ${failures} failures, ${skipped} skipped (documented divergences)`);
process.exit(failures ? 1 : 0);
