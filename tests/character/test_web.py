"""Integration tests for the character web UI routes."""

from fastapi.testclient import TestClient

from ceres.character.app import build_app
from ceres.character.store import SqliteCharacterBackend


def _client() -> TestClient:
    backend = SqliteCharacterBackend(':memory:')
    app = build_app(backend)
    return TestClient(app, follow_redirects=True)


def _client_with_backend() -> tuple[TestClient, SqliteCharacterBackend]:
    backend = SqliteCharacterBackend(':memory:')
    app = build_app(backend)
    return TestClient(app, follow_redirects=True), backend


# ── character list ────────────────────────────────────────────────────────────


def test_character_list_empty():
    client = _client()
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Characters' in r.text


def test_character_list_shows_characters():
    client, backend = _client_with_backend()
    backend.start(sophont='Humaniti', player='NPC', name='Aria')
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Aria' in r.text


# ── character creation ────────────────────────────────────────────────────────


def test_new_character_form():
    client = _client()
    r = client.get('/ui/characters/new')
    assert r.status_code == 200
    assert 'New Character' in r.text
    assert 'Humaniti' in r.text


def test_create_character_redirects_to_wizard():
    client = _client()
    r = client.post('/ui/characters/new', data={'name': 'Bob', 'sophont': 'Humaniti', 'player': 'NPC'})
    assert r.status_code == 200
    assert 'wizard' in str(r.url) or 'Bob' in r.text


def test_create_character_blank_name_returns_form():
    client = _client()
    r = client.post('/ui/characters/new', data={'name': '', 'sophont': 'Humaniti', 'player': 'NPC'})
    assert r.status_code == 422
    assert 'required' in r.text.lower()


# ── wizard ────────────────────────────────────────────────────────────────────


def test_wizard_shows_ucp_pending():
    client, backend = _client_with_backend()
    row = backend.start(sophont='Humaniti', player='NPC', name='Clio')
    r = client.get(f'/ui/characters/{row["id"]}/wizard')
    assert r.status_code == 200
    assert 'ucp' in r.text


def test_wizard_404_for_missing_character():
    client = _client()
    r = client.get('/ui/characters/9999/wizard')
    assert r.status_code == 404


# ── event submission (HTMX) ───────────────────────────────────────────────────


def test_submit_ucp_event():
    client, backend = _client_with_backend()
    row = backend.start(sophont='Humaniti', player='NPC', name='Drax')
    cid = row['id']
    projection = backend.get_projection(cid)
    assert projection is not None
    pi = projection.pending_inputs[0]
    assert pi.kind == 'ucp'

    r = client.post(
        f'/ui/characters/{cid}/events',
        data={
            'kind': 'ucp',
            'fulfills': pi.id,
            'STR': '7',
            'DEX': '7',
            'END': '7',
            'INT': '7',
            'EDU': '7',
            'SOC': '7',
        },
    )
    assert r.status_code == 200
    # Should now show background_skills pending
    assert 'background_skills' in r.text or 'background' in r.text.lower()


def test_submit_bad_kind_shows_error():
    client, backend = _client_with_backend()
    row = backend.start(sophont='Humaniti', player='NPC', name='Eryn')
    r = client.post(
        f'/ui/characters/{row["id"]}/events',
        data={'kind': 'unknown_kind', 'fulfills': '1.0'},
    )
    assert r.status_code == 200
    assert 'error' in r.text.lower() or 'unknown' in r.text.lower()


# ── character sheet ───────────────────────────────────────────────────────────


def test_character_sheet_shows_name():
    client, backend = _client_with_backend()
    row = backend.start(sophont='Humaniti', player='NPC', name='Fyra')
    r = client.get(f'/ui/characters/{row["id"]}')
    assert r.status_code == 200
    assert 'Fyra' in r.text


def test_character_sheet_404():
    client = _client()
    r = client.get('/ui/characters/9999')
    assert r.status_code == 404


# ── career assignments endpoint ───────────────────────────────────────────────


def test_career_assignments_returns_html():
    client = _client()
    r = client.get('/ui/careers/Scout/assignments')
    assert r.status_code == 200
    assert 'Courier' in r.text or 'option' in r.text.lower()


def test_career_assignments_unknown_career():
    client = _client()
    r = client.get('/ui/careers/NonexistentCareer/assignments')
    assert r.status_code == 200
    assert r.text == ''


# ── gallery ───────────────────────────────────────────────────────────────────


