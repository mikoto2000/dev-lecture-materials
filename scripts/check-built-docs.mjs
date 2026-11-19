import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { runInNewContext } from 'node:vm';

const output = path.resolve('doc_build');
const routes = JSON.parse(readFileSync(new URL('./legacy-routes.json', import.meta.url), 'utf8'));

for (const [route, target] of Object.entries(routes)) {
  const [page, anchor] = target.split('#');
  const html = readFileSync(path.join(output, page, 'index.html'), 'utf8');
  assert.ok(html.includes(`id="${anchor}"`), `${route}: missing destination chapter ${target}`);
  for (const name of [`${route}.html`, `${route}/index.html`]) {
    const redirect = readFileSync(path.join(output, name), 'utf8');
    const href = redirect.match(/<link rel="canonical" href="([^"]+)">/)?.[1];
    assert.ok(href, `${name}: missing canonical destination`);
    assert.equal(new URL(href, `https://example.test/dev-lecture-materials/${name}`).href,
      new URL(`https://example.test/dev-lecture-materials/${target}`).href, `${name}: wrong redirect destination`);
    assert.ok(redirect.includes(`content="0;url=${href}"`), `${name}: missing no-script redirect`);
    assert.ok(redirect.includes(`new URL(${JSON.stringify(href)}, location.href)`), `${name}: wrong script destination`);
    assert.ok(redirect.includes('location.replace(target.href)'), `${name}: must replace browser history`);
    const script = redirect.match(/<script>([\s\S]+?)<\/script>/)?.[1];
    for (const prefix of ['/', '/dev-lecture-materials/']) {
      const url = new URL(`https://example.test${prefix}${name}?from=bookmark#old-section`);
      let destination;
      runInNewContext(script, { URL, location: {
        href: url.href, search: url.search, replace: value => { destination = value; },
      } });
      const expected = new URL(`https://example.test${prefix}${target}`);
      expected.search = url.search;
      assert.equal(destination, expected.href, `${name}: preserve query and site base, replace old fragment`);
    }
  }
}

for (const course of new Set(Object.values(routes).map(target => target.split('/')[0]))) {
  const html = readFileSync(path.join(output, course, 'index.html'), 'utf8');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, `${course}: duplicate HTML ID`);
  // Markdown chapters stay consolidated even while old HTML routes are served.
  const pages = readdirSync(path.join('docs', course), { recursive: true }).filter(name => name.endsWith('.md'));
  assert.deepEqual(pages, ['index.md']);
}
console.log('PASS: legacy destinations, redirect variants, unique HTML IDs and consolidated Markdown');
