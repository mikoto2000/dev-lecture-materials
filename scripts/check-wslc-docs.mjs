import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { checkCourseDocs } from './check-course-docs.mjs';
import { parseArgs } from 'node:util';

const docs = path.resolve('docs');
const root = path.join(docs, 'wslc-postgresql');
const files = [path.join(root, 'index.md')];
checkCourseDocs('wslc-postgresql', ['guide-01-prepare', 'guide-02-start', 'guide-03-sql',
  'guide-04-persist', 'guide-05-connect', 'guide-06-cleanup', 'troubleshooting', 'facilitator', 'references']);
const commandSheet = path.join(docs, 'public/wslc-postgresql/examples/commands.ps1.txt');
const sources = new Map([...files, commandSheet].map(file => [file, readFileSync(file, 'utf8')]));
const allText = [...sources.values()].join('\n');
assert.ok(!/^\s*wslc .*\bprune\b/m.test(allText), 'Broad prune command found');
assert.ok(!/postgres:(?:latest|18)\b/.test(allText), 'PostgreSQL version drift');
const requiredSources = new Set([
  path.join(root, 'index.md'),
  commandSheet,
]);
for (const [file, text] of sources) {
  const lines = text.replace(/`\r?\n[ \t]*/g, ' ');
  const runs = [...lines.matchAll(/^[ \t]*wslc[ \t]+run[ \t]+([^\r\n]+)$/gmi)]
    .filter(([, command]) => !/^(?:-h|--help)$/.test(command.trim()));
  if (requiredSources.has(file)) {
    assert.ok(runs.length, `${file}: PostgreSQL startup command missing`);
  }
  for (const [, command] of runs) {
    let parsed;
    try {
      parsed = parseArgs({
        args: command.trim().split(/\s+/),
        allowPositionals: true,
        tokens: true,
        options: {
          detach: { type: 'boolean', short: 'd' },
          name: { type: 'string' },
          env: { type: 'string', short: 'e', multiple: true },
          publish: { type: 'string', short: 'p', multiple: true },
          volume: { type: 'string', short: 'v', multiple: true },
        },
      });
    } catch (error) {
      throw new Error(`${file}: invalid wslc run arguments`, { cause: error });
    }
    const { values, positionals, tokens } = parsed;
    assert.equal(tokens.at(-1)?.kind, 'positional', `${file}: put the image after the options`);
    assert.deepEqual(positionals, ['postgres:17'], `${file}: use the PostgreSQL 17 image`);
    assert.equal(values.detach, true, `${file}: start the workshop database in the background`);
    assert.equal(values.name, 'wslc-workshop-db', `${file}: use the workshop container name`);
    assert.deepEqual(values.publish, ['127.0.0.1:15432:5432'], `${file}: publish only to loopback`);
    assert.deepEqual(values.volume, ['wslc-workshop-pgdata:/var/lib/postgresql/data'], `${file}: use the workshop data volume`);
    assert.deepEqual((values.env ?? []).toSorted(), [
      'POSTGRES_DB=workshop',
      'POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256',
      'POSTGRES_PASSWORD=workshop-local-only',
    ], `${file}: use the workshop database and SCRAM authentication`);
  }
}
assert.ok(existsSync(path.join(docs, 'public/wslc-postgresql/examples/01-tasks.sql')));
console.log(`PASS: ${files.length} pages, local links, sidebar, fences, sample assets and PostgreSQL safety settings`);
