"""Integration tests for the character web UI routes."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.app import build_app
from ceres.character.sophonts import HUMANITI, VILANI
from ceres.character.store import SqliteCharacterBackend
from tests.character.helpers import MOCK_WORLD


@pytest.fixture
def client():
    with SqliteCharacterBackend(':memory:') as backend:
        yield TestClient(build_app(backend), follow_redirects=True)


@pytest.fixture
def client_with_backend():
    with SqliteCharacterBackend(':memory:') as backend:
        yield TestClient(build_app(backend), follow_redirects=True), backend


# ── character list ────────────────────────────────────────────────────────────


def test_character_list_empty(client):
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Characters' in r.text


def test_character_list_shows_characters(client_with_backend):
    client, backend = client_with_backend
    backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Aria')
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Aria' in r.text


# ── character creation ────────────────────────────────────────────────────────


def test_new_character_form(client):
    r = client.get('/ui/characters/new')
    assert r.status_code == 200
    assert 'New Character' in r.text
    assert 'Humaniti' in r.text


def test_create_character_redirects_to_wizard(client):
    r = client.post('/ui/characters/new', data={'name': 'Bob', 'sophont': 'Humaniti', 'player': 'NPC'})
    assert r.status_code == 200
    assert 'wizard' in str(r.url) or 'Bob' in r.text


def test_create_character_blank_name_returns_form(client):
    r = client.post('/ui/characters/new', data={'name': '', 'sophont': 'Humaniti', 'player': 'NPC'})
    assert r.status_code == 422
    assert 'required' in r.text.lower()


# ── character deletion ───────────────────────────────────────────────────────


def test_delete_character_redirects_to_list(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Doomed')
    r = client.post(f'/ui/characters/{row["id"]}/delete')
    assert r.status_code == 200
    assert 'Doomed' not in r.text


def test_delete_character_removes_from_list(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Ephemeral')
    client.post(f'/ui/characters/{row["id"]}/delete')
    assert backend.get_projection(row['id']) is None


def test_delete_nonexistent_character_redirects(client):
    r = client.post('/ui/characters/9999/delete')
    assert r.status_code == 200


# ── wizard ────────────────────────────────────────────────────────────────────


def test_wizard_shows_ucp_pending(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    r = client.get(f'/ui/characters/{row["id"]}/wizard')
    assert r.status_code == 200
    assert 'ucp' in r.text


def test_wizard_404_for_missing_character(client):
    r = client.get('/ui/characters/9999/wizard')
    assert r.status_code == 404


# ── event submission (HTMX) ───────────────────────────────────────────────────


def test_submit_ucp_event(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Drax')
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


def test_submit_nonexistent_fulfills_shows_error(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Eryn')
    r = client.post(
        f'/ui/characters/{row["id"]}/events',
        data={'fulfills': 'nonexistent.999'},
    )
    assert r.status_code == 200
    assert 'error' in r.text.lower() or 'nonexistent' in r.text.lower()


# ── character sheet ───────────────────────────────────────────────────────────


def test_character_sheet_shows_name(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Fyra')
    r = client.get(f'/ui/characters/{row["id"]}')
    assert r.status_code == 200
    assert 'Fyra' in r.text


def test_character_sheet_404(client):
    r = client.get('/ui/characters/9999')
    assert r.status_code == 404


# ── career assignments endpoint ───────────────────────────────────────────────


def test_career_assignments_returns_html(client):
    r = client.get('/ui/careers/Scout/assignments')
    assert r.status_code == 200
    assert 'Courier' in r.text or 'option' in r.text.lower()


def test_career_assignments_unknown_career(client):
    r = client.get('/ui/careers/NonexistentCareer/assignments')
    assert r.status_code == 200
    assert r.text == ''


# ── gallery ───────────────────────────────────────────────────────────────────


def test_gallery_form_renders(client):
    r = client.get('/ui/gallery/new')
    assert r.status_code == 200
    assert 'Scout' in r.text or 'career' in r.text.lower()


def test_gallery_generate_returns_specs(client):
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


# ── event_from_form unit tests ────────────────────────────────────────────────


def test_event_from_form_ucp():
    from starlette.datastructures import FormData

    from ceres.character.events import UcpEvent
    from ceres.character.projection import PendingUcp

    pi = PendingUcp(id='1.0', instruction='')
    form = FormData({'STR': '7', 'DEX': '8', 'END': '6', 'INT': '9', 'EDU': '10', 'SOC': '5'})
    event = pi.event_from_form(form)
    assert isinstance(event, UcpEvent)
    assert event.ucp == '7869A5'
    assert event.fulfills == '1.0'


def test_event_from_form_career_choice():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerEvent
    from ceres.character.projection import PendingCareerChoice

    pi = PendingCareerChoice(id='3.0', instruction='')
    form = FormData({'career': 'Scout', 'assignment': 'Courier', 'roll': '8'})
    event = pi.event_from_form(form)
    assert isinstance(event, CareerEvent)
    assert event.career == 'Scout'
    assert event.assignment == 'Courier'
    assert event.qualification_roll == 8


def test_event_from_form_career_event_uses_self_context():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerChoiceEvent
    from ceres.character.projection import PendingCareerEvent

    pi = PendingCareerEvent(id='9.0', career='Scholar', roll=8, instruction='')
    form = FormData({'choice': 'accept'})
    event = pi.event_from_form(form)
    assert isinstance(event, CareerChoiceEvent)
    assert event.context == 'scholar_event_8'
    assert event.choice == 'accept'
    assert event.fulfills == '9.0'


def test_event_from_form_career_mishap_uses_self_context():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerChoiceEvent
    from ceres.character.projection import PendingCareerMishap

    pi = PendingCareerMishap(id='8.0', career='Agent', roll=5, instruction='')
    form = FormData({'choice': 'ally'})
    event = pi.event_from_form(form)
    assert isinstance(event, CareerChoiceEvent)
    assert event.context == 'agent_mishap_5'
    assert event.choice == 'ally'
    assert event.fulfills == '8.0'


def test_event_from_form_reenlist_true():
    from starlette.datastructures import FormData

    from ceres.character.events import ReenlistEvent
    from ceres.character.projection import PendingReenlist

    pi = PendingReenlist(id='5.1', instruction='')
    form = FormData({'reenlist': 'true'})
    event = pi.event_from_form(form)
    assert isinstance(event, ReenlistEvent)
    assert event.reenlist is True


def test_event_from_form_reenlist_false():
    from starlette.datastructures import FormData

    from ceres.character.events import ReenlistEvent
    from ceres.character.projection import PendingReenlist

    pi = PendingReenlist(id='5.1', instruction='')
    form = FormData({'reenlist': 'false'})
    event = pi.event_from_form(form)
    assert isinstance(event, ReenlistEvent)
    assert event.reenlist is False


def test_build_event_unknown_raises():
    from starlette.datastructures import FormData

    from ceres.character.projection import CharacterProjection, CharacterSummary
    from ceres.character.web.routes import _build_event_from_form

    projection = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    form = FormData({})
    with pytest.raises(ValueError):
        _build_event_from_form('no_such_kind', 'nonexistent.0', form, projection)


# ── career_skill_choice with advancement_dm_4 sentinel ────────────────────────


def test_input_specs_includes_advancement_dm_4():
    """advancement_dm_4 sentinel appears in input_specs Select options with a readable label."""
    from ceres.character.input_specs import Select
    from ceres.character.projection import CharacterProjection, CharacterSummary, PendingCareerSkillChoice

    pi = PendingCareerSkillChoice(
        id='6.0',
        career='Agent',
        roll=11,
        advancement_precreated=False,
        instruction='Investigate or DM+4',
        options=['Investigate', 'advancement_dm_4'],
    )
    projection = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )

    specs = pi.input_specs(projection)
    assert specs
    select = next((s for s in specs if isinstance(s, Select)), None)
    assert select is not None
    values = [v for _, v in select.options]
    labels = [lbl for lbl, _ in select.options]

    assert 'advancement_dm_4' in values
    assert any('advancement' in lbl.lower() or 'DM' in lbl for lbl in labels)


def test_event_from_form_career_skill_choice_advancement_dm_4():
    """Submitting advancement_dm_4 via career_skill_choice creates AdvancementDmChoiceEvent."""
    from starlette.datastructures import FormData

    from ceres.character.events import AdvancementDmChoiceEvent
    from ceres.character.projection import PendingCareerSkillChoice

    pi = PendingCareerSkillChoice(id='6.0', career='Agent', roll=11, instruction='')
    form = FormData({'skill': 'advancement_dm_4'})
    event = pi.event_from_form(form)
    assert isinstance(event, AdvancementDmChoiceEvent)
    assert event.fulfills == '6.0'


def test_event_from_form_career_skill_choice_skill():
    """Submitting a skill JSON via career_skill_choice creates SkillChoiceEvent."""
    from starlette.datastructures import FormData

    from ceres.character.events import SkillChoiceEvent
    from ceres.character.projection import PendingCareerSkillChoice
    from ceres.character.skills import Investigate, Level

    pi = PendingCareerSkillChoice(id='6.0', career='Agent', roll=11, instruction='')
    skill_json = '{"type":"Investigate","level":{"value":1}}'
    form = FormData({'skill': skill_json})
    event = pi.event_from_form(form)
    assert isinstance(event, SkillChoiceEvent)
    assert isinstance(event.skill, Investigate)
    assert event.skill.level == Level(value=1)


# ── _diff_summaries unit tests ────────────────────────────────────────────────


def _make_summary(**kwargs):
    from ceres.character.projection import CharacterSummary

    kwargs.setdefault('name', 'Test')
    kwargs.setdefault('sophont', VILANI)
    kwargs.setdefault('homeworld', MOCK_WORLD)
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


def test_post_event_response_includes_char_summary_oob(client_with_backend):
    """HTMX response should include an OOB char-summary div after event submission."""
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Oryn')
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
