# Sophonts — Playable Species Reference

This document summarises every species in `refs/` that has published character-creation
rules for Mongoose Traveller 2nd Edition, with emphasis on what matters for Ceres
implementation: characteristic generation differences, characteristic replacements,
career restrictions, and special creation-time mechanics.

Current Ceres status: only `Humaniti` and `Vilani` are defined in
`src/ceres/character/domain/sophont/`.

---

## Quick-reference table

| Sophont                     | Category | Code | Location          | Source            | Characteristic changes                                                                      | Special                                                                                                            |
| --------------------------- | -------- | ---- | ----------------- | ----------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Ael Yael                    | Alien    | —    | —                 | JTAS 3            | STR-1                                                                                       | No Noble; 90% cash donated; DM-2 enlistment                                                                        |
| Aezorgh                     | Alien    | Aezo | Wind              | JTAS 11           | STR=1D, DEX=2D+3, END=1D+1, INT=2D+2, EDU=1D, SOC=1D                                        | DM+4 aging until term 16                                                                                           |
| Akeed                       | Alien    | Akee | Gate              | Trail             | STR-2, END-2, INT+1                                                                         | Akeed Debate DM+2; Akeed Friendship bond; slug-like; careers not listed                                            |
| Amindii                     | Alien    | —    | —                 | JTAS 9            | STR=3D (+2 Activator; +END 1 Bearer)                                                        | Three genders; age 14 start; Perception ability                                                                    |
| Aniyun                      | Alien    | —    | —                 | Spinext           | STR=1D, EDU-2                                                                               | Citizen/Drifter only; natural flight                                                                               |
| Ape                         | Uplift   | UApe | Imperial/Solomani | Sol               | STR+1, END+1, SOC-1                                                                         | Chimp: Small (-1); Gorilla: Athletics(str) 2; Heightened Senses; all Core careers                                  |
| Aquamorph                   | Human    | Aqua | Alph              | Sol               | STR halved when out of water                                                                | Amphibious; gill/lung; indefinite underwater breathing; all Core careers                                           |
| Ascondi                     | Alien    | —    | —                 | Great Rift 1      | END+1; caste mods at age ~20                                                                | Caste replaces background; SOC starts at 1                                                                         |
| Aslan (Darrian)             | Alien    | Asla | major             | AoCS 3            | STR+1, DEX+1, EDU+1                                                                         | Any Darrian career; gender preferences softened; Roget Aslan may also use AoCS 1 options                           |
| Aslan (Hierate)             | Major    | Asla | major             | AoCS 1            | (m) STR+2 DEX-2 END+1; SOC → TER; (f) STR+1 DEX-1 END+2                                     | Rite of Passage; Clan Shares; gender-locked assignments                                                            |
| Aslan (Humaniti)            | Major    | Asla | major             | Core              | STR+2, DEX-2                                                                                | Core careers; Dewclaw (1D+2); Heightened Senses                                                                    |
| Bosaki                      | Alien    | —    | —                 | JTAS 17           | STR=1D+1, DEX=2D+2, END=1D+1, INT=2D+1, EDU=2D, SOC=4                                       | Age 24 start; Combat Aversion                                                                                      |
| Bruhre                      | Alien    | Bruh | Daib/Reav         | Deepdark          | STR=3D(max 18), DEX=1D, END=3D+2(max 20), SOC=1D                                            | No Drifter/Entertainer/Rogue                                                                                       |
| Bwap                        | Alien    | Bwap | Imperial/Vilani   | AoCS 3            | STR-4 END-4                                                                                 | Faster aging; no Rogue; Structured Mind trait                                                                      |
| Caprisaps (Alpine)          | Uplift   | —    | —                 | JTAS 12           | STR-2, DEX+2                                                                                | Goat uplift; Improved Digestion                                                                                    |
| Caprisaps (Boar)            | Uplift   | —    | —                 | JTAS 12           | STR-1, DEX+1                                                                                | Goat uplift; Improved Digestion                                                                                    |
| Capry                       | Alien    | —    | —                 | Trail             | Female: STR-3 DEX+2 END-2 INT+1; Big Male: STR-1 END+1; Small Male: STR-4 DEX+3 END-3 EDU+2 | 3 sexes; Liberating Fatalism; Third Hand; endangered species                                                       |
| Chokari                     | Uplift   | —    | —                 | BTC               | END+1, SOC-1; new PSI (2D)                                                                  | Ancient uplift (Foelen); psionic training before career; Deep Diver (100m); Swimmer (6m)                           |
| Crenduthaar                 | Alien    | —    | —                 | BTC               | STR=3D, END=3D, DEX=1D                                                                      | Army/Citizen/Drifter/Marine/Rogue; Armour +3; IR Vision; Slasher 2D; dark phobia; kill Vargr on sight              |
| Darrian                     | Human    | Dary | Spin              | AoCS 3 / BTC      | STR-1 DEX+1 END-1 INT+1 EDU+1                                                               | Restricted career list; first term forced                                                                          |
| Dolphin (Foelen)            | Uplift   | Dolp | Imperial/Solomani | BTC               | END+1, SOC-1                                                                                | Ancient uplift near Foelen; all Core careers                                                                       |
| Dolphin (Solomani)          | Uplift   | Dolp | Imperial/Solomani | AoCS 3            | STR+4 END+2 SOC-4                                                                           | Solomani uplift; age 12 start; restricted careers                                                                  |
| Droashav                    | Alien    | —    | —                 | Trail             | STR+2, DEX-1, END+3, INT-1                                                                  | Natural Defences +1 + claws 1D+2; six-limbed pseudoreptilians; careers not listed                                  |
| Droyne                      | Major    | Droy | major             | AoCS 2            | STR/DEX/END/INT/EDU=1D+1; PSI=2D; caste mods; SOC → PSI                                     | Caste-based careers; no standard career flow                                                                       |
| Dynchia                     | Alien    | Dync | Leon              | JTAS 1            | STR=1D+3, DEX+1, EDU+1                                                                      | DM-2 enlistment outside Comitia                                                                                    |
| Ebokin                      | Alien    | —    | —                 | BTC               | DEX-2, END+3                                                                                | Methane breather; UV Vision; Armour +3; limited career list                                                        |
| Eslyat                      | Alien    | Esly | Beyo/Vang         | Spinext           | Three sub-races (Selyin/Chutin/Magsin) by SOC; males STR+1                                  | Amphibious; Heightened Hearing; caste-limited careers                                                              |
| Faar                        | Alien    | —    | —                 | Trail             | STR+1, END+1, DEX-1                                                                         | Closed Book (DM-2 reading Faar); Homesickness (END check every 2D days off-world)                                  |
| Freni                       | Alien    | —    | —                 | Spinext           | 6 subspecies, various; SOC=EDU                                                              | Flexible Digits; Reputation as Cook; Steward 1/Profession(freeloading)1/Survival 0 start                           |
| Geonee                      | Human    | Geon | Mass              | AoCS 3            | STR+2 DEX-1 END+2 SOC-1                                                                     | Extra background skill                                                                                             |
| Ghenani                     | Human    | —    | —                 | Spinext           | STR+2, DEX-2                                                                                | STR max 17; DM-1 aging; no cyber/psionics; career-restricted until emigrated                                       |
| Girug'kagh                  | Alien    | —    | —                 | JTAS 1            | STR=1D+2, END=1D+2, DEX=1D+7                                                                | Translator-only; serve K'kree for life                                                                             |
| Githiaskio                  | Alien    | —    | —                 | JTAS 2            | —                                                                                           | Zero-g/aquatic specialist; gravity injures without suit                                                            |
| Gl'lu                       | Alien    | —    | —                 | BTC               | END-1, DEX+1, EDU-2                                                                         | Ammonia breather; IR Vision; Heightened Senses; all Core careers; tiny staterooms (8 per cabin)                    |
| Gmina                       | Alien    | —    | —                 | Spinext           | STR=2D+4, EDU=1D, SOC=2 (fixed), DEX-1                                                      | Drifter only; four arms                                                                                            |
| Gurungan                    | Alien    | Guru | Solo              | Sol               | DEX+2                                                                                       | Fully aquatic; Sonar 120m; Bite 1D; Deep Diver 1000m; Swimmer 8m; all Core careers                                 |
| Gurvin                      | Alien    | Gurv | Hiver space       | AoCS 4            | Females INT+1 EDU+1; Males STR-1 DEX+1                                                      | Male INT/EDU=1D+1; age 16 start                                                                                    |
| Halkans                     | Alien    | —    | —                 | JTAS 8            | END+1, EDU-1                                                                                | Pacifism; reroll combat skills during creation                                                                     |
| Happrhani                   | Human    | —    | —                 | Deepdark          | END+1                                                                                       | Barbarian only if steppe/desert nomad                                                                              |
| Hhkar                       | Alien    | —    | —                 | JTAS 12           | STR+3 END+3; reset per gender transformation                                                | Serial hermaphroditism reverses aging                                                                              |
| Hiver                       | Major    | Hive | Hiver space       | AoCS 2            | STR-2; SOC → RES                                                                            | RES=1D+6; no survival checks; aging from 38                                                                        |
| Hlanssai                    | Alien    | —    | —                 | JTAS 4            | STR-2 DEX+2 EDU-2, SOC=1D+4 / fixed 5                                                       | Bypasses standard career system entirely                                                                           |
| Humaniti                    | Human    | Huma | Imperial/Solomani | Core              | —                                                                                           | Catch-all for standard humans not fitting a specific minor race                                                    |
| Iltharans                   | Human    | —    | —                 | Deepdark          | END+1                                                                                       | Longevity +6 aging                                                                                                 |
| Ithklur                     | Alien    | Ithk | Hiver space       | JTAS 7            | EDU-1; SOC → RES                                                                            | EDU=1D+1, RES=1D+1; Fourfold Way path system                                                                       |
| J'aadje                     | Alien    | —    | —                 | Deepdark          | STR-2, DEX+2                                                                                | All careers                                                                                                        |
| Jonkeereen                  | Human    | Jonk | Dene/Spin         | BTC / Trail       | BTC: END+1, EDU-1; Trail: END+2 only                                                        | Heat resistance; Desert Survival DM+3; ⚠ discrepancy between sources                                               |
| K'kree                      | Major    | K'kr | K'kree space      | AoCS 1            | STR+6, INT+2, EDU+2 (patriarch)                                                             | Creates whole household; Patriarchy skill; Claustrophobic; Gregarious                                              |
| Katangan                    | Human    | —    | —                 | Spinext           | STR+1, DEX-1, END+1                                                                         | Fully human; heavy worlder; draft first term; DM-1 aging; Katangan Culture modifier                                |
| Kemlae                      | Alien    | —    | —                 | Spinext           | DEX+1, END+1, EDU-1, SOC-1                                                                  | Age 8 start; Kuftu transformation/death after term 7                                                               |
| Kirissukyoya                | Alien    | —    | —                 | BTC               | STR-1                                                                                       | All Core careers; Eidetic Sense (hearing); Claws 1D; Mechanic 1 innate                                             |
| Krotan                      | Alien    | —    | —                 | JTAS 15           | END=3D, DEX-2, SOC=2D (age indicator)                                                       | Merchant/Citizen only; no survival checks                                                                          |
| Ktiauao                     | Alien    | —    | —                 | Spinext           | STR+1, DEX+2; SOC → TER (Aslan-style)                                                       | Uses Aslan careers; three genders                                                                                  |
| Ladybug                     | Alien    | —    | —                 | Sol               | STR/END/SOC=1D+2; INT/EDU=2D3; DEX=2D+3                                                     | Gentle Soul DM-2 combat/confrontation; Beautiful DM+2 help; DM-2 military careers                                  |
| Lhshana                     | Alien    | —    | —                 | JTAS 16           | DEX+1, INT+1, SOC-2                                                                         | Standard careers; trilateral physiology                                                                            |
| Llellewyloly                | Alien    | Llel | Spin              | BTC               | STR=2D3, END=2D3                                                                            | Alien Digits DM-2 non-adapted devices; Atmosphere (thin); careers not listed in source                             |
| Lurent                      | Alien    | —    | —                 | BTC               | STR=2D+4, END=2D+4                                                                          | Drifter/Merchant/Noble/Rogue/Scout/Scholar; Tentacle Bash 2D; Wanderlust compulsion cycles                         |
| Luriani                     | Human    | Luri | Forn/Ley          | Trail             | DEX+1, END+1, SOC-2                                                                         | Aquatic Adaptation (genetically Luriani); Histrionics; Ancient-modified humans                                     |
| Mal'Gnar                    | Alien    | Mal' | Beyo              | Spinext           | EDU=1D+1                                                                                    | Drifter only; cannot speak Galanglic                                                                               |
| Martian                     | Alien    | —    | —                 | BTC               | STR-1, END-1, DEX+1; EDU=1D (max 7)                                                         | Most Core careers; Adaptability; immune to telepathy                                                               |
| Mewey                       | Alien    | —    | —                 | JTAS 13           | STR-2, INT+1, EDU+1                                                                         | Heightened Senses; Empathetic; limited Navy                                                                        |
| Murian                      | Alien    | Muri | Vang              | Spinext           | STR+1, DEX-2, END+2; SOC=2D3+4                                                              | All Core; Armour +1; Claw 1D+2; Short Limbs 4m speed; IR vision                                                    |
| Nenlat                      | Alien    | —    | —                 | JTAS 10           | STR+1, EDU-2 (assim.); STR+1, EDU=1D (trad.); gender mods                                   | Amphibious; age 14 start; trilateral                                                                               |
| Oo-ne-beto-pon-tee          | Alien    | —    | —                 | 3i                | STR=D3, END=D3, SOC=D3; DEX=1D+4; INT=2D-1; EDU=2D                                          | (Whistler) neuter sex recommended; Sticky Feet; Stealth 2 innate; High-freq Communication                          |
| Orca                        | Uplift   | Orca | Imperial/Solomani | AoCS 3            | STR+8 END+4 SOC-4                                                                           | Solomani uplift; 12× ship space; restricted careers                                                                |
| Ormine                      | Alien    | Ormi | Dark              | Deepdark          | DEX-2, END+2                                                                                | 28-year terms; start at 30; aging at 254                                                                           |
| Rammak                      | Alien    | Ramm | Krus              | Rimexp            | DEX=1D+8                                                                                    | All-round Perception; Specialised Limbs (DM+2 climbing, DM-2 strength); careers not listed                         |
| Resavolk                    | Alien    | —    | —                 | Spinext           | SOC=D3+5                                                                                    | Drifter (barbarian) first term, then any except Noble unless SOC 10+; no exceptional traits                        |
| Saurus                      | Alien    | —    | —                 | BTC               | STR+2, END+2; INT=2D3; EDU=1D                                                               | Citizen (worker)/Drifter only; Armour +2                                                                           |
| Segani                      | Alien    | —    | —                 | BTC               | END=1D+2 (max 10); all others 2D                                                            | Army/Citizen/Entertainer/Rogue/Scholar; jump travel causes madness                                                 |
| Selenite                    | Human    | Sele | Alph              | Sol               | DEX+2; STR=2D3+1; END=1D+1                                                                  | Low-G adapted humans; Great Indoors (uneasy outdoors); Low-G DM+2; all Core careers                                |
| Shi'awei                    | Alien    | —    | —                 | BTC               | STR=3D, END=3D, DEX=1D; males also STR-1 END+1                                              | Drifter/Entertainer/Noble/Rogue; aquatic; Echolocation (30m); Grippers 2D                                          |
| Solomani                    | Major    | Huma | Imperial/Solomani | AoCS 2            | —                                                                                           | Race roll; party patronage; SolSec monitor                                                                         |
| Souggvuez                   | Alien    | —    | —                 | BTC               | DEX+1, INT-1, EDU+1; caste mods                                                             | All Core careers; Armour +1; Bite 1D+2; four gender castes                                                         |
| Ssienjhiovla                | Alien    | —    | —                 | 3i                | STR-2, DEX+1                                                                                | Carapace +6; Composite Imaging (olfactory); Non-verbal Communication 5km; Scout/Navy preferred                     |
| Suerrat                     | Alien    | Suer | Ilel              | AoCS 4            | STR+1 DEX+2 SOC-1                                                                           | Cold/radiation resistance                                                                                          |
| Sword Worlders              | Human    | Huma | Imperial/Solomani | Sword             | —                                                                                           | Patrol career (max age 30 to join)                                                                                 |
| Sydites                     | Human    | Sydi | Ley               | Trail             | STR+2, END+2, DEX-2, INT-3, EDU-3                                                           | Resilient +1; Plodding Along (DM-4 Leadership/Tactics, DM+4 morale); 4-armed                                       |
| Sylean                      | Human    | Syle | Core              | 3i                | STR-1, EDU+1                                                                                | All Core; Cooperation DM+2 Admin/Diplomat/Streetwise on Sylean worlds; DM+1 cash benefits                          |
| Teakhea                     | Alien    | —    | —                 | Spinext           | STR+1, DEX-1, END+1, SOC-2                                                                  | Aslan careers (exc. Ceremonial/Envoy/Space Officer); Amphibious; Large +2; Shell +3; gender-changing career system |
| Tezcat                      | Alien    | —    | —                 | AoCS 4            | DEX+1 END-1                                                                                 | No Noble; mandatory combat background skills                                                                       |
| Thonane                     | Alien    | —    | —                 | Spinext           | STR=1D, DEX=3D, END=2D, INT=2D, EDU=D3, SOC=D3                                              | Drifter (barbarian) only; Flyer; Hunter innate skills                                                              |
| Tlinzha                     | Alien    | —    | —                 | Sector 8          | END=3D                                                                                      | 8-year terms; age 8 start; no psionics                                                                             |
| Tlyetrai                    | Alien    | Tlye | Reav              | Deepdark          | STR-2, DEX+1, INT+1                                                                         | No Army/Navy/Marine/Rogue unless emigrated                                                                         |
| Ulane                       | Alien    | Ulan | Dark              | Deepdark          | DEX+2; STR/END=1D+1                                                                         | Fast Metabolism; Multi-limbed; Small (-1)                                                                          |
| Ursa                        | Uplift   | Ursa | Forn/Ley          | Trail             | STR+4, END+2                                                                                | Uplifted bears; Claws & Teeth 1D+3; Sore Head (DM-2 social with humans)                                            |
| Vargr (Extents)             | Major    | Varg | Vargr space       | AoCS 1            | STR-2, DEX+1, END-1; SOC → CHA (1D+2)                                                       | Vargr careers; CHA gain/loss mechanic; Bite (1D+1); Heightened Senses                                              |
| Vargr (Humaniti)            | Major    | Varg | Imperial/Solomani | Core              | STR-1, DEX+1, END-1                                                                         | Core careers; Bite (1D+1); Heightened Senses (DM-1 sight in dark)                                                  |
| Vegan                       | Alien    | Vega | Solo              | Sol/AoCS          | EDU+2, SOC-2                                                                                | First career must be Drifter; 200+ year lifespan                                                                   |
| Vilani                      | Major    | Huma | Imperial/Solomani | Core              | —                                                                                           | No mechanical differences                                                                                          |
| Virushi                     | Alien    | —    | —                 | JTAS 5 / Deepdark | STR=1D+10, END=1D+10, DEX+2, SOC-2                                                          | SOC career gains → EDU; no Army/Navy/Marines; 8-ton staterooms                                                     |
| Wanderer (Wandering People) | Alien    | —    | —                 | Trail             | DEX+2, STR-1, END-1                                                                         | Carapace +1; Weird Movement; insectoid                                                                             |
| Yafizethe                   | Alien    | —    | —                 | BTC               | STR=1D, END=1D, DEX=3D, INT+1                                                               | Careers not listed in source; Enhanced Vision (EM fields); Small (-1)                                              |
| Yn-tsai                     | Alien    | —    | —                 | Deepdark          | STR-2, INT+2                                                                                | All Core careers; Low Pressure trait                                                                               |
| Za'tachk                    | Alien    | Za't | Wren              | AoCS 4            | STR+1; Matriarchs INT+1 EDU+1 BOL-1; Scouts INT-1 EDU-1 BOL+1; new BOL (1D+1)               | Three sexes; age 10/15 start; Coward trait                                                                         |
| Zhdianshe                   | Alien    | —    | —                 | Spinext           | STR=1 (fixed), DEX=2D+2; new PSI=2D (min 2); SOC=PSI                                        | All Core + Psion; no aging until term 8; Echolocation; Flyer; Telepathy 2 + Clairvoyance 1 innate                  |
| Zhodani                     | Major    | Zhod | Zhodani space     | AoCS 1 / BTC      | EDU min 8 if SOC 10+; new PSI (rolled first)                                                | Social class tiers gate careers                                                                                    |

