import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';

const docs = path.resolve('docs');
const root = path.join(docs, 'wslc-postgresql');
const files = [];
function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(file);
    else if (file.endsWith('.md')) files.push(file);
  }
}
walk(root);
assert.equal(files.length, 10, 'Expected ten workshop pages');
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  assert.equal((text.match(/^```/gm) || []).length % 2, 0, `${file}: unclosed fence`);
  for (const match of text.matchAll(/\]\(([^)#]+)(?:#[^)]*)?\)/g)) {
    const target = match[1];
    if (/^(https?:|mailto:)/.test(target)) continue;
    const local = target.startsWith('/')
      ? path.join(docs, 'public', target)
      : path.resolve(path.dirname(file), target);
    assert.ok(existsSync(local), `${file}: missing ${target}`);
  }
  for (const match of text.matchAll(/href="\.\/([^"]+)"/g)) {
    const routeDirectory = path.dirname(path.relative(docs, file));
    const asset = path.join(docs, 'public', routeDirectory, match[1]);
    const local = path.resolve(path.dirname(file), match[1]);
    assert.ok(existsSync(asset) || existsSync(local), `${file}: missing ${match[1]}`);
  }
}
const metadata = JSON.parse(readFileSync(path.join(root, '_meta.json'), 'utf8'));
for (const item of metadata) {
  const target = typeof item === 'string' ? path.join(root, `${item}.md`)
    : item.type === 'custom-link' ? path.join(docs, `${item.link}.md`)
      : path.join(root, `${item.name}.md`);
  assert.ok(existsSync(target), `Sidebar target missing: ${target}`);
}
const commandSheet = path.join(docs, 'public/wslc-postgresql/examples/commands.ps1.txt');
const sources = new Map([...files, commandSheet].map(file => [file, readFileSync(file, 'utf8')]));
const allText = [...sources.values()].join('\n');
assert.ok(!/^\s*wslc .*\bprune\b/m.test(allText), 'Broad prune command found');
assert.ok(!/postgres:(?:latest|18)\b/.test(allText), 'PostgreSQL version drift');
const requiredSources = new Set([
  path.join(root, 'guide/02-start.md'),
  path.join(root, 'guide/04-persist.md'),
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
