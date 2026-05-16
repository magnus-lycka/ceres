# Plan: Komplett manipulatorregel

**Källa**: `refs/robot/09_manipulators.md` (Robot Handbook sid. 25–28)

## Mål

Implementera det fullständiga manipulatorregelverket från Robot Handbook. Nuläget
är en naiv `list[str]` med `['Standard', 'Standard']` som inte modellerar STR, DEX,
storlek eller ombyggnadskostnad. Den fullt implementerade modellen ska kunna
beräkna korrekt slotåtgång, kostnad och statistik för alla manipulatorkonfigurationer.

## Nuläge

`Robot.manipulators: list[str]` håller strängar som `'Standard'`. Enda regeln
som är implementerad är borttagning av manipulatorer: rabatt `Cr100 × storlek × antal`
och +slots per borttagen manipulator. Rabatten är inte cappat till max 20 % av BCC.
Inga STR- eller DEX-värden beräknas. Inga alternativa storlekar stöds. Inget
ombyggnadssystem finns.

## Regler att implementera

### Standardmanipulatorer

Robotens baschassipris inkluderar två manipulatorer av samma storlek som chassit.
Default STR = 2 × Size − 1. Default DEX = ceil(TL / 2) + 1. Ingen extra
slots- eller kostnadspåverkan vid standardkonfiguration.

### Borttagning

Varje borttagen manipulator frigör `ceil(10 % × base_slots)` slots, minst 1.
Kostnadsrabatt = `Cr100 × robot_size` per manipulator, max 20 % av BCC totalt
för alla manipulatorborttagningar. (Den nuvarande implementationen saknar
20 %-taket.)

### Ytterligare manipulatorer (AdditionalManipulator)

Slots per extra manipulator beror på storleksskillnad mot chassit:

| Skillnad | % av base_slots | Minst |
|----------|----------------|-------|
| +2       | 40 %           | 1     |
| +1       | 20 %           | 1     |
| ±0       | 10 %           | 1     |
| −1       | 5 %            | 1     |
| −2       | 2 %            | 1     |
| ≤−3      | 1 %            | 1     |

Kostnad = `Cr100 × manipulator_size`. Maximal storlek = robot_size + 2, med
undantag att Size 8 kan ha Size 10. `AdditionalManipulator` är redan implementerad
för detta fall men visas för närvarande bara i manipulatorraden; se sektion
Spec-visning nedan.

### Ombyggnad av basmanipulatorer (ResizedManipulator)

Att byta storlek på en basmanipulator räknas som att ta bort den och lägga till en
ny av annan storlek:

- Slots att återvinna = slot-kravet för standardstorlek (10 % × base_slots, min 1)
- Slots att betala = slot-kravet för ny storlek per tabellen ovan, min 1
- Nettoskillnad: om ny storlek < standard → minst +1 slot till chassit;
  om ny storlek > standard → minst −1 slot (kräver minst 1 slot extra)
- Kostnadsskillnad = `Cr100 × (slots_ny − slots_standard)`, max −20 % BCC totalt

### STR-förstärkning

Kostnad = `Cr100 × manipulator_size × (delta_str)²`.
Max STR = 2 × default_str. Ingen slotåtgång.

### DEX-förstärkning

Kostnad = `Cr200 × manipulator_size × (delta_dex)²`.
Max DEX = TL + 3. Ingen slotåtgång.

### Walkerben som manipulatorer

Kostnad = `Cr100 × robot_size` per ben som konverteras. Storleken kan inte
ändras. En robot med alla ben konverterade räknas fortfarande som att ha 2 ben;
ben utöver de 2 standardmanipulatorerna räknas som ytterligare manipulatorer.

## Föreslagen modell

### `Manipulator`-klass

Ersätter `list[str]` som den primära representationen:

```python
class Manipulator(CeresModel):
    model_config = {'frozen': True}

    size: int          # manipulator-storlek (1–10)
    str_bonus: int = 0 # förstärkning utöver default STR
    dex_bonus: int = 0 # förstärkning utöver default DEX
    is_leg: bool = False

    def default_str(self) -> int:
        return 2 * self.size - 1

    def default_dex(self, tl: int) -> int:
        return ceil(tl / 2) + 1

    def effective_str(self) -> int:
        return self.default_str() + self.str_bonus

    def effective_dex(self, tl: int) -> int:
        return self.default_dex(tl) + self.dex_bonus

    def stat_label(self, tl: int) -> str:
        return f'STR {self.effective_str()} DEX {self.effective_dex(tl)}'
```

`Robot.manipulators` byts från `list[str]` till `list[Manipulator]`. Befintliga
strängar (`'Standard'`) ersätts med `Manipulator(size=robot_size)`.

### Kopplade beräkningar på `Robot`

`available_slots`-beräkningen måste ta hänsyn till storleksskillnad, inte bara antal:

