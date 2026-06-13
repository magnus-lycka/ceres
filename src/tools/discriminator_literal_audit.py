from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceSpan:
    path: Path
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int

    def contains(self, *, lineno: int, col_offset: int) -> bool:
        if lineno < self.lineno or lineno > self.end_lineno:
            return False
        if lineno == self.lineno and col_offset < self.col_offset:
            return False
        return not (lineno == self.end_lineno and col_offset >= self.end_col_offset)


@dataclass(frozen=True)
class DiscriminatorDeclaration:
    field_name: str
    literal: str
    span: SourceSpan


@dataclass(frozen=True)
class LiteralOccurrence:
    literal: str
    path: Path
    lineno: int
    col_offset: int


@dataclass(frozen=True)
class AuditResult:
    declarations: tuple[DiscriminatorDeclaration, ...]
    violations: tuple[LiteralOccurrence, ...]

    @property
    def ok(self) -> bool:
        return not self.violations

    def declarations_by_literal(self) -> dict[str, tuple[DiscriminatorDeclaration, ...]]:
        grouped: dict[str, list[DiscriminatorDeclaration]] = {}
        for declaration in self.declarations:
            grouped.setdefault(declaration.literal, []).append(declaration)
        return {literal: tuple(declarations) for literal, declarations in grouped.items()}


def _is_literal_annotation(annotation: ast.expr) -> bool:
    value = annotation.value if isinstance(annotation, ast.Subscript) else None
    if isinstance(value, ast.Name):
        return value.id == 'Literal'
    if isinstance(value, ast.Attribute):
        return value.attr == 'Literal'
    return False


def _literal_string_values(annotation: ast.expr) -> tuple[str, ...]:
    if not isinstance(annotation, ast.Subscript) or not _is_literal_annotation(annotation):
        return ()

    slice_node = annotation.slice
    values = slice_node.elts if isinstance(slice_node, ast.Tuple) else [slice_node]
    return tuple(value.value for value in values if isinstance(value, ast.Constant) and isinstance(value.value, str))


PYTHON_SUFFIX = '.py'
HTML_SUFFIX = '.html'
SCAN_SUFFIXES = (PYTHON_SUFFIX, HTML_SUFFIX)


def _iter_files(paths: list[Path], *, suffixes: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix in suffixes:
            files.append(path)
        elif path.is_dir():
            for suffix in suffixes:
                files.extend(sorted(path.rglob(f'*{suffix}')))
    return files


def _parse_python_file(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding='utf-8'), filename=str(path))


def collect_discriminator_declarations(paths: list[Path]) -> tuple[DiscriminatorDeclaration, ...]:
    declarations: list[DiscriminatorDeclaration] = []
    for path in _iter_files(paths, suffixes=(PYTHON_SUFFIX,)):
        tree = _parse_python_file(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.AnnAssign):
                continue
            if not isinstance(node.target, ast.Name):
                continue
            if node.value is None:
                continue
            if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                continue

            literal_values = _literal_string_values(node.annotation)
            if not literal_values or node.value.value not in literal_values:
                continue

            end_lineno = getattr(node, 'end_lineno', node.lineno)
            end_col_offset = getattr(node, 'end_col_offset', node.col_offset + 1)
            declarations.append(
                DiscriminatorDeclaration(
                    field_name=node.target.id,
                    literal=node.value.value,
                    span=SourceSpan(
                        path=path,
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        end_lineno=end_lineno,
                        end_col_offset=end_col_offset,
                    ),
                )
            )
    return tuple(declarations)


def _declaration_spans_by_literal(
    declarations: tuple[DiscriminatorDeclaration, ...],
) -> dict[str, list[SourceSpan]]:
    spans: dict[str, list[SourceSpan]] = {}
    for declaration in declarations:
        spans.setdefault(declaration.literal, []).append(declaration.span)
    return spans


