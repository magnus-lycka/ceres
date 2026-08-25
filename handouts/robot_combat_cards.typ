// Traveller robot-combat handouts — two A4 cards.
// Build: uv run python -c "import pathlib,typst; pathlib.Path('output/pdf/traveller-robot-combat-cards.pdf').write_bytes(typst.compile('handouts/robot_combat_cards.typ'))"

#set page(paper: "a4", margin: 12mm)
#set text(font: ("Helvetica Neue", "Helvetica", "Arial"), size: 8.5pt, fill: rgb("#111820"))
#set par(justify: false, leading: 0.5em)

#let accent = rgb("#123c52")
#let pos = rgb("#1f5348")
#let neg = rgb("#7c2c1a")
#let faint = rgb("#5b636b")
#let rule = rgb("#aab2ba")
#let soft = rgb("#eef1f4")

#let mono(body) = text(font: ("SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"), body)

#let card(name, lede, body) = {
  block(spacing: 0pt)[
    #text(font: ("SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"), size: 7pt,
          tracking: 1.2pt, fill: faint)[MONGOOSE TRAVELLER 2E · ROBOT COMBAT]
    #v(3pt)
    #text(font: ("SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"),
          size: 19pt, weight: "bold", fill: rgb("#111820"))[#name]
    #v(3pt)
    #text(size: 9pt, fill: rgb("#39414a"))[#lede]
    #v(5pt)
    #line(length: 100%, stroke: 1.2pt + accent)
    #v(7pt)
  ]
  body
}

#let sect(title, body, first: false) = block(breakable: false, width: 100%, below: 8pt)[
  #if not first {
    line(length: 100%, stroke: 0.5pt + rule)
    v(5pt)
  }
  #text(font: ("SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"),
        size: 7.2pt, weight: "bold", tracking: 1.1pt, fill: accent)[#upper(title)]
  #v(4pt)
  #body
]

#let formula(body) = block(
  width: 100%, fill: soft, stroke: 0.5pt + rule, inset: (x: 7pt, y: 6pt), radius: 1pt,
)[#mono(text(size: 9.2pt, weight: "bold")[#body])]

#let note(label, body) = block(
  width: 100%, fill: soft, inset: (x: 8pt, y: 6pt),
  stroke: (left: 2pt + accent),
)[
  #text(font: ("SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"),
        size: 6.8pt, tracking: 1pt, fill: accent)[#upper(label)]
  #v(2pt)
  #body
]

#let dm(v, kind: "n") = {
  let c = if kind == "p" { pos } else if kind == "m" { neg } else { rgb("#111820") }
  mono(text(weight: "bold", fill: c)[#v])
}

#let rows(..args) = table(
  columns: (1fr, auto),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 10pt,
  align: (left, right),
  ..args
)

#let colophon(body) = {
  v(2pt)
  line(length: 100%, stroke: 0.5pt + rule)
  v(3pt)
  text(font: ("SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New"), size: 6.6pt, fill: faint)[#body]
}

// CARD 1
#card("Running a Robot in Combat",
  [Use the normal personal-combat sequence. The robot record changes which numbers you use — and physical form decides what it can actually do.])[

#grid(columns: (1fr, 1fr), gutter: 8mm, [

#sect("Start with the robot record", first: true)[
Before combat, mark these six lines:

- *Hits* and *Armour (Protection)* — robot injury is not characteristic damage.
- *Speed* and locomotion — use these instead of a humanoid's usual 6 m.
- *Skills* — programmed skills and adjusted fire-control values.
- *Attacks* — installed weapons and their already-recorded damage and traits.
- *Manipulators* — each may have different STR and DEX.
- *Small/Large* — in Traits, from chassis Size. Works as it does for any target.
]

#sect("Initiative and actions")[
#formula[2D + overall DEX or INT DM → Effect = Initiative]
#v(4pt)
The normal round applies: one Significant and one Minor action, or three Minor actions; normal Free actions and Reactions. The referee may still roll once for a whole side.

#v(3pt)
*Form matters.* A wheeled turret cannot automatically crouch, dive, climb or wield a loose rifle merely because a humanoid can. Allow an action when its locomotion, manipulators and description make it possible.
]

#sect("Ranged attacks — held weapons")[
#formula[2D + weapon skill + actual manipulator DEX DM ≥ 8]
#v(4pt)
Use the DEX of the manipulator that aims or fires — not simply the best DEX anywhere on the robot. Bulky and Very Bulky requirements likewise use the STR of the manipulator handling the weapon.