---

## Major Sophonts

The eight species that independently discovered jump drive. They are the dominant political
and cultural powers of Charted Space.

### Vilani

*Source: Core rules default (`refs/core/02_traveller_creation.md`)*

Standard human characteristics and career access. Same as `Humaniti` but indicating a
Vilani cultural context. The cultural traits (conservative, specialist-focused) are 
roleplaying flavour rather than mechanical rules.

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

### Vargr (Extents)

*Source: AoCS Vol. 1 (`refs/alien1/12_vargr_travellers.md`)*

Uplifted wolves. Genetically engineered by the Ancients from Earth canines. A Major Race
by virtue of their independent development of jump drive. These rules cover Vargr born and
raised in the Vargr Extents.

- **SOC replaced by CHA (Charisma).** CHA starts at 1D+2. When a SOC check is required in
  a non-Vargr context, increase difficulty one step and use CHA.
- CHA changes during play via a 2D+CHA DM vs current CHA check (Ceres: this is a
  career-term mechanic, not just mid-campaign).
- **Additional careers:** Emissary, Corsair, Scientist, Psion.
- Pack Events table added to Life Events.
- **Ship benefits:** Corsair career can muster out a Ruguelka-class ship (25% mortgage).

### Vargr (Humaniti)

*Source: Core (`refs/core/02_traveller_creation.md`)*

