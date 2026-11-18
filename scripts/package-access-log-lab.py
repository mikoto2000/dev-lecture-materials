"""Deterministic archive of the learner lab; no runtime data is included."""
import io
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'docs/public/access-log-monitoring/lab'
ARCHIVE = LAB.parent / 'access-log-lab.zip'
NAMES = ['README.md', 'compose.yaml', 'config.alloy', 'loki.yaml', 'demo.py',
         'grafana/provisioning/datasources/loki.yaml',
         'grafana/provisioning/dashboards/local.yaml',
         'grafana/provisioning/alerting/local.json',
         'grafana/dashboards/access-log.json']


def archive_bytes():
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in NAMES:
            entry = zipfile.ZipInfo('access-log-lab/' + name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (LAB / name).read_bytes())
    return output.getvalue()


if __name__ == '__main__':
    expected = archive_bytes()
    if '--check' in sys.argv:
        if not ARCHIVE.exists() or ARCHIVE.read_bytes() != expected:
            raise SystemExit('ZIP differs: run npm run package:access-log')
        print('PASS: access log ZIP matches lab sources')
    else:
        ARCHIVE.write_bytes(expected)
        print('Wrote', ARCHIVE.relative_to(ROOT))
