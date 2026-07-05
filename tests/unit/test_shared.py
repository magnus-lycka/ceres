from pydantic import BaseModel
import pytest

from ceres.shared import (
    Assembly,
    CeresModel,
    CeresPart,
    Equipment,
    NoteList,
    _append_note,
    _Note,
    _NoteCategory,
    ehex_to_int,
    int_to_ehex,
)


class TestEhexToInt:
    def test_digits(self) -> None:
        assert [ehex_to_int(str(d)) for d in range(10)] == list(range(10))

    def test_a_through_h(self) -> None:
        assert ehex_to_int('A') == 10
        assert ehex_to_int('B') == 11
        assert ehex_to_int('F') == 15
        assert ehex_to_int('G') == 16
        assert ehex_to_int('H') == 17

    def test_j_skips_i(self) -> None:
        assert ehex_to_int('J') == 18

    def test_k_through_n(self) -> None:
        assert ehex_to_int('K') == 19
        assert ehex_to_int('N') == 22

    def test_p_skips_o(self) -> None:
        assert ehex_to_int('P') == 23

    def test_q_through_z(self) -> None:
        assert ehex_to_int('Q') == 24
        assert ehex_to_int('Z') == 33

    def test_lowercase_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('a')

    def test_i_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('I')

    def test_o_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('O')

    def test_invalid_char_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('!')


class TestIntToEhex:
    def test_digits(self) -> None:
        assert [int_to_ehex(d) for d in range(10)] == [str(d) for d in range(10)]

    def test_10_through_17(self) -> None:
        assert int_to_ehex(10) == 'A'
        assert int_to_ehex(15) == 'F'
        assert int_to_ehex(16) == 'G'
        assert int_to_ehex(17) == 'H'

    def test_18_is_j(self) -> None:
        assert int_to_ehex(18) == 'J'

    def test_19_through_22(self) -> None:
        assert int_to_ehex(19) == 'K'
        assert int_to_ehex(22) == 'N'

    def test_23_is_p(self) -> None:
        assert int_to_ehex(23) == 'P'

    def test_24_through_33(self) -> None:
        assert int_to_ehex(24) == 'Q'
        assert int_to_ehex(33) == 'Z'

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            int_to_ehex(-1)

    def test_34_raises(self) -> None:
        with pytest.raises(ValueError):
            int_to_ehex(34)


class TestEhexRoundtrip:
    def test_all_values_roundtrip(self) -> None:
        for i in range(34):
            assert ehex_to_int(int_to_ehex(i)) == i


class TestNoteList:
    def test_note_factories_set_category_and_message(self):
        assert _Note.item('hull').model_dump() == {'category': 'item', 'message': 'hull'}
        assert _Note.content('fluff').model_dump() == {'category': 'content', 'message': 'fluff'}
        assert _Note.info('info').model_dump() == {'category': 'info', 'message': 'info'}
        assert _Note.warning('warning').model_dump() == {'category': 'warning', 'message': 'warning'}
        assert _Note.error('error').model_dump() == {'category': 'error', 'message': 'error'}

    def test_fluent_note_methods_append_and_return_self(self):
        notes = NoteList()

        result = notes.item('item').content('content').info('info').warning('warning').error('error')

        assert result is notes
        assert notes.items == ['item']
        assert notes.contents == ['content']
        assert notes.infos == ['info']
        assert notes.warnings == ['warning']
        assert notes.errors == ['error']

    def test_item_note_is_replaced_when_added_again(self):
        notes = NoteList().item('old').info('info')

        notes.item('new')

        assert notes.items == ['new']
        assert notes[0].message == 'new'
        assert notes.infos == ['info']

    def test_item_note_is_inserted_before_existing_details(self):
        notes = NoteList().info('info')

        notes.item('item')

        assert [note.message for note in notes] == ['item', 'info']

    def test_advisories_problems_and_details_filter_categories(self):
        notes = NoteList().item('item').content('content').info('info').warning('warning').error('error')

        assert [note.message for note in notes.advisories] == ['info', 'warning']
        assert [note.message for note in notes.problems] == ['warning', 'error']
        assert [note.message for note in notes.details] == ['content', 'info', 'warning', 'error']
        assert notes.detail_entries == [
            {'category': 'content', 'message': 'content'},
            {'category': 'info', 'message': 'info'},
            {'category': 'warning', 'message': 'warning'},
            {'category': 'error', 'message': 'error'},
        ]

    def test_item_message_returns_first_item_or_none(self):
        assert NoteList().item_message is None
        assert NoteList().item('item').item_message == 'item'

    def test_pydantic_validation_returns_note_list(self):
        class Container(BaseModel):
            notes: NoteList

        container = Container.model_validate({'notes': [{'category': 'info', 'message': 'hello'}]})

        assert isinstance(container.notes, NoteList)
        assert container.notes.infos == ['hello']

    def test_append_note_with_item_category_sets_item_note(self):
        notes = NoteList().info('info')

        _append_note(notes, _NoteCategory.ITEM, 'item')

        assert [note.message for note in notes] == ['item', 'info']


