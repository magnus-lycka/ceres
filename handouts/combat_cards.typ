// Traveller personal-combat handouts — three A4 cards.
// Build:  uv run python -c "import typst,pathlib; pathlib.Path('handouts/traveller-combat-cards.pdf').write_bytes(typst.compile('handouts/combat_cards.typ'))"
// The PDF is generated and gitignored.

#set page(paper: "a4", margin: 12mm)
#set text(font: ("Helvetica Neue", "Helvetica", "Arial"), size: 8.7pt, fill: rgb("#111820"))
#set par(justify: false, leading: 0.52em)

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
          tracking: 1.2pt, fill: faint)[MONGOOSE TRAVELLER 2E · PERSONAL COMBAT]
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

#let sect(title, body, first: false) = block(breakable: false, width: 100%, below: 9pt)[
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
)[#mono(text(size: 9.5pt, weight: "bold")[#body])]

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

// ══════════════════════════════ CARD 1 ══════════════════════════════
#card("The Combat Round",
  [What everyone can do each round, in what order, and what happens when you get hit. Melee and ranged specifics are on their own cards.])[

#grid(columns: (1fr, 1fr), gutter: 8mm, [

#sect("Initiative", first: true)[
At the start of combat each Traveller makes a *DEX or INT check*. The *Effect* is their Initiative, and it stands for the whole fight — apart from an ambush in round one.

- The referee may make *one check for a whole side*, using the highest DEX or INT among them.
- *Tactics:* one unsurprised Traveller per side may make a Tactics check; its Effect applies to everyone on that side.
- *Ambush:* the aware side adds #dm("+6", kind: "p") to its Initiative, the unaware side #dm("−6", kind: "m") — *round one only*, then both revert. The adjustment is to *Initiative alone*: the ambushed are slower to react, not worse at everything.
]

#sect("Acting order")[
- Highest Initiative acts first.
- Tied? Higher *DEX* goes first.
- Still tied? They act *simultaneously*.
- You may *delay freely* and act later in the turn — Initiative is only your first opportunity, not an obligation.
- Otherwise Initiative does not change between rounds.
]

#sect("Your round — about six seconds")[
+ One *Significant* action and one *Minor* action — _or_ three *Minor* actions instead.
+ Any number of *Reactions*, each at a cost.
+ Any number of *Free* actions.

#v(3pt)
You take your Minor and Significant actions together when your turn comes, then play moves on. The round ends once everyone has had the chance to act.
]

#sect("Significant actions")[
*Attack.* Declare target, they may react, then roll.

*Leadership.* INT, EDU or SOC. Effect = how many #dm("+1", kind: "p") bonuses you may hand to allies you can talk to. Max #dm("+1", kind: "p") per Traveller per check, so spread them. A negative Effect lets the enemy deal that many #dm("−1", kind: "m") penalties the same way.

*Anything needing full attention* — first aid, bypassing a security system, using a psionic talent.
]

#sect("Minor actions")[
#rows(
  [*Aim* — same target, nothing else], dm("+1 each, max +6", kind: "p"),
  [*Change stance* — stand, crouch, prone], [—],
  [*Draw or reload*], [—],
  [*Move* up to your Movement (usually 6 m)], [—],
  [Something small — spot a position, identify kit], [—],
)
#v(3pt)
Difficult terrain halves Movement. Being prone quarters it.
]

], [

#sect("Reactions — unlimited, never free", first: true)[
#note("The cost")[
Every Reaction you take gives you #dm("−1", kind: "m") on your *next set of actions*. Dodge two shots, take #dm("−2", kind: "m").
]
#v(4pt)
- *Dodge* — attacker suffers your DEX DM or Athletics (dexterity), whichever is higher. Melee and ranged. Each attack dodged separately.
- *Dive for cover* — ranged only. #dm("−2", kind: "m") to everyone shooting at you this round, and you may gain Protection. *You forgo your next actions entirely.*
- *Parry* — melee only. Attacker suffers your Melee skill as a negative DM.
]

#sect("Damage")[
+ Roll the weapon's dice and *add the Effect* of the attack roll.
+ Subtract the target's *Protection*. An attack with *Effect 6+ always does at least 1 damage*.
+ Take it off *END* first.
+ Once END is 0, the excess comes off *STR or DEX — the target chooses*.

