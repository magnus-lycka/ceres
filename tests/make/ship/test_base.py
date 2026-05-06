from ceres.make.ship.base import CeresModel, NoteList, ShipBase


class ExampleModel(CeresModel):
    def build_item(self) -> str | None:
        return 'Example Item'

    def build_notes(self):
        return []


class ExampleModelWithNotes(CeresModel):
    def build_item(self) -> str | None:
        return 'Built Item'

    def build_notes(self):
        return []


def test_model_post_init_adds_item_note_from_build_item():
    model = ExampleModel()

    assert model.notes.items == ['Example Item']


def test_item_replaces_existing_first_item_note():
    model = ExampleModelWithNotes()

    model.item('Replacement Item')

    assert model.notes.items == ['Replacement Item']


def test_info_warning_and_error_append_notes():
    model = CeresModel()

    assert isinstance(model.notes, NoteList)

    model.content('Content message')
    model.info('Info message')
    model.warning('Warning message')
    model.error('Error message')

    notes = model.notes
    assert notes.contents == ['Content message']
    assert notes.infos == ['Info message']
    assert notes.warnings == ['Warning message']
    assert notes.errors == ['Error message']


def test_note_list_builds_notes():
    notes = NoteList()
    notes.content('Beam Laser × 2')
    notes.info('DM +1')

    assert notes.contents == ['Beam Laser × 2']
    assert notes.infos == ['DM +1']


def test_note_list_item_replaces_existing_first_item_note():
    notes = NoteList()
    notes.item('Old Item')
    notes.info('Info')
    notes.item('New Item')

    assert notes.items == ['New Item']
    assert notes.infos == ['Info']


def test_note_list_exposes_category_views():
    notes = NoteList()
    notes.item('Item')
    notes.content('Content')
    notes.info('Info')
    notes.warning('Warning')
    notes.error('Error')

    assert notes.item_message == 'Item'
    assert notes.contents == ['Content']
    assert notes.infos == ['Info']
    assert notes.warnings == ['Warning']
    assert notes.errors == ['Error']
    assert notes.detail_entries == [
        {'category': 'content', 'message': 'Content'},
        {'category': 'info', 'message': 'Info'},
        {'category': 'warning', 'message': 'Warning'},
        {'category': 'error', 'message': 'Error'},
    ]


def test_ship_base_default_helpers():
    ship = ShipBase(tl=12, displacement=100)

    assert ship.armour_volume_modifier == 1.0
    assert ship.parts_of_type(object) == []
    assert ship.remaining_usable_tonnage() == 0.0
