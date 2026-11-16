import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

const root = 'docs/コンテナで構築する開発環境';
const chapters = ['INTRODUCTION.md', 'Vol0.md', 'Vol1.md', 'Vol2.md', 'まとめ.md'];
const pages = ['index.md', ...chapters];
const read = file => readFileSync(path.join(root, file), 'utf8');

assert.deepEqual(readdirSync(root).filter(file => file.endsWith('.md')).sort(), [...pages].sort());
const sidebar = JSON.parse(read('_meta.json'));
assert.deepEqual(sidebar.map(item => typeof item === 'string' ? item : `${item.name}.md`), pages);
const indexLinks = [...read('index.md').matchAll(/\]\(\.\/([^/)]+\.md)\)/g)];
assert.deepEqual(indexLinks.map(match => match[1]), chapters);

for (const [position, file] of pages.entries()) {
  const text = read(file);
  assert.equal((text.match(/^```/gm) || []).length % 2, 0, `${file}: unclosed fence`);
  if (position > 0 && position < pages.length - 1) {
    assert.ok(text.trimEnd().split('\n').at(-1).includes(`](./${pages[position + 1]})`),
      `${file}: missing next chapter link`);
  }
}
console.log(`PASS: ${pages.length} Dev Container pages, chapter order, next links and fences`);
