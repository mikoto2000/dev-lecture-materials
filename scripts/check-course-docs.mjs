import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

// Every course is a single document; downloads remain in docs/public.
export function checkCourseDocs(course, sections, { topAnchor = true } = {}) {
  const docs = path.resolve('docs');
  const root = path.join(docs, course);
  const file = path.join(root, 'index.md');
  const pages = readdirSync(root, { recursive: true }).filter(name => name.endsWith('.md'));
  assert.deepEqual(pages, ['index.md'], `${course}: keep the course in one Markdown file`);
  const text = readFileSync(file, 'utf8');
  assert.equal((text.match(/^```/gm) ?? []).length % 2, 0, `${course}: unclosed fence`);
  const prose = text.replace(/^```[^\n]*\n[\s\S]*?^```[^\n]*$/gm, '');
  assert.equal((prose.match(/^# /gm) ?? []).length, 1, `${course}: expected one document title`);
  const anchors = [...prose.matchAll(/<a id="([^"]+)"><\/a>/g)].map(match => match[1]);
  assert.deepEqual(anchors, [...(topAnchor ? ['top'] : []), ...sections], `${course}: chapter order or anchors changed`);
  assert.equal(new Set(anchors).size, anchors.length, `${course}: duplicate anchor`);
  const metadata = JSON.parse(readFileSync(path.join(root, '_meta.json'), 'utf8'));
  assert.deepEqual(metadata, [{ type: 'file', name: 'index', label: '教材全文' }]);
  for (const [, target] of prose.matchAll(/\]\(([^)]+)\)/g)) {
    if (/^(?:[a-z][\w+.-]*:|\/\/)/i.test(target)) continue;
    const [name, fragment] = target.split('#');
    const local = name ? (name.startsWith('/') ? path.join(docs, 'public', name) : path.resolve(root, name)) : file;
    assert.ok(existsSync(local), `${course}: missing ${target}`);
    if (fragment && local.endsWith('.md')) {
      assert.ok(readFileSync(local, 'utf8').includes(`<a id="${fragment}"></a>`), `${course}: missing anchor ${target}`);
    }
  }
  for (const [, target] of prose.matchAll(/(?:href|src)="([^"#]+)"/g)) {
    if (/^(?:[a-z][\w+.-]*:|\/\/)/i.test(target)) continue;
    assert.ok(existsSync(path.resolve(root, target)) || existsSync(path.join(docs, 'public', course, target)),
      `${course}: missing download ${target}`);
  }
  return text;
}
