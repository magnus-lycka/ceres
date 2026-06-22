from pathlib import Path

from tools.discriminator_literal_audit import audit_discriminator_literals, format_violation


def test_audit_discriminator_literals_repo_wide() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = audit_discriminator_literals(
        declaration_paths=[
            repo_root / 'src' / 'ceres',
        ],
        scan_paths=[
            repo_root / 'src' / 'ceres' / 'character',
            repo_root / 'tests' / 'character',
        ],
    )

    declarations_by_literal = result.declarations_by_literal()
    violations = '\n'.join(
        format_violation(
            violation,
            declarations=declarations_by_literal[violation.literal],
            repo_root=repo_root,
        )
        for violation in result.violations
    )
    assert result.ok, (
        f'Discriminator literal re-use detected outside canonical Literal declarations '
        f'({len(result.violations)} found):\n'
        f'{violations}'
    )
