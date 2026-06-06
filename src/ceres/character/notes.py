"""LLM-generated NPC notes via Ollama, cached by content hash."""

from datetime import UTC
import hashlib
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ceres.character.state import CharacterSummary

_DEFAULT_CACHE = Path.home() / '.cache' / 'ceres' / 'npc_notes.db'
_DEFAULT_MODEL = 'llama3.2:3b'
_DEFAULT_HOST = 'http://localhost:11434'


def _career_context_lines(summary: CharacterSummary) -> str:
    """Build career/assignment description lines for all distinct (career, assignment) pairs in history."""
    from ceres.character.domain.career.loader import load_careers

    careers_data = load_careers()
    seen: set[tuple[str, str | None]] = set()
    pairs: list[tuple[str, str | None]] = []
    for term in summary.career_terms:
        key = (term.career.name, term.assignment)
        if key not in seen:
            seen.add(key)
            pairs.append(key)
    current = summary.current_career or summary.last_career
    current_assignment = summary.current_assignment or summary.last_assignment
    if current:
        key = (current.name, current_assignment)
        if key not in seen:
            pairs.append(key)

    if not pairs:
        return ''

    lines: list[str] = []
    for career_name, assignment_name in pairs:
        career_data = careers_data.get(career_name)
        if career_data is None:
            continue
        if career_data.description:
            lines.append(f'{career_name}: {career_data.description}')
        if assignment_name:
            asgn = career_data.assignment(assignment_name)
            if asgn and asgn.description:
                lines.append(f'  {assignment_name}: {asgn.description}')

    return '\n'.join(lines)


