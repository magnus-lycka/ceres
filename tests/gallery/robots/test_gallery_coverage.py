"""Enforce that every approval robot test file is registered in test_gallery.py."""

from pathlib import Path
import re


def test_all_approval_robots_in_gallery():
    approval_dir = Path(__file__).parent.parent.parent / 'approval' / 'robots'
    excluded = {'__init__.py'}

    approval_files = {f.stem for f in approval_dir.glob('test_*.py') if f.name not in excluded}

    gallery_text = (Path(__file__).parent / 'test_gallery.py').read_text(encoding='utf-8')
    imported_modules = set(re.findall(r'from tests\.approval\.robots\.(test_\w+) import', gallery_text))

    missing = approval_files - imported_modules
    assert not missing, (
        f'Approval robot files not imported in gallery: {sorted(missing)}\nAdd the builder to test_gallery.py.'
    )