def test_gallery_form_renders():
    client = _client()
    r = client.get('/ui/gallery/new')
    assert r.status_code == 200
    assert 'Scout' in r.text or 'career' in r.text.lower()


def test_gallery_generate_returns_specs():
    client = _client()
    r = client.post(
        '/ui/gallery/generate',
        data={
            'career': 'Scout',
            'assignment': '',
            'sophont': 'Humaniti',
            'min_terms': '2',
            'max_terms': '3',
            'count': '3',
            'name_prefix': 'Scout',
        },
    )
    assert r.status_code == 200
    assert 'Scout' in r.text


# ── build_event_from_form unit tests ─────────────────────────────────────────


def test_build_event_ucp():
    from starlette.datastructures import FormData

    from ceres.character.events import UcpEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'STR': '7', 'DEX': '8', 'END': '6', 'INT': '9', 'EDU': '10', 'SOC': '5'})
    event = _build_event_from_form('ucp', '1.0', form)
    assert isinstance(event, UcpEvent)
    assert event.ucp == '7869A5'
    assert event.fulfills == '1.0'


def test_build_event_career_choice():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'career': 'Scout', 'assignment': 'Courier', 'roll': '8'})
    event = _build_event_from_form('career_choice', '3.0', form)
    assert isinstance(event, CareerEvent)
    assert event.career == 'Scout'
    assert event.assignment == 'Courier'
    assert event.qualification_roll == 8


def test_build_event_career_event_uses_generic_context():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerChoiceEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'career': 'Scholar', 'roll': '8', 'choice': 'accept'})
    event = _build_event_from_form('career_event', '9.0', form)
    assert isinstance(event, CareerChoiceEvent)
    assert event.context == 'scholar_event_8'
    assert event.choice == 'accept'
    assert event.fulfills == '9.0'


def test_build_event_career_mishap_uses_generic_context():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerChoiceEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'career': 'Agent', 'roll': '5', 'choice': 'ally'})
    event = _build_event_from_form('career_mishap', '8.0', form)
    assert isinstance(event, CareerChoiceEvent)
    assert event.context == 'agent_mishap_5'
    assert event.choice == 'ally'
    assert event.fulfills == '8.0'


def test_build_event_reenlist_true():
    from starlette.datastructures import FormData

    from ceres.character.events import ReenlistEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'reenlist': 'true'})
    event = _build_event_from_form('reenlist', '5.1', form)
    assert isinstance(event, ReenlistEvent)
    assert event.reenlist is True


def test_build_event_reenlist_false():
    from starlette.datastructures import FormData

    from ceres.character.events import ReenlistEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'reenlist': 'false'})
    event = _build_event_from_form('reenlist', '5.1', form)
    assert isinstance(event, ReenlistEvent)
    assert event.reenlist is False


def test_build_event_unknown_raises():
    from starlette.datastructures import FormData

    from ceres.character.web.routes import _build_event_from_form

    form = FormData({})
    try:
        _build_event_from_form('no_such_kind', '', form)
        assert False, 'should have raised'
    except ValueError:
        pass


# ── _diff_summaries unit tests ────────────────────────────────────────────────


def _make_summary(**kwargs):
    from ceres.character.projection import CharacterSummary

    return CharacterSummary(**kwargs)


def test_diff_shows_characteristic_change():
    from ceres.character.characteristics import Chars
    from ceres.character.web.routes import _diff_summaries

    before = _make_summary(characteristics={Chars.STR: 7, Chars.DEX: 8})
    after = _make_summary(characteristics={Chars.STR: 8, Chars.DEX: 8})
    changes = _diff_summaries(before, after)
    assert any('STR' in c and '7' in c and '8' in c for c in changes)


def test_diff_shows_new_skill():
    from ceres.character.skills import Admin
    from ceres.character.web.routes import _diff_summaries

    before = _make_summary()
    after = _make_summary(skills=[Admin()])
    changes = _diff_summaries(before, after)
    assert any('Admin' in c for c in changes)


def test_diff_shows_skill_level_up():
    from ceres.character.skills import Admin, Level
    from ceres.character.web.routes import _diff_summaries

    before = _make_summary(skills=[Admin()])
    after = _make_summary(skills=[Admin(level=Level(value=1))])
    changes = _diff_summaries(before, after)
    assert any('Admin' in c and '0' in c and '1' in c for c in changes)


def test_diff_shows_rank_change():
    from ceres.character.web.routes import _diff_summaries

    before = _make_summary(rank=0)
    after = _make_summary(rank=1)
    changes = _diff_summaries(before, after)
    assert any('Rank' in c and '1' in c for c in changes)


