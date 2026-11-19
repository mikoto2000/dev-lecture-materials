import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const output = path.resolve('doc_build');
const routes = JSON.parse(readFileSync(new URL('./legacy-routes.json', import.meta.url), 'utf8'));

for (const [route, target] of Object.entries(routes)) {
  for (const name of [`${route}.html`, `${route}/index.html`]) {
    const [page, anchor] = target.split('#');
    const directory = path.posix.relative(path.posix.dirname(name), page);
    const destination = `${directory ? `${directory}/` : './'}#${anchor}`;
    const file = path.join(output, name);
    // Relative destinations preserve the site's base path on GitHub Pages.
    // Old section fragments are replaced with the consolidated chapter anchor.
    const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>教材の移動先</title>
<link rel="canonical" href="${destination}">
<meta http-equiv="refresh" content="0;url=${destination}">
<script>
const target = new URL(${JSON.stringify(destination)}, location.href);
target.search = location.search;
location.replace(target.href);
</script>
</head>
<body><p>教材を統合しました。<a href="${destination}">該当章へ移動</a></p></body>
</html>
`;
    mkdirSync(path.dirname(file), { recursive: true });
    writeFileSync(file, html);
  }
}
console.log(`PASS: generated redirects for ${Object.keys(routes).length} legacy chapter URLs`);
