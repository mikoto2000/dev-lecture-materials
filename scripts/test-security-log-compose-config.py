"""Reject unsafe or incorrect learner Compose models without needing Docker."""
import copy
import unittest

from security_log_compose import validate


def model():
    # Independent expected model: Docker's normalized Compose JSON shape.
    services = {name: {'image': image, 'volumes': []} for name, image in {
        'demo': 'python:3.12.14-slim', 'traffic': 'python:3.12.14-slim',
        'notification-sink': 'python:3.12.14-slim', 'loki': 'grafana/loki:3.7.10',
        'grafana': 'grafana/grafana:13.3.1', 'alloy': 'grafana/alloy:v1.22.0'}.items()}
    for name, published, target in [('demo', '18790', 8080), ('grafana', '13010', 3000)]:
        services[name]['ports'] = [{'host_ip': '127.0.0.1', 'published': published,
                                   'target': target, 'protocol': 'tcp'}]
    for name in ('demo', 'traffic'):
        services[name]['volumes'] = [{'type': 'volume', 'source': 'demo-state', 'target': '/state'}]
    return {'name': 'security-log-lab', 'services': services}


class ComposeConfigTests(unittest.TestCase):
    def test_expected_model(self):
        validate(model())

    def test_rejects_regressions(self):
        original = model()
        mutations = [
            lambda c: c.update(name='access-log-lab'),
            lambda c: c['services']['demo']['ports'][0].update(published='18780'),
            lambda c: c['services']['grafana']['ports'][0].update(published='13000'),
            lambda c: c['services']['grafana']['ports'][0].update(host_ip='0.0.0.0'),
            lambda c: c['services']['grafana']['ports'][0].pop('host_ip'),
            lambda c: c['services']['demo']['ports'][0].update(target=80),
            lambda c: c['services']['loki'].update(ports=c['services']['demo']['ports']),
            lambda c: c['services']['alloy'].update(image='grafana/alloy:latest'),
            lambda c: c['services']['demo']['volumes'].append(
                {'type': 'bind', 'source': '/var/run/docker.sock', 'target': '/socket'}),
            lambda c: c['services']['demo']['volumes'].append(
                {'type': 'bind', 'source': '/socket', 'target': '/var/run/docker.sock'}),
            lambda c: c['services']['traffic'].update(volumes=[]),
            lambda c: c['services']['traffic']['volumes'][0].update(read_only=True),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = copy.deepcopy(original)
                mutate(changed)
                with self.assertRaises((AssertionError, KeyError)):
                    validate(changed)


if __name__ == '__main__':
    unittest.main()
