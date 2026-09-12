"""The worksheet extractor reads tables out of an .xlsx without a spreadsheet."""

import json
from pathlib import Path
import zipfile

from tools.extract_vehicle_worksheet import Worksheet, main

_CONTENT_TYPES = '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
_WORKBOOK = (
    '<?xml version="1.0"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets><sheet name="Reference" sheetId="1" r:id="rId1"/></sheets></workbook>'
)
_WB_RELS = (
    '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>'
)
_SHEET_RELS = (
    '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Target="../tables/table1.xml"/></Relationships>'
)
_SHARED = (
    '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<si><t>Size Name</t></si><si><t>Small</t></si><si><t>Heavy</t></si></sst>'
)
_SHEET = (
    '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>Cost</t></is></c></row>'
    '<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>0</v></c></row>'
    '<row r="3"><c r="A3" t="s"><v>2</v></c><c r="B3"><v>2.5</v></c></row>'
    '</sheetData></worksheet>'
)
_TABLE = (
    '<?xml version="1.0"?>'
    '<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" displayName="SizeNumber" ref="A1:B3">'
    '<tableColumns><tableColumn name="Size Name"/><tableColumn name="Cost"/></tableColumns></table>'
)


def _workbook(path: Path) -> Path:
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('[Content_Types].xml', _CONTENT_TYPES)
        archive.writestr('xl/workbook.xml', _WORKBOOK)
        archive.writestr('xl/_rels/workbook.xml.rels', _WB_RELS)
        archive.writestr('xl/worksheets/sheet1.xml', _SHEET)
        archive.writestr('xl/worksheets/_rels/sheet1.xml.rels', _SHEET_RELS)
        archive.writestr('xl/tables/table1.xml', _TABLE)
        archive.writestr('xl/sharedStrings.xml', _SHARED)
    return path


def test_it_reads_a_table_by_its_declared_columns(tmp_path):
    tables = Worksheet(_workbook(tmp_path / 'w.xlsx')).tables()

    assert list(tables) == ['SizeNumber']
    assert tables['SizeNumber']['columns'] == ['Size Name', 'Cost']
    assert tables['SizeNumber']['sheet'] == 'Reference'


def test_it_resolves_shared_strings_and_numbers(tmp_path):
    rows = Worksheet(_workbook(tmp_path / 'w.xlsx')).tables()['SizeNumber']['rows']

    # The header row is not data, and a whole number stays whole.
    assert rows == [{'Size Name': 'Small', 'Cost': 0}, {'Size Name': 'Heavy', 'Cost': 2.5}]


def test_it_writes_one_file_per_table_plus_an_index(tmp_path):
    out = tmp_path / 'out'

    assert main([str(_workbook(tmp_path / 'w.xlsx')), str(out)]) == 0

    assert json.loads((out / 'SizeNumber.json').read_text())['columns'] == ['Size Name', 'Cost']
    assert json.loads((out / 'index.json').read_text())['SizeNumber']['rows'] == 2
