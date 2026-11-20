import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { checkCourseDocs } from './check-course-docs.mjs';

const docs = path.resolve('docs');
const expectedOrder = [
  '00-prepare',
  '01-url',
  '02-periodic',
  '03-operation',
  '05-alerts',
  '04-latency',
  '06-diagnose',
  '09-disk',
  '10-cpu-memory',
  '11-network',
  '07-watchdog',
  '08-review',
];
const text = checkCourseDocs('monitoring-intro', [
  ...expectedOrder.map((name) => `guide-${name}`),
  'appendix-custom-checker',
  'troubleshooting',
  'facilitator',
  'references',
]);
for (const name of ['index.md', '_nav.json']) {
  assert.ok(
    readFileSync(path.join(docs, name), 'utf8').includes('/monitoring-intro/'),
    `Missing course entry: ${name}`,
  );
}
// Preparation and review have their own structure; every practical lesson is checked.
// Disk and network lessons observe bounded commands instead of injecting faults.
const observationLessons = new Set(['09-disk', '11-network']);
for (const name of expectedOrder.filter(
  (name) => !['00-prepare', '08-review'].includes(name),
)) {
  const section = text
    .split(`<a id="guide-${name}"></a>`)[1]
    .split('<a id="')[0];
  const safetyStage = observationLessons.has(name)
    ? '安全な観察'
    : '安全な故障';
  for (const label of [
    '困りごと',
    '小さな追加',
    safetyStage,
    '復旧',
    '確かめた範囲',
    'チェックポイント',
  ]) {
    assert.match(
      section,
      new RegExp(`^### ${label}(?:[\\s:：]|$)`, 'm'),
      `${name}: missing teaching stage ${label}`,
    );
  }
}
const mainText = text.replace(
  /<a id="appendix-custom-checker"><\/a>[\s\S]*?(?=<a id=")/,
  '',
);
assert.ok(
  mainText.includes('louislam/uptime-kuma:2.5.5'),
  'Missing pinned stable image',
);
assert.ok(
  mainText.includes('http://demo:18080/health'),
  'Missing container-network monitor URL',
);
assert.ok(
  !/```bash/m.test(mainText),
  'Main course commands must stay in PowerShell',
);
assert.ok(
  !/^(?:python3 )?(?:monitor|watchdog)\.py/m.test(mainText),
  'Custom checker belongs only in appendix',
);
execFileSync(
  process.execPath,
  ['scripts/monitoring-python.mjs', 'check-package'],
  { stdio: 'inherit' },
);
console.log(
  'PASS: monitoring single document, anchors, links, downloads, course entry and lesson structure',
);
