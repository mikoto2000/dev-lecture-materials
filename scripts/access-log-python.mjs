import { runPythonScripts } from './python-runner.mjs';

const actions = {
  package: [
    ['scripts/access_log_config.py'],
    ['scripts/package-access-log-lab.py'],
  ],
  'check-package': [
    ['scripts/access_log_config.py', '--check'],
    ['scripts/package-access-log-lab.py', '--check'],
  ],
  test: [['scripts/test-access-log.py']],
  'test-compose': [['scripts/test-access-log-compose.py']],
  'security-package': [
    ['scripts/security_log_config.py'],
    ['scripts/package-security-log-lab.py'],
  ],
  'security-check-package': [
    ['scripts/security_log_config.py', '--check'],
    ['scripts/package-security-log-lab.py', '--check'],
    ['scripts/test-security-log-assets.py'],
  ],
  'security-test': [
    ['scripts/test-security-log.py'],
    ['scripts/test-security-log-compose-config.py'],
  ],
  'security-test-compose': [['scripts/test-security-log-compose.py']],
};
const action = process.argv[2];
if (!Object.hasOwn(actions, action))
  throw new Error(`Unknown access log action: ${action}`);
runPythonScripts(actions[action]);
