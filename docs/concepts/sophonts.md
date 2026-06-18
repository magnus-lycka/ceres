# Sophonts — Playable Species Reference

This document summarises every species in `refs/` that has published character-creation
rules for Mongoose Traveller 2nd Edition, with emphasis on what matters for Ceres
implementation: characteristic generation differences, characteristic replacements,
career restrictions, and special creation-time mechanics.

Current Ceres status: only `Humaniti` and `Vilani` are defined in
`src/ceres/character/domain/sophont/`.

---

## Quick-reference table

| Species | Category | Source | Characteristic changes | Replacement char | New char | Special |
|---|---|---|---|---|---|---|
| Ael Yael | Alien | JTAS 3 | STR-1 | — | — | No Noble; 90% cash donated; DM-2 enlistment |
| Aezorgh | Alien | JTAS 11 | STR=1D, DEX=2D+3, END=1D+1, INT=2D+2, EDU=1D, SOC=1D | — | — | DM+4 aging until term 16 |
| Amindii | Alien | JTAS 9 | STR=3D (+2 Activator; +END 1 Bearer) | — | — | Three genders; age 14 start; Perception ability |
| Aniyun | Alien | Spinext | STR=1D, EDU-2 | — | — | Citizen/Drifter only; natural flight |
| Ascondi | Alien | Great Rift 1 | END+1; caste mods at age ~20 | — | — | Caste replaces background; SOC starts at 1 |
| Aslan | Major | AoCS 1 | STR+2 DEX-2 END+1 (m); STR+1 DEX-1 END+2 (f) | SOC → TER | — | Rite of Passage; Clan Shares; gender-locked assignments |
| Aslan (Darrian) | Alien | AoCS 3 | STR+1, DEX+1, EDU+1 | SOC → TER | — | Any Darrian career; gender preferences softened; Roget Aslan may also use AoCS 1 options |
| Bosaki | Alien | JTAS 17 | STR=1D+1, DEX=2D+2, END=1D+1, INT=2D+1, EDU=2D, SOC=4 | — | — | Age 24 start; Combat Aversion |
| Bruhre | Alien | Deepdark | STR=3D(max 18), DEX=1D, END=3D+2(max 20), SOC=1D | — | — | No Drifter/Entertainer/Rogue |
| Bwap | Alien | AoCS 3 | STR-4 END-4 | — | — | Faster aging; no Rogue; Structured Mind trait |
| Caprisaps (Alpine) | Uplift | JTAS 12 | STR-2, DEX+2 | — | — | Goat uplift; Improved Digestion |
| Caprisaps (Boar) | Uplift | JTAS 12 | STR-1, DEX+1 | — | — | Goat uplift; Improved Digestion |
| Chokari | Uplift | BTC | END+1, SOC-1 | — | PSI (2D) | Ancient uplift (Foelen); psionic training before career; Deep Diver (100m); Swimmer (6m) |
| Darrian | Human | AoCS 3 / BTC | STR-1 DEX+1 END-1 INT+1 EDU+1 | — | — | Restricted career list; first term forced |
| Dolphin (Foelen) | Uplift | BTC | END+1, SOC-1 | — | — | Ancient uplift near Foelen; all Core careers |
| Dolphin (Solomani) | Uplift | AoCS 3 | STR+4 END+2 SOC-4 | — | — | Solomani uplift; age 12 start; restricted careers |
| Droyne | Major | AoCS 2 | STR/DEX/END/INT/EDU=1D+1; PSI=2D; caste mods | SOC → PSI | — | Caste-based careers; no standard career flow |
| Dynchia | Alien | JTAS 1 | STR=1D+3, DEX+1, EDU+1 | — | — | DM-2 enlistment outside Comitia |
| Geonee | Human | AoCS 3 | STR+2 DEX-1 END+2 SOC-1 | — | — | Extra background skill |
| Girug'kagh | Alien | JTAS 1 | STR=1D+2, END=1D+2, DEX=1D+7 | — | — | Translator-only; serve K'kree for life |
| Githiaskio | Alien | JTAS 2 | — | — | — | Zero-g/aquatic specialist; gravity injures without suit |
| Gmina | Alien | Spinext | STR=2D+4, EDU=1D, SOC=2 (fixed), DEX-1 | — | — | Drifter only; four arms |
| Gurvin | Alien | AoCS 4 | Females INT+1 EDU+1; Males STR-1 DEX+1 | — | — | Male INT/EDU=1D+1; age 16 start |
| Halkans | Alien | JTAS 8 | END+1, EDU-1 | — | — | Pacifism; reroll combat skills during creation |
| Happrhani | Human | Deepdark | END+1 | — | — | Barbarian only if steppe/desert nomad |
| Hhkar | Alien | JTAS 12 | STR+3 END+3; reset per gender transformation | — | — | Serial hermaphroditism reverses aging |
| Hiver | Major | AoCS 2 | STR-2 | SOC → RES | — | RES=1D+6; no survival checks; aging from 38 |
| Hlanssai | Alien | JTAS 4 | STR-2 DEX+2 EDU-2, SOC=1D+4 / fixed 5 | — | — | Bypasses standard career system entirely |
| Iltharans | Human | Deepdark | END+1 | — | — | Longevity +6 aging |
| Ithklur | Alien | JTAS 7 | EDU-1 | SOC → RES | — | EDU=1D+1, RES=1D+1; Fourfold Way path system |
| J'aadje | Alien | Deepdark | STR-2, DEX+2 | — | — | All careers |
| Jonkeereen | Human | BTC | END+1, EDU-1 | — | — | Heat resistance |
| K'kree | Major | AoCS 1 | STR+6, INT+2, EDU+2 (patriarch) | — | — | Creates whole household; Patriarchy skill; Claustrophobic; Gregarious |
| Kemlae | Alien | Spinext | DEX+1, END+1, EDU-1, SOC-1 | — | — | Age 8 start; Kuftu transformation/death after term 7 |
| Krotan | Alien | JTAS 15 | END=3D, DEX-2, SOC=2D (age indicator) | — | — | Merchant/Citizen only; no survival checks |
| Ktiauao | Alien | Spinext | STR+1, DEX+2 | SOC → TER (Aslan-style) | — | Uses Aslan careers; three genders |
| Lhshana | Alien | JTAS 16 | DEX+1, INT+1, SOC-2 | — | — | Standard careers; trilateral physiology |
| Mal'Gnar | Alien | Spinext | EDU=1D+1 | — | — | Drifter only; cannot speak Galanglic |
| Mewey | Alien | JTAS 13 | STR-2, INT+1, EDU+1 | — | — | Heightened Senses; Empathetic; limited Navy |
| Nenlat | Alien | JTAS 10 | STR+1, EDU-2 (assim.); STR+1, EDU=1D (trad.); gender mods | — | — | Amphibious; age 14 start; trilateral |
| Orca | Uplift | AoCS 3 | STR+8 END+4 SOC-4 | — | — | Solomani uplift; 12× ship space; restricted careers |
| Ormine | Alien | Deepdark | DEX-2, END+2 | — | — | 28-year terms; start at 30; aging at 254 |
| Solomani | Major | AoCS 2 | — | — | — | Race roll; party patronage; SolSec monitor |
| Suerrat | Alien | AoCS 4 | STR+1 DEX+2 SOC-1 | — | — | Cold/radiation resistance |
| Sword Worlders | Human | Sword | — | — | — | Patrol career (max age 30 to join) |
| Tezcat | Alien | AoCS 4 | DEX+1 END-1 | — | — | No Noble; mandatory combat background skills |
| Tlinzha | Alien | Sector 8 | END=3D | — | — | 8-year terms; age 8 start; no psionics |
| Tlyetrai | Alien | Deepdark | STR-2, DEX+1, INT+1 | — | — | No Army/Navy/Marine/Rogue unless emigrated |
| Ulane | Alien | Deepdark | DEX+2; STR/END=1D+1 | — | — | Fast Metabolism; Multi-limbed; Small (-1) |
| Yn-tsai | Alien | Deepdark | STR-2, INT+2 | — | — | All Core careers; Low Pressure trait |
| Vargr | Major | AoCS 1 | — | SOC → CHA | — | CHA gain/loss mechanic |
| Vegan | Alien | Sol/AoCS | EDU+2, SOC-2 | — | — | First career must be Drifter; 200+ year lifespan |
| Vilani | Major | Core | — | — | — | No mechanical differences |
| Virushi | Alien | JTAS 5 / Deepdark | STR=1D+10, END=1D+10, DEX+2, SOC-2 | — | — | SOC career gains → EDU; no Army/Navy/Marines; 8-ton staterooms |
| Za'tachk | Alien | AoCS 4 | STR+1; Matriarchs INT+1 EDU+1 BOL-1; Scouts INT-1 EDU-1 BOL+1 | — | BOL (1D+1) | Three sexes; age 10/15 start; Coward trait |
| Zhodani | Major | AoCS 1 / BTC | EDU min 8 if SOC 10+ | — | PSI (rolled first) | Social class tiers gate careers |