class DescribedModel(CeresModel):
    description: str = ''

    def build_notes(self) -> list[_Note]:
        return [_Note.info('built')]


class TestCeresModel:
    def test_item_description_defaults_to_empty_string(self):
        assert CeresModel().item_description() == ''

    def test_item_description_uses_description_attribute(self):
        assert DescribedModel(description='desc').item_description() == 'desc'

    def test_build_item_combines_display_label_and_description(self):
        assert DescribedModel(display_label='Label', description='Desc').build_item() == 'Label (Desc)'

    def test_build_item_can_use_only_label_or_only_description(self):
        assert CeresModel(display_label='Label').build_item() == 'Label'
        assert DescribedModel(description='Desc').build_item() == 'Desc'
        assert CeresModel().build_item() is None

    def test_notes_include_built_item_built_notes_and_manual_notes(self):
        model = DescribedModel(display_label='Label', description='Desc')
        model.content('content')
        model.info('info')
        model.warning('warning')
        model.error('error')

        assert model.notes.items == ['Label (Desc)']
        assert model.notes.contents == ['content']
        assert model.notes.infos == ['built', 'info']
        assert model.notes.warnings == ['warning']
        assert model.notes.errors == ['error']

    def test_manual_item_overrides_built_item(self):
        model = DescribedModel(display_label='Label', description='Desc')

        model.item('Manual')

        assert model.notes.items == ['Manual']

    def test_model_post_init_is_no_op(self):
        assert CeresModel().model_post_init(None) is None

    def test_base_build_notes_is_empty(self):
        assert CeresModel().build_notes() == []

    def test_base_notes_can_be_empty(self):
        assert CeresModel().notes == []


class TestCeresPart:
    def test_unbound_assembly_raises(self):
        part = CeresPart()
        with pytest.raises(RuntimeError, match='not bound to an Assembly'):
            _ = part.assembly

    def test_bound_assembly_is_returned(self):
        assembly = Assembly(tl=12)
        part = CeresPart()
        part._assembly = assembly

        assert part.assembly is assembly


class TestEquipment:
    def test_empty_defaults(self):
        e = Equipment()
        assert e.tl == 0
        assert e.cost == 0.0
        assert e.mass_kg == 0.0
        assert e.parts == []

    def test_with_explicit_fields(self):
        part = CeresPart(tl=12, cost=1000.0)
        e = Equipment(parts=[part], tl=12, cost=1000.0, mass_kg=0.5)
        assert e.tl == 12
        assert e.cost == 1000.0
        assert e.mass_kg == 0.5
        assert e.parts == [part]

    def test_is_frozen(self):
        from pydantic import ValidationError

        e = Equipment()
        with pytest.raises(ValidationError):
            e.tl = 5

    def test_serialises_and_roundtrips(self):
        part = CeresPart(tl=10, cost=500.0)
        e = Equipment(parts=[part], tl=10, cost=500.0, mass_kg=0.25)
        json_str = e.model_dump_json()
        e2 = Equipment.model_validate_json(json_str)
        assert e2.tl == 10
        assert e2.cost == 500.0
        assert e2.mass_kg == 0.25
        assert e2.parts[0].tl == 10
