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
assert.equal(pages.length, 18, 'Expected original course, three resource chapters and appendix');
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
const expectedOrder = ['00-prepare', '01-url', '02-periodic', '03-operation',
  '05-alerts', '04-latency', '06-diagnose', '09-disk', '10-cpu-memory',
  '11-network', '07-watchdog', '08-review'];
const guideItems = metadata.filter(item => typeof item === 'object' && item.type === 'custom-link');
assert.deepEqual(guideItems.map(item => path.basename(item.link)), expectedOrder,
  'Learning order must move from service behavior to alerts, latency, logs and scoped resource observations');
for (const [position, name] of expectedOrder.entries()) {
  const text = readFileSync(path.join(root, 'guide', `${name}.md`), 'utf8');
  const footer = text.trim().split('\n').at(-1);
  if (position > 0) assert.ok(footer.includes(`./${expectedOrder[position - 1]}.md`), `${name}: missing previous chapter`);
  if (position + 1 < expectedOrder.length) assert.ok(footer.includes(`./${expectedOrder[position + 1]}.md`), `${name}: missing next chapter`);
}
for (const item of metadata) {
  const target = typeof item === 'string' ? path.join(root, `${item}.md`)
    : item.type === 'custom-link' ? path.join(docs, `${item.link}.md`)
      : path.join(root, `${item.name}.md`);
  assert.ok(existsSync(target), `Sidebar target missing: ${target}`);
}
for (const file of pages) {
  const text = readFileSync(file, 'utf8');
  for (const match of text.matchAll(/href="\.\/([^"]+)"/g)) {
    const routeDirectory = path.dirname(path.relative(docs, file));
    assert.ok(existsSync(path.join(docs, 'public', routeDirectory, match[1])), `Missing download: ${match[1]}`);
  }
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
const mainText = pages.filter(file => !file.endsWith('appendix-custom-checker.md')).map(file => readFileSync(file, 'utf8')).join('\n');
assert.ok(mainText.includes('louislam/uptime-kuma:2.5.5'), 'Missing pinned stable image');
assert.ok(mainText.includes('http://demo:18080/health'), 'Missing container-network monitor URL');
assert.ok(!/```bash/m.test(mainText), 'Main course commands must stay in PowerShell');
assert.ok(!/^(?:python3 )?(?:monitor|watchdog)\.py/m.test(mainText), 'Custom checker belongs only in appendix');
execFileSync('python3', ['scripts/package-monitoring-lab.py', '--check'], { stdio: 'inherit' });
console.log(`PASS: ${pages.length} monitoring pages, local links, sidebar, downloads, course entry and lesson structure`);