#v(3pt)
When STR _or_ DEX reaches 0 the Traveller falls *unconscious*, and further damage goes to the remaining characteristic. With all three at 0, they are *dead*.

#v(3pt)
Recalculate characteristic DMs as they drop, and use the impaired DM until healed.
]

#sect("Being down")[
*Unconscious.* An END check every minute to come round. Each failure adds a cumulative #dm("+1", kind: "p") to the next attempt.

*Stunned.* Stun damage comes off END only, after Protection. If it takes END to 0 you are incapacitated for as many rounds as the damage _exceeded_ your END. An hour's rest heals it completely.

*Destructive weapons* (written #mono[3DD]) multiply the damage total by #mono[10].
]

])
#colophon[Core Rulebook, Combat — pp. 73–79, 82]
]

#pagebreak()

// ══════════════════════════════ CARD 2 ══════════════════════════════
#card("Melee Combat",
  [Knives, blades, clubs and fists — and what changes once you are close enough to be grabbed.])[

#grid(columns: (1fr, 1fr), gutter: 8mm, [

#sect("The attack", first: true)[
#formula[2D + Melee (speciality) + STR #text(style: "italic")[or] DEX DM ≥ 8]
#v(4pt)
Use whichever of STR or DEX suits the weapon and the fighter.
#v(4pt)
#note("Damage")[
Weapon dice *+ your STR DM* + the Effect of the attack roll. Bigger things hit harder.
]
]

#sect("Close combat — within two metres")[
- You may attack *only* those you are locked in close combat with, and they may attack only you.
- Only *single-handed* ranged weapons may be fired — and a pistol *can be parried*, knocked aside as it comes up.
- Rifles and other larger weapons may only be used as *clubs*.
- Move while locked and your enemy gets an immediate free attack at #dm("+2", kind: "p").
]

#sect("Defending")[
#rows(
  [*Parry* — close combat only], dm("−your Melee skill", kind: "m"),
  [*Dodge* — DEX DM or Athletics (dex), whichever is higher], dm("−that DM", kind: "m"),
)
#v(3pt)
You cannot dive for cover against a melee attack. Each Reaction still costs #dm("−1", kind: "m") on your next actions.
]

], [

#sect("Grappling", first: true)[
Opposed *Melee (unarmed)* checks, each side using STR or DEX DM. The winner chooses one:

- Force the opponent *prone*.
- *Disarm* them — on Effect 6+, take the weapon.
- *Throw* them #mono[1D] metres for #mono[1D] damage. Ends the grapple.
- Inflict #mono[2 + Effect] damage, *ignoring armour*.
- Attack with a pistol or blade-sized weapon.
- *Escape* and move away, or *drag* them up to 3 m.
- Hold on, with no other effect.

#v(3pt)
While grappling you may take *no other Significant or Minor action* — only further opposed Melee (unarmed) checks.
]

#sect("Two weapons")[
With a weapon in each hand — two blades, or a blade and a pistol — you may attack with both in the same round, at #dm("−2", kind: "m") to _both_ rolls, and you may not aim.

#v(3pt)
Carrying two but attacking with one? No penalty.
]

#sect("Heavy weapons")[
#table(
  columns: (auto, auto, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 9pt,
  align: (left, left, right),
  [*Bulky*], [STR 9+], dm("STR DM − (+1)", kind: "m"),
  [*Very Bulky*], [STR 12+], dm("STR DM − (+2)", kind: "m"),
)
#v(3pt)
A STR 7 fighter (DM #mono[+0]) with a Bulky weapon attacks at #dm("−1", kind: "m").
]

])
#colophon[Core Rulebook, Combat — pp. 75–79, 125]
]

#pagebreak()

