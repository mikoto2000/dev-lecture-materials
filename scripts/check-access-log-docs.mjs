import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { checkCourseDocs } from './check-course-docs.mjs';

const docs = path.resolve('docs');
const course = process.argv[2] ?? 'access-log-monitoring';
assert.ok(['access-log-monitoring', 'security-log-monitoring'].includes(course));
const sections = course === 'access-log-monitoring'
  ? ['guide-00-prepare', 'guide-01-read', 'guide-02-filter', 'guide-03-measure', 'guide-04-monitor', 'guide-05-review']
  : ['guide-00-prepare', 'guide-01-auth', 'guide-02-paths', 'guide-03-triage', 'guide-04-review'];
checkCourseDocs(course, [...sections, 'troubleshooting', 'facilitator', 'references']);
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
console.log(`${course}: single document, chapter order, anchors, links and downloads checked`);
