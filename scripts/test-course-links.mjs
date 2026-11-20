import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { checkLocalLink } from './check-course-docs.mjs';

test('site routes, base paths and downloads resolve to files and validate anchors', () => {
  const directory = mkdtempSync(path.join(os.tmpdir(), 'course-links-'));
  try {
    const docs = path.join(directory, 'docs');
    const root = path.join(docs, 'course');
    const file = path.join(root, 'index.md');
    for (const name of [
      'course',
      '日本語',
      'public/course',
      'public/assets-only',
    ]) {
      mkdirSync(path.join(docs, name), { recursive: true });
    }
    writeFileSync(file, '<a id="chapter"></a>');
    writeFileSync(path.join(docs, 'index.md'), '# Home');
    writeFileSync(path.join(docs, 'privacy.md'), '# Privacy');
    writeFileSync(path.join(docs, '日本語/index.md'), '<a id="intro"></a>');
    writeFileSync(path.join(docs, 'public/course/lab.zip'), 'download');
    const context = { docs, root, file, base: '/dev-lecture-materials/' };
    for (const target of [
      '/',
      '/dev-lecture-materials/',
      '/dev-lecture-materials',
      '/course/#chapter',
      '/dev-lecture-materials/course/#chapter',
      '/course/index.html#chapter',
      '/privacy',
      '/privacy.html',
      '/日本語/#intro',
      '/%E6%97%A5%E6%9C%AC%E8%AA%9E/#intro',
      '/course/lab.zip',
      '/dev-lecture-materials/course/lab.zip?download=1',
      './lab.zip',
      '../日本語/#intro',
      '#chapter',
      'https://example.test/missing',
    ]) {
      assert.doesNotThrow(() => checkLocalLink(target, context), target);
    }
    for (const target of [
      '/missing/',
      '/assets-only/',
      '/dev-lecture-materials/assets-only/',
      '/course/#missing',
      '/dev-lecture-materials/course/#missing',
      './missing.zip',
      '#missing',
    ]) {
      assert.throws(() => checkLocalLink(target, context), /missing/, target);
    }
    assert.doesNotThrow(() =>
      checkLocalLink('/course/#chapter', { ...context, base: '/' }),
    );
  } finally {
    rmSync(directory, { recursive: true });
  }
});