---

## Major Races

The eight species that independently discovered jump drive. They are the dominant political
and cultural powers of Charted Space.

### Vilani
*Source: core (no separate creation chapter in refs)*

Standard human characteristics and career access. No mechanical differences from Core
character creation. Vilani cultural traits (conservative, specialist-focused) are roleplaying
flavour rather than mechanical rules.

### Solomani
*Source: AoCS Vol. 2 (`refs/alien2/13_solomani_travellers.md`)*

Standard human characteristics. Key creation mechanics:
- **Race roll:** After generating characteristics, roll 2D+SOC DM. Non-Solomani suffer DM-2
  enlistment in SolSec, Navy, and Marines, and DM-2 advancement in all careers except Drifter,
  Rogue, and Citizen (worker). Mixed race is slightly less penalised.
- **Party patronage:** SOC modifier applied to all career qualification rolls (all careers
  except Rogue and Drifter). SOC 10+ enables automatic commission/promotion when roll fails
  (up to rank limits in table).
- **SolSec Monitor:** Parallel to any career; grants DM+1 advancement. Can be entered/exited
  each term.
- **Home Forces Reserves:** Parallel reserve service alongside any non-Rogue/Drifter career.
- **New careers:** Party (SOC 6+, racial Solomani), SolSec (INT 6+), Confederation Navy.
- **Restricted careers:** No Noble, no Scout. Marine: star marines assignment only.
- **Pensions:** Half pension for most careers; full for Party and SolSec.
- **Anagathics:** Confederation cannot manufacture them; SOC 11+ needed to acquire imported ones.

### Zhodani
*Source: AoCS Vol. 1 (`refs/alien1/15_the_zhodani.md`); BTC (`refs/btc/04_creating_zhodani_travellers.md`)*

- **PSI rolled first** (2D) before other characteristics.
- PSI 9+ raises SOC to minimum 10 (prole elevated to intendant).
- **EDU hard-capped by SOC** for proles; SOC 10+ raises EDU to minimum 8.
- **Social class tiers** (prole/intendant/noble) gate career access; intendant/noble required
  for Noble career.
- Psionic training is mandatory before the first career term.
- Full Zhodani career list: Agent, Army, Entertainer, Merchant, Navy, Noble, Scholar, and
  Zhodani-specific assignments. BTC simplified version uses Core careers.

### Vargr
*Source: AoCS Vol. 1 (`refs/alien1/12_vargr_travellers.md`)*

Uplifted wolves. Genetically engineered by the Ancients from Earth canines. A Major Race
by virtue of their independent development of jump drive.

- **SOC replaced by CHA (Charisma).** When a SOC check is required in a non-Vargr context,
  increase difficulty one step and use SOC.
- CHA changes during play via a 2D+CHA DM vs current CHA check (Ceres: this is a
  career-term mechanic, not just mid-campaign).
