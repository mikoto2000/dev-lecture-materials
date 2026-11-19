/* global LogAnalysis, LogSamples */
(() => {
  const el = id => document.getElementById(id);
  let records = [];
  let loadVersion = 0;
  function table(id, rows) {
    const fragment = document.createDocumentFragment();
    for (const values of rows) {
      const tr = document.createElement('tr');
      for (const value of values) {
        const td = document.createElement('td');
        td.textContent = String(value ?? '');
        tr.append(td);
      }
      fragment.append(tr);
    }
    el(id).replaceChildren(fragment);
  }
  function render() {
    try {
      const query = Object.fromEntries(['ip', 'path', 'status', 'event', 'outcome'].map(key => [key, el(key).value]));
      for (const key of ['start', 'end']) query[key] = el(key).value ? `${el(key).value}Z` : '';
      const rows = LogAnalysis.filter(records, query).sort((a, b) => a.time.localeCompare(b.time));
      const groups = LogAnalysis.aggregate(rows, el('group').value);
      const errors = rows.filter(row => row.status >= 400).length;
      el('result-status').textContent = `${records.length}件中 ${rows.length}件 / 4xx・5xx ${errors}件（${rows.length ? (100 * errors / rows.length).toFixed(1) : '0.0'}%）/ 集計 ${groups.length}行。表示は各500行まで、集計は全該当ログが対象です。`;
      table('summary', groups.slice(0, 500).map(row => [row.value, row.count, row.errors, row.failures, row.paths, row.first, row.last]));
      table('rows', rows.slice(0, 500).map(row => [row.time, row.client_ip, row.method, row.path, row.status, row.event, row.account, row.outcome, row.user_agent, row.request_id]));
    } catch (error) {
      el('result-status').textContent = error.message;
      table('summary', []);
      table('rows', []);
    }
  }
  function clear(message) {
    records = [];
    el('load-status').textContent = message;
    el('errors').textContent = '';
    el('parse-errors').hidden = true;
    render();
  }
  function load(source, name) {
    el('filters').reset();
    try {
      const result = LogAnalysis.parse(source);
      records = result.records;
      el('load-status').textContent = `${name}: 有効 ${records.length}件 / 除外 ${result.errors.length}行。除外行は集計に含みません。`;
      el('errors').textContent = result.errors.slice(0, 100).map(row => `${row.line}行: ${row.message}`).join('\n');
      el('parse-errors').hidden = !result.errors.length;
      el('parse-errors').open = !!result.errors.length;
      render();
    } catch (error) { clear(error.message); }
  }
  el('load').addEventListener('click', () => {
    loadVersion++;
    el('file').value = '';
    load(LogSamples[el('sample').value], el('sample').selectedOptions[0].textContent);
  });
  el('file').addEventListener('change', async () => {
    const version = ++loadVersion;
    const file = el('file').files[0];
    if (!file) return;
    clear('読み込み中…');
    if (file.size > 2 * 1024 * 1024) { clear('2 MiB以下のファイルを選んでください。'); return; }
    try {
      const source = await file.text();
      if (version === loadVersion) load(source, file.name);
    } catch { if (version === loadVersion) clear('ファイルを読み込めませんでした。'); }
  });
  el('filters').addEventListener('submit', event => { event.preventDefault(); render(); });
  el('reset-filters').addEventListener('click', () => { el('filters').reset(); render(); });
  load(LogSamples.baseline, '01 正常時');
})();
