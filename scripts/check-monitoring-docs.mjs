import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { checkCourseDocs } from './check-course-docs.mjs';
import { execFileSync } from 'node:child_process';

const docs = path.resolve('docs');
const expectedOrder = ['00-prepare', '01-url', '02-periodic', '03-operation',
  '05-alerts', '04-latency', '06-diagnose', '09-disk', '10-cpu-memory',
  '11-network', '07-watchdog', '08-review'];
const text = checkCourseDocs('monitoring-intro', [
  ...expectedOrder.map(name => `guide-${name}`), 'appendix-custom-checker',
  'troubleshooting', 'facilitator', 'references',
]);
for (const name of ['index.md', '_nav.json']) {
  assert.ok(readFileSync(path.join(docs, name), 'utf8').includes('/monitoring-intro/'), `Missing course entry: ${name}`);
}
for (let chapter = 1; chapter <= 7; chapter++) {
  const name = expectedOrder.find(name => name.startsWith(`0${chapter}-`));
  const section = text.split(`<a id="guide-${name}"></a>`)[1].split('<a id="')[0];
  for (const label of ['困りごと', '小さな追加', '安全な故障', '復旧', '確かめた範囲', 'チェックポイント']) {
    assert.ok(section.includes(label), `${name}: missing teaching stage ${label}`);
  }
}
const mainText = text.replace(/<a id="appendix-custom-checker"><\/a>[\s\S]*?(?=<a id=")/, '');
assert.ok(mainText.includes('louislam/uptime-kuma:2.5.5'), 'Missing pinned stable image');
assert.ok(mainText.includes('http://demo:18080/health'), 'Missing container-network monitor URL');
assert.ok(!/```bash/m.test(mainText), 'Main course commands must stay in PowerShell');
assert.ok(!/^(?:python3 )?(?:monitor|watchdog)\.py/m.test(mainText), 'Custom checker belongs only in appendix');
execFileSync(process.execPath, ['scripts/monitoring-python.mjs', 'check-package'], { stdio: 'inherit' });
console.log(`PASS: monitoring single document, anchors, links, downloads, course entry and lesson structure`);