def build_prompt(summary: CharacterSummary) -> str:
    from ceres.character.domain.characteristics import UCP_STATS

    char_lines = ', '.join(f'{stat} {summary.characteristics.get(stat, 0)}' for stat in UCP_STATS)
    career = summary.current_career or summary.last_career or 'Unknown'
    assignment = summary.current_assignment or summary.last_assignment
    career_label = f'{career} ({assignment})' if assignment else career
    narrative_events = list(summary.narrative)

    # Final characteristic extremes (after all career modifications)
    for stat, val in summary.characteristics.items():
        if val <= 2:
            narrative_events.append(f'Notably weak {stat} ({val})')
        elif val >= 14:
            narrative_events.append(f'Exceptional {stat} ({val})')

    # Career advancement pace
    rank = summary.rank or 0
    terms = summary.terms_started_in_all_careers
    if terms >= 2:
        ratio = rank / terms
        if ratio >= 1.0:
            narrative_events.append(f'Career pace: advanced every term (rank {rank} after {terms} terms)')
        elif ratio >= 0.75:
            narrative_events.append(f'Career pace: above average (rank {rank} after {terms} terms)')
        elif rank == 0:
            narrative_events.append(f'Career pace: never promoted despite {terms} terms')
        elif ratio <= 0.25:
            narrative_events.append(f'Career pace: below average (rank {rank} after {terms} terms)')

    # Muster-out benefits — exceptional ones annotated
    benefit_parts: list[str] = []
    if summary.cash:
        benefit_parts.append(f'Cr{summary.cash:,}')
    for b in summary.benefits:
        label = b.display_label
        if b.exceptional:
            label += ' [exceptional — top of the muster-out table]'
        benefit_parts.append(label)
    if benefit_parts:
        narrative_events.append(f'Mustered out with: {", ".join(benefit_parts)}')

    narrative_block = '\n'.join(f'- {e}' for e in narrative_events) or '- (no notable events)'
    problems_block = '\n'.join(f'- {p}' for p in summary.problems)
    mishap_section = f'\nMishaps:\n{problems_block}' if problems_block else ''
    career_context = _career_context_lines(summary)
    career_context_section = f'\nCareer context:\n{career_context}' if career_context else ''
    terms = summary.terms_started_in_all_careers
    n_sentences = terms + 2
    return (
        f'You are writing flavour notes for a Mongoose Traveller 2nd Edition NPC stat block.\n'
        f'Setting: Third Imperium (ca. 1105). '
        f'Vilani are a human subspecies — citizens of the Imperium, not a separate species. '
        f'Scouts are members of the IISS (Imperial Interstellar Scout Service), '
        f'not called "Vilani Scouts".\n\n'
        f'Name: {summary.name or "Unknown"}\n'
        f'Species: {summary.sophont.name}\n'
        f'Career: {career_label} — Rank {summary.rank}, {terms} terms\n'
        f'Age: {summary.age}\n'
        f'Characteristics: {char_lines}\n\n'
        f'Career history:\n{narrative_block}'
        f'{mishap_section}'
        f'{career_context_section}\n\n'
        f'Write exactly {n_sentences} sentences of flavour notes. '
        f'One paragraph, no line breaks inside it. Stop after {n_sentences} sentences.\n\n'
        f'Tone: plain, dry, understated. No hyperbole or emotional inflation. '
        f'Lead with the most unusual or exceptional fact about this character. '
        f'If an exceptional benefit such as a ship is listed, that is almost certainly the most '
        f'remarkable thing about this person and should not be buried or ignored.\n\n'
        f'You MAY:\n'
        f'- Infer personality traits and motivations from events\n'
        f'- Add plausible emotional reactions to mishaps or windfalls\n'
        f'- Connect events causally (imply one led to another)\n'
        f'- Invent minor colour details (habits, mannerisms, a catchphrase)\n'
        f'- Suggest a rumour or secret hinted at by their history\n\n'
        f'You MUST NOT:\n'
        f'- Change the career outcome, rank, or number of terms\n'
        f'- Invent major life events not in the log above\n'
        f'- Add significant relationships (allies, enemies, rivals) not listed\n'
        f'- Alter age, skills, injuries, or physical characteristics\n'
    )


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class NpcNotesCache:
    def __init__(self, path: Path = _DEFAULT_CACHE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            'CREATE TABLE IF NOT EXISTS notes_cache (input_hash TEXT PRIMARY KEY, notes TEXT, created_at TEXT)'
        )
        self._conn.commit()

    def get(self, prompt_hash: str) -> str | None:
        row = self._conn.execute('SELECT notes FROM notes_cache WHERE input_hash = ?', (prompt_hash,)).fetchone()
        return row[0] if row else None

    def put(self, prompt_hash: str, notes: str) -> None:
        from datetime import datetime

        self._conn.execute(
            'INSERT OR REPLACE INTO notes_cache (input_hash, notes, created_at) VALUES (?, ?, ?)',
            (prompt_hash, notes, datetime.now(UTC).isoformat()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def generate_notes(
    summary: CharacterSummary,
    *,
    model: str = _DEFAULT_MODEL,
    host: str = _DEFAULT_HOST,
    cache: NpcNotesCache | None = None,
    cache_path: Path = _DEFAULT_CACHE,
) -> str | None:
    """Generate NPC notes via Ollama. Returns None if Ollama is unavailable."""
    prompt = build_prompt(summary)
    h = _prompt_hash(prompt)
    owned_cache = cache is None
    if owned_cache:
        cache = NpcNotesCache(cache_path)
    try:
        cached = cache.get(h)
        if cached is not None:
            return cached
        import ollama

        response = ollama.Client(host=host).generate(model=model, prompt=prompt)
        if not response.response:
            return None
        notes = response.response.strip()
        cache.put(h, notes)
    except Exception:
        return None
    else:
        return notes
    finally:
        if owned_cache:
            cache.close()


def clear_notes_cache(path: Path = _DEFAULT_CACHE) -> None:
    """Delete the notes cache file. Equivalent to: rm ~/.cache/ceres/npc_notes.db"""
    path.unlink(missing_ok=True)
