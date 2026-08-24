"""Parties, as a grid, with the selected party's members beneath it.

Two AG Grids rather than one table of rows: arrow-key movement between cells is
what makes this feel like a control instead of a styled HTML table.

The selection is mirrored here as it changes, never fetched from the browser.
`get_selected_rows()` is a round trip to JavaScript, which means it cannot be
driven by the in-process test user at all — so nothing may depend on it.
"""

from collections.abc import Sequence
from typing import Any

from nicegui import ui

from ceres.rounds.library.ids import ActorId, PartyId
from ceres.rounds.library.models import Party
from ceres.rounds.library.store import Library

MISSING = '—'
EDITABLE_FIELDS = frozenset({'name', 'note'})

PILL_STYLE = 'background:#e2e8f0;border-radius:9999px;padding:1px 8px;margin-right:4px'

TAG_PILLS = f"""(params) => (params.value || '')
    .split(' ').filter(Boolean)
    .map((tag) => `<span style="{PILL_STYLE}">${{tag}}</span>`)
    .join('')"""

FOCUS_SELECTS_THE_ROW = """(params) => {
    const node = params.api.getDisplayedRowAtIndex(params.rowIndex);
    if (node && !node.isSelected()) node.setSelected(true, true);
}"""
"""Arrow keys move the focused cell but do not select it, so the detail below
would follow the mouse only. Selecting the focused row in the browser makes the
keyboard behave like the mouse, and Python hears about it either way."""

PARTY_COLUMNS = [
    {'field': 'id', 'headerName': 'Id', 'width': 70, 'sort': 'asc'},
    {'field': 'name', 'editable': True, 'flex': 2},
    {'field': 'members', 'headerName': 'Actors', 'type': 'numericColumn', 'width': 100},
    {
        'field': 'tags',
        'flex': 1,
        # AG Grid renders its own cells, so pills need JavaScript. A string
        # returned by a cellRenderer is inserted as HTML.
        ':cellRenderer': TAG_PILLS,
    },
    {'field': 'note', 'editable': True, 'flex': 3},
]

MEMBER_COLUMNS = [
    {'field': 'id', 'headerName': 'Id', 'width': 70},
    {'field': 'name', 'flex': 2},
    {'field': 'kind', 'width': 110},
    {'field': 'STR', 'width': 80},
    {'field': 'DEX', 'width': 80},
    {'field': 'END', 'width': 80},
    {'field': 'tags', 'flex': 1},
]


def known_tags(library: Library) -> list[str]:
    """Every tag already in use, to be offered while typing a new one."""
    return sorted({tag for party in library.parties() for tag in party.tags})


def party_rows(library: Library, *, tags: Sequence[str] = ()) -> list[dict]:
    """Parties, narrowed to those carrying every selected tag.

    Picking a second tag asks for both rather than for either: a filter is for
    narrowing, and widening is what clearing one does.
    """
    return [
        {
            'id': party.id,
            'name': party.name,
            'members': party.size,
            'tags': ' '.join(party.tags),
            'note': party.note,
        }
        for party in library.parties()
        if set(tags) <= set(party.tags)
    ]


def row_id(args: dict) -> PartyId | None:
    """The party a grid event is about, or None if the payload does not say.

    Grid events are untrusted dictionaries: keys its own JavaScript appears to
    promise have turned up missing, so nothing here may raise.
    """
    identifier = (args.get('data') or {}).get('id')
    return PartyId(identifier) if identifier is not None else None


def member_rows(library: Library, party_id: PartyId | None) -> list[dict]:
    """The selected party's members, with dashes where one has been deleted.

    A deleted actor leaves its id behind rather than vanishing, so the referee
    can see there is a hole and take the reference out themselves.
    """
    if party_id is None:
        return []
    party = library.party(party_id)
    if party is None:
        return []
    return [_member_row(library, actor_id) for actor_id in party.actors]


def _member_row(library: Library, actor_id: ActorId) -> dict:
    actor = library.actor(actor_id)
    if actor is None:
        return {
            'id': actor_id,
            'name': MISSING,
            'kind': MISSING,
            'STR': MISSING,
            'DEX': MISSING,
            'END': MISSING,
            'tags': MISSING,
        }
    return {
        'id': actor.id,
        'name': actor.name,
        'kind': actor.kind.value,
        'STR': actor.strength if actor.strength is not None else MISSING,
        'DEX': actor.dexterity if actor.dexterity is not None else MISSING,
        'END': actor.endurance if actor.endurance is not None else MISSING,
        'tags': ' '.join(actor.tags),
    }


