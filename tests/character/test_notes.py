"""Tests for NPC notes generation and caching."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from ceres.character.notes import NpcNotesCache, build_prompt, generate_notes
from ceres.character.sophonts import VILANI
from ceres.character.state import CharacterSummary
from tests.character.helpers import MOCK_WORLD


def _summary(**kwargs) -> CharacterSummary:
    defaults = {
        'name': 'Test Character',
        'sophont': VILANI,
        'homeworld': MOCK_WORLD,
        'age': 26,
        'characteristics': {'STR': 7, 'DEX': 8, 'END': 6, 'INT': 9, 'EDU': 7, 'SOC': 5},
        'current_career': 'Scout',
        'current_assignment': 'Explorer',
        'rank': 1,
        'term_count': 2,
    }
    return CharacterSummary.model_validate({**defaults, **kwargs})


def test_build_prompt_includes_career_and_name():
    s = _summary()
    prompt = build_prompt(s)
    assert 'Test Character' in prompt
    assert 'Scout' in prompt
    assert 'Explorer' in prompt


def test_build_prompt_includes_narrative_events():
    s = _summary(narrative=['Term 1 event (Scout): Made first contact with alien life', 'Life event: new contact made'])
    prompt = build_prompt(s)
    assert 'Made first contact with alien life' in prompt
    assert 'Life event: new contact made' in prompt


def test_build_prompt_includes_mishaps():
    s = _summary(problems=['Injured. Lose 1 point from STR, DEX, or END.'])
    prompt = build_prompt(s)
    assert 'Injured' in prompt


def test_build_prompt_sentence_count_scales_with_terms():
    s2 = _summary(term_count=2)
    s4 = _summary(term_count=4)
    prompt2 = build_prompt(s2)
    prompt4 = build_prompt(s4)
    # 2 terms → 4 sentences requested, 4 terms → 6 sentences requested
    assert '4 sentences' in prompt2
    assert '6 sentences' in prompt4


def test_build_prompt_includes_characteristics():
    s = _summary()
    prompt = build_prompt(s)
    assert 'STR 7' in prompt
    assert 'INT 9' in prompt


def test_prompt_hash_is_deterministic():
    from ceres.character.notes import _prompt_hash

    s = _summary(narrative=['Term 1 event: something happened'])
    p1 = build_prompt(s)
    p2 = build_prompt(s)
    assert _prompt_hash(p1) == _prompt_hash(p2)


def test_prompt_hash_differs_for_different_summaries():
    from ceres.character.notes import _prompt_hash

    s1 = _summary(narrative=['Event A'])
    s2 = _summary(narrative=['Event B'])
    assert _prompt_hash(build_prompt(s1)) != _prompt_hash(build_prompt(s2))


class TestNpcNotesCache:
    def test_miss_returns_none(self, tmp_path: Path):
        cache = NpcNotesCache(tmp_path / 'test.db')
        assert cache.get('nonexistent') is None
        cache.close()

    def test_put_and_get_roundtrip(self, tmp_path: Path):
        cache = NpcNotesCache(tmp_path / 'test.db')
        cache.put('abc123', 'Some generated notes.')
        assert cache.get('abc123') == 'Some generated notes.'
        cache.close()

    def test_put_overwrites(self, tmp_path: Path):
        cache = NpcNotesCache(tmp_path / 'test.db')
        cache.put('abc123', 'First version.')
        cache.put('abc123', 'Second version.')
        assert cache.get('abc123') == 'Second version.'
        cache.close()

    def test_persists_across_instances(self, tmp_path: Path):
        db = tmp_path / 'test.db'
        cache1 = NpcNotesCache(db)
        cache1.put('key', 'stored value')
        cache1.close()

        cache2 = NpcNotesCache(db)
        assert cache2.get('key') == 'stored value'
        cache2.close()


class TestGenerateNotes:
    def test_returns_cached_value_without_calling_ollama(self, tmp_path: Path):
        cache = NpcNotesCache(tmp_path / 'test.db')
        s = _summary()
        prompt = build_prompt(s)
        from ceres.character.notes import _prompt_hash

        cache.put(_prompt_hash(prompt), 'Cached notes text.')

        with patch('ollama.Client') as mock_client:
            result = generate_notes(s, cache=cache)

        mock_client.assert_not_called()
        assert result == 'Cached notes text.'
        cache.close()

    def test_returns_none_when_ollama_unavailable(self, tmp_path: Path):
        with patch('ollama.Client') as mock_client:
            mock_client.return_value.generate.side_effect = ConnectionRefusedError('no server')
            result = generate_notes(_summary(), cache_path=tmp_path / 'test.db')
        assert result is None

    def test_result_is_cached_after_generation(self, tmp_path: Path):
        db = tmp_path / 'test.db'
        mock_response = MagicMock()
        mock_response.response = '  Generated notes here.  '

        with patch('ollama.Client') as mock_client:
            mock_client.return_value.generate.return_value = mock_response
            result = generate_notes(_summary(), cache_path=db)

        assert result == 'Generated notes here.'
        cache = NpcNotesCache(db)
        s = _summary()
        from ceres.character.notes import _prompt_hash

        assert cache.get(_prompt_hash(build_prompt(s))) == 'Generated notes here.'
        cache.close()

    def test_ollama_called_with_configured_model_and_host(self, tmp_path: Path):
        mock_response = MagicMock()
        mock_response.response = 'Notes.'

        with patch('ollama.Client') as mock_client:
            mock_client.return_value.generate.return_value = mock_response
            generate_notes(
                _summary(),
                model='llama3.1:8b',
                host='http://my-server:11434',
                cache_path=tmp_path / 'test.db',
            )

        mock_client.assert_called_once_with(host='http://my-server:11434')
        mock_client.return_value.generate.assert_called_once()
        call_kwargs = mock_client.return_value.generate.call_args
        assert (
            call_kwargs.kwargs.get('model') == 'llama3.1:8b'
            or call_kwargs.args[0] == 'llama3.1:8b'
            or 'llama3.1:8b' in str(call_kwargs)
        )
