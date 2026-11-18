import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

const docs = path.resolve('docs');
const root = path.join(docs, 'access-log-monitoring');
const files = readdirSync(root, { recursive: true })
  .filter(file => file.endsWith('.md'))
  .map(file => path.join(root, file));
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  assert.equal((text.match(/^```/gm) ?? []).length % 2, 0, `${file}: unclosed fence`);
  for (const [, target] of text.matchAll(/\]\(([^)#]+)(?:#[^)]*)?\)/g)) {
    if (/^https?:/.test(target)) continue;
    assert.ok(existsSync(path.resolve(path.dirname(file), target)), `${file}: missing ${target}`);
  }
  for (const [, target] of text.matchAll(/href="\.\/([^"]+)"/g)) {
    const asset = path.join(docs, 'public', path.relative(docs, path.dirname(file)), target);
    assert.ok(existsSync(asset), `${file}: missing download ${target}`);
  }
}
const sidebar = JSON.parse(readFileSync(path.join(root, '_meta.json'), 'utf8'));
const targets = sidebar.map(item => typeof item === 'string'
  ? path.join(root, `${item}.md`)
  : item.type === 'custom-link'
    ? path.join(docs, `${item.link}.md`)
    : path.join(root, `${item.name}.md`));
assert.deepEqual(new Set(targets), new Set(files), 'All pages must be in the sidebar');
const rows = readFileSync(path.join(docs, 'public/access-log-monitoring/lab/access.jsonl'), 'utf8')
  .trim().split(/\r?\n/).map(line => JSON.parse(line));
assert.equal(rows.length, 30);
assert.equal(new Set(rows.map(row => row.request_id)).size, 30);
assert.ok(readFileSync(path.join(docs, 'index.md'), 'utf8').includes('/access-log-monitoring/'));
const nav = JSON.parse(readFileSync(path.join(docs, '_nav.json'), 'utf8'));
assert.ok(nav.some(item => item.link === '/access-log-monitoring/'));
console.log(`Access log course: ${files.length} pages, sidebar, links and downloads checked`);
