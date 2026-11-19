"""Validate the learner's Compose model before tests change published ports."""
import json
import subprocess


def validate(config):
    assert config['name'] == 'security-log-lab', 'unexpected project name'
    services = config['services']
    images = {'demo': 'python:3.12.14-slim', 'traffic': 'python:3.12.14-slim',
              'notification-sink': 'python:3.12.14-slim', 'loki': 'grafana/loki:3.7.10',
              'grafana': 'grafana/grafana:13.3.1', 'alloy': 'grafana/alloy:v1.22.0'}
    assert set(services) == set(images), 'unexpected services'
    ports = {'demo': ('18790', 8080), 'grafana': ('13010', 3000)}
    for name, service in services.items():
        assert service['image'] == images[name], f'{name}: unexpected image'
        bindings = service.get('ports', [])
        if name in ports:
            assert len(bindings) == 1, f'{name}: expected one loopback port'
            port = bindings[0]
            assert port['host_ip'] == '127.0.0.1', f'{name}: non-loopback port'
            assert (str(port['published']), port['target']) == ports[name], f'{name}: wrong port'
            assert port['protocol'] == 'tcp', f'{name}: wrong protocol'
        else:
            assert not bindings, f'{name}: must not publish ports'
        for volume in service.get('volumes', []):
            assert 'docker.sock' not in volume.get('source', ''), f'{name}: Docker socket source'
            assert 'docker.sock' not in volume['target'], f'{name}: Docker socket target'
    for name in ('demo', 'traffic'):
        assert any(volume['type'] == 'volume' and volume['source'] == 'demo-state'
                   and volume['target'] == '/state' and not volume.get('read_only', False)
                   for volume in services[name]['volumes']), f'{name}: missing shared scenario state'


def check(lab):
    result = subprocess.run(['docker', 'compose', '--project-directory', str(lab),
                             'config', '--format', 'json'], check=True,
                            capture_output=True, text=True, timeout=30)
    validate(json.loads(result.stdout))
    print('PASS: security Compose images, original ports, loopback bindings and scenario state', flush=True)
