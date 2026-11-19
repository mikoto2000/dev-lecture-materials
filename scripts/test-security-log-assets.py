"""Changes to shared templates must fail explicitly instead of producing a bad ZIP."""
from pathlib import Path
import unittest
from unittest import mock

from package_access_log_assets import security_assets


class TemplateTests(unittest.TestCase):
    def test_current_templates(self):
        files = security_assets()
        self.assertIn(b'name: security-log-lab', files['compose.yaml'])
        self.assertIn(b'"job" = "security-log-lab"', files['config.alloy'])

    def test_rejects_changed_templates(self):
        read_text = Path.read_text
        mutations = [
            ('compose.yaml', '    depends_on: [demo]', '    depends_on:\n      - demo'),
            ('compose.yaml', '    depends_on: [demo]', '    depends_on: [demo]\n    depends_on: [demo]'),
            ('compose.yaml', '127.0.0.1:13000:3000', '127.0.0.1:13001:3000'),
            ('compose.yaml', '127.0.0.1:18780:8080', '127.0.0.1:18781:8080'),
            ('compose.yaml', 'name: access-log-lab', 'name: renamed-lab'),
            ('compose.yaml', '/lab/demo.py, server', '/lab/demo.py, serve'),
            ('compose.yaml', '/lab/demo.py, traffic', '/lab/demo.py, generate'),
            ('compose.yaml', '- ./demo.py:/lab/demo.py:ro', '- ./demo.py:/lab/demo.py:ro,Z'),
            ('config.alloy', 'access-log-lab', 'renamed-lab'),
        ]
        for filename, old, new in mutations:
            with self.subTest(filename=filename, marker=old):
                def changed(path, *args, **kwargs):
                    text = read_text(path, *args, **kwargs)
                    return text.replace(old, new) if path.name == filename else text
                with mock.patch.object(Path, 'read_text', autospec=True, side_effect=changed):
                    with self.assertRaisesRegex(ValueError, 'Security lab template changed'):
                        security_assets()


if __name__ == '__main__':
    unittest.main()
