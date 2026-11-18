import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

const docs = path.resolve('docs');
const course = process.argv[2] ?? 'access-log-monitoring';
assert.ok(['access-log-monitoring', 'security-log-monitoring'].includes(course));
const root = path.join(docs, course);
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
const lab = path.join(docs, 'public/access-log-monitoring/lab');
const compose = readFileSync(path.join(lab, 'compose.yaml'), 'utf8');
for (const pinned of ['grafana/loki:3.7.10', 'grafana/grafana:13.3.1', 'grafana/alloy:v1.22.0']) {
  assert.ok(compose.includes(pinned), `Missing pinned image: ${pinned}`);
}
assert.ok(!compose.includes('docker.sock'), 'Do not mount the host Docker socket');
const action = course === 'security-log-monitoring' ? 'security-check-package' : 'check-package';
execFileSync(process.execPath, ['scripts/access-log-python.mjs', action], { stdio: 'inherit' });
assert.ok(readFileSync(path.join(docs, 'index.md'), 'utf8').includes(`/${course}/`));
const nav = JSON.parse(readFileSync(path.join(docs, '_nav.json'), 'utf8'));
assert.ok(nav.some(item => item.link === `/${course}/`));
console.log(`${course}: ${files.length} pages, sidebar, links and downloads checked`);
