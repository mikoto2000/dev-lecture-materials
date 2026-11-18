import { checkCourseDocs } from './check-course-docs.mjs';

checkCourseDocs('コンテナで構築する開発環境', ['introduction', 'vol0', 'vol1', 'vol2', 'summary']);
console.log('PASS: Dev Container single document, chapter order, anchors, links and fences');
