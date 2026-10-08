import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const docs = path.resolve('docs');
const root = path.join(docs, 'monitoring-intro');
const pages = [];
function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(file);
    else if (file.endsWith('.md')) pages.push(file);
  }
}
walk(root);
assert.equal(pages.length, 14, 'Expected introduction, nine chapters and four support pages');
for (const file of pages) {
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
for (const match of index.matchAll(/href="\.\/([^"]+)"/g)) {
  assert.ok(existsSync(path.join(docs, 'public/monitoring-intro', match[1])), `Missing download: ${match[1]}`);
}
for (const name of ['index.md', '_nav.json']) {
  assert.ok(readFileSync(path.join(docs, name), 'utf8').includes('/monitoring-intro/'), `Missing course entry: ${name}`);
}
for (let chapter = 1; chapter <= 7; chapter++) {
  const file = pages.find(file => path.basename(file).startsWith(`0${chapter}-`));
  const text = readFileSync(file, 'utf8');
  for (const label of ['困りごと', '小さな追加', '安全な故障', '復旧', '確かめた範囲', 'チェックポイント']) {
    assert.ok(text.includes(label), `${file}: missing teaching stage ${label}`);
  }
}
execFileSync('python3', ['scripts/package-monitoring-lab.py', '--check'], { stdio: 'inherit' });
console.log(`PASS: ${pages.length} monitoring pages, local links, sidebar, downloads, course entry and lesson structure`);
