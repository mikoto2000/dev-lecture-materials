"""Build a reproducible source-only archive, or check it against source bytes."""
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'docs/public/monitoring-intro/lab'
ARCHIVE = LAB.parent / 'monitoring-lab.zip'
NAMES = ['.gitignore', 'README.md', 'app.py', 'common.py', 'labctl.py',
         'monitor.py', 'watchdog.py', 'test_lab.py']


def archive_bytes():
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in NAMES:
            info = zipfile.ZipInfo('monitoring-lab/' + name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LAB / name).read_bytes())
    return buffer.getvalue()


expected = archive_bytes()
if '--check' in sys.argv:
    if not ARCHIVE.exists() or ARCHIVE.read_bytes() != expected:
        raise SystemExit('Archive differs from lab sources: run npm run package:monitoring')
    print('PASS: reproducible monitoring ZIP matches the eight source files')
else:
    ARCHIVE.write_bytes(expected)
    print(f'Wrote {ARCHIVE.relative_to(ROOT)} ({len(expected)} bytes)')
