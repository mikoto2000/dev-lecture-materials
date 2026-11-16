import { execFileSync, spawnSync } from 'node:child_process';

const commands = {
  package: [['scripts/package-monitoring-lab.py']],
  'check-package': [['scripts/package-monitoring-lab.py', '--check']],
  test: [
    ['docs/public/monitoring-intro/lab/test_lab.py'],
    ['docs/public/monitoring-intro/lab/test_container.py'],
    ['scripts/test-resource-command-checks.py'],
  ],
  'check-compose': [['scripts/check-monitoring-compose.py']],
  'test-compose': [['scripts/test-compose-monitoring.py']],
};

const action = process.argv[2];
if (!Object.hasOwn(commands, action)) {
  throw new Error(`Unknown monitoring command: ${action}`);
}

const candidates = process.platform === 'win32'
  ? [['python'], ['py', '-3'], ['python3']]
  : [['python3'], ['python']];
const python = candidates.find(([file, ...args]) =>
  spawnSync(file, [...args, '-c', 'import sys; sys.exit(sys.version_info < (3, 10))']).status === 0);
if (!python) {
  throw new Error('Python 3.10 or newer is required. Add Python to PATH.');
}
const [file, ...args] = python;
for (const script of commands[action]) {
  execFileSync(file, [...args, '-B', ...script], { stdio: 'inherit' });
}
