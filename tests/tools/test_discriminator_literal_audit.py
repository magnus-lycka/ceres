from pathlib import Path

from tools.discriminator_literal_audit import (
    audit_discriminator_literals,
    collect_discriminator_declarations,
    format_violation,
    relative_to_repo_root,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def test_collects_literal_default_declarations(tmp_path: Path) -> None:
    model_file = tmp_path / 'src' / 'ceres' / 'models.py'
    _write(
        model_file,
        """
from typing import Literal


class MarineEvent:
    type: Literal['marines_event_5'] = 'marines_event_5'
    kind: Literal['agent_mishap_2_refuse'] = 'agent_mishap_2_refuse'
    drive_type: Literal['mdrive_2'] = 'mdrive_2'
""",
    )

    declarations = collect_discriminator_declarations([tmp_path / 'src' / 'ceres'])

    assert {(declaration.field_name, declaration.literal) for declaration in declarations} == {
        ('type', 'marines_event_5'),
        ('kind', 'agent_mishap_2_refuse'),
        ('drive_type', 'mdrive_2'),
    }


def test_audit_ignores_the_original_declaration_statement(tmp_path: Path) -> None:
    model_file = tmp_path / 'src' / 'ceres' / 'models.py'
    _write(
        model_file,
        """
from typing import Literal


class MarineEvent:
    type: Literal['marines_event_5'] = 'marines_event_5'
""",
    )

    result = audit_discriminator_literals(
        declaration_paths=[tmp_path / 'src' / 'ceres'],
        scan_paths=[tmp_path / 'src' / 'ceres'],
    )

    assert result.ok


def test_audit_reports_illegal_reuse_in_tests_or_src(tmp_path: Path) -> None:
    _write(
        tmp_path / 'src' / 'ceres' / 'models.py',
        """
from typing import Literal


class MarineEvent:
    type: Literal['marines_event_5'] = 'marines_event_5'
""",
    )
    _write(
        tmp_path / 'tests' / 'test_bad.py',
        """
def test_thing():
    assert 'marines_event_5'
""",
    )

    result = audit_discriminator_literals(
        declaration_paths=[tmp_path / 'src' / 'ceres'],
        scan_paths=[tmp_path / 'src' / 'ceres', tmp_path / 'tests'],
    )

    assert not result.ok
    assert len(result.violations) == 1
    violation = result.violations[0]
    assert violation.literal == 'marines_event_5'
    assert violation.path == tmp_path / 'tests' / 'test_bad.py'


def test_audit_can_limit_scan_paths_to_avoid_known_noise(tmp_path: Path) -> None:
    _write(
        tmp_path / 'src' / 'ceres' / 'models.py',
        """
from typing import Literal


class MarineEvent:
    type: Literal['marines_event_5'] = 'marines_event_5'
""",
    )
    _write(
        tmp_path / 'tests' / 'allowed_for_now.py',
        """
X = 'marines_event_5'
""",
    )
    _write(
        tmp_path / 'tests' / 'scanned' / 'test_bad.py',
        """
Y = 'marines_event_5'
""",
    )

    result = audit_discriminator_literals(
        declaration_paths=[tmp_path / 'src' / 'ceres'],
        scan_paths=[tmp_path / 'tests' / 'scanned'],
    )

    assert not result.ok
    assert {violation.path for violation in result.violations} == {tmp_path / 'tests' / 'scanned' / 'test_bad.py'}


def test_audit_reports_illegal_reuse_in_html_templates(tmp_path: Path) -> None:
    _write(
        tmp_path / 'src' / 'ceres' / 'models.py',
        """
from typing import Literal


class MarineEvent:
    type: Literal['marines_event_5'] = 'marines_event_5'
""",
    )
    template_path = tmp_path / 'src' / 'ceres' / 'templates' / 'bad.html'
    _write(
        template_path,
        """
<div data-kind="marines_event_5">bad</div>
""",
    )

    result = audit_discriminator_literals(
        declaration_paths=[tmp_path / 'src' / 'ceres'],
        scan_paths=[tmp_path / 'src' / 'ceres'],
    )

    assert not result.ok
    assert any(
        violation.literal == 'marines_event_5' and violation.path == template_path for violation in result.violations
    )


def test_audit_real_source_code_scans_marines_file() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    marines_path = repo_root / 'src' / 'ceres' / 'character' / 'careers' / 'marines.py'

    declarations = collect_discriminator_declarations([marines_path])
    result = audit_discriminator_literals(
        declaration_paths=[marines_path],
        scan_paths=[marines_path],
    )

    assert 'marines_event_5' in {declaration.literal for declaration in declarations}
    assert result.ok


def test_format_violation_uses_relative_paths_and_definition_location(tmp_path: Path) -> None:
    model_file = tmp_path / 'src' / 'ceres' / 'models.py'
    test_file = tmp_path / 'tests' / 'test_bad.py'
    _write(
        model_file,
        """
from typing import Literal


class MarineEvent:
    type: Literal['marines_event_5'] = 'marines_event_5'
""",
    )
    _write(
        test_file,
        """
VALUE = 'marines_event_5'
""",
    )

    result = audit_discriminator_literals(
        declaration_paths=[tmp_path / 'src' / 'ceres'],
        scan_paths=[tmp_path / 'tests'],
    )
    declarations = result.declarations_by_literal()['marines_event_5']
    rendered = format_violation(result.violations[0], declarations=declarations, repo_root=tmp_path)

    assert rendered == "tests/test_bad.py:2:8: 'marines_event_5' (defined at src/ceres/models.py:6)"


def test_relative_to_repo_root_returns_relative_path_when_possible(tmp_path: Path) -> None:
    path = tmp_path / 'src' / 'ceres' / 'thing.py'
    _write(path, '')

    assert relative_to_repo_root(path, tmp_path) == Path('src/ceres/thing.py')
