/* Shared analysis engine: no network, storage, or external dependencies. */
globalThis.LogAnalysis = (() => {
  const required = ['time', 'client_ip', 'method', 'path', 'status', 'user_agent', 'request_id', 'event'];
  const groups = ['minute', 'client_ip', 'path', 'status', 'account', 'outcome', 'user_agent'];
  function parse(source) {
    const records = [];
    const errors = [];
    const lines = source.split(/\r?\n/);
    if (lines.length > 10001) throw new Error('行数の上限は10,000行です。');
    for (const [index, line] of lines.entries()) {
      if (!line.trim()) continue;
      try {
        const row = JSON.parse(line);
        if (!row || Array.isArray(row) || required.some(key => !Object.hasOwn(row, key))) throw new Error('必須項目が不足しています');
        if (required.filter(key => key !== 'status').some(key => typeof row[key] !== 'string' || !row[key].length)) throw new Error('文字列項目が不正です');
        if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(row.time) || !Number.isFinite(Date.parse(row.time)) || new Date(row.time).toISOString().replace('.000Z', 'Z') !== row.time.replace('.000Z', 'Z')) throw new Error('時刻は実在するUTC日時（末尾Z）にしてください');
        if (!Number.isInteger(row.status) || row.status < 100 || row.status > 599) throw new Error('statusは100〜599の整数です');
        if (!['access', 'auth'].includes(row.event)) throw new Error('eventはaccessまたはauthです');
        if (row.event === 'auth' && (!['success', 'failure'].includes(row.outcome) || typeof row.account !== 'string' || !row.account)) throw new Error('認証イベントにはaccountとoutcomeが必要です');
        records.push({ ...row, minute: `${row.time.slice(0, 16)}:00Z` });
      } catch (error) {
        errors.push({ line: index + 1, message: error.message });
      }
    }
    return { records, errors };
  }
  function filter(records, query = {}) {
    for (const key of ['start', 'end']) {
      if (query[key] && !Number.isFinite(Date.parse(query[key]))) throw new Error('日時の形式を確認してください。');
    }
    if (query.start && query.end && Date.parse(query.start) >= Date.parse(query.end)) throw new Error('終了時刻は開始時刻より後にしてください。');
    return records.filter(row =>
      (!query.start || Date.parse(row.time) >= Date.parse(query.start)) &&
      (!query.end || Date.parse(row.time) < Date.parse(query.end)) &&
      (!query.ip || row.client_ip === query.ip) &&
      (!query.path || row.path.includes(query.path)) &&
      (!query.status || String(row.status) === query.status) &&
      (!query.event || row.event === query.event) &&
      (!query.outcome || row.outcome === query.outcome));
  }
  function aggregate(records, key) {
    if (!groups.includes(key)) throw new Error('集計項目が不正です。');
    const buckets = new Map();
    for (const row of records) {
      const value = String(row[key] ?? '（なし）');
      const bucket = buckets.get(value) ?? { value, count: 0, errors: 0, failures: 0, paths: new Set(), first: row.time, last: row.time };
      bucket.count++;
      bucket.errors += Number(row.status >= 400);
      bucket.failures += Number(row.event === 'auth' && row.outcome === 'failure');
      bucket.paths.add(row.path);
      if (row.time < bucket.first) bucket.first = row.time;
      if (row.time > bucket.last) bucket.last = row.time;
      buckets.set(value, bucket);
    }
    return [...buckets.values()].map(row => ({ ...row, paths: row.paths.size }))
      .sort((a, b) => key === 'minute' ? a.value.localeCompare(b.value) : b.count - a.count || a.value.localeCompare(b.value));
  }
  return { parse, filter, aggregate };
})();