def test_diff_shows_cash_gain():
    from ceres.character.web.routes import _diff_summaries

    before = _make_summary(cash=0)
    after = _make_summary(cash=5000)
    changes = _diff_summaries(before, after)
    assert any('5000' in c or '5,000' in c for c in changes)


def test_diff_shows_new_narrative():
    from ceres.character.web.routes import _diff_summaries

    before = _make_summary(narrative=['Term 1'])
    after = _make_summary(narrative=['Term 1', 'Survived the storm'])
    changes = _diff_summaries(before, after)
    assert any('Survived the storm' in c for c in changes)


def test_diff_empty_when_nothing_changed():
    from ceres.character.web.routes import _diff_summaries

    s = _make_summary(characteristics={}, skills=[])
    assert _diff_summaries(s, s) == []


def test_post_event_response_includes_char_summary_oob():
    """HTMX response should include an OOB char-summary div after event submission."""
    client, backend = _client_with_backend()
    row = backend.start(sophont='Humaniti', player='NPC', name='Oryn')
    cid = row['id']
    projection = backend.get_projection(cid)
    assert projection is not None
    pi = projection.pending_inputs[0]
    r = client.post(
        f'/ui/characters/{cid}/events',
        data={
            'kind': 'ucp',
            'fulfills': pi.id,
            'STR': '7',
            'DEX': '8',
            'END': '6',
            'INT': '9',
            'EDU': '10',
            'SOC': '5',
        },
    )
    assert r.status_code == 200
    assert 'char-summary' in r.text


# ── connection_type_from_instruction ─────────────────────────────────────────


def test_connection_type_from_instruction_enemy():
    from ceres.character.web.routes import _connection_type_from_instruction

    assert _connection_type_from_instruction('Roll D3 for number of Enemies gained') == 'enemy'


def test_connection_type_from_instruction_contact():
    from ceres.character.web.routes import _connection_type_from_instruction

    assert _connection_type_from_instruction('Roll 1D6 for number of contacts') == 'contact'


def test_connection_type_from_instruction_fallback():
    from ceres.character.web.routes import _connection_type_from_instruction

    assert _connection_type_from_instruction('Something vague') == 'contact'


# ── career_skill_choice with advancement_dm_4 sentinel ────────────────────────


def test_compute_skill_choices_includes_advancement_dm_4():
    """advancement_dm_4 sentinel appears in skill_choices list with a readable label."""
    from ceres.character.projection import CharacterProjection, CharacterSummary, PendingCareerSkillChoice
    from ceres.character.web.routes import _compute_skill_choices_for_pending

    pi = PendingCareerSkillChoice(
        id='6.0',
        career='Agent',
        roll=11,
        advancement_precreated=False,
        instruction='Investigate or DM+4',
        options=['Investigate', 'advancement_dm_4'],
    )
    projection = CharacterProjection(character_id=1)
    projection.summary = CharacterSummary(name='Test')

    choices = _compute_skill_choices_for_pending(pi, projection)
    values = [v for _, v in choices]
    labels = [lbl for lbl, _ in choices]

    assert 'advancement_dm_4' in values
    assert any('advancement' in lbl.lower() or 'DM' in lbl for lbl in labels)


def test_build_event_career_skill_choice_advancement_dm_4():
    """Submitting advancement_dm_4 via career_skill_choice creates AdvancementDmChoiceEvent."""
    from starlette.datastructures import FormData

    from ceres.character.events import AdvancementDmChoiceEvent
    from ceres.character.web.routes import _build_event_from_form

    form = FormData({'skill': 'advancement_dm_4'})
    event = _build_event_from_form('career_skill_choice', '6.0', form)
    assert isinstance(event, AdvancementDmChoiceEvent)
    assert event.fulfills == '6.0'


def test_build_event_career_skill_choice_skill():
    """Submitting a skill JSON via career_skill_choice creates SkillChoiceEvent."""
    from starlette.datastructures import FormData

    from ceres.character.events import SkillChoiceEvent
    from ceres.character.skills import Investigate, Level
    from ceres.character.web.routes import _build_event_from_form

    skill_json = '{"type":"Investigate","level":{"value":1}}'
    form = FormData({'skill': skill_json})
    event = _build_event_from_form('career_skill_choice', '6.0', form)
    assert isinstance(event, SkillChoiceEvent)
    assert isinstance(event.skill, Investigate)
    assert event.skill.level == Level(value=1)
