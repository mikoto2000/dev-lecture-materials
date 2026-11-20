import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { checkCourseDocs } from './check-course-docs.mjs';

const course = 'access-log-analysis';
const text = checkCourseDocs(
  course,
  ['read', 'baseline', 'guided', 'challenge', 'answers'],
  { topAnchor: false },
);
for (const file of [
  'analyzer.html',
  'access-log-analysis.zip',
  'samples/01-baseline.jsonl',
  'samples/02-guided.jsonl',
  'samples/03-challenge.jsonl',
]) {
  assert.ok(
    text.includes(`href="./${file}"`),
    `${course}: missing distribution link ${file}`,
  );
}
const home = readFileSync('docs/index.md', 'utf8');
const hero = home.match(/^hero:\s*\n([\s\S]*?)^features:/m)?.[1];
const features = home.match(/^features:\s*\n([\s\S]*?)^---/m)?.[1];
for (const [name, section] of [
  ['hero', hero],
  ['features', features],
]) {
  assert.ok(
    section?.includes(`link: /${course}/`),
    `${course}: missing home ${name} link`,
  );
}
const nav = JSON.parse(readFileSync('docs/_nav.json', 'utf8'));
assert.ok(
  nav.some((item) => item.link === `/${course}/`),
  `${course}: missing navigation link`,
);
console.log(
  'PASS: log analysis chapter order, anchors, distribution links and home/navigation entries',
);