class PartiesPage:
    def __init__(self, library: Library):
        self.library = library
        self.selected: PartyId | None = None
        self.tag_filter: list[str] = []

    def build(self) -> None:
        ui.label('Parties').classes('text-xl font-bold')
        with ui.row().classes('items-center gap-2'):
            ui.input('Search', on_change=self.search).props('dense clearable').mark('search')
            self.filter_tags = (
                ui.select(
                    known_tags(self.library),
                    label='Tags',
                    multiple=True,
                    clearable=True,
                    on_change=self.filter_by_tags,
                )
                .props('dense use-chips')
                .classes('min-w-48')
                .mark('filter-tags')
            )
            ui.button('New party', on_click=self.new_party).mark('new-party')
            ui.button('Delete', on_click=self.delete_selected).props('flat color=negative').mark('delete-party')
        self.grid = (
            ui.aggrid(
                {
                    'columnDefs': PARTY_COLUMNS,
                    'rowData': party_rows(self.library),
                    'rowSelection': 'single',
                    'stopEditingWhenCellsLoseFocus': True,
                    ':onCellFocused': FOCUS_SELECTS_THE_ROW,
                }
            )
            .classes('h-72')
            .mark('parties')
        )
        self.grid.on('rowClicked', self.row_clicked)
        self.grid.on('rowSelected', self.row_selected)
        self.grid.on('cellValueChanged', self.party_edited)

        self.detail = ui.row().classes('items-center gap-2 mt-2 w-full')
        self.render_detail()

        self.members_label = ui.label('Members').classes('text-lg font-bold mt-4')
        self.members = (
            ui.aggrid(
                {
                    'columnDefs': MEMBER_COLUMNS,
                    'rowData': [],
                    'rowSelection': 'multiple',
                }
            )
            .classes('h-64')
            .mark('members')
        )

    def refresh(self) -> None:
        self.grid.options['rowData'] = party_rows(self.library, tags=self.tag_filter)
        self.grid.update()
        self.filter_tags.set_options(known_tags(self.library), value=self.tag_filter)
        self.render_detail()
        self.refresh_members()

    def render_detail(self) -> None:
        """Tags as removable chips, which a grid cell cannot give us.

        AG Grid renders its own cells in JavaScript, so a Python chip cannot
        live inside one. The column stays plain text for scanning and sorting,
        and this is where a tag is added or taken off.
        """
        self.detail.clear()
        party = self.library.party(self.selected) if self.selected else None
        with self.detail:
            if party is None:
                ui.label('Select a party to edit its tags').classes('text-sm italic')
                return
            ui.label(party.name).classes('font-bold')
            ui.select(
                known_tags(self.library),
                value=list(party.tags),
                label='Tags',
                multiple=True,
                with_input=True,
                new_value_mode='add-unique',
                on_change=self.tags_changed,
            ).props('dense use-chips').classes('min-w-64').mark('party-tags')

    def tags_changed(self, event: Any) -> None:
        party = self.library.party(self.selected) if self.selected else None
        if party is None:
            return
        self.library.save_party(party.model_copy(update={'tags': list(event.value)}))
        self.grid.options['rowData'] = party_rows(self.library, tags=self.tag_filter)
        self.grid.update()
        self.filter_tags.set_options(known_tags(self.library), value=self.tag_filter)

    def filter_by_tags(self, event: Any) -> None:
        self.tag_filter = list(event.value or [])
        self.grid.options['rowData'] = party_rows(self.library, tags=self.tag_filter)
        self.grid.update()

    def refresh_members(self) -> None:
        party = self.library.party(self.selected) if self.selected else None
        self.members_label.text = f'Members of {party.name}' if party else 'Members'
        self.members.options['rowData'] = member_rows(self.library, self.selected)
        self.members.update()

    def row_clicked(self, event: Any) -> None:
        """A click is unambiguous: that row is now the one being looked at."""
        self.show(row_id(event.args))

    def row_selected(self, event: Any) -> None:
        """Only a positive selection is trusted.

        `rowSelected` fires for the row being left as well as the one being
        taken, and the payload has been seen to arrive with no flag to tell
        them apart — which is how the panel ended up showing the row before
        the one highlighted. Anything not explicitly selected is ignored, and
        a single-select grid always follows a deselection with a selection.
        """
        if event.args.get('selected') is True:
            self.show(row_id(event.args))

    def show(self, party_id: PartyId | None) -> None:
        if party_id is None or party_id == self.selected:
            return
        self.selected = party_id
        self.render_detail()
        self.refresh_members()

    def party_edited(self, event: Any) -> None:
        """Take an edit from the grid, ignoring any payload that makes no sense."""
        row = event.args.get('data') or {}
        field = event.args.get('colId')
        if row.get('id') is None or field not in EDITABLE_FIELDS:
            return
        party = self.library.party(PartyId(row['id']))
        if party is not None:
            self.library.save_party(party.model_copy(update={field: event.args.get('newValue') or ''}))
        self.refresh()

    def new_party(self) -> None:
        self.library.save_party(Party(name='New party'))
        self.refresh()

    def delete_selected(self) -> None:
        """No confirmation: deleting is the referee's business, not the app's."""
        if self.selected is None:
            return
        self.library.delete_party(self.selected)
        self.selected = None
        self.refresh()

    def search(self, event: Any) -> None:
        self.grid.run_grid_method('setGridOption', 'quickFilterText', event.value or '')
