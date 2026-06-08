"""NPC report rendering — builds context and calls the template engine."""

from pathlib import Path

from ceres.character.domain.spec import NpcSpec, format_npc_skills

_TEMPLATES = Path(__file__).parent / 'templates'


def render_npc_gallery_typst(
    specs: list[NpcSpec],
    notes: list[str | None] | None = None,
    *,
    page_size: str = 'a4',
) -> str:
    from ceres.report.render import render_typst_source

    notes_list = notes or [None] * len(specs)
    npcs = [_build_npc_context(spec, notes=n) for spec, n in zip(specs, notes_list, strict=False)]
    return render_typst_source(_TEMPLATES / 'npc_gallery.typ', {'npcs': npcs, 'page_size': page_size})


def render_npc_gallery_pdf(
    specs: list[NpcSpec],
    notes: list[str | None] | None = None,
    *,
    page_size: str = 'a4',
) -> bytes:
    from ceres.report.render import render_pdf

    notes_list = notes or [None] * len(specs)
    npcs = [_build_npc_context(spec, notes=n) for spec, n in zip(specs, notes_list, strict=False)]
    return render_pdf(_TEMPLATES / 'npc_gallery.typ', {'npcs': npcs, 'page_size': page_size})


def _career_rank_line(spec: NpcSpec) -> str:
    parts: list[str] = []
    if spec.career:
        label = spec.career
        if spec.assignment:
            label += f' ({spec.assignment})'
        parts.append(label)
    if spec.rank is not None:
        parts.append(f'Rank {spec.rank}')
    if spec.terms:
        parts.append(f'{spec.terms} term{"s" if spec.terms != 1 else ""}')
    return ' / '.join(parts) if parts else '—'


def _build_npc_context(spec: NpcSpec, *, notes: str | None = None) -> dict:
    equipment: list[str] = []
    if spec.cash:
        equipment.append(f'Cr{spec.cash:,}')
    equipment.extend(b.display_label for b in spec.equipment)
    from ceres.character.domain.characteristics import Chars

    psi = spec.characteristics.get(Chars.PSI)
    ucp_display = spec.ucp + (f' PSI {psi}' if psi is not None else '')
    return {
        'name': spec.name,
        'career_rank': _career_rank_line(spec),
        'sophont': spec.sophont,
        'ucp': ucp_display,
        'age': spec.age,
        'skills': format_npc_skills(spec.skills),
        'equipment': equipment,
        'notes': notes if notes is not None else spec.notes,
    }
