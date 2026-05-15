"""Enforce that every ship test file is registered in test_gallery.py."""

import ast
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


def test_all_gallery_outputs_cover_the_same_ship_set():
    gallery_path = Path(__file__).parent / 'test_gallery.py'
    tree = ast.parse(gallery_path.read_text(encoding='utf-8'))

    parametrized_ship_sets: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith('test_ship_gallery_'):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == 'parametrize'
                and len(decorator.args) >= 2
            ):
                parametrized_ship_sets[node.name] = _ship_names_from_parametrize(decorator)

    assert parametrized_ship_sets
    expected = next(iter(parametrized_ship_sets.values()))
    mismatches = {
        name: sorted(ship_set ^ expected) for name, ship_set in parametrized_ship_sets.items() if ship_set != expected
    }
    assert not mismatches, f'Gallery output parametrizations differ: {mismatches}'


def _ship_names_from_parametrize(node: ast.Call) -> set[str]:
    rows = node.args[1]
    if not isinstance(rows, ast.List):
        return set()
    names: set[str] = set()
    for row in rows.elts:
        if isinstance(row, ast.Tuple) and row.elts and isinstance(row.elts[0], ast.Constant):
            name = row.elts[0].value
            if isinstance(name, str):
                names.add(name)
    return names