```python
# Slots frigjorda av ej standardkonfiguration:
for m in removed_or_resized_manipulators:
    freed = max(1, ceil(0.10 * base_slots))      # slot för standardstorlek
    added = max(1, ceil(pct(m.size) * base_slots))  # slot för faktisk storlek
    net_slots += freed - added
```

`total_cost`-beräkningen lägger till STR/DEX-kostnader och hanterar 20 %-taket:

```python
removal_discount = sum(Cr100 × robot_size for removed)
resize_discount  = sum(Cr100 × (std_slots - new_slots) for resized if smaller)
total_discount   = min(removal_discount + resize_discount, 0.20 × BCC)
```

### Spec-visning

Manipulatorraden visar `STR`/`DEX`-statistik för varje manipulator. Nuläget
(default `'Standard'`) visar inget. Målformat:

```
2x (STR 9 DEX 7)
```

eller om manipulatorer har olika statistik:

```
(STR 12 DEX 7), (STR 12 DEX 7), (STR 5 DEX 12)
```

`AdditionalManipulator.description` genererar redan rätt format — den egenskapen
bör återanvändas för `Manipulator` med ombyggd eller förstärkt statistik.

## Fasindelning

### Fas 1 — `Manipulator`-modell och standardfall

- Definiera `Manipulator`-klass i `ceres.make.robot.manipulators` (ny fil).
- Migrera `Robot.manipulators: list[str]` → `list[Manipulator]`.
- Bevara bakåtkompatibel deserialisering för befintliga tester (de som använder
  strängen `'Standard'` kan ersättas med `Manipulator(size=robot_size)` under
  `model_post_init` eller via ett valideringsalias).
- Uppdatera spec-visning så att standardparet visas som `2x (STR N DEX M)`.
- Uppdatera `available_slots`- och `total_cost`-beräkningarna för att ta bort
  20 %-taksbuggen vid borttagning.
- Tester: verifiera STR/DEX-visning för en Size 5 TL10-robot och att borttagning
  av båda manipulatorer inte rabatterar mer än 20 % BCC.

### Fas 2 — Ombyggnad och tillägg

- Implementera `ResizedManipulator` som ett alternativ till standardstorleken vid
  design (d.v.s. `Manipulator` med `size != robot_size`).
- Uppdatera slots- och kostnadsberäkningar för storleksavvikelse.
- Tester: verifiera slot-nettot och kostnaden för StarTek-exemplet
  (`refs/robot/37_startek.md`) med dess ombyggda Size 3-manipulator.

### Fas 3 — STR/DEX-förstärkning

- Implementera `str_bonus` och `dex_bonus` med kostnadsformler och maxvärden.
- Tester: verifiera att StarTek-exemplets armförstärkning (STR +3, Cr4500 per arm)
  ger korrekt kostnad och att maxgränsen respekteras.

### Fas 4 — Walkerben

- Implementera `is_leg=True` med kostnad `Cr100 × robot_size` och stödet för
  att räkna benen som tillkommande manipulatorer.
- Tester: välj ett exempelrobot med benmanipulatorer (t.ex. `refs/robot/91_hive_queen.md`
  om den har detta).

## Tolkningsfrågor att dokumentera i RULE_INTERPRETATIONS.md

1. **20 %-taket gäller kombinerat**: Borttagning och nedskalning av basmanipulatorer
   delar samma tak. Om de är separata tak är det oklart i reglerna.
2. **Ombyggnadens slot-formel**: "Slots gained" för resizing = slots för
   standard − slots för ny. Formuleringen är inte helt entydig; tolkning och
   räkneexempel bör dokumenteras.
3. **Walker-bens manipulatorräkning**: Reglerna säger "designing an eight-limbed
   robot with all limbs as manipulators would involve keeping the two original
   manipulators, adding four manipulators and altering the two default legs to become
   manipulators". Det antyder att ben-konvertering aldrig räknas som ytterligare
   manipulatorer utöver de fyra extra + de två standard — men detta bör bekräftas
   mot ett exempelrobot.

## Testfall

- **Steward Droid** (`refs/robot/101_steward_droid.md`): standardmanipulatorer
  Size 4, STR 7 DEX 7 — enkelt röktest för Fas 1.
- **StarTek** (`refs/robot/99_startek.md`): ombyggd Size 3-arm (DEX+4) + två
  förstärkta Size 5-armar (STR+3) — röktest för Fas 2 och 3.
- **AG300** (`tests/robots/test_ag300.py`): har redan `AdditionalManipulator` —
  kontrollera att Fas 1-migrering inte bryter befintliga assertions.

## Inte i scope

- Vapenmount på manipulatorer (se `docs/plan-gear-backed-robot-options.md`).
- Athletics-skicklighetskrav för STR/DEX DM (presentationslogik, inte
  domänlogik — dokumentera tolkning men implementera inte förrän skicklighetsvisning
  behöver det).
- Biologiska manipulatorer (biologiska robotar är ett separat underdomän).
