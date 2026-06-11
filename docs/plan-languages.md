# Plan: Language Skills

Languages in Traveller are tied to sophonts, polities, and cultures, but the
correlation is fuzzy — anyone can learn any language, some are broad (Galanglic,
spoken across the Third Imperium) and some narrow (Imperial Marine Battle
Language, used only within a specific military context).

The Game obviously assumes that PCs and NPCs can speak to each other even if
they don't formally have any language skill. The idea here is to make the
possibly non-academic langage skills explicit.

Every character will have a mother-tongue, probably determined by birthworld
and sophont properties. This would appear as an extra Background skill.
A long exposure to a dominating culture should also lead to some knowledge
in that language. Finally, other aspects of life such as careers might expose
people to e.g. trade languages.

The current language skill rolls would mainly be for learning foreign languages
or for academic depth.

This plan covers: module structure, the mother tongue house rule, career-based
language grants, and the skills table UX problem posed by 50+ languages.

## Module structure

Languages are skills, but there are too many to live in `skills.py`. Extract
them to `src/ceres/character/domain/languages.py`. Each language is a `Skill`
subclass following the same pattern as today's `LanguageGalanglic` etc.

Languages have a soft association with sophonts/polities — stored as metadata
on the class (e.g. a `polity` or `spoken_by` class variable), not enforced by
the type system. This association is useful for UI filtering and character sheet
display but does not restrict who can learn the language.

The existing six in `skills.py` move to the new module. `AnySkill` and the
`Languages` union type are updated to import from there.

## Mother tongue (house rule)

At age 18, every character receives their mother tongue as an extra background
skill, in addition to the normal EDU-based background skills. Level depends on
EDU DM:

| EDU DM  | Mother tongue level |
|---------|-------------------|
| < 0     | 0                 |
| 0 or 1  | 1                 |
| > 1     | 2                 |

Mother tongue is determined by sophont/homeworld. The sophont definition (or
homeworld, if sophont has no native language) carries a `native_language` field
pointing to the relevant language class. This feeds into character start.

Document this in `RULE_INTERPRETATIONS.md` when implemented.

## Career language grants

Some careers grant a language at specific rank thresholds rather than as a
skill table entry.

**Example: Imperial Marine Battle Language (Sign)**

Marines learn the Battle Language through service, keyed to rank. Support
assignment is excluded (they do not operate in the same tactical environments).

| Rank threshold | Level granted |
|----------------|---------------|
| E2 or O1       | 1             |
| E4 or O2       | 2             |
| E6 or O3       | 3             |

Implementation: rank bonus handler in the Marines career, analogous to existing
rank skill grants. Checks assignment != Support before applying.

Other careers may have similar grants — document them here as they are
identified.

## Skills table UX: the 50+ language problem

A skills table entry of `Language` cannot expand to a flat list of 50+ options.
Two tiers:

**Tier 1 — common/featured languages**: a short curated list offered directly
when Language appears in a skill table. Candidates: Galanglic, Vilani, Sagamaal,
Zdetl, Trokh, Gvegh, Oynprith, and any language relevant to the career/sophont
context.

**Tier 2 — Language Other**: a fallback option in Tier 1 that opens a secondary
choice with the full list. If the full list still does not cover the desired
language, a free-text note is accepted as a cop-out (recorded as an unresolved
annotation on the character, not as a typed skill).

The featured list for Tier 1 is configurable per career or context, not global.

## Language list

Source: https://wiki.travellerrpg.com/Languages_of_Charted_Space (50+ entries).

We do not need all of them on day one. Curate as careers and sophonts are
implemented. Priority order roughly follows Third Imperium / Spinward Marches
focus of the current ruleset:

- Galanglic (Third Imperium common tongue) — already implemented
- Vilani (First Imperium / Vilani people) — already implemented
- Sagamaal (Sword Worlds Confederation) — first addition
- Zdetl (Zhodani Consulate) — already implemented
- Trokh (Aslan Hierate) — already implemented
- Gvegh (Vargr Extents) — already implemented
- Oynprith (Droyne) — already implemented
- Darrian (Darrian Confederation)
- Anglic (Solomani Confederation variant)
- Luriani (Luriani cultural region)
- Imperial Marine Battle Language (career-specific, non-geographic)
- K'kree Lisun — add when K'kree sophont is implemented
- Others as needed

## Open questions

- **Native language on sophont vs. homeworld**: should `Sophont` carry
  `native_language`, or should it be inferred from the homeworld UWP/culture
  code? Homeworld is more flexible but adds complexity at character start.

- **Multilingual sophonts**: some sophonts (e.g. Aslan) may have regional
  dialects that are separate skills — treat as distinct language classes or
  as specialities of a single `LanguageTrokh`?

- **"Language Other" free-text**: where does this live in the data model?
  Probably as a `Note` on the character summary rather than a typed skill.
  Needs a decision before implementing Tier 2 selection.

- **Career featured list**: who owns the Tier 1 language list for a given
  career? Career data, sophont definition, or a separate configuration?

## Implementation order

1. Move existing languages to `languages.py`; update imports — no behaviour change
2. Add Sagamaal (and other Spinward Marches priorities) to the new module
3. Mother tongue house rule at character start
4. Career language grants (Marines Battle Language as first example)
5. Skills table Tier 1 / Tier 2 selection UX
