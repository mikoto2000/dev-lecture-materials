import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

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
assert.equal(files.length, 11, 'Expected ten workshop pages and a verification record');
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
}
const metadata = JSON.parse(readFileSync(path.join(root, '_meta.json'), 'utf8'));
for (const item of metadata) {
  const target = typeof item === 'string' ? path.join(root, `${item}.md`)
    : item.type === 'custom-link' ? path.join(docs, `${item.link}.md`)
      : path.join(root, `${item.name}.md`);
  assert.ok(existsSync(target), `Sidebar target missing: ${target}`);
}
const index = readFileSync(path.join(root, 'index.md'), 'utf8');
for (const match of index.matchAll(/href="\.\/examples\/([^"]+)"/g)) {
  assert.ok(existsSync(path.join(docs, 'public/wslc-postgresql/examples', match[1])), `Missing download: ${match[1]}`);
}
const commands = readFileSync(path.join(docs, 'public/wslc-postgresql/examples/commands.ps1.txt'), 'utf8');
const allText = [...files.map(file => readFileSync(file, 'utf8')), commands].join('\n');
assert.ok(!/^\s*wslc .*\bprune\b/m.test(allText), 'Broad prune command found');
assert.ok(!/postgres:(?:latest|18)\b/.test(allText), 'PostgreSQL version drift');
for (const file of ['guide/02-start.md', 'guide/04-persist.md']) {
  const text = readFileSync(path.join(root, file), 'utf8');
  for (const required of ['postgres:17', '127.0.0.1:15432:5432',
    'wslc-workshop-pgdata:/var/lib/postgresql/data',
    'POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256']) {
    assert.ok(text.includes(required), `${file}: missing ${required}`);
    assert.ok(commands.includes(required), `Command sheet: missing ${required}`);
  }
}
assert.ok(existsSync(path.join(docs, 'public/wslc-postgresql/examples/01-tasks.sql')));
console.log(`PASS: ${files.length} pages, local links, sidebar, fences, sample assets and PostgreSQL safety settings`);
