# Issue-driven library imports

Status: proposed implementation plan

Tracking issue: [#61](https://github.com/magnus-lycka/ceres/issues/61)

Parent plan: [plan-rounds.md](plan-rounds.md)

## Purpose

Let an AI assistant, a person, or another offline author propose reusable library
content without direct access to the application's store. A proposal is filed as a
GitHub issue in the private data repository. GitHub Actions validates it and places a
JSON bundle in `inbox/`. On the application's next successful sync, the bundle is
installed into the Actor and Party libraries and synced back to the repository.

This is a **library import**, not an NPC import. A bundle is one Party containing any
supported kind of Actor — PCs, NPCs, animals, robots, or a mixture. The import
mechanism neither knows nor cares which actors the referee will control.

The intended result is:

```text
issue -> validated inbox bundle -> sync -> Actors and Parties -> receipt
```

## Goals

- An author needs only permission to create an issue in the data repository. They do
  not need the application, its GitHub token, or a running service.
- One bundle creates one Party and the Actors embedded in it.
- The application remains the only allocator of stored Actor and Party ids.
- Exactly the same runtime schema validates a bundle in CI and in the application.
- A valid bundle is imported automatically during the next successful sync.
- Import is replay-safe: retries, crashes, refreshes, and repeated syncs cannot create
  duplicate Actors or Parties.
- A GitHub commit which changes only `inbox/` can be incorporated while local edits
  are waiting. Remote changes to application-owned data still block sync.
- The issue, inbox file, import receipt, and resulting commit leave a readable audit
  trail.
- An already-open Actors or Parties page notices a completed import without requiring
  a browser refresh.

## Non-goals

- No synchronous AI API, MCP server, or application endpoint.
- No creation or modification of Situations.
- No editing, merging, or deletion of existing Actors or Parties through the inbox.
- No imported injuries, stun, robot criticals, initiative, or other temporal state.
- No ids supplied by an author or GitHub Action.
- No attempt to infer structured data from arbitrary prose.
- No general automatic merge when two machines changed application-owned data.

An imported mistake is corrected through the normal Actor and Party editors. Updating
existing entities through proposals would require identity, authorization, and merge
semantics which creation does not need; it is a separate feature.

## Terms and ownership

**Library bundle** is one id-free Party with its Actors embedded in member order. It is
the proposal carried by an issue and an inbox file.

**Import receipt** records the Party id and ordered Actor ids allocated to a bundle. It
makes installation resumable and prevents a bundle from being installed twice.

The ownership boundary is strict:

| Owner | May write |
| --- | --- |
| Issue author | Issue title and body |
| GitHub Action | `inbox/issue-<number>.json` |
| Application | Store documents, receipts and consumed inbox entries |

The workflow never writes stored entities. The application never interprets issue
prose directly.

## Bundle contract

The inbox schema is a separate strict object assembled from named pieces of the stored
Actor and Party schemas. It describes one Party with `name`, `tags`, `note` and an
array of embedded Actors. It is not the persistence schema with optional ids or
ActorId references. That distinction prevents application-owned state from becoming
an accidental import interface.

An illustrative bundle is:

```json
{
  "name": "Starport security",
  "tags": ["security"],
  "note": "The night shift at the downport.",
  "actors": [
    {
      "name": "Sergeant Vela",
      "kind": "sophont",
      "strength": 9,
      "dexterity": 8,
      "endurance": 10,
      "tags": ["security", "starport"],
      "note": "Carries a laser carbine."
    },
    {
      "name": "Guard beast",
      "kind": "animal",
      "hits": 20,
      "tags": ["security", "animal"]
    }
  ]
}
```

The mechanism is explicit in `schema/actor.ts`:

- Extract the reusable Actor definition fields into one named shape.
- Extract the kind-dependent STR/DEX/END-versus-Hits check into one named refinement
  function.
- Build both the stored `actorSchema` and strict `importActorSchema` from that shape,
  and apply the same refinement function to both.
- Build `libraryBundleSchema` as a strict object using `importActorSchema`.

The import schema must use `z.strictObject()` or `.strict()`. Ordinary Zod objects
strip unknown keys; they do not satisfy the promised rejection merely because a field
is absent from the shape. The import schema also must not be made by applying `omit()`
to the refined `actorSchema`, because that would lose its `superRefine()` rules.

Rules enforced by `libraryBundleSchema`:

- Party `name`, `tags`, `note` and `actors` are the only top-level fields.
- `actors` contains at least one Actor. Its array order becomes Party member order.
- Actor kind determines its required combat properties: sophonts have STR, DEX and
  END; animals and robots have Hits.
- Stored ids, injuries and critical damage are rejected rather than ignored.
- Unknown fields are rejected so spelling mistakes do not silently disappear.

GitHub metadata does not enter the submitted object. Within the one configured data
repository, the issue number is the deterministic identity: `issue-<number>`.

The authoritative validator is the Zod runtime schema. Generated JSON Schema is
published for assistants and editor tooling, but CI must run the Zod parser as well.
The current Actor model uses `superRefine()` for kind-specific rules, which cannot be
assumed to survive JSON Schema generation.

## Data-repository interface

The data repository contains these generic, library-oriented files:

```text
.github/ISSUE_TEMPLATE/library-import.yml
.github/workflows/receive-library-import.yml
inbox/
imports/
```

The small workflow in the private data repository calls a reusable workflow in the
Ceres code repository, where parsing, validation, canonicalisation and tests live.
The reusable workflow checks out Ceres at its pinned revision and the data repository
into separate directories, then runs:

```text
npm ci --prefix web
npm run validate:library-import -- <event-file> <canonical-output>
```

The package script invokes a small TypeScript command-line entry point through a
lockfile-pinned `tsx` development dependency. That entry point reads
`GITHUB_EVENT_PATH`, extracts the one labelled JSON block, calls
`libraryBundleSchema.safeParse()`, prints Zod paths on failure, and writes canonical
JSON on success. CI therefore executes the application's runtime validator rather
than maintaining a second validator in workflow YAML or shell.

The caller grants only:

```yaml
permissions:
  contents: write
  issues: write
```

The issue form contains one clearly marked JSON textarea and applies a distinguishing
label such as `ceres-library-import`. GitHub converts issue-form answers to Markdown,
so the workflow extracts exactly one labelled JSON code block; it does not attempt to
parse the other prose in the issue.

The workflow runs for labelled import issues on `opened`, `edited`, and `reopened`:

1. Pass `GITHUB_EVENT_PATH` to the TypeScript entry point. Never interpolate the issue
   title or body into a shell script.
2. Let the entry point extract, parse, validate and canonicalise the one JSON bundle.
3. On success, write canonical JSON to `inbox/issue-<number>.json`, replace any older
   version of that path, label the issue ready, and report success.
4. On failure, ensure that the deterministic inbox path is absent, remove the ready
   label, label the issue invalid, and comment with useful JSON paths and messages.

The deterministic path makes an edited issue an update, not a second proposal. A
workflow concurrency group serialises inbox commits so simultaneous issues cannot
race while advancing the data repository branch.

Before creating an inbox file, the workflow checks for a completed
`imports/issue-<number>.json`. An imported issue cannot be edited or reopened into a
second installation; a genuinely new proposal uses a new issue.

The completion workflow reacts only through the Issues API: it comments, labels and
closes. It writes no repository files. Otherwise its own completion commit would be a
non-inbox remote change capable of blocking a later application sync.

## Sync: the inbox-only exception

The first working loop does not change `Sync.run()`. When the local copy is clean, its
existing remote-advanced branch already calls `replaceAll()` and brings an inbox file
down. `session.now()` then scans the local inbox, installs valid bundles, and calls
`Sync.run()` a second time only when installation made changes. That second call pushes
the entities, receipt, counter and inbox deletion against the head just pulled.

This proves the complete useful path — a hand-committed inbox file becomes a visible
Party — before adding reconciliation logic. If local edits and a remote inbox commit
arrive together at this stage, sync retains its current safe `blocked` result.

The following inbox-only exception is a later hardening slice. It is required for the
finished feature, but it is not a prerequisite for testing the first vertical loop.

The existing safe default remains: if the remembered remote head, the current remote
head, and local dirty state have all moved, sync stops rather than guessing.

There is one narrow exception. When local changes are waiting and the remote branch
has advanced, sync compares the repository trees at the remembered and current heads.
It may rebase automatically only when every remote addition, modification, and deletion
is beneath `inbox/`. If any remote change is elsewhere, the existing blocked result is
returned without changing the local copy.

For a safe inbox-only advance, sync:

1. Captures every non-inbox local dirty operation and the current content of local
   writes.
2. Replaces the local snapshot with the files at the new remote head.
3. Replays the captured non-inbox writes and deletions, preserving their dirty reasons.
4. Records the new remote head as the parent for the eventual push.
5. Runs inbox import before pushing anything.

The application never writes an inbox file; its only local inbox mutation is deleting
one after installation. If the same issue was edited remotely after that deletion, the
remote file is taken. The existing receipt then makes the importer delete it again
without creating duplicate entities. A locally dirty inbox write is an invariant
violation and still blocks.

This produces:

```text
new remote snapshot + previous local edits + newly installed bundles
```

A clean local copy may continue to take the remote snapshot wholesale. A first sync
where both an unrelated local store and a populated remote repository already exist
still blocks: without a remembered base there is no meaningful remote diff to classify.

Once this hardening lands, the sync operation is split conceptually into three ordered
steps:

```text
reconcile remote -> consume inbox -> push local changes
```

This ordering ensures that normal pending edits and a new import go into one commit.
If the branch advances again before the push, GitHub refuses the non-fast-forward
update, all local changes remain dirty, and the next sync performs the same analysis.

## Application-side installation

`Library.importBundle()` is the one domain operation that installs a bundle. `Sync`
continues to understand heads, paths, and file contents; it does not allocate ActorIds
or construct Parties.

`Library.importBundle()` submits the **entire installation** as one `queued()` task.
None of its internal writes is separately queued, and it does not call the public
queued `saveActor()` or `saveParty()` methods. Internal unqueued write helpers let the
one outer task retain exclusive ownership from reservation through inbox deletion, so
an ordinary save cannot interleave with installation.

The existing `nextId(kind)` becomes the one-id case of
`reserveIds(kind, count)`. The range allocator retains `nextId()`'s present-file guard:
it starts above both the stored counter and every id actually present, then advances
the counter once for the whole range. Import does not create a second allocation path
with subtly different collision rules.

Installation proceeds as follows:

1. Read and validate the canonical inbox document again. CI is useful feedback, not a
   trust boundary, and the running application may have a newer schema.
2. If a completed receipt exists, remove the stale inbox file and stop successfully.
3. If an `installing` receipt exists, resume with the ids already recorded there.
4. Otherwise reserve one range of Actor ids and one Party id by advancing
   `counters.json` once. A crash here may leave unused ids, which is harmless.
5. Write an `installing` receipt containing the Party id and ordered Actor ids.
6. Materialise healthy Actors at the assigned ids.
7. Materialise the Party with the allocated Actor ids in the submitted array order.
8. Mark the receipt complete and remove the consumed inbox file.

Writing counters before the first receipt matters. If the application stops before the
receipt is written, retry reserves a new range and merely leaves an id gap. If it stops
afterwards, retry reuses the recorded ids and overwrites or completes the same entity
files instead of creating duplicates.

An import failure leaves the inbox file and an actionable problem visible. It never
marks a receipt complete or silently skips an invalid entity.

An illustrative completed receipt is:

```json
{
  "schemaVersion": 1,
  "bundle": "issue-123",
  "issue": 123,
  "status": "complete",
  "actors": [41, 42],
  "party": 9
}
```

Receipts are retained. Besides idempotence, they answer which stored entities an issue
created. A data-repository workflow triggered by a completed receipt may comment on
and close the corresponding issue; the application's personal access token therefore
continues to need Contents permission only.

## Application feedback

Successful sync reports imported bundles and entities separately from ordinary file
changes, for example:

```text
Imported 7 actors and 1 party from issue #123; 11 changes synced.
```

The shared session store exposes a monotonically increasing library revision. Actors
and Parties pages reload their library data when it changes.

Safe reload is a component change of its own, not merely a session counter. `ActorGrid`
and `PartyGrid` must report whether an inline edit is open. Their pages retain a pending
revision while that is true and reload after the edit commits or cancels. A background
sync therefore cannot throw away text being typed.

Invalid or unsupported inbox files remain visible on the Sync page with their filename
and validation paths. The page offers **Discard**, which removes the inbox file without
creating entities and syncs that deletion. One bad bundle does not prevent other valid
bundles from being installed, but all installations and their resulting push still run
serially.

## Security constraints

- Issue contents are untrusted even in a private repository.
- The issue number, never submitted text, determines the file path.
- Submitted text is parsed as JSON and is never executed or interpolated into shell.
- Workflow permissions are explicit and minimal.
- Third-party Actions and the reusable workflow are pinned to reviewed revisions.
- CI and the application both validate; neither ignores unknown fields.
- The Action can write only an inbox proposal, never application-owned documents.
- The application creates new entities only; a proposal cannot name an existing id and
  overwrite it.

## Implementation slices

Each slice ends in a usable, tested boundary rather than scaffolding for a later one.
The first milestone deliberately proves import without changing reconciliation.

### Milestone 1: one bundle through the existing clean-pull path

1. **Proposal and receipt schemas.** Extract the shared Actor definition shape and
   kind refinement, add the strict bundle schema, generated JSON Schema, receipt
   schema, examples, and tests for every Actor kind.
2. **Library installer.** Generalise `nextId()` into `reserveIds()`, add resumable
   receipts and implement the whole `Library.importBundle()` installation as one
   queued task. Test Party membership and replay after interruption at every step.
3. **Clean-pull session integration.** After an ordinary successful `Sync.run()`, scan
   the local inbox and install valid bundles. Run sync once more when installation made
   changes. Hand-commit `inbox/issue-1.json` and see the Party appear. `Sync.run()` is
   unchanged in this milestone.

### Milestone 2: create inbox entries from issues

1. **Validator command and reusable workflow.** Add the `tsx` command-line entry point,
   package script and reusable workflow. Parse the event, run the runtime validator,
   write or remove the deterministic inbox path, manage labels and comments, and
   serialise commits.
2. **Data-repository form and caller.** Add the generic `library-import` issue form and
   `receive-library-import` caller workflow to the private repository. Document the
   JSON an assistant submits and prove the complete issue-to-Party loop.

### Milestone 3: hardening and feedback

1. **Inbox-only reconciliation.** Add remote-tree comparison and incorporate a remote
   inbox-only advance while non-inbox local edits wait. Retain blocking for every other
   divergence and for the invariant violation of a local inbox write.
2. **Library revision.** Report imported bundles and publish a session-level library
   revision after installation.
3. **Grid-safe refresh.** Give `ActorGrid` and `PartyGrid` an explicit edit-state output;
   their pages defer a revision-triggered reload until the open edit finishes.
4. **Completion feedback.** React to completed receipts using only the Issues API,
   report the allocated entities on the source issue, and close it without committing
   repository files.

## Acceptance tests

- One issue creates one Party containing a mixture of sophonts, animals and robots in
  the submitted order.
- An empty Actor list, imported ids, temporal state, inappropriate combat properties
  and unknown fields are rejected in both CI and the application.
- Editing a pending issue replaces its one inbox entry rather than creating another.
- Making an edited issue invalid removes any older ready inbox entry.
- Re-running sync and recreating an already-consumed inbox file creates no duplicates.
- Interrupting installation after counters, receipt, any Actor, or the Party resumes to
  exactly one complete result.
- Local Actor edits plus a remote inbox-only commit reconcile and push successfully.
- A remote Actor, Party, Situation, counter, receipt, or workflow change while local
  edits wait remains blocked.
- A remote edit of an inbox file already deleted locally is accepted; its completed
  receipt causes it to be deleted again without creating entities.
- A locally written, rather than deleted, inbox file is treated as an invariant
  violation and remains blocked.
- Issue text containing shell syntax is stored or rejected purely as data and never
  executed.
- An open Actors or Parties page shows imported entities after sync without discarding
  an active cell edit.