- In the Vargr Extents, CHA replaces SOC throughout; outside Vargr space, both characteristics
  may apply depending on context.
- **Additional careers:** Emissary, Corsair, Scientist, Psion.
- Pack Events table added to Life Events.
- **Ship benefits:** Corsair career can muster out a Ruguelka-class ship (25% mortgage).

### Aslan
*Source: AoCS Vol. 1 (`refs/alien1/02_aslan_travellers_chapter_two.md`)*

Feline species from the Aslan Hierate.

- **Characteristics:** STR+2, DEX-2, END+1 (male); STR+1, DEX-1, END+2 (female).
- **SOC replaced by TER (Territorial Imperative).**
- **Rite of Passage** (roll 10+) replaces qualification for the first career.
- **Clan Shares** replace pensions (tradeable for cash, land, ship shares, favours).
- **Gender-locked assignments:** Commander (male only), Shipmaster and Navigator (female only);
  Wanderer career (male only).
- Male cash mustering out limited to rolls equal to Independence skill level; cash at half value.
  Females have unlimited cash rolls.
- Aslan-specific Life Events table.

### Hivers
*Source: AoCS Vol. 2 (`refs/alien2/36_chapter_thirty_four.md`)*

Manipulative, star-faring species from the Hive Federation.

- **Characteristics:** STR-2. **SOC replaced by RES (Resolve) = 1D+6.**
- No basic training. **No survival checks** during careers.
- Aging begins at 38. Anagathics do not work for Hivers.
- Nest-based career system: Academic, Generalist, Manipulator, Merchant.
- Cannot gain Leadership skill.
- Cash mustering-out results can be negative (debt mechanic).
- Physical Coward trait: must check RES/BOL when physically threatened within 25m.
- Natural armor 2; regeneration; dormancy ability.

### K'kree
*Source: AoCS Vol. 1 (`refs/alien1/07_chapter_seven.md`; lore in `refs/alien1/06_chapter_six.md`)*

