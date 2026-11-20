import { execFileSync, spawnSync } from 'node:child_process';

export function runPythonScripts(scripts) {
  const candidates = process.platform === 'win32'
    ? [['python'], ['py', '-3'], ['python3']]
    : [['python3'], ['python']];
  const python = candidates.find(([file, ...args]) =>
    spawnSync(file, [...args, '-c', 'import sys; sys.exit(sys.version_info < (3, 10))']).status === 0);
  if (!python) throw new Error('Python 3.10 or newer is required. Add Python to PATH.');
  const [file, ...args] = python;
  for (const script of scripts) {
    execFileSync(file, [...args, '-B', ...script], { stdio: 'inherit' });
  }
}