#v(3pt)
All ordinary modifiers still apply: aim, range, cover, prone target, Auto, Scope, AP and so on. Damage is weapon dice + Effect.
]

#sect("Mounted weapons and fire control")[
- An integrated weapon's fire-control value is its weapon skill DM.
- A mounted weapon without fire control needs the relevant skill package; otherwise it attacks unskilled at #dm("−3", kind: "m").
- For a weapon on a manipulator, add the robot's weapon skill and the *higher* of that manipulator's DEX DM or its dedicated fire-control DM — never both.
- A fire-control system tracks one primary target. Linked identical mounts make one attack; published robot damage already includes their linked bonus.
]

], [

#sect("Defending", first: true)[
Robots use normal Reactions when physically capable:

#rows(
  [*Dodge* — overall DEX DM or Athletics (dex), whichever is higher], [−that DM],
  [*Parry* — close combat, using Melee skill], [−Melee],
  [*Dive for cover* — ranged; suitable movement and nearby cover required], dm("−2", kind: "m"),
)
#v(3pt)
Overall DEX is based on the most dexterous manipulator plus any agility enhancement. A weapon's fire control does *not* improve Dodge.

#v(3pt)
Each Reaction still inflicts #dm("−1", kind: "m") on the robot's next actions. Diving still forfeits those actions.
]

#sect("Melee attacks")[
#formula[2D + Melee + actual manipulator STR or DEX DM ≥ 8]
#v(4pt)
Use the STR or DEX of the limb actually attacking. Normal melee damage is weapon dice + that manipulator's STR DM + Effect.

#v(3pt)
Use a listed melee attack when the robot has one. If improvising an unarmed manipulator attack, the Robot Handbook suggests manipulator Size ÷ 2 as a rough guide to damage dice. A robot does not normally use manipulators as weapons without an appropriate Melee package.
]

#sect("Close combat and grappling")[
Within 2 m, the standard close-combat restrictions apply: engage only those locked with you; pistols may fire and be parried; larger guns become clubs; moving away allows the enemy's immediate attack at #dm("+2", kind: "p").

#v(3pt)
*Grapple:* opposed Melee (unarmed), using the actual manipulator's STR or DEX DM. Use the normal choices — prone, disarm, throw, damage, attack with a small weapon, escape, drag or hold.

#v(3pt)
Grapple damage that ignores armour removes *Hits*. Anatomy still controls what is plausible: a robot needs suitable limbs or another stated means to seize, drag or disarm. A purpose-built crush attack is not automatically a grapple.
]

#sect("What is genuinely different")[
#note("Do not treat it like a sophont or animal")[
Hits do not reduce STR, DEX or END, and low Hits alone cause no action DM. Capacity falls when *critical hits damage systems*. At 0 Hits the robot is wrecked, not unconscious or dead. See the Robot Damage card.
]
]

])
#colophon[Core Rulebook, Combat — pp. 73–79, 125 · Robot Handbook — pp. 13–14, 25–28, 60–61, 76, 115–117]
]

#pagebreak()

// CARD 2
#set text(size: 8.1pt)
#card("Robot Damage",
  [Conventional ranged and melee attacks only. Apply Hits and system criticals — not sophont characteristic damage or animal injury thresholds.])[

#grid(columns: (0.88fr, 1.12fr), gutter: 8mm, [

#sect("Resolve the hit", first: true)[
+ Roll weapon damage and add attack *Effect*; for melee, also add the attacking limb's *STR DM*.
+ Apply AP, then subtract the robot's *Protection*.
+ Remove the remainder from *Hits*. Effect 6+ always inflicts at least 1 damage despite Protection.
+ Check for an *attack critical* and every newly crossed *sustained-damage* threshold. Both can happen from one attack.

#v(3pt)
#formula[current Hits = starting Hits − cumulative damage]
]

#sect("Hits are not animal Hits")[
#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 9pt,
  [*Above 0*], [Operational, except for critical-hit effects],
  [*0 or less*], [*Wrecked and inoperable*, but potentially repairable],
  [*−starting Hits*], [*Irreparably destroyed* — cumulative damage equals twice starting Hits],
)
#v(3pt)
There is no animal-style driven-off, half-Hits or 10%-Hits unconscious state. A robot also takes no automatic general penalty merely for having few Hits left.
]

#sect("Attack critical — a precise hit")[
If the attack has *Effect 6+* and inflicts damage after Protection:

#formula[Severity = attack Effect − 5]
#v(4pt)
Roll 2D for location, then apply that Severity's effect. This critical is additional to the Hits already lost.
]