Vargr who have grown up in human space use the Core rules. Characteristic mods and traits
are biologically the same species, but STR modifier is -1 (not -2 as for Extents Vargr),
SOC is retained, and all Core careers are available.

- **Traits:** Bite (1D+1, Melee natural); Heightened Senses (DM+1 Recon/Survival; DM-1
  sight in dark conditions).

### Aslan (Hierate)

*Source: AoCS Vol. 1 (`refs/alien1/02_aslan_travellers_chapter_two.md`)*

Feline species from the Aslan Hierate.

- **Characteristics:** STR+2, DEX-2, END+1 (male); STR+1, DEX-1, END+2 (female).
- **SOC replaced by TER (Territorial Imperative) for males only.** Females retain SOC.
- **Rite of Passage** (roll 10+) replaces qualification for the first career.
- **Clan Shares** replace pensions (tradeable for cash, land, ship shares, favours).
- **Gender-locked assignments:** Commander (male only), Shipmaster and Navigator (female only);
  Wanderer career (male only).
- Male cash mustering out limited to rolls equal to Independence skill level; cash at half value.
  Females have unlimited cash rolls.
- Aslan-specific Life Events table.

### Aslan (Humaniti)

*Source: Core (`refs/core/02_traveller_creation.md`)*

Aslan integrated into human space use the Core rules. No gender-split characteristics, no
TER, no Rite of Passage or Clan mechanics. All Core careers are available.

