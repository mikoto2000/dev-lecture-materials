import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

export function checkLocalLink(target, { docs, root, file, base }) {
  if (/^(?:[a-z][\w+.-]*:|\/\/)/i.test(target)) return;
  const [resource, fragment] = target.split('#');
  let name = decodeURIComponent(resource.split('?')[0]);
  let candidates;
  if (!name) {
    candidates = [file];
  } else if (name.startsWith('/')) {
    if (name === base.slice(0, -1)) name = '/';
    else if (name.startsWith(base)) name = '/' + name.slice(base.length);
    const source = path.join(docs, name);
    candidates = [
      ...(name.endsWith('.md') ? [source] : []),
      ...(name.endsWith('.html') ? [source.slice(0, -5) + '.md'] : []),
      ...(path.extname(name) === '' ? [source + '.md', path.join(source, 'index.md')] : []),
      path.join(docs, 'public', name),
      path.join(docs, 'public', name, 'index.html'),
    ];
  } else {
    const source = path.resolve(root, name);
    candidates = [source, path.join(source, 'index.md'),
      path.resolve(docs, 'public', path.basename(root), name)];
  }
  const local = candidates.find(candidate => existsSync(candidate) && statSync(candidate).isFile());
  assert.ok(local, `${path.basename(root)}: missing ${target}`);
  if (fragment && local.endsWith('.md')) {
    assert.ok(readFileSync(local, 'utf8').includes(`<a id="${decodeURIComponent(fragment)}"></a>`),
      `${path.basename(root)}: missing anchor ${target}`);
  }
}

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
  const base = readFileSync('rspress.config.ts', 'utf8').match(/^\s*base:\s*['"]([^'"]+)['"]/m)?.[1];
  assert.ok(base?.startsWith('/') && base.endsWith('/'), 'Expected an explicit site base in rspress.config.ts');
  const context = { docs, root, file, base };
  for (const [, target] of prose.matchAll(/\]\(([^)]+)\)/g)) {
    checkLocalLink(target, context);
  }
  for (const [, target] of prose.matchAll(/(?:href|src)="([^"]+)"/g)) {
    checkLocalLink(target, context);
  }
  return text;
}