#sect("Sustained damage — systems degrade")[
Every time cumulative damage crosses another *10% of starting Hits*, roll a location and inflict a *Severity 1* critical.

#v(3pt)
For a 20-Hit robot, mark one at 2, 4, 6, 8 … cumulative damage. Critical extra damage can cross more thresholds; keep resolving until no new threshold has been crossed.
]

#sect("Roll 2D for location")[
#table(
  columns: (auto, 1fr, auto, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 2.5pt),
  column-gutter: 7pt,
  [*2–4*], [Power supply], [*8–9*], [Locomotion],
  [*5*], [Weapon], [*10–11*], [Options],
  [*6*], [Armour], [*12*], [Brain],
  [*7*], [Chassis], [], [],
)
#v(3pt)
If the location does not exist, reroll. Where several weapons or options exist, select the affected one randomly.
]

], [

#sect("Critical-hit effects", first: true)[
#set text(size: 6.6pt)
#table(
  columns: (0.95fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
  stroke: 0.35pt + rule,
  fill: (x, y) => if y == 0 { soft } else { none },
  inset: (x: 2.5pt, y: 3pt),
  align: (left, left, left, left, left, left, left),
  text(weight: "bold")[Location],
  text(weight: "bold")[S1], text(weight: "bold")[S2], text(weight: "bold")[S3],
  text(weight: "bold")[S4], text(weight: "bold")[S5], text(weight: "bold")[S6],

  text(weight: "bold")[Power],
  [Speed −1 m/band], [Remaining Endurance half], [Half again], [Half again],
  [Explodes; shutdown; Chassis S+1], [Explodes; shutdown; Chassis S+1D],

  text(weight: "bold")[Weapon],
  [Random weapon attack DM−2], [Disabled], [Destroyed],
  [Explodes; Chassis S+1], [Explodes; Chassis S+1], [Explodes; Chassis S+1],

  text(weight: "bold")[Armour],
  [Protection −1], [Protection −1D], [Protection −1D], [Protection −2D],
  [Protection −2D; Chassis S+1], [Protection −2D; Chassis S+1],

  text(weight: "bold")[Chassis],
  [Suffer 1D], [Suffer 2D], [Suffer 3D], [Suffer 4D], [Suffer 5D], [Suffer 6D],

  text(weight: "bold")[Locom.],
  [Speed −1 m/band], [Speed −1 m/band], [Speed −1 m/band], [Speed −1 m/band],
  [Immobilised], [Immobilised; Chassis S+1],

  text(weight: "bold")[Options],
  [Random option DM−2], [Random option disabled], [Random option destroyed],
  [Two random options destroyed], [Random option destroyed; Chassis S+1],
  [Random option destroyed; Chassis S+1],

  text(weight: "bold")[Brain],
  [DM−2 to one skill], [DM−2 to all skills], [Cannot perform skills], [INT halved],
  [Brain disabled], [Brain destroyed; Chassis S+1],
)
#set text(size: 8.1pt)
]

#sect("Repeat hits to one location")[
#formula[new Severity = max(rolled Severity, old Severity + 1)]
#v(4pt)
Apply the newly reached effect immediately. Once a location is already Severity 6, every further hit there instead inflicts *6D Hits*. Any extra damage caused by a critical ignores Protection.
]

#sect("Reading the effects")[
- Reductions happen when each new Severity is reached. Record them; they remain until repaired.
- *Disabled brain* or shutdown makes the robot inoperable. *Immobilised* only prevents movement; usable weapons may still fire.
- Weapon and option effects apply to the particular component rolled. They are not a general action penalty.
- Chassis damage and all other critical extra damage bypass Protection, reduce Hits, and may trigger sustained-damage criticals.
]

#sect("Combat record")[
#table(
  columns: (1.1fr, 0.65fr, 1.65fr),
  stroke: 0.4pt + rule,
  inset: (x: 4pt, y: 3pt),
  fill: (x, y) => if y == 0 { soft } else { none },
  text(weight: "bold")[Location], text(weight: "bold")[Severity], text(weight: "bold")[Component / effect],
  [Power], [], [],
  [Weapon], [], [],
  [Armour], [], [],
  [Chassis], [], [],
  [Locomotion], [], [],
  [Options], [], [],
  [Brain], [], [],
)
]

])
#colophon[Core Rulebook, Combat — pp. 77, 125 · Robot Handbook — pp. 106, 109–110 · Specialist anti-robot, radiation, ion and stun rules deliberately omitted]
]
