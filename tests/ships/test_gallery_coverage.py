"""Enforce that every ship test file is registered in test_gallery.py."""

from pathlib import Path
import re


def test_all_ship_test_files_in_gallery():
    ships_dir = Path(__file__).parent
    excluded = {'test_gallery.py', 'test_gallery_coverage.py'}

    ship_files = {f.stem for f in ships_dir.glob('test_*.py') if f.name not in excluded}

    gallery_text = (ships_dir / 'test_gallery.py').read_text(encoding='utf-8')
    imported_modules = set(re.findall(r'from \.(test_\w+) import', gallery_text))

    missing = ship_files - imported_modules
    assert not missing, (
        f'Ship test files not imported in test_gallery.py: {sorted(missing)}\n'
        'Add a build_<name>() function and register it in test_gallery.py.'
    )