- **Traits:** Dewclaw (1D+2, Melee natural); Heightened Senses (DM+1 Recon/Survival).

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

| SOC  | Caste                          |
| ---- | ------------------------------ |
| 0    | Outcast / casteless            |
| 1–3  | Lowest Value Servant           |
| 4–6  | Servant                        |
| 7–10 | Merchant                       |
| 11   | Noble (Small Family Patriarch) |
| 12   | Noble (Big Family Patriarch)   |
| 13   | Herdlord                       |
| 14   | Clanlord                       |
| 15   | Steppelord                     |

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

| Career                        | Qualification |
| ----------------------------- | ------------- |
| K'kree (pastoral/traditional) | Automatic     |
| Servant                       | SOC 1–6       |
| Merchant                      | SOC 7–10      |
| Noble                         | SOC 11+       |

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

| Caste      | Modifiers                  |
| ---------- | -------------------------- |
| Worker     | STR+2, END+4               |
| Warrior    | STR+3, DEX+1, END+2        |
| Drone      | DEX+1, INT+3, EDU+2        |
| Technician | DEX+2, INT+3, EDU+1        |
| Sport      | DEX+1, END+1, INT+2, EDU+2 |
| Leader     | INT+4, EDU+2               |

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

## Minor Sophonts

Sophont populations that did not independently develop jump drive technology.

---

### Human Minor Races

Branches of Humaniti, or groups of human descent, with their own distinct mechanics.

#### Aquamorph

*Source: Solomani Front (`refs/sol/02_overview_of_the_solomani_front.md`)*

Genetically modified humans adapted for aquatic environments via gill/lung apparatus. Resemble humans but with webbed hands/feet, longer limbs, and dense insulating body fat. Can breathe underwater indefinitely; safe to 30m, can push to 100m with risk. Required to keep gill-lungs wet when on land (periodic immersion in water or gel-impregnated clothing).

- **Characteristics:** Standard roll. STR is considered halved when operating out of water.
- **Aquatic Adaptation:** breathe underwater indefinitely via gill/lung apparatus; safe to 30m unaided, can push to ~100m with risk. Gill-lungs must be kept wet on land (periodic immersion or gel-impregnated clothing).
- All Core careers available.

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

#### Humaniti

*Source: Core rules default (`refs/core/02_traveller_creation.md`)*

Standard human characteristics and career access. Used as default / catch-all e.g. for
most humans in non-aligned worlds, or in polities which are not associated to a certain
major or minor race. Technically the same as `Vilani` but without that cultural context.

Humaniti can be used for humans with origins in Vilani, Solomani, minor races or mixes
of these which don't clearly fit elsewhere.

#### Iltharans

*Source: Deep and the Dark (`refs/deepdark/03_aliens_of_the_buffer.md`)*

