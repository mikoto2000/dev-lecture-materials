import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const root = 'docs/public/access-log-analysis';
const context = {};
runInNewContext(readFileSync(`${root}/core.js`, 'utf8'), context);
runInNewContext(readFileSync(`${root}/samples.js`, 'utf8'), context);
const { parse, filter, aggregate } = context.LogAnalysis;
const load = (name) =>
  parse(readFileSync(`${root}/samples/${name}.jsonl`, 'utf8'));
const baseline = load('01-baseline');
const guided = load('02-guided');
const challenge = load('03-challenge');
for (const [data, total] of [
  [baseline, 60],
  [guided, 114],
  [challenge, 154],
]) {
  assert.equal(data.records.length, total);
  assert.equal(data.errors.length, 0);
  assert.equal(new Set(data.records.map((row) => row.request_id)).size, total);
}
assert.ok(
  aggregate(baseline.records, 'minute').every((row) => row.count === 6),
);
assert.ok(
  aggregate(baseline.records, 'client_ip').every((row) => row.count === 20),
);
const minute = filter(guided.records, {
  start: '2026-11-01T09:03:00Z',
  end: '2026-11-01T09:04:00Z',
  status: '404',
});
assert.equal(minute.length, 30);
assert.ok(aggregate(minute, 'path').every((row) => row.count === 10));
assert.equal(
  filter(guided.records, {
    start: '2026-11-01T09:06:00Z',
    end: '2026-11-01T09:07:00Z',
    status: '404',
  }).length,
  24,
);
assert.equal(
  filter(baseline.records, {
    start: '2026-11-01T09:00:00Z',
    end: '2026-11-01T09:00:10Z',
  }).length,
  1,
);
assert.equal(
  filter(challenge.records, { event: 'auth', outcome: 'failure' }).length,
  30,
);
assert.equal(challenge.records.filter((row) => row.status >= 400).length, 31);
assert.equal(
  aggregate(
    filter(challenge.records, { event: 'auth', outcome: 'failure' }),
    'account',
  ).find((row) => row.value === 'learner-b').count,
  18,
);
assert.equal(
  filter(challenge.records, { ip: '203.0.113.40', outcome: 'success' })[0]
    .request_id,
  'req-0127',
);
assert.equal(
  aggregate(challenge.records, 'client_ip')[0].value,
  '198.51.100.30',
);
assert.equal(
  filter(challenge.records, { ip: '203.0.113.60', path: '%3Cscript%3E' })
    .length,
  1,
);
const valid = JSON.stringify(baseline.records[0]);
assert.equal(parse(`${valid}\n{bad}\n{}\n\n`).errors.length, 2);
assert.equal(parse(valid.replace('2026-11-01', '2026-02-30')).errors.length, 1);
assert.equal(
  parse(valid.replace('"status":200', '"status":"200"')).errors.length,
  1,
);
assert.equal(
  parse(valid.replace('"event":"access"', '"event":"auth"')).errors.length,
  1,
);
assert.throws(() => parse('\n'.repeat(10001)));
assert.throws(() => filter([], { start: '2026-11-02', end: '2026-11-01' }));
assert.throws(() => aggregate([], '__proto__'));
for (const [key, name] of [
  ['baseline', '01-baseline'],
  ['guided', '02-guided'],
  ['challenge', '03-challenge'],
]) {
  assert.equal(
    context.LogSamples[key],
    readFileSync(`${root}/samples/${name}.jsonl`, 'utf8'),
  );
}
assert.equal(
  readFileSync(`${root}/lesson.md`, 'utf8'),
  readFileSync('docs/access-log-analysis/index.md', 'utf8'),
);
const html = readFileSync(`${root}/analyzer.html`, 'utf8');
for (const file of ['core.js', 'app.js', 'samples.js', 'style.css']) {
  assert.ok(html.includes(`"${file}"`));
  readFileSync(`${root}/${file}`);
}
assert.ok(html.includes("connect-src 'none'"));
assert.ok(
  !/<(?:input|button|select)[^>]+(?:id|name)="reset"/.test(html),
  'Form controls must not shadow form.reset()',
);
assert.ok(!readFileSync(`${root}/app.js`, 'utf8').includes('innerHTML'));
execFileSync(process.platform === 'win32' ? 'python' : 'python3', [
  '-c',
  `
from pathlib import Path
from zipfile import ZipFile
root = Path('${root}')
with ZipFile(root / 'access-log-analysis.zip') as archive:
    expected = { 'access-log-analysis/' + p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file() and p.suffix != '.zip' }
    assert set(archive.namelist()) == set(expected)
    for name, source in expected.items():
        assert archive.read(name) == source.read_bytes(), name
`,
]);
console.log(
  'PASS: exercise answers, time boundaries, input errors, embedded samples and offline ZIP consistency',
);
