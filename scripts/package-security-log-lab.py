"""Standalone security ZIP composed from shared base assets and security overrides."""
import io
from pathlib import Path
import sys
import zipfile

from package_access_log_assets import security_assets

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'docs/public/security-log-monitoring/security-log-lab.zip'


def archive_bytes():
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(security_assets().items()):
            entry = zipfile.ZipInfo('security-log-lab/' + name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return output.getvalue()


if __name__ == '__main__':
    expected = archive_bytes()
    if '--check' in sys.argv:
        if not ARCHIVE.exists() or ARCHIVE.read_bytes() != expected:
            raise SystemExit('Security ZIP differs: run npm run package:security-log')
        print('PASS: security ZIP matches sources')
    else:
        ARCHIVE.write_bytes(expected)
        print('Wrote', ARCHIVE.relative_to(ROOT))