// ══════════════════════════════ CARD 3 ══════════════════════════════
#card("Ranged Combat",
  [Guns, grenades and rocket launchers — range, cover, and the traits that change how a weapon behaves.])[

#grid(columns: (1fr, 1fr), gutter: 8mm, [

#sect("The attack", first: true)[
#formula[2D + Gun Combat (speciality) + DEX DM ≥ 8]
#v(4pt)
Some weapons use a different skill: *Heavy Weapons (portable)* for a rocket launcher, *Athletics (dexterity)* for grenades and anything else thrown.
#v(4pt)
#note("Damage")[
Weapon dice + the Effect of the attack roll. *No STR DM* — that is melee only.
]
]

#sect("Range")[
Measured against the weapon's own *Range* score.
#v(3pt)
#table(
  columns: (auto, 1fr, auto),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 9pt,
  align: (left, left, right),
  [*Short*], [within ¼ of Range], dm("+1", kind: "p"),
  [*Range*], [up to Range], dm("+0"),
  [*Long*], [up to 2× Range], dm("−2", kind: "m"),
  [*Extreme*], [up to 4× Range], dm("−4", kind: "m"),
)
#v(3pt)
Without a *Scope*, anything beyond #mono[100 m] counts as Extreme regardless. Out of combat the referee may stretch that to 300 m.
]

#sect("Common modifiers")[
#rows(
  [Aiming, per Minor Action spent], dm("+1", kind: "p"),
  [Laser sight, if aiming], dm("+1", kind: "p"),
  [Target in cover], dm("−2", kind: "m"),
  [Prone target], dm("−1", kind: "m"),
  [Fast-moving target, per full 10 m relative to you], dm("−1", kind: "m"),
)
]

#sect("Cover")[
Anyone fighting from cover inflicts #dm("−2", kind: "m") on ranged attacks against them.

Fully hidden and _not_ attacking, they also gain bonus Protection — the best single source only, never two added together.
#v(3pt)
#rows(
  [Vegetation], dm("+2", kind: "p"),
  [Tree trunk], dm("+6", kind: "p"),
  [Stone wall], dm("+8", kind: "p"),
  [Civilian vehicle], dm("+10", kind: "p"),
  [Armoured vehicle], dm("+15", kind: "p"),
  [Fortifications], dm("+20", kind: "p"),
)
]

], [

#sect("Automatic fire — Auto X", first: true)[
#table(
  columns: (auto, 1fr, auto),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 9pt,
  align: (left, left, right),
  [*Single*], [Normal attack], mono[1],
  [*Burst*], [Add the Auto score to damage], mono[Auto],
  [*Full auto*], [Auto score separate attacks, targets within 6 m of each other], mono[3× Auto],
)
#v(3pt)
Automatic fire *loses all benefit from aiming*, and cannot be combined with the Scope trait.
]

#sect("Blast X")[
Damage is rolled against *every target within X metres*.

- *Dodge does not work* against a Blast weapon.
- Targets *may still dive for cover*.
- Cover counts only if it lies between the target and the *centre* of the blast.
]

#sect("Traits worth remembering")[
#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 9pt,
  align: (left, left),
  [*AP X*], [Ignores X points of Protection],
  [*Smart*], [DM equal to the TL difference over the target, +1 to +6],
  [*Scope*], [Ignores the 100 m Extreme rule, if you aim first],
  [*Stun*], [Damage to END only; see The Combat Round],
  [*Zero-G*], [No Athletics (dexterity) check in low or zero gravity],
  [*Radiation*], [Target takes 2D×20 rads],
)
]

#sect("Firing in close combat")[
Within two metres of an enemy you are *locked in close combat*, and the ranged rules narrow sharply:

- You may attack only those you are locked with.
- Only *single-handed* weapons — pistols — may be fired.
- A fired pistol *can be parried*, knocked aside as it comes up.
- Rifles and anything larger may only be used as *clubs*.

The rest of close combat is on the *Melee Combat* card.
]

#sect("Encounter range bands")[
#rows(
  [Close], mono[up to 5 m],
  [Short], mono[5–10 m],
  [Medium], mono[11–50 m],
  [Long], mono[51–250 m],
  [Very Long], mono[251–500 m],
  [Distant], mono[501–5,000 m],
  [Very Distant], mono[over 5 km],
)
#v(3pt)
Most firefights open at *Medium* range. One map square or hex is 1.5 m.
]

])
#colophon[Core Rulebook, Combat — pp. 74–80, 85]
]
