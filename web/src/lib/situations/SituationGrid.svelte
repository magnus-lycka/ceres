<script module lang="ts">
  /** Distinguishes each grid's marker stylesheet from any other on the page. */
  let instances = 0;

  function nextGridId(): string {
    instances += 1;
    return `situation-grid-${instances}`;
  }
</script>

<script lang="ts">
  /**
   * The round table: who is in the fight, in what order, and whose turn it is.
   *
   * Built on SvGrid openly, as `ActorGrid` and `PartyGrid` are. The boundary is
   * the same shape as theirs and is drawn in application concepts: a situation
   * and a roster go in, and what comes back out is what the referee did — typed
   * an initiative, finished a turn, let one pass. This component owns no state;
   * the page holds the situation.
   *
   * **Nothing here is typed.** Initiative is decided before the round, on the
   * setup screen, and by the time the turn order matters it is settled. What
   * changes inside a round is who has acted and who got hurt. That is also why
   * this grid does not sort or filter: the order *is* the turn order, and a
   * sortable header is an invitation to break it.
   *
   * **Row background is the turn state and nothing else.** That channel was
   * reserved for exactly this: green for an actor who may act now, grey for one
   * who is finished. The cursor is a frame and the Id cell and column header
   * carry the marker fill, so none of them compete for it. `ActorGrid` has a
   * test asserting selection keeps off row backgrounds; this is what it was
   * protecting.
   */
  import { SvGrid, renderComponent, type CellContext, type GridColumns } from '@svgrid/grid';
  import '@svgrid/grid/themes/excel.css';
  import { memberState, turnOrder, type MemberState, type Situation } from '$lib/rules/rounds/situation';
  import { maxVitality, nowVitality, stunCell } from '$lib/rules/rounds/vitality';
  import type { Actor, ActorId } from '$lib/schema/actor';
  import TurnCell from './TurnCell.svelte';

  let {
    situation,
    roster,
    ondone,
    onwait,
  }: {
    situation: Situation;
    /** The actors the rows refer to, for names and the DEX tie-break. */
    roster: Actor[];
    ondone: (actor: ActorId) => void;
    onwait: (actor: ActorId) => void;
  } = $props();

  /**
   * One row per member, in turn order, flattened for the grid.
   *
   * The actor's name is looked up rather than stored on the row: a situation
   * refers to actors by id, and copying the name here would be a second
   * definition that goes stale the moment the actor is renamed.
   */
  type Row = {
    id: ActorId;
    name: string;
    party: string;
    initiative: number | null;
    /** Half a UCP unhurt, or starting Hits. See `$lib/rules/rounds/vitality`. */
    max: string;
    /** The same, as it stands now. */
    now: string;
    /** How much of the loss is stun, and will come back. */
    stun: string;
    state: MemberState;
  };

  /** The health cells for one row, or dashes when the actor cannot be found. */
  function vitality(id: ActorId) {
    const actor = roster.find((each) => each.id === id);
    if (!actor) return { max: '-', now: '-', stun: '' };
    return { max: maxVitality(actor), now: nowVitality(actor), stun: stunCell(actor) };
  }

  const rows = $derived(
    turnOrder(situation, roster).map((member) => ({
      id: member.actor,
      name: roster.find((actor) => actor.id === member.actor)?.name ?? 'unknown',
      party: member.party,
      initiative: member.initiative,
      ...vitality(member.actor),
      state: memberState(situation, member, roster),
    })),
  );

  type Cell = CellContext<Row>;

  const columns: GridColumns<Row> = [
    { field: 'name', header: 'Name', editable: false },
    // Editable, because an actor dropped in on their own arrives with no side
    // and a fight may be split or re-sided as it goes. It is a plain name, not
    // a reference to the Party that may have supplied it.
    { field: 'party', header: 'Party', editable: false },
    // The one thing typed here. The referee rolls; the app never does.
    { field: 'initiative', header: 'Ini', width: 80, editable: false },
    // What the actor is, and what is left of it. Two cells rather than one
    // column per characteristic: the pair reads as a before and an after, and
    // an actor hurt through Hits has one score rather than three.
    { field: 'max', header: 'Max', width: 80, editable: false },
    { field: 'now', header: 'Now', width: 80, editable: false },
    { field: 'stun', header: 'Stun', width: 80, editable: false },
    {
      id: 'turn',
      header: 'Turn',
      width: 140,
      editable: false,
      cell: (ctx: Cell) =>
        renderComponent(TurnCell, {
          state: ctx.row.original.state,
          // Turns are taken inside a round, and only there. Before the round
          // begins nobody has one to spend; a plan has not reached them and a
          // record is past them.
          offered: situation.state === 'current' && situation.phase === 'round',
          ondone: () => ondone(ctx.row.original.id),
          onwait: () => onwait(ctx.row.original.id),
        }),
    },
  ];

  const uid = nextGridId();
</script>

<div class="grid" id={uid}>
  <SvGrid
    data={rows}
    {columns}
    selectionMode="cell"
    containerHeight="auto"
    enableRowSummaries={false}
    rowClass={({ row }) => `turn-${row.state}`}
  />
</div>

<style>
  .grid {
    /* Same channels as the other grids: the excel theme's green is exactly the
       colour that has to mean "can act", so the cursor is blue here too. */
    --sg-accent: #1a73e8;
    --sg-selection-bg: rgba(26, 115, 232, 0.1);
  }

  .grid :global(.sv-grid-cell-active[data-selected-range='true']) {
    background: transparent;
  }

  /*
   * Green for an actor who may act now, grey for one who is finished. An actor
   * the turn has not reached keeps the plain background: there are three
   * states, and colouring two of them says more than colouring all three.
   *
   * Set on the cells rather than the row, because the theme paints `td`
   * backgrounds and a colour on `tr` would sit behind them.
   */
  .grid :global(tr.turn-ready > td) {
    background: #e6f4ea;
  }

  .grid :global(tr.turn-acted > td) {
    background: #f1f3f4;
    color: #5f6368;
  }
</style>
