import { runPythonScripts } from './python-runner.mjs';

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

runPythonScripts(commands[action]);