Large centauroid herbivores from the Two Thousand Worlds. Militant herbivores who view
meat-eaters (G'naak) as vermin. Psychologically dependent on the herd — a lone K'kree
will quickly go mad. Creating a K'kree Traveller generates a **patriarch and his entire
household**, not just an individual.

#### Characteristics

- **Patriarch (Traveller):** STR+6, INT+2, EDU+2.
- Other males in the family: STR+6, INT-4, EDU-4.
- Females: STR+3, EDU-5.
- SOC rolled normally and determines caste (see SOC Rank table below).

#### SOC / Caste

| SOC | Caste |
|---|---|
| 0 | Outcast / casteless |
| 1–3 | Lowest Value Servant |
| 4–6 | Servant |
| 7–10 | Merchant |
| 11 | Noble (Small Family Patriarch) |
| 12 | Noble (Big Family Patriarch) |
| 13 | Herdlord |
| 14 | Clanlord |
| 15 | Steppelord |

Within each rank there are three degrees: Servant-of-Rankholder → Kinsman-of-Rankholder
→ Rankholder, advanced by Patriarchy checks.

#### Background Skills

Melee Combat 0, Patriarchy 0, Recon 0, Survival 0.

#### New Skill: Patriarchy

Replaces both Diplomacy and Leadership when dealing with other K'kree. Governs correct
conduct of rituals, social positioning, and control of the household. Determines max
family size (Patriarchy 0 = D3+3; each additional level adds D3). Leadership and Diplomat
still exist for non-K'kree interactions.

#### Traits

**Big and Tough:** END damage halved; END treated as doubled for duration (not magnitude)
of physical activity. **Claustrophobic:** Difficult (10+) END check to enter confined
spaces; DM-2 for staterooms, DM-4 for crawlways. Failure = will not enter. Already-
confined K'kree must re-check when disturbed. **Gregarious:** Average (8+) END check each
day when isolated; failure = DM penalty; Effect -6 = collapse. **Speed of Hoof:** If all
three minor actions are movement, gain a fourth movement action.

#### Careers

All K'kree spend their **first term as warriors** regardless of intended career.

| Career | Qualification |
|---|---|
| K'kree (pastoral/traditional) | Automatic |
| Servant | SOC 1–6 |
| Merchant | SOC 7–10 |
| Noble | SOC 11+ |

Promotion is based on SOC and Patriarchy skill. Gaining wives (via Patriarchy checks
of increasing difficulty each term) adds D3 family members. K'kree Life Events table
replaces the standard Life Events table.

#### Household in Play

Patriarch's family functions as a small-unit force. Warriors can absorb up to 15 damage
points meant for the patriarch (one per attack). Specialist functionaries grant DM+2 to
tasks when the patriarch lacks the relevant skill. Family size can exceed the Patriarchy
control limit, imposing DM-1 per excess member on all Patriarchy checks.

#### Outsider K'kree

A K'kree raised outside traditional society gains Outsider skill (level 0) in addition
to background skills. Outsider can be increased in place of characteristic improvements
during events. Still has Gregarious and Claustrophobic. Outsider skill gives DM to cope
with loneliness but imposes equal DM-penalty when interacting with 'real' K'kree. Can
enter any career a human could (referee's discretion for very enclosed roles). Outsider K'kree
have SOC 0 in K'kree society.

### Droyne
*Source: AoCS Vol. 2 (`refs/alien2/23_chapter_twenty_one.md`, `refs/alien2/24_droyne_as_travellers.md`)*

Ancient, widespread caste-based species. Playing a Droyne is demanding; they are
psychologically shaped by their Oytrip (community) and deeply distressed when separated
from it. Still entirely playable — requires a separate creation path.

#### Characteristics

An immature Droyne's first five characteristics (STR, DEX, END, INT, EDU) are rolled on
**1D+1** rather than the usual 2D. The sixth characteristic is **PSI (rolled on 2D)**;
Droyne have **no SOC**.

#### Caste

At age 12 the casting ceremony determines caste (roll 1D or choose):
1 = Worker, 2 = Warrior, 3 = Drone, 4 = Technician, 5 = Sport, 6 = Leader.

All casted Droyne immediately gain **+1 to STR, DEX, END, INT, and EDU**. Then apply
caste modifiers:

| Caste | Modifiers |
|---|---|
| Worker | STR+2, END+4 |
| Warrior | STR+3, DEX+1, END+2 |
| Drone | DEX+1, INT+3, EDU+2 |
| Technician | DEX+2, INT+3, EDU+1 |
| Sport | DEX+1, END+1, INT+2, EDU+2 |
| Leader | INT+4, EDU+2 |

All Droyne receive psionic testing (see CRB p.196) upon casting, before their first term.

#### Wings

Roll 1D: 1–3 vestigial, 4–5 small (Flight 0), 6 large (Flight 0). A Traveller may trade
STR/DEX/END points to improve wing size. Flight on worlds of Size 5– (standard) with large
wings; Size 7– in dense atmosphere.

#### Traits

Close Combat Aversion (extra damage from impact weapons; DM-2 unarmed); Droyne Claws
(1D+2, also gripping aid).

#### Skills

New Droyne-only skills: **Flight**, **Ancients Tech**, **Appeal**, **Caste (caste)**,
**Outsider (culture)**, **Prediction**. All Droyne receive all caste-specific skills at 0,
plus one at 1.

**Black Skills:** Carouse, Deception, Gambler, Persuade, Streetwise. Each Black Skill
level penalises advancement and continuation checks by its level.

#### Careers

Six separate career paths (one per caste). Droyne cannot change caste. No rank in the
usual sense. No survival check is automatically career-ending; instead, any Mishap triggers
a Continuation check (2+, DM = Caste skill − caste number). Failure = ejection from the
Oytrip; most Droyne commit Krinaytsyu (ritual suicide) at that point, but a Traveller need
not. No standard mustering-out; start-of-adventure circumstances are narrated.

Droyne Life Events table replaces the standard table (2D+caste number; event on 10+).

Aging from age 28 (after 4th term). Optional Iron Droyne Rule: must roll caste number or
higher on 2D each term or be ejected.

---

## Minor Races

All species that did not independently develop jump drive technology.

---

### Human Minor Races

Branches of Humaniti, or groups of human descent, with their own distinct mechanics.

#### Darrian
*Source: AoCS Vol. 3 (`refs/alien3/04_darrian_travellers.md`); BTC (`refs/btc/17_creating_darrian_travellers.md`)*

- **Characteristics:** STR-1, DEX+1, END-1, INT+1, EDU+1 from standard roll.
- Additional background skill: Science 0.
- **First term mandatory:** must be military service or university.
- **Restricted careers:** no Noble, Rogue, or Scout.
- **Darrian career list:** Agent, Entertainer, Envoy, Guard, Merchant, Militia, Navy, Scholar,
  Special Arm (INT 9+; Psion assignment also requires PSI 9+), Worker, Wanderer.
- Wanderer auto-qualifies; includes Exile assignment with Parole Threshold mechanic.
- **Aging:** first check after 4th term (age 34) with DM = -(terms÷2); less severe than humans.

#### Geonee
*Source: AoCS Vol. 3 (`refs/alien3/10_geonee_travellers.md`)*

- **Characteristics:** STR+2, DEX-1, END+2, SOC-1.
- Extra background skill: Electronics 0, Engineer 0, or Mechanic 0.
- DM-2 Scholar qualification; DM+2 ADRAT qualification.
- **Additional careers:** ADRAT (INT 8+), Geonee Self Defence Army/Navy.
- Hyper-acclimatisation: adapts quickly to new gravity.

#### Happrhani
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Human Minor Race from Rejhappur (Reaver's Deep). Harsh desert environment has produced
a leathery-skinned, tough people known for honour and courage.

- **Characteristics:** END+1.
- All Core careers available. Steppe/desert nomads limited to Barbarian assignment.

#### Iltharans
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Human Minor Race from Drexilthar (Reaver's Deep). Unusually long-lived and militaristic;
once ruled an interstellar empire destroyed by the Imperium in 268.

- **Characteristics:** END+1.
- Longevity: DM+6 to all aging rolls.
- All Core careers available.

#### Jonkeereen
*Source: BTC (`refs/btc/20_creating_jonkeereen_travellers.md`)*

- **Characteristics:** END+1, EDU-1.
- Heat resistance: -2 damage from temperature extremes.
- Otherwise standard Core career access and aging.

#### Sword Worlders
*Source: Sword Worlds (`refs/sword/09_sword_worlds_travellers.md`)*

Humans of Scandinavian/North European cultural heritage in the Spinward Marches. No
characteristic differences from other Humaniti. Mechanically relevant only through the
unique Patrol career.

- **The Patrol:** Qualification INT 7+. Must be 30 or younger to apply. DM+1 if previous
  army or navy term; DM+2 for honours university/academy graduate.
- Three arms: **Security** (END 6+/INT 7+), **Investigative** (INT 7+/EDU 9+),
  **Interstellar** (DEX 7+/INT 8+).
- First term is training (Basic qualification END 9+; Advanced qualification per arm); no
  mustering-out from the training term.
- Otherwise all standard Core careers are accessible.

---

### Terran Uplifts

Species of Terran origin uplifted to sophonce (other than Vargr, who are a Major Race).

#### Caprisaps
*Source: JTAS Vol. 12 (`refs/jtas/12/03_high_guard.md`)*

Nomadic sophonts uplifted from Terran goats by Solomani scientists. Two subspecies
(Alpine and Boar) can interbreed but children are always one subspecies. Common around
the Vilani–Vargr border, working as miners and astrogators.

- **Alpine characteristics:** STR-2, DEX+2.
- **Boar characteristics:** STR-1, DEX+1.
- **Traits:** Headbutt (1D, Melee natural); Heightened Taste (DM+1 Survival); Improved
  Digestion (eat most metals, DM+4 vs ingested poison); Natural Starfarers (may choose
  Astrogation 0 as background skill).
- All Core careers available.
- Caprisap ships must have an Arena (4 tons, MCr0.5) per full 10,000 tons.

#### Chokari
*Source: BTC (`refs/btc/05_jewell.md`)*

Humanoids Ancient-engineered from the same stock as the Foelen Dolphins; share their world
and get along well with them. Adapted for aquatic life but comfortable on land. Strong
psionic tendencies; under Zhodani occupation of Foelen but taking the long view.

- **Characteristics:** END+1, SOC-1; PSI = 2D.
- Psionic training may be taken before the first career term.
- **Traits:** Deep Diver (100m without risk; 10-minute breath hold); Swimmer (6m speed).
- All Core careers available.

#### Foelen Dolphins
*Source: BTC (`refs/btc/05_jewell.md`)*

Dolphins apparently uplifted to full sentience by the Ancients, found on Foelen in the
Jewell subsector of the Spinward Marches (Consulate space). Separated from the
Solomani-uplifted Dolphins (see below) by several hundred thousand years of evolution;
adapted for unusually deep diving. Get along well with the Chokari (also on Foelen).

- **Characteristics:** END+1, SOC-1.
- **Traits:** Deep Diver (300m without risk; 15-minute breath hold); Echolocation (100m,
  works underwater or in darkness); Swimmer (12m speed).
- All Core careers available.

#### Dolphin (Solomani-uplifted)
*Source: AoCS Vol. 3 (`refs/alien3/15_dolphin_travellers.md`)*

Earth dolphins uplifted by Solomani scientists.

- **Characteristics:** STR+4, END+2, SOC-4.
- **Starting age 12.** Aging checks begin at end of 2nd term (age 20).
- DM-1 university; DM+1 Scholar, DM+1 Scout.
- **Restricted careers:** no Drifter, Merchant, Noble; no Broker or Gambler skills.
- Cash from non-Dolphin careers = 10% of listed value.
- **Dolphin careers:** Civilian (Liaison/Nomad auto; Historian-poet EDU 8+), Military (EDU 6+).
- Solomani Dolphins may also enter Home Guard or SolSec Monitor.
- Succour Syndrome: cetacean distress within range triggers INT/EDU check; on failure both
  drop to 0.

#### Orca
*Source: AoCS Vol. 3 (`refs/alien3/21_orca_travellers.md`)*

Uplifted Earth orcas (killer whales).

- **Characteristics:** STR+8, END+4, SOC-4.
- Starting age 18. Aging checks begin at end of 4th term (age 32).
- DM-2 university; DM+1 Military Academy.
- **Restricted careers:** no Drifter, Merchant, Noble; no Broker or Gambler skills.
- Cash from most careers = 10% of listed value.
- **Orca careers:** Philosopher-Elder (SOC 12+; DM+1 per previous term), Spirit Singer
  (automatic). Can also enter Dolphin Military and Dolphin Civilian (except Historian-poet).
- Require 12× normal ship space.

---

### Minor Alien Races

Non-human, non-Terran species. Listed alphabetically.

#### Ael Yael
*Source: JTAS Vol. 3 (`refs/jtas/3/09_alien.md`)*

Winged avian sophonts from Jaeyelya.

- **Characteristics:** STR-1.
- No Noble; cannot join any mercantile organisation. DM-1 all enlistment; DM+2 Scout.
- 90% of all cash mustering-out benefits donated to Planetary Development Fund.
- SOC represents interstellar experience, not social standing.
- Dense atmosphere flight on Size 6- worlds; glide on Size 7-8.

#### Aezorgh
*Source: JTAS Vol. 11 (`refs/jtas/11/10_aezorgh_by_geir_lanesskog.md`)*

Gecko-like sophonts from Vargr/Imperial border regions.

- **All characteristics non-standard:** STR=1D, DEX=2D+3, END=1D+1, INT=2D+2, EDU=1D, SOC=1D.
  DEX max 18, INT max 16.
- In Vargr society, CHA = SOC÷2 (round down).
- DM+4 on all aging checks until age 82 (term 16).
- DM-2 to qualify/graduate from pre-career options.
- Gecko climbing (walls at full speed, ceilings at half speed).

#### Amindii
*Source: JTAS Vol. 9 (`refs/jtas/9/08_amindii.md`)*

Four-armed sophonts from the Regina system.

- **STR = 3D** (not 2D). Activators additionally STR+2, EDU-2; Bearers END+1.
- Three genders (determined by 1D roll).
- **Starting age 14.** Aging begins end of 4th term (age 30).
- First term: Citizen (colonist) or Drifter (barbarian) only if unassimilated; all careers
  from 2nd term onward.
- Perception ability (Recon equivalent, not psionic) once per hour.
- DM+1 psionic Telepathy and Awareness talent checks.

#### Ascondi
*Source: Great Rift Book 1 (`refs/great-rift/book1/06_peoples_of_the_great_rift.md`)*

Communal sophonts with complex life-phase aging from the Great Rift area.

- **Characteristics:** END+1. Caste modifiers applied at casteing (~age 20):
  Hunter: STR+1 END+1 INT-3 EDU-3; Finder: INT+2 DEX+2 STR-2; Hearthkeeper: EDU+2 SOC+2 STR-2.
- **SOC starts at 1** and rises through life phases (not through careers). Increases
  automatically until SOC 9, then by roll each phase.
- **Aging model completely replaces standard:** SOC determines the Decline chance per phase.
  Decline is irreversible — lose 1 point from a physical characteristic per year.
- SOC 11+ (late life, ~age 80–120): STR/DEX/END each -1, INT/EDU each +1D3.

#### Bosaki
*Source: JTAS Vol. 17 (`refs/jtas/17/20_bosaki_by_geir_lanesskog.md`)*

Four-armed pacifist sophonts from Far Frontiers.

- **All characteristics non-standard:** STR=1D+1, DEX=2D+2, END=1D+1, INT=2D+1, EDU=2D,
  SOC fixed at 4. Species maxima: STR 10, others 16.
- **Starting age 24** after mandatory 8-year apprenticeship (Physical or Mental Path).
- No Drifter, Rogue. No infantry or ground assault assignments.
- Within Bosaki society: automatic qualification, no survival checks, SOC+1 per term (max 16).
- **Combat Aversion:** DM-3 on all Melee and Gun Combat checks.
- Aging checks begin after 5th term (age 44); DM+2 unless any characteristic already at 1.

#### Bruhre
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Massive hexapedal omnivore/scavengers from Corve (Daibei sector).

- **Characteristics:** STR=3D (max 18), DEX=1D, END=3D+2 (max 20), SOC=1D.
- **Traits:** Garbage Eaters (DM+1 vs ingested poisons); Intolerant (DM-1 Deception/Diplomat/
  Persuade with non-Bruhre); Large (+1 to ranged attacks against them); No Fine Manipulators;
  Peripheral Vision (DM+1 initiative and Recon).
- Cannot enter Drifter, Entertainer, or Rogue careers.

#### Bwap
*Source: AoCS Vol. 3 (`refs/alien3/25_bwap_travellers.md`)*

Bureaucratic amphibious species within the Third Imperium.

- **Characteristics:** STR-4, END-4.
- **Faster aging:** DM-1 additional on aging checks.
- No Agent career (except law enforcement); no Rogue.
- Auto-qualify Citizen (corporate). DM-2 Marines, DM-1 Army, DM+1 Scout, DM+2 Merchant.
- **Structured Mind:** Admin, Advocate, Broker auto-advance to level 1 on first acquisition.
- Regeneration (limbs regrow over months).
- PSI = 2D-3 minus terms served.

#### Dynchia
*Source: JTAS Vol. 1 (`refs/jtas/1/07_alien.md`)*

Humanoid traders from the trailing Old Expanses.

- **Characteristics:** STR=1D+3, DEX+1, EDU+1.
- DM-2 enlistment/commission/promotion in Army, Navy, Marines, and large merchant
  organisations when outside the Dynchia Comitia.
- Mature Technology trait: can modify TL12 or lower devices 10% better in one area.

#### Githiaskio
*Source: JTAS Vol. 2 (`refs/jtas/2/05_alien.md`)*

Tentacled aquatic sophonts from Antares Sector.

- Characteristics rolled normally (no modifiers listed).
- DM+3 all movement/agility in zero-g and underwater; up to three melee attacks per round
  in water/zero-g.
- Cannot operate in gravity without a sealed support suit (Cr300,000); standard gravity
  causes internal injuries.
- Custom equipment +10–60%.

#### Girug'kagh
*Source: JTAS Vol. 1 (`refs/jtas/1/19_alien.md`)*

Servitor species of the K'kree. The only form encountered by outsiders is the Translator,
a permanent hereditary servant of K'kree masters.

- **Characteristics:** STR=1D+2, END=1D+2, DEX=1D+7.
- No rank structure, no mustering-out benefits; serve for life.
- Kr'rrir trait: DM-6 on any check that conflicts with K'kree loyalty.
- As Travellers, Girug'kagh operate only as translators in K'kree service. Independent
  career play would require significant referee interpretation.

#### Gmina
*Source: Spinward Extents (`refs/spinext/11_aliens_of_the_beyond.md`)*

- **Characteristics:** STR=2D+4, EDU=1D, SOC=2 (fixed), DEX-1. Four arms.
- Drifter (barbarian) only. Infrared vision.

#### Gurvin
*Source: AoCS Vol. 4 (`refs/alien4/40_gurvin_travellers.md`)*

Six-limbed species from the Hive Federation.

- **Female characteristics:** INT+1, EDU+1.
- **Male characteristics:** STR-1, DEX+1. **INT and EDU rolled on 1D+1** (not 2D).
- Starting age 16.
- Female Gurvin rarely attend Military Academy.
- Arm-Antlers (males only): seasonal; Melee (natural) 1D+2.
- Extra Limbs: intermediate pair usable as arms or legs; move 8m as legs.

#### Halkans
*Source: JTAS Vol. 8 (`refs/jtas/8/10_halkans.md`)*

Gentle humanoids from the Florian League.

- **Characteristics:** END+1, EDU-1.
- Pacifism: any Melee, Gun Combat, or Heavy Weapons skill during creation should be
  rerolled (second combat skill is accepted).
- Reduced light vision: DM+1 perception except in total darkness; DM-1 bright light.

#### Hhkar
*Source: JTAS Vol. 12 (`refs/jtas/12/11_hhkar.md`)*

Reptilian serial hermaphrodites from the Julian Protectorate.

- **Characteristics:** STR+3, END+3 (max STR/END 18). Starting age 22; aging begins after
  5th term.
- **Serial hermaphroditism:** born male; can transform male→female→male. Each transformation
  resets STR/DEX/END to initial rolled values. INT/EDU/SOC always retained. Skills from the
  opposite gender drop to 0 after transformation.
- Only males are Travellers (females remain on homeworlds).
- Mental States (meditation-triggered): Learning, Combat, Labourer, Oration.
- Will not accept psionic testing.

#### Hlanssai
*Source: JTAS Vol. 4 (`refs/jtas/4/09_alien.md`)*

Slender, philosophical sophonts found throughout Charted Space.

- **Characteristics:** STR-2, DEX+2, EDU-2. SOC=1D+4 in Hlanssai society; fixed at 5 in
  alien societies.
- **Two philosophical paths:** N'tarronth (action-oriented) or N'tarronchii'a (comprehension-
  oriented). Within Hlanssai society, path bypasses the standard career system entirely: no
  survival/commission/promotion/re-enlistment checks; 1 skill per term.
- DM-6 military career enlistment/advancement; DM-3 major corporate careers.

#### Ithklur
*Source: JTAS Vol. 7 (`refs/jtas/7/07_ithklur.md`)*

Aggressive humanoids, client species of the Hive Federation.

- **SOC replaced by RES (Resolve) = 1D+1. EDU = 1D+1** (not 2D).
- **Fourfold Way path system:** Facilitator (INT 5+), Guardian (STR 5+), Explorer (END 6+),
  Seeker (INT 6+). Characters choose a path (Holists stay on one; Radialists sample all four).
  Path replaces career qualification.
- RES gains +1 per successful advancement term.
- Claws (1D+2); Club tail (2D, DM-2); infrared sense DM+1 Recon/Survival.
- Extended aging resistance: DM+4 until age 82 (term 16).

#### J'aadje
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Small humanoids with unusual arm articulation and two opposable thumbs, from Gaajpadje
(Reaver's Deep). Peaceful and artistic; recently discovered interstellar travel.

- **Characteristics:** STR-2, DEX+2.
- No special traits listed.
- All Core careers available.

#### Kemlae
*Source: Spinward Extents (`refs/spinext/11_aliens_of_the_beyond.md`)*

- **Characteristics:** DEX+1, END+1, EDU-1, SOC-1. **Starting age 8.**
- **Kuftu transformation:** after term 7, roll each subsequent term or die/transform
  (Noble career: annual 11+ roll or Kuftu). No aging until term 7.

#### Krotan
*Source: JTAS Vol. 15 (`refs/jtas/15/01_the_krotan.md`)*

Sessile carapace sophonts between the Hive Federation and Two Thousand Worlds.

- **Characteristics:** END=3D, DEX-2. SOC=2D represents time in adult phase (not social
  standing). Adult phase length = INT×4 years.
- **Careers:** Merchant and Citizen only. No survival checks required.
- No pre-career education. First-term skill via Pre-Sessile Learning table.
- Movement 3m only. Natural armor Protection +10. Require 5× normal passenger space.

#### Ktiauao
*Source: Spinward Extents (`refs/spinext/11_aliens_of_the_beyond.md`)*

- **Characteristics:** STR+1, DEX+2. **SOC replaced by TER** (Aslan-style Territorial
  Imperative).
- Uses Aslan career list. Three genders; neuter fills female role.
- Aging: gendered after 7 terms DM+2 (STR/DEX/END only); neuter after 10 terms.

#### Lhshana
*Source: JTAS Vol. 16 (`refs/jtas/16/05_the_lhshana_by_randy_dorman.md`)*

Trilaterally symmetrical sophonts from Reaver's Deep.

- **Characteristics:** DEX+1, INT+1, SOC-2.
- All Core careers available. Small (-1): ranged attacks vs them DM-1.

#### Mal'Gnar
*Source: Spinward Extents (`refs/spinext/11_aliens_of_the_beyond.md`)*

- **Characteristics:** EDU=1D+1. Cannot speak Galanglic.
- Drifter (barbarian) only.

#### Mewey
*Source: JTAS Vol. 13 (`refs/jtas/13/02_the_star_angel_ambulance_pinnace.md`)*

Humanoid sophonts possibly sharing ancestry with both Aslan and Humaniti; in the Five
Sisters subsector. Diplomatic, empathetic, recently space-faring (jump drive acquired
from Aslan corporation). Their Mewey Empire is built on cooperative city-states.

- **Characteristics:** STR-2, INT+1, EDU+1.
- **Traits:** Heightened Senses (DM+1 Recon and Survival); Empathetic (DM+1 Diplomat,
  DM-1 Deception).
- Most Core careers available. No Drifter (use Citizen instead — represents Empire service
  rather than wandering). Navy requires INT 8+ to qualify.

#### Nenlat
*Source: JTAS Vol. 10 (`refs/jtas/10/08_professor_dania_jereua.md`)*

Trilateral amphibious sophonts from Deneb (Usani subsector). Thought to have been
engineered by the Ancients. Approximately half are assimilated into Imperial society;
the rest maintain traditional village life. Three genders (Activator, Bearer, Egg Layer).

- **Assimilated:** STR+1, EDU-2. Plus gender: Activator DEX+1; Bearer STR+1; Egg Layer END+1.
- **Traditional:** STR+1, EDU=1D; auto-gain Athletics 0 and Survival 0. Same gender mods.
- **Starting age 14.**
- **Traits:** Amphibious (indefinite aquatic function); Natural Weapon (Stinger, 1D AP2 +
  neurotoxin vs Denebian life); Ultraviolet Vision (DM-1 at night/red light); Very Thin
  Atmosphere (can breathe Very Thin unaided; Dense atmosphere causes oxygen euphoria
  without filter suit); Leg Armour (Protection +4 vs leg attacks); Nenlat Hands (DM-1
  with non-Nenlat equipment).
- All Core careers. Cannot attend university or military academies.
- Require specialised filter suit in tainted atmospheres.

#### Ormine
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Slow-metabolising bipedal pseudo-reptiles from Akhlare (Dark Nebula). Extremely long-lived,
deliberate, and patient. Their Gerontocracy of Ormine is a stable polity with a long
cooperative history with humanity.

- **Characteristics:** DEX-2, END+2.
- **Traits:** Aquatic (DM+2 swimming; indefinite underwater breathing; safe to 30m); Armour
  (+1); Slow and Steady (**28-year career terms**, start first term at age 30, aging begins
  at age 254); Slow Metabolism (DM-2 initiative).
- All Core careers available.

#### Suerrat
*Source: AoCS Vol. 4 (`refs/alien4/12_suerrat_travellers.md`)*

Mammalian sophonts from the Trojan Reach / Hive Federation sphere.

- **Characteristics:** STR+1, DEX+2, SOC-1.
- Cold resistance, radiation resistance (ignore first 50 rads), poor vision in bright light.
- All Core careers plus Regional Criminal Police Organisation and Regional Security Force.
- Must include Athletics 0 in background skills.

#### Tezcat
*Source: AoCS Vol. 4 (`refs/alien4/55_tezcat_travellers.md`)*

Chameleon-like sophonts.

- **Characteristics:** DEX+1, END-1.
- No Noble career (democratic society).
- Background skills must start with Gun Combat 0, Melee 0, and Stealth 0.
- Chameleon: DM+2 Stealth; DM-2 Deception vs other Tezcat.
- Natural weapons: claws 1D+1; venomous bite 1D+2.
- Unique careers: Soulhunter (military), Shaper (priest).

#### Tlinzha
*Source: Sector Construction Guide (`refs/sector/08_creating_tlinzha_travellers.md`)*

Multi-armed xenophobic sophonts from Foreven Sector.

- **Characteristics:** END=3D (not 2D). STR+1.
- **Starting age 8.** 8-year career terms.
- All Core careers except Psion. Psionic events rerolled.
- **Psionic blank:** cannot be psionically detected or read. No PSI characteristic.
- Two sets of arms: two non-movement actions per round without penalty.
- Natural weapons: beak (1D+1) and palm nails (1D+2) from each end.

#### Tlyetrai
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Gentle, cooperative three-sexed bipeds from Hoa (Reaver's Deep). Long peaceful; only
recently encountered interstellar travel (via Aslan contact around -1000).

- **Characteristics:** STR-2, DEX+1, INT+1.
- No special traits listed.
- Most Core careers. Army, Navy, Marine, and Rogue not available unless the Traveller
  has emigrated from their homeworld.

#### Ulane
*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Small six-limbed arboreal sophonts from Ul (Dark Nebula, Union of Harmony). Originally
contacted by Aslan; adopted and adapted Aslan cultural forms enthusiastically.

- **Characteristics:** DEX+2. **STR and END each rolled on 1D+1.**
- **Traits:** Fast Metabolism (DM+1 initiative); Multi-limbed (use up to two items
  simultaneously; two action sets per round; but DM-2 with equipment not made for Ulane);
  Small (-1: ranged attacks vs them DM-1).

#### Vegan
*Source: Solomani Front (`refs/sol/06_the_vegan_autonomous_district.md`)*

Tall (~2.2m) bipeds from Muan Gwi in the Vega subsector. The Tyui (self-name) are an
ancient civilisation (~10,000 years) with 200+ year lifespans. Society is organised around
*tuhuir* (philosophical/cultural communities). They became famous as Terra's first major
interstellar allies during the Interstellar Wars. Now govern the Vegan Autonomous District
within the Third Imperium.

- **Characteristics:** EDU+2, SOC-2.
- **First career must be Drifter.** This represents the *irrishtyoshun* (period of search
  before choosing a *tuhuir*) that all Vegans undergo at maturity (~age 50).
- **Traits:** Eye Membrane (IR vision, equivalent to IR goggles; dust/grit protection);
  Heat Tolerance (ignore END points of heat damage per hour); High Gravity Intolerance
  (double all high-gravity penalties; can never acclimatise).

#### Virushi
*Source: JTAS Vol. 5 (`refs/jtas/5/07_alien.md`); also The Deep Dark (`refs/deepdark/03_aliens_of_the_buffer.md`) — same mechanics, adds explicit stateroom sizes*

Enormous pacifist herbivores from Reaver's Deep.

- **Characteristics:** STR=1D+10 (max 20), END=1D+10 (max 20), DEX=2D+2, SOC=2D-2.
- **SOC career increases are applied to EDU instead.**
- No Army, Navy, or Marines careers. DM+1 Scout enlistment.
- Weapons Aversion: first combat skill always acquired at level 0.
- Natural armor Protection +4. Two natural weapon attacks (tail/stomp) per round, 2D each.
- Require 8-ton staterooms.

#### Yn-tsai
*Source: The Deep Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Bipedal, fur-covered sophonts transplanted to Tsanesi (Reaver's Deep) by the Saie; descended from carnivores but culturally pacifistic.

- **Characteristics:** STR-2, INT+2.
- All Core careers available.
- **Low Pressure:** DM-1 on checks in high-pressure atmospheres (types 8, 9, 13).

#### Za'tachk
*Source: AoCS Vol. 4 (`refs/alien4/30_za_tachk_travellers.md`)*

Three-sexed arboreal sophonts.

- **Characteristics:** STR+1 all sexes. Matriarchs: INT+1, EDU+1, BOL-1; Scouts: INT-1,
  EDU-1, BOL+1.
- **New characteristic: BOL (Boldness) = 1D+1.** BOL 10+ = considered insane.
- **Starting age:** Scouts and Homesteaders at 10; Matriarchs at 15.
- Career access is sex-dependent: Matriarchs (Citizen, Drifter, Merchant, Noble, Rogue,
  Scholar); Homesteaders (Citizen, Drifter, Entertainer, Merchant, Rogue, Scholar); Scouts
  (Agent, Citizen-worker/colonist, Drifter, Rogue, Scout, Za'tachk military).
- Coward trait: BOL check when threatened within 50m; failure = retreat or catatonia.
- Brachiator (DM+2 climbing); infrared vision (DM+2 Recon/Survival in dark; DM-2 bright light).

---

## Species Without Published MgT2 Creation Rules

These species appear in refs but have no character-creation mechanics published:

- **Hloans** — mysterious aquatic species from Hloa (Dark Nebula); too little is known
  for creation rules to exist.
- **Ayansh'i** — human Minor Race from Ghost (Reaver's Deep); the source states they are
  "not suitable as Travellers" due to insularity. No creation rules published.
- **Weregre** — human characteristics; no mechanical differences from Core creation.
- **Ewurmer** (Spinext) — explicitly marked as not suitable in source.
- **Sred'Ni** (Spinext) — explicitly marked as not suitable in source.
- **Aniyun** (Spinext) — has creation rules (STR=1D, EDU-2; Citizen/Drifter only; listed
  in table above).
