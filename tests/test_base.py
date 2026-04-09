from ceres.base import CeresModel, NoteCategory, ShipBase


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

    assert [(note.category.value, note.message) for note in model.notes] == [
        ('item', 'Example Item'),
    ]


def test_item_replaces_existing_first_item_note():
    model = ExampleModelWithNotes()

    model.item('Replacement Item')

    assert [(note.category.value, note.message) for note in model.notes] == [
        ('item', 'Replacement Item'),
    ]


def test_info_warning_and_error_append_notes():
    model = CeresModel()

    model.info('Info message')
    model.warning('Warning message')
    model.error('Error message')

    assert [(note.category, note.message) for note in model.notes] == [
        (NoteCategory.INFO, 'Info message'),
        (NoteCategory.WARNING, 'Warning message'),
        (NoteCategory.ERROR, 'Error message'),
    ]


def test_ship_base_default_helpers():
    ship = ShipBase(tl=12, displacement=100)

    assert ship.armour_volume_modifier == 1.0
    assert ship.parts_of_type(object) == []
    assert ship.remaining_usable_tonnage() == 0.0
