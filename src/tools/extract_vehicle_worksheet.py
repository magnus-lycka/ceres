"""Extract the tables from the official Vehicle Design Worksheet.

The worksheet distributed with the Vehicle Handbook holds the rules as data: two
dozen named tables covering options, weapons, features, power, armour and the
type ladders. The tables are literals rather than formulas, so they can be read
without a spreadsheet application, and are far easier to check a transcription
against than the book's typeset tables.

Reads only the standard library: an .xlsx is a zip of XML.

    uv run python -m tools.extract_vehicle_worksheet WORKSHEET.xlsx [OUT_DIR]

Writes one JSON file per table plus an index. The default output directory is
under refs/, which is not committed, because the worksheet is source material
rather than something Ceres owns.
"""

import json
from pathlib import Path
import re
import sys
from typing import TypedDict
import zipfile

from defusedxml import ElementTree as DefusedElementTree

_NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
_REL_NS = {'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
_DEFAULT_OUT = Path('refs/vehicle/worksheet')


class Table(TypedDict):
    """One named table, as it is declared in the workbook."""

    sheet: str
    ref: str
    columns: list[str]
    rows: list[dict[str, object]]


def _column_index(reference: str) -> int:
    """Turn a cell reference such as 'AB12' into a 1-based column number."""
    letters = re.sub(r'[^A-Z]', '', reference)
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord('A') + 1)
    return index


def _row_number(reference: str) -> int:
    return int(re.sub(r'[A-Z]+', '', reference))


class Worksheet:
    """One .xlsx, opened for reading."""

    def __init__(self, path: Path):
        self._zip = zipfile.ZipFile(path)
        self._shared = self._read_shared_strings()

    def _xml(self, name: str):
        """Parse one part of the archive.

        Defused rather than the standard parser: the file is whatever the caller
        points at, and a hostile .xlsx could otherwise exhaust memory through
        entity expansion.
        """
        return DefusedElementTree.fromstring(self._zip.read(name))

    def _read_shared_strings(self) -> list[str]:
        if 'xl/sharedStrings.xml' not in self._zip.namelist():
            return []
        root = self._xml('xl/sharedStrings.xml')
        return [''.join(t.text or '' for t in si.iter(f'{{{_NS["m"]}}}t')) for si in root]

    def _cell_value(self, cell) -> object:
        """The cell's value, resolving shared strings and preferring cached results."""
        kind = cell.get('t')
        if kind == 'inlineStr':
            return ''.join(t.text or '' for t in cell.iter(f'{{{_NS["m"]}}}t'))
        value = cell.find('m:v', _NS)
        if value is None or value.text is None:
            return None
        if kind == 's':
            return self._shared[int(value.text)]
        if kind in (None, 'n'):
            number = float(value.text)
            return int(number) if number.is_integer() else number
        if kind == 'b':
            return value.text == '1'
        return value.text

    def sheet_parts(self) -> dict[str, str]:
        """Sheet name to the archive path holding it."""
        rels = self._xml('xl/_rels/workbook.xml.rels')
        targets = {rel.get('Id', ''): rel.get('Target', '') for rel in rels}
        sheets: dict[str, str] = {}
        for sheet in self._xml('xl/workbook.xml').iter(f'{{{_NS["m"]}}}sheet'):
            rel = sheet.get(f'{{{_REL_NS["r"]}}}id', '')
            name = sheet.get('name', '')
            sheets[name] = 'xl/' + targets.get(rel, '').lstrip('/')
        return sheets

    def _table_owner(self) -> dict[str, tuple[str, str]]:
        """Table part path to the sheet it belongs to, as (sheet name, part)."""
        owners: dict[str, tuple[str, str]] = {}
        for name, part in self.sheet_parts().items():
            rel_name = part.replace('worksheets/', 'worksheets/_rels/') + '.rels'
            if rel_name not in self._zip.namelist():
                continue
            for rel in self._xml(rel_name):
                target = rel.get('Target', '')
                if '/tables/' in target:
                    owners['xl/tables/' + target.rsplit('/', 1)[-1]] = (name, part)
        return owners

    def _cells(self, sheet_part: str) -> dict[tuple[int, int], object]:
        grid: dict[tuple[int, int], object] = {}
        for cell in self._xml(sheet_part).iter(f'{{{_NS["m"]}}}c'):
            reference = cell.get('r')
            if reference:
                grid[(_row_number(reference), _column_index(reference))] = self._cell_value(cell)
        return grid

    def tables(self) -> dict[str, Table]:
        """Every named table, as its declared columns and the rows beneath them."""
        owners = self._table_owner()
        extracted: dict[str, Table] = {}
        for part, (sheet_name, sheet_part) in sorted(owners.items()):
            root = self._xml(part)
            name = root.get('displayName') or root.get('name') or part
            first, last = root.get('ref', 'A1:A1').split(':')
            columns = [c.get('name', '') for c in root.iter(f'{{{_NS["m"]}}}tableColumn')]
            grid = self._cells(sheet_part)
            left = _column_index(first)
            header_row = _row_number(first)
            header_offset = 1 if root.get('headerRowCount') != '0' else 0
            rows = []
            for row in range(header_row + header_offset, _row_number(last) + 1):
                values = {col: grid.get((row, left + i)) for i, col in enumerate(columns)}
                if any(v is not None for v in values.values()):
                    rows.append(values)
            extracted[name] = Table(sheet=sheet_name, ref=root.get('ref', ''), columns=columns, rows=rows)
        return extracted


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    source = Path(argv[0]).expanduser()
    out_dir = Path(argv[1]) if len(argv) > 1 else _DEFAULT_OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    tables = Worksheet(source).tables()
    index = {}
    for name, table in tables.items():
        path = out_dir / f'{name}.json'
        path.write_text(json.dumps(table, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        index[name] = {'sheet': table['sheet'], 'ref': table['ref'], 'rows': len(table['rows'])}
        print(f'{name:22} {len(table["rows"]):>4} rows -> {path}')
    (out_dir / 'index.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')
    print(f'\n{len(tables)} tables written to {out_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