def _find_python_literal_occurrences(path: Path, literals: set[str]) -> list[LiteralOccurrence]:
    occurrences: list[LiteralOccurrence] = []
    tree = _parse_python_file(path)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if node.value not in literals:
            continue
        occurrences.append(
            LiteralOccurrence(
                literal=node.value,
                path=path,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        )
    return occurrences


def _find_text_literal_occurrences(path: Path, literals: set[str]) -> list[LiteralOccurrence]:
    occurrences: list[LiteralOccurrence] = []
    text = path.read_text(encoding='utf-8')
    for literal in literals:
        start = text.find(literal)
        while start != -1:
            lineno = text.count('\n', 0, start) + 1
            line_start = text.rfind('\n', 0, start)
            col_offset = start if line_start == -1 else start - line_start - 1
            occurrences.append(
                LiteralOccurrence(
                    literal=literal,
                    path=path,
                    lineno=lineno,
                    col_offset=col_offset,
                )
            )
            start = text.find(literal, start + max(1, len(literal)))
    return occurrences


def find_literal_occurrences(paths: list[Path], literals: set[str]) -> tuple[LiteralOccurrence, ...]:
    occurrences: list[LiteralOccurrence] = []
    for path in _iter_files(paths, suffixes=SCAN_SUFFIXES):
        if path.suffix == PYTHON_SUFFIX:
            occurrences.extend(_find_python_literal_occurrences(path, literals))
            continue
        if path.suffix == HTML_SUFFIX:
            occurrences.extend(_find_text_literal_occurrences(path, literals))
    return tuple(occurrences)


def audit_discriminator_literals(
    *,
    declaration_paths: list[Path],
    scan_paths: list[Path],
) -> AuditResult:
    declarations = collect_discriminator_declarations(declaration_paths)
    spans_by_literal = _declaration_spans_by_literal(declarations)
    occurrences = find_literal_occurrences(scan_paths, set(spans_by_literal))

    violations = tuple(
        occurrence
        for occurrence in occurrences
        if not any(
            span.path == occurrence.path and span.contains(lineno=occurrence.lineno, col_offset=occurrence.col_offset)
            for span in spans_by_literal[occurrence.literal]
        )
    )
    return AuditResult(declarations=declarations, violations=violations)


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def relative_to_repo_root(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path


def format_violation(
    occurrence: LiteralOccurrence,
    *,
    declarations: tuple[DiscriminatorDeclaration, ...],
    repo_root: Path,
) -> str:
    rendered_declarations = ', '.join(
        f'{relative_to_repo_root(declaration.span.path, repo_root)}:{declaration.span.lineno}'
        for declaration in declarations
    )
    return (
        f'{relative_to_repo_root(occurrence.path, repo_root)}:'
        f'{occurrence.lineno}:{occurrence.col_offset}: {occurrence.literal!r} '
        f'(defined at {rendered_declarations})'
    )


def _parse_args(argv: list[str] | None = None) -> tuple[list[Path], list[Path]]:
    repo_root = _default_repo_root()
    parser = argparse.ArgumentParser(
        description=(
            'Find pydantic discriminator literal strings declared as '
            "field: Literal['value'] = 'value' and report any other Python string "
            'or HTML/template text occurrences under the scanned paths.'
        )
    )
    parser.add_argument(
        '--declaration-path',
        action='append',
        default=[],
        help='Path to scan for canonical Literal declarations. Defaults to src/ceres.',
    )
    parser.add_argument(
        '--scan-path',
        action='append',
        default=[],
        help='Path to audit for illegal re-use in .py and .html files. Defaults to src/ceres and tests.',
    )
    args = parser.parse_args(argv)

    declaration_paths = args.declaration_path or [str(repo_root / 'src' / 'ceres')]
    scan_paths = args.scan_path or [str(repo_root / 'src' / 'ceres'), str(repo_root / 'tests')]
    return ([Path(path) for path in declaration_paths], [Path(path) for path in scan_paths])


def main(argv: list[str] | None = None) -> int:
    repo_root = _default_repo_root()
    declaration_paths, scan_paths = _parse_args(argv)
    result = audit_discriminator_literals(
        declaration_paths=declaration_paths,
        scan_paths=scan_paths,
    )
    if result.ok:
        print(f'OK: scanned {len(result.declarations)} discriminator declarations and found no illegal re-use.')
        return 0

    print(f'Found {len(result.violations)} illegal discriminator literal re-uses:')
    declarations_by_literal = result.declarations_by_literal()
    for occurrence in result.violations:
        print(
            '  '
            + format_violation(
                occurrence,
                declarations=declarations_by_literal[occurrence.literal],
                repo_root=repo_root,
            )
        )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
