import { execFileSync, spawnSync } from 'node:child_process';

const actions = {
  package: [['scripts/access_log_config.py'], ['scripts/package-access-log-lab.py']],
  'check-package': [['scripts/access_log_config.py', '--check'], ['scripts/package-access-log-lab.py', '--check']],
  test: [['scripts/test-access-log.py']],
  'test-compose': [['scripts/test-access-log-compose.py']],
  'security-package': [['scripts/security_log_config.py'], ['scripts/package-security-log-lab.py']],
  'security-check-package': [['scripts/security_log_config.py', '--check'], ['scripts/package-security-log-lab.py', '--check'], ['scripts/test-security-log-assets.py']],
  'security-test': [['scripts/test-security-log.py']],
  'security-test-compose': [['scripts/test-security-log-compose.py']],
};
const action = process.argv[2];
if (!Object.hasOwn(actions, action)) throw new Error(`Unknown access log action: ${action}`);
const candidates = process.platform === 'win32'
  ? [['python'], ['py', '-3'], ['python3']] : [['python3'], ['python']];
const python = candidates.find(([file, ...args]) =>
  spawnSync(file, [...args, '-c', 'import sys; sys.exit(sys.version_info < (3, 10))']).status === 0);
if (!python) throw new Error('Python 3.10 or newer is required for authoring checks.');
const [file, ...args] = python;
for (const script of actions[action]) execFileSync(file, [...args, '-B', ...script], { stdio: 'inherit' });