Human Minor Race from Drexilthar (Reaver's Deep). Unusually long-lived and militaristic;
once ruled an interstellar empire destroyed by the Imperium in 268.

- **Characteristics:** END+1.
- Longevity: DM+6 to all aging rolls.
- All Core careers available.

#### Ghenani

*Source: Spinward Extents (`refs/spinext/43_freni_language.md`)*

Descendants of humans transplanted to a heavy-gravity world by the Ancients. Extremely powerful, with a strict social structure that limits access to technology.

- **Characteristics:** STR+2, DEX-2. STR maximum 17.
- DM-1 to all aging rolls.
- No cyberware or psionics available.
- Career access is limited while on the homeworld; after emigrating, most Core careers become available.

#### Jonkeereen

*Source: BTC (`refs/btc/20_creating_jonkeereen_travellers.md`); also Trail (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Genetically engineered desert-adapted humans, first settled on Jonkeer (Deneb sector). Live on ~20% normal water intake; excellent digestion; UV-filtering membrane over eyes.

- **BTC characteristics:** END+1, EDU-1. **Trail characteristics:** END+2 only. ⚠ Discrepancy between sources.
- **Desert Survival:** breathe most tainted atmospheres without mask; DM+3 Survival in desert/hot environments.
- Short-lived: average 60–65 years.
- Standard Core career access and aging.

#### Katangan

*Source: Spinward Extents (`refs/spinext/16_balleau.md`)*

Humans native to the heavy-gravity world of Katanga (Foreven sector), part of the former Sindalian Empire region. Physically identical to standard humans but physiologically adapted.

- **Characteristics:** STR+1, DEX-1, END+1.
- **Draft:** all Katangan serve a mandatory military term in the first career.
- **Heavy Worlder:** DM-1 to aging rolls.
- **Katangan Culture:** DM+1 to social and cultural checks in familiar Katangan contexts; DM-1 in unfamiliar situations.

#### Luriani

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Humans modified by the Ancients for aquatic environments, now with an extensive interstellar culture in the Gateway/Ley region. About 35% of Luriani society are non-Luriani humans absorbed culturally (Verasti Dtareen and Mmarislusant).

- **Characteristics:** DEX+1, END+1, SOC-2.
- **Aquatic Adaptation (genetically Luriani only):** safe dives to 500m unaided; breathe without air for up to 1 hour; DM+2 Survival and swimming/underwater checks.
- **Histrionics (all Luriani culture members):** DM-2 concealing feelings; DM+2 drawing attention to themselves.

#### Selenite

*Source: Solomani Front (`refs/sol/02_overview_of_the_solomani_front.md`)*

Long-limbed, lightly-built humans engineered for low-gravity environments during early Sol system colonisation. Homeworld is Velscur (Alpha Crucis); enclaves across many paraterraformed worlds.

- **Characteristics:** DEX+2; STR=2D3+1; END=1D+1.
- **Great Indoors:** uncomfortable outdoors on uncontrolled planets; must make Routine (6+) INT check or panic when exposed to uncontrolled weather; more dangerous phenomena trigger harder checks.
- **Low-G:** DM+2 physical activity in low-gravity/microgravity; never loses orientation in 3D environments.
- All Core careers available; space-related careers preferred.

#### Sylean

*Source: Third Imperium (`refs/3i/39_khiinra_ash.md`)*

Human Minor Race created by the Ancients, native to Sylea. Taller than average with pale skin and dark hair. Culturally focused and spiritually driven; played a key role in the establishment of the Third Imperium. Billions of genetically pure Syleans remain despite centuries of interbreeding.

- **Characteristics:** STR-1, EDU+1.
- **Cooperation:** DM+2 on Admin, Diplomat, and Streetwise checks on Sylean worlds (50%+ Sylean population).
- **Wealth:** DM+1 on all Cash Benefit rolls at mustering out.
- Almost all Core careers available. Drifter (barbarian/wanderer) is very rare; Rogue requires extenuating circumstances. Psion/Believer (from Companion) suitable for religiously-inclined Syleans.

#### Sydites

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Very large (~2.5m) four-armed humans engineered by the Ancients as workers or expendable warriors. Upper arms handle power, lower arms fine work — but the muscle groups are interlinked, making simultaneous use awkward. Cannot interbreed with other humans. Once ruled the Khuur League.

- **Characteristics:** STR+2, END+2, DEX-2, INT-3, EDU-3. When using upper limbs for power tasks: additional STR+2. When using lower limbs for fine work: additional DEX+2 (offsetting the base penalty).
- **Resilient:** Protection +1; DM+2 vs electric shocks, heat, and cold damage.
- **Plodding Along (most Sydites):** DM-4 on Leadership or Tactics checks; DM+4 on morale checks to avoid discouragement. Travellers may lack this trait at Referee's discretion.

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

#### Ape

*Source: Solomani Front (`refs/sol/02_overview_of_the_solomani_front.md`)*

Uplifted Terran apes (gorilla and chimpanzee hybrid) engineered by Old Earth Union scientists late in the Interstellar Wars period. Two interfertile subtypes: chimpanzee-types are small and agile; gorilla-types are massively strong. Small scattered communities exist on Solomani worlds; legally treated as people by both the Imperium and Confederation, though often second-class citizens in practice.

- **Characteristics:** STR+1, END+1, SOC-1.
- **Heightened Senses:** DM+1 Recon and Survival checks.
- **Chimpanzee subtype:** Small (-1, DM-1 against them with ranged attacks).
- **Gorilla subtype:** Athletics (strength) 2 innate.
- All Core careers available; in the Confederation, Army/Marine/Navy are most common.

#### Ursa

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Uplifted Terran brown bears, adapted by Solomani scientists for colonisation of high-gravity worlds. Most were killed in a Solomani corporate termination programme; the survivors are few and deeply scarred by this history. Live in small rural communities; loyal and jovial once trust is earned, despite a surly exterior with strangers. Great craftspeople who hate to destroy things.

- **Characteristics:** STR+4, END+2.
- **Claws and Teeth:** Claws deal 1D+3 in close combat; DM+2 climbing natural surfaces. Claws and teeth also serve as improvised tools.
- **Sore Head:** DM-2 to all social interactions with humans (except those who have become like family to the Ursa).

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

#### Crenduthaar

*Source: BTC (`refs/btc/31_trin.md`)*

Enormous hexapedal sophonts from Kretikaa (Lamas subsector, Deneb). Covered in thick armoured hide; two trunk-like appendages serve as arms. Despite fearsome appearance, have an advanced industrial civilisation and form the core of the Crenduthaar Hierarchy. Harbour deep hostility towards Vargr (rumoured genocidal history); may attack Vargr on sight. Terrified of darkness — never willingly enter unlit spaces.

- **Characteristics:** STR=3D, END=3D, DEX=1D.
- **Traits:** Armour (+3, thick hide); IR Vision; Natural Weapon (Slasher, 2D).
- Careers: Army, Citizen, Drifter, Marine, Rogue.

#### Dynchia

*Source: JTAS Vol. 1 (`refs/jtas/1/07_alien.md`)*

Humanoid traders from the trailing Old Expanses.

- **Characteristics:** STR=1D+3, DEX+1, EDU+1.
- DM-2 enlistment/commission/promotion in Army, Navy, Marines, and large merchant
  organisations when outside the Dynchia Comitia.
- Mature Technology trait: can modify TL12 or lower devices 10% better in one area.

#### Ebokin

*Source: BTC (`refs/btc/09_spinwards_marches_subsctor_d.md`)*

Large arthropod-descended sophonts from Aramanx (Aramis subsector). Originally ammonia-breathing methane-worlders now adapted to a standard atmosphere via biological engineering. Patient, methodical, and surprisingly social for a species evolved in toxic isolation.

- **Characteristics:** DEX-2, END+3.
- **Traits:** Atmospheric Requirements (originally methane; adapted individuals require filter mask in standard atmosphere); Armour (+3); UV Vision (see into ultraviolet spectrum).
- Careers: Agent, Army, Citizen, Drifter, Merchant, Noble, Scholar, Scout.

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

#### Gl'lu

*Source: BTC (`refs/btc/31_trin.md`)*

Asymmetric insectoid sophonts from Kubishush (Magash subsector, Deneb) — a world with a corrosive ammonia atmosphere. Friendly and cultured despite nightmarish appearance. Hermaphroditic single gender. Obsessed with redundancy in starship design; their staterooms are tiny, fitting 8 per standard cabin.

- **Characteristics:** END-1, DEX+1, EDU-2.
- **Traits:** Atmospheric Requirements (ammonia — need sealed suit elsewhere); Fast Metabolism (DM+1 initiative); Heightened Senses (DM+1 Recon/Survival); IR Vision (see only in infrared); Natural Weapon (fangs, 1D+2).
- All Core careers available.

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

#### Kirissukyoya

*Source: BTC (`refs/btc/31_trin.md`)*

Trilateral sophonts from Giikusu (Dunmag subsector, Deneb). Three arms and three legs; brain in torso rather than head. Nearly destroyed themselves in a TL7 global war around -2000; saved by Droyne intervention. Innate mechanical aptitude.

- **Characteristics:** STR-1.
- **Traits:** Eidetic Sense (hearing — perfect recall of anything heard); Natural Weapon (claws, 1D); Skill (Mechanic 1 innate).
- All Core careers available.

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

#### Llellewyloly

*Source: BTC (`refs/btc/09_spinwards_marches_subsctor_d.md`)*

Five-limbed spherical sophonts native to Junidy (Aramis subsector). All five limbs function interchangeably as arms or legs. Highly complex social hierarchy where an individual's rank can shift minute to minute; using the wrong form of address is a serious gaffe. Share their world with humans, with recurring tensions.

- **Characteristics:** STR=2D3, END=2D3.
- **Traits:** Alien Digits (DM-2 on checks using devices not adapted for Llellewyloly); Atmosphere (thin — comfortable in very thin atmosphere, need protection from dense).
- Careers not listed in source.

#### Lurent

*Source: BTC (`refs/btc/31_trin.md`)*

Large headless sophonts from Borlund (Lamas subsector, Deneb). Thorax carries sense organs and two manipulation tentacles; abdomen has two legs and vestigial tail. Covered in pale blue or green fur. Subject to compulsion cycles — wandering, homeward-bound, or sedentary — that override rational choice.

- **Characteristics:** STR=2D+4, END=2D+4.
- **Traits:** Natural Weapon (Tentacle Bash, 2D); Wanderlust (compelling cycle: wandering, homeward, or sedentary).
- Careers: Drifter, Merchant, Noble, Rogue, Scout, Scholar.

#### Mal'Gnar

*Source: Spinward Extents (`refs/spinext/11_aliens_of_the_beyond.md`)*

- **Characteristics:** EDU=1D+1. Cannot speak Galanglic.
- Drifter (barbarian) only.

#### Martian

*Source: BTC (`refs/btc/31_trin.md`)*

Lightly built humanoids from Marz (Pretoria subsector, Deneb), living in warm spindly forests. No concept of themselves as a species — each village is simply "us," everywhere else is "not home." Will happily combine stone-age techniques with high technology in bizarre but effective ways.

- **Characteristics:** STR-1, END-1, DEX+1; EDU=1D (cannot be increased beyond 7).
- **Traits:** Adaptability (INT check to improvise tools/solutions); Telepathic Confusion (telepathy attempts on Martians always fail, leaving telepath baffled).
- Most Core careers suitable; gravitate to frontiersman/infantry roles.

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

#### Saurus

*Source: BTC (`refs/btc/12_saurus.md`)*

Reptilian sophonts native to Saurus (Sword Worlds subsector). Heavily built, warm-blooded, peaceable hunters. Primitive when humans arrived; some now work in human settlements but most still live traditionally. Quite accepting of strangers.

- **Characteristics:** STR+2, END+2; INT=2D3; EDU=1D.
- **Traits:** Armour (+2, thick scaly skin).
- Careers: Citizen (worker), Drifter (barbarian, wanderer) only.

#### Segani

*Source: BTC (`refs/btc/31_trin.md`)*

Tall, leathery-skinned sophonts from Segan (Deneb), probably transplanted there by unknown entities — not native to their world. Aggressive desert-adapted fighters. Jump travel causes progressive madness; Segani who venture interstellar typically use low berths.

- **Characteristics:** END=1D+2 (maximum 10 by any means); all other characteristics 2D.
- **Traits:** Desert Adaptation (DM+2 Survival/Recon in arid environments); Quick to Anger (DM+2 initiative).
- Careers: Army, Citizen, Entertainer, Rogue, Scholar.

#### Shi'awei

*Source: BTC (`refs/btc/31_trin.md`)*

Bullet-shaped aquatic sophonts from Chaosheo (Star Lane subsector, Deneb). Highly fragmented society — some communities are friendly, others lethal to visitors; the pattern is unpredictable even between visits to the same group.

- **Characteristics:** STR=3D, END=3D, DEX=1D. Males also: STR-1, END+1.
- **Traits:** Echolocation (30m); Fast Metabolism (DM+1 initiative); Natural Weapon (grippers, 2D); Swimmer (9m).
- Careers: Drifter, Entertainer, Noble, Rogue.

#### Souggvuez

*Source: BTC (`refs/btc/31_trin.md`)*

Indigenous people of Talon (Million subsector, Deneb), now intermingled with Vargr migrants who arrived around -300. Three-section asymmetric torso, eight legs, four dual-thumbed arms. Four gender castes: Designer, Explorer, Hunter, Worker.

- **Characteristics:** DEX+1, INT-1, EDU+1 (all castes). Designer also: DEX+1, END-1. Explorer also: DEX+1, END-1, INT-1, EDU+1. Hunter also: DEX+1, INT-1. Worker also: INT-1, EDU+1.
- **Traits:** Armour (+1); Bite (1D+2).
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

#### Yafizethe

*Source: BTC (`refs/btc/31_trin.md`)*

Multi-legged sophonts from Kernal (Star Lane subsector, Deneb). Rear body is carried low on eight pairs of walking legs; front pair held upright serves as arms. Able to perceive electromagnetic fields. Renowned negotiators and diplomats.

- **Characteristics:** STR=1D, END=1D, DEX=3D, INT+1.
- **Traits:** Enhanced Vision (electromagnetic fields); Small (-1, DM-1 to ranged attacks against them).
- Careers not listed in source.

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

#### Akeed

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Slug-like sophonts from Akeen (Gateway sector), ruling a multi-world state where humans live as willing partners. Upper body has four pairs of tentacles; lower body is a boneless locomotion pad. Blind in the visual spectrum — navigate by sonar and chemical sense. No mouth; breathe through a hole that can produce speech and even singing. Feed by drawing minerals from soil through foot openings.

- **Characteristics:** STR-2, END-2, INT+1.
- **Akeed Debate:** DM+2 to argue a point, convince someone, or mediate a fair settlement.
- **Akeed Friendship:** Difficult (10+) Persuade check after several hours of interaction; on success, forms a permanent deep bond granting DM+1 on all checks benefiting the friend. One bond at a time.
- Movement 4m; can traverse slopes up to 70° at 1m/round. Careers not listed in source.

#### Capry

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Feathered bipeds from Basternevis (Gateway sector), now nearly extinct following ecological collapse of their homeworld. Three sexes: females (technical), big males (physical), small males (abstract intellect). All have a prehensile tail ending in a cluster of feather-fingers for delicate manipulation. Wiry build, ~1.4–1.6m tall. Deeply fatalistic but liberated by their species' doom.

- **Female characteristics:** STR-3, DEX+2, END-2, INT+1.
- **Big Male characteristics:** STR-1, END+1.
- **Small Male characteristics:** STR-4, DEX+3, END-3, EDU+2.
- **Liberating Fatalism:** choose 3 areas of special interest; DM+1 on tasks that can benefit from near-obsession with those areas.
- **Third Hand:** feather-fingers can assist with fine tasks (holding things, steadying a repair) granting DM+2; too weak to wield weapons or support body weight.
- Careers not listed in source.

#### Droashav

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Six-limbed pseudoreptilians from Trevannic (Gateway sector). Two pairs of arms, clawed feet useful in combat. Greeny-brown hide provides natural armour. Most live as TL1 desert nomads; a small TL4 civilisation exists. Possibly related to the K'kree — a contested theory that would make them the ancient G'naak the K'kree tried to exterminate.

- **Characteristics:** STR+2, DEX-1, END+3, INT-1.
- **Natural Defences:** Protection +1; claws deal 1D+2 in close combat.
- Careers not listed in source.

#### Eslyat

*Source: Spinward Extents (`refs/spinext/42_portmanteau_shipping_services.md`)*

Three-caste aquatic sophonts of the Spinward Extents, divided by SOC into sub-races: Selyin (high SOC), Chutin (mid SOC), Magsin (low SOC). Males of all castes have STR+1 but suffer DM-1 advancement at Rank 4+; females receive DM+1 advancement. Well adapted to underwater environments.

- **Characteristics:** By caste (Selyin/Chutin/Magsin vary); males also STR+1.
- **Amphibious:** can breathe and operate underwater indefinitely.
- **Heightened Hearing:** DM+1 Recon in any situation relying on sound.
- Careers limited by caste.

#### Faar

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Squat, powerfully built humanoids from the high-gravity world of Alphaaric (Gateway sector). Pale skin, no body hair, pale eyes. Advanced technology but no interest in interstellar expansion — most visitors meet Faar representatives at the orbital station Faarview. Appear fearful of something "out there" and desperately want to stay home.

- **Characteristics:** STR+1, END+1, DEX-1.
- **Closed Book:** all skills involving reading Faar emotions or reactions, including psionics, suffer DM-2.
- **Homesickness:** every 2D days away from home, END check (Average 8+) or fall into melancholy (DM-1 all non-survival tasks for 1D days).
- Careers not listed in source.

#### Freni

*Source: Spinward Extents (`refs/spinext/42_portmanteau_shipping_services.md`)*

Six-subspecies sophonts of the Spinward Extents, with SOC equal to EDU rather than social standing. Renowned throughout the region as exceptional cooks and freeloaders. All start with Steward 1, Profession (freeloading) 1, and Survival 0 as innate skills. Flexible, prehensile digit structure.

- **Subspecies characteristics:** Type 1: STR-1, DEX+2, INT-1; Type 2: DEX-2, END+1, INT+1; Type 3: STR+1, DEX-2, END+1; Type 4: DEX-1, END+2, INT-1; Type 5: STR-1, END-1, INT+2; Type 6: STR+1, DEX-1, END-1, INT+1.
- **SOC = EDU** at start of character generation.
- **Flexible Digits:** DM+1 on fine manipulation tasks.
- All Core careers available; DM+1 Entertainer and Merchant; DM-1 Agent and Scholar.

#### Gurungan

*Source: Solomani Front (`refs/sol/02_overview_of_the_solomani_front.md`)*

Blind deep-sea octopoid sophonts from Ugarup (Ultima subsector, Solomani Rim). Six tentacles, no eyes — primary sense is sonar. Males are tiny parasites absorbed during mating; only females are sophonts. Strong sense of community identity over self; infuriating habit of refusing to address aliens directly, yet excellent negotiators. Allied with the Terran Confederation historically, now within the Third Imperium.

- **Characteristics:** DEX+2.
- **Aquatic:** breathe underwater naturally; on land, speed 2m, END check every minute (increasing difficulty) or suffer 1D damage; resets after 5 minutes fully immersed.
- **Bite:** 1D damage, Melee (natural).
- **Deep Diver (1,000m):** safe to 1,000m depth.
- **Sonar (120m):** navigate by sonar in water or complete darkness.
- **Swimmer (8m):** move at 8m in water.
- All Core careers available.

#### Ladybug

*Source: Solomani Front (`refs/sol/02_overview_of_the_solomani_front.md`)*

Slender humanoids with multifaceted eyes, feathery ears, and shimmering blue-violet skin, native to Amiens (Alpha Crucis). Serial hermaphrodites; spend most time as female or neuter. Gentle, docile, and widely considered beautiful by most sentient species. Commonly employed as domestic workers and servants throughout the Confederation of Turin. Whether their apparent intellectual limitations are innate or socially conditioned is debated.

- **Characteristics:** STR=1D+2, END=1D+2, SOC=1D+2; INT=2D3; EDU=2D3; DEX=2D+3.
- **Gentle Soul:** DM-2 to all checks involving combat or confrontation (including leadership, bargaining).
- **You Beautiful Thing:** DM+2 to obtain assistance when asking for help or appearing in need. Attackers roll 2D — on 12+, they hesitate and refuse to harm the Ladybug.
- All careers in theory; DM-2 to qualify for and advance in military or confrontational careers.

#### Murian

*Source: Spinward Extents (`refs/spinext/43_freni_language.md`)*

Short-limbed, heavily built sophonts of the Spinward Extents. SOC is generated on 2D3+4. STR and END have a racial maximum of 18. Move at 4m (Short Limbs). Cannot see green, blue, or violet wavelengths; see into infrared.

- **Characteristics:** STR+1, DEX-2, END+2; SOC=2D3+4.
- **Traits:** Armour (+1, thick hide); Natural Weapon (claw, 1D+2); Short Limbs (movement 4m, DM-1 on all checks penalised by reach or speed); IR Vision (no green/blue/violet).
- All Core careers available.

#### Oo-ne-beto-pon-tee

*Source: Third Imperium (`refs/3i/48_creating_oo_ne_beto_pon_tee_whistler_travellers.md`)*

Four-sexed insectoid sophonts from Night (Third Imperium region), commonly called Whistlers by humans. Matchers, males, and females are extremely focused/specialised and poorly suited as Travellers; neuters are recommended for play. Groups of Whistlers aboard a ship gradually affect the crew with a calming, community-building influence after 4–6 weeks — effective on most Major Races except half of Hivers.

- **Characteristics:** STR=D3, END=D3, SOC=D3; DEX=1D+4; INT=2D-1; EDU=2D.
- **Sticky Feet:** can climb virtually any surface.
- **Sneaky:** automatically have Stealth 2 due to their quiet, unassuming nature.
- **High-frequency Communication and Perception:** hear from 20Hz to 60kHz.
- Careers not listed in source; neuter sex recommended.

#### Rammak

*Source: Rimward Expeditions (`refs/rimexp/23_ivy_subsector.md`)*

Humanoid-ish sophonts from the Rammak system (Ivy subsector, close rimward). Two legs and two arms with an extra joint, creating unsettling fluid movement. Two sets of eyes: forward-facing for detail, side-mounted large ones for low-light/infrared peripheral and all-round awareness. Egg-layers; young raised communally in "nests" — attacking nests causes lasting enmity. Developed jump drive by reverse-engineering a derelict Rule of Man colony ship.

- **Characteristics:** DEX=1D+8 (range 9–14); all others rolled normally.
- **All-round Perception:** DM+2 moving through cluttered areas; DM-2 for anyone trying to surprise them physically.
- **Specialised Limbs:** DM+2 climbing, reaching into awkward spaces; DM-2 on strength-based actions (wrestling, dragging heavy objects).
- Careers not listed in source.

#### Resavolk

*Source: Spinward Extents (`refs/spinext/43_freni_language.md`)*

Multi-stage sophonts of the Spinward Extents with unusually low SOC (generated on D3+5). No notable physical traits beyond their life cycle. After a mandatory Drifter (barbarian) first career, may enter almost any career except Noble (unless SOC reaches 10+).

- **Characteristics:** SOC=D3+5; all others rolled normally.
- No exceptional physical traits listed.
- **Careers:** Drifter (barbarian) mandatory for first term; thereafter any Core career except Noble unless SOC 10+.

#### Ssienjhiovla

*Source: Third Imperium (`refs/3i/55_dinenruum.md`)*

Shelled mollusc-like sophonts from Shimaraak (Third Imperium), native to a thin-atmosphere high-gravity world. Two squat dextrous feet with suckers; four arm-like appendages each with six malleable fingers; brain and senses in the torso rather than a head. Asexual, bearing immediately independent live young. Decorate their dorsal carapace using natural acids. Communicate via gas/pheromone excretion and arm gestures; human-interface devices required for verbal speech.

- **Characteristics:** STR-2, DEX+1.
- **Carapace:** Protection +6.
- **Composite Imaging:** on worlds with Atmosphere 3–7, detect events out of visual range up to 1km via olfactory composite sense (similar to Clairvoyance but not psionic; doesn't work through sealed environments).
- **Non-verbal Communication:** communicate with other Ssienjhiovla over up to 5km via pheromone excretion.
- Most common career choices: Scout Service and Navy (Imperial or planetary).

#### Teakhea

*Source: Spinward Extents (`refs/spinext/13_outstanding_questions.md`)*

Serially hermaphroditic snail-like sophonts of the Spinward Extents, culturally integrated into Aslan space. Shell provides significant natural protection. Move via a large muscular foot (snail locomotion) but can also move on land or water. Can change biological sex, which affects career path. Gender-changing career system governs advancement.

- **Characteristics:** STR+1, DEX-1, END+1, SOC-2.
- **Traits:** Amphibious (indefinite aquatic operation); Heightened Senses (DM+1 Recon/Survival); IR Vision and UV Vision; Large (+2, larger target for ranged attacks); Shell (+3 natural armour); Snail Foot (specific movement rules apply); Language (Trokh) 2 innate.
- Careers: Aslan career list, excluding Ceremonial, Envoy, and Military Space Officer.

#### Thonane

*Source: Spinward Extents (`refs/spinext/43_freni_language.md`)*

Tiny avian sophonts of the Spinward Extents with extremely variable characteristics. EDU and SOC are rolled on D3, reflecting their primitive barbarian culture. Natural hunters; several hunter-related skills come innate. Natural flyers.

- **Characteristics:** STR=1D, DEX=3D, END=2D, INT=2D, EDU=D3, SOC=D3.
- **Flyer:** natural winged flight.
- **Hunter:** innate hunter skills at character creation.
- Careers: Drifter (barbarian) only.

#### Wanderer (Wandering People)

*Source: The Trailing Frontier (`refs/trail/03_pthe_trailing_frontier_eople_of.md`)*

Insectoid sophonts originating in the Trailing Frontier, now spread across Gateway and Ley sectors on worldships (huge non-jump vessels) with jump-capable scouts ranging from them. Mysterious and secretive about culture and religion. Their jump drive is derived from a captured/reverse-engineered Vilani type; they are sometimes misidentified as a Major Race but are not — they did not independently develop jump technology. Most have an overwhelming sense of community; "rogue Wanderers" who travel independently are rare and poorly understood.

- **Characteristics:** DEX+2, STR-1, END-1.
- **Carapace:** Protection +1.
- **Weird Movement:** body construction makes movement unsettling to most species. DM-2 to read Wanderer body language or intentions. DM-1 to hit Wanderers with ranged weapons for those unused to their physiology.
- Careers not listed in source.

#### Zhdianshe

*Source: Spinward Extents (`refs/spinext/43_freni_language.md`)*

Tiny psionic flyers of the Spinward Extents. STR is fixed at 1; all physical strength comes from psionics. SOC equals PSI (social standing derived from psionic power). Extraordinarily long-lived — no aging rolls until term 8, with DM+6 thereafter. Echolocate and fly naturally. Born with Telepathy 2 and Clairvoyance 1; must train Psion career to develop further.

- **Characteristics:** STR=1 (fixed); DEX=2D+2; PSI=2D (minimum 2); SOC=PSI (same value). Other characteristics 2D.
- **Traits:** Echolocation; Flyer; Telepathy 2 (auto); Clairvoyance 1 (auto).
- **Aging:** no aging checks until start of term 8; all subsequent aging checks have DM+6.
- All Core careers + Psion available; DM-4 Army and Marine.

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
- **Veghu** (Spinext, `refs/spinext/43_freni_language.md`) — explicitly "not suitable as Travellers" in source.
- **Weeven** (Sol, `refs/sol/02_overview_of_the_solomani_front.md`) — flat-topped cone creatures with 3D+30 hits and a lifespan/thought speed incompatible with standard play; characteristics not meaningful to humans.
- **Aniyun** (Spinext) — has creation rules (STR=1D, EDU-2; Citizen/Drifter only; listed
  in table above).

---

## T5SS Sophonts Not Yet in Our Table

These sophonts appear in the [T5SS sophont list](https://travellermap.com/t5ss/sophonts)
but are not yet covered by published creation rules in `refs/`. Notes column is for
future tracking (rule sources found, refs added, creation rules status, etc.).

| Code | Sophont | Location (sector abbrev.) | Notes |
|------|---------|---------------------------|-------|
| Adda | Addaxur | Zhodani space | |
| Bhun | Brunj | Forn | |
| Brin | Brinn | Corr | |
| Buru | Burugdi | Dagu/Thet | |
| Chir | Chirpers | major | Not player-characters |
| Clot | Clotho | Tien | |
| Darm | Darmine | Zaru | |
| Flor | Floriani | Beyo/Troj | |
| Gnii | Gniivi | Hint | |
| Gray | Graytch | Dagu/Gush/Ilel | |
| Hama | Hamaran | Dagu | |
| Jaib | Jaibok | Thet | |
| Jala | Jala'lak | Dagu | |
| Jend | Jenda | Hint/Leon | |
| Kafo | Kafoe | Cruc | |
| Kagg | Kaggushus | Mass | |
| Karh | Karhyri | Cruc | |
| Kiak | Kiakh'iee | Dagu | |
| Lamu | Lamura Gav/Teg | Hint | |
| Lanc | Lancians | Dagu/Gush | |
| Libe | Liberts | Daib/Dias | |
| Mask | Maskai | Glim | |
| Mitz | Mitzene | Thet | |
| Murr | Murrissi | Hlak | |
| S'mr | S'mrii | Dagu | |
| Scan | Scanians | Dagu | |
| Stal | Stalkers | Hint | |
| Sull | Sulliji | Dene | |
| Swan | Swanfei | Gate | |
| Tapa | Tapazmal | Reft | |
| Taur | Taureans | Alde | |
| Tent | Tentrassi | Zaru | |
| Urun | Urunishani | Anta | |
| Yile | Yileans | Gash | |
| Ziad | Ziadd | Dagu | |
