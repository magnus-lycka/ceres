from typing import Annotated, Any, cast, overload

from pydantic import BaseModel, BeforeValidator, Field, SerializeAsAny, model_validator

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.benefits import ItemBenefit
from ceres.character.domain.career.career_data import AssignmentData, CareerData, CareerTerm
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import AnyConnection
from ceres.character.domain.psionics import Psionics
from ceres.character.domain.skills import AnySkill, Level, Skill, level_fields
from ceres.character.domain.sophont import Sophont
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.pending_input import PendingInputBase, _deserialise_pending_input
from ceres.shared import int_to_ehex


class CharacterSummary(BaseModel):
    name: str
    age: int = 18
    sophont: Sophont
    homeworld: TravellerMapWorld
    birthworld: TravellerMapWorld | None = None

    @model_validator(mode='after')
    def _default_birthworld(self) -> CharacterSummary:
        if self.birthworld is None:
            self.birthworld = self.homeworld
        return self

    characteristics: dict[Chars, int] = Field(default_factory=dict)
    psionics: Psionics | None = None
    last_career: CareerData | None = None
    last_career_ejected: bool = False  # True when last_career ended via mishap ejection
    last_assignment: AssignmentData | None = None
    rank: int | None = None
    career_terms: list[CareerTerm] = Field(default_factory=list)
    drafted: bool = False
    skills: list[AnySkill] = Field(default_factory=list)
    connections: list[AnyConnection] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    narrative: list[str] = Field(default_factory=list)
    cash: int = 0
    dead: bool = False
    precareer: str | None = None  # pre-career currently in progress
    precareer_completed: str | None = None  # pre-career that was attended (whether graduated or not)
    precareer_skills: list[SerializeAsAny[AnySkill]] = Field(
        default_factory=list
    )  # skills chosen during university (for graduation boost)
    parole_threshold: int | None = None  # Prisoner career: current Parole Threshold (3-12)

    @property
    def current_career(self) -> CareerData | None:
        if self.dead or not self.career_terms:
            return None
        last = self.career_terms[-1]
        mo = last.muster_out
        if mo is None or mo.used or mo.pending_setup or mo.rolls_remaining > 0:
            return None
        return last.career

    @property
    def current_assignment(self) -> AssignmentData | None:
        if self.dead or not self.career_terms:
            return None
        last = self.career_terms[-1]
        mo = last.muster_out
        if mo is None or mo.used or mo.pending_setup or mo.rolls_remaining > 0:
            return None
        return last.assignment

    @property
    def ucp(self) -> str | None:
        if any(stat not in self.characteristics for stat in self.sophont.ucp_stats):
            return None
        return ''.join(int_to_ehex(self.characteristics[stat]) for stat in self.sophont.ucp_stats)

    @property
    def latest_career(self) -> CareerData | None:
        return self.current_career or self.last_career

    def latest_career_run_terms(self, career: CareerData) -> list[CareerTerm]:
        terms: list[CareerTerm] = []
        for term in reversed(self.career_terms):
            if term.career != career:
                break
            terms.append(term)
        return list(reversed(terms))

    def current_term(self) -> CareerTerm:
        if not self.career_terms:
            raise ReplayError('No current career term')
        return self.career_terms[-1]

    def test_psionic_strength(self, *, raw_roll: int, terms_served: int) -> int:
        psi, psionics = Psionics.from_strength_test(raw_roll=raw_roll, terms_served=terms_served)
        if psi == 0:
            self.characteristics.pop(Chars.PSI, None)
            self.psionics = None
            return 0
        self.characteristics[Chars.PSI] = psi
        self.psionics = psionics
        return psi

    @property
    def rank_title(self) -> tuple[str, str]:
        if self.rank is None:
            return ('0', '')
        if not self.career_terms:
            return (str(self.rank), '')
        term = self.career_terms[-1]
        return term.career.rank_title(term.commission, self.rank, term.assignment)

    @property
    def benefits(self) -> list[ItemBenefit]:
        return [benefit for term in self.career_terms if term.muster_out for benefit in term.muster_out.benefits]

    @property
    def muster_out_cash_count(self) -> int:
        return sum(term.muster_out.cash_count for term in self.career_terms if term.muster_out)

    def add_muster_out_benefit(self, benefit: ItemBenefit) -> None:
        self.current_term().require_muster_out().benefits.append(benefit)

    def record_muster_out_cash_roll(self) -> None:
        self.current_term().require_muster_out().cash_count += 1

    def terms_started(self, *, only_current_career: bool, include_precareer: bool) -> int:
        terms = self.career_terms
        if only_current_career:
            career = self.current_career
            terms = self.latest_career_run_terms(career) if career is not None else []
        count = len(terms)
        if include_precareer and (self.precareer is not None or self.precareer_completed is not None):
            count += 1
        return count

    @property
    def terms_started_in_current_career(self) -> int:
        return self.terms_started(only_current_career=True, include_precareer=False)

    @property
    def terms_started_in_all_careers(self) -> int:
        return self.terms_started(only_current_career=False, include_precareer=False)

    @property
    def terms_started_in_pre_and_careers(self) -> int:
        return self.terms_started(only_current_career=False, include_precareer=True)

    @overload
    def skill_level(self, skill_cls: type[Skill], default: int) -> int: ...
    @overload
    def skill_level(self, skill_cls: type[Skill], default: None = None) -> int | None: ...
    def skill_level(self, skill_cls: type[Skill], default: int | None = None) -> int | None:
        for skill in self.skills:
            if type(skill) is skill_cls:
                fields = level_fields(skill_cls)
                if not fields:
                    return 0
                return max(getattr(skill, f).value for f in fields)
        return default

    def diff(self, other: CharacterSummary) -> list[str]:
        changes: list[str] = []

        changes.extend(other.narrative[len(self.narrative) :])

        if other.current_career != self.current_career and other.current_career:
            line = f'Joined {other.current_career.name}'
            if other.current_assignment:
                line += f' ({other.current_assignment.name})'
            changes.append(line)

        before_rt = self.rank_title
        after_rt = other.rank_title
        if other.rank is not None and after_rt != before_rt:
            b_code, b_title = before_rt
            a_code, a_title = after_rt
            b_display = f'{b_code} {b_title}'.strip() if b_title else b_code
            a_display = f'{a_code} {a_title}'.strip() if a_title else a_code
            changes.append(f'Rank {b_display} → {a_display}')

        all_chars = set(self.characteristics) | set(other.characteristics)
        for char in sorted(all_chars, key=lambda c: c.value):
            b_val = self.characteristics.get(char, 0)
            a_val = other.characteristics.get(char, 0)
            if a_val != b_val:
                changes.append(f'{char.value} {b_val} → {a_val}')

        before_by_type = {type(s): s for s in self.skills}
        after_by_type = {type(s): s for s in other.skills}
        new_types = sorted(set(after_by_type) - set(before_by_type), key=lambda cls: cls.name())
        changes.extend(f'Gained {cls.name()} {other.skill_level(cls, 0)}' for cls in new_types)
        for cls in sorted(set(after_by_type) & set(before_by_type), key=lambda cls: cls.name()):
            b_lvl = self.skill_level(cls, 0)
            a_lvl = other.skill_level(cls, 0)
            if a_lvl != b_lvl:
                changes.append(f'{cls.name()} {b_lvl} → {a_lvl}')

        if other.cash != self.cash:
            delta = other.cash - self.cash
            sign = '+' if delta > 0 else ''
            changes.append(f'Cash {sign}Cr{delta:,}')

        changes.extend(f'Benefit: {b.display_label}' for b in other.benefits[len(self.benefits) :])
        changes.extend(
            f'New {c.display_name}: {c.origin or "unknown"}' for c in other.connections[len(self.connections) :]
        )
        changes.extend(f'Problem: {p}' for p in other.problems[len(self.problems) :])

        return changes


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary
    pending_inputs: list[SerializeAsAny[Annotated[PendingInputBase, BeforeValidator(_deserialise_pending_input)]]] = (
        Field(default_factory=list)
    )
    pending_advancement_dm: int = 0
    pending_qualification_dm: int = 0
    auto_qualify_careers: list[str] = Field(default_factory=list)
    pending_reenlist: bool | None = None  # stores reenlist decision during aging chain
    forced_next_career: CareerData | None = None  # set by prison-sending events; consumed by next career choice
    prisoner_freed: bool = False  # set by _apply_prisoner_advancement when parole granted
    forced_stay: bool = False  # natural 12 on advancement: character must stay this term
    forced_leave: bool = False  # advancement roll ≤ terms: character must leave this term

    def add_connection(self, kind: Any, *, origin: str = '') -> None:
        from ceres.character.domain.connection import make_connection
        from ceres.character.domain.connection_events import PendingConnectionName

        self.summary.connections.append(
            make_connection(kind, term=self.summary.terms_started_in_pre_and_careers, origin=origin)
        )
        conn_idx = len(self.summary.connections) - 1
        kind_label = kind.value.replace('connection_', '').title()
        self.pending_inputs.append(
            PendingConnectionName(
                pending_id=f'connection_name_{conn_idx}',
                connection_index=conn_idx,
                connection_kind=kind,
                note_prefill=origin,
                instruction=f'Name this {kind_label} ({origin})',
            )
        )

    def has_blocking_pending(self) -> bool:
        return any(p.blocking for p in self.pending_inputs)

    def clear_current_career(self, ejected: bool = False) -> None:
        if self.summary.current_career is not None:
            self.summary.last_career = self.summary.current_career
            self.summary.last_career_ejected = ejected
            self.summary.last_assignment = self.summary.current_assignment

    def get_current_career(self) -> CareerData:
        current = self.summary.current_career
        if current is None:
            raise ReplayError('No active career')
        return current

    def fulfill_pending(self, event: Any) -> None:
        fulfills = event.fulfills
        matched = next((p for p in self.pending_inputs if p.pending_id == fulfills), None)
        if matched is None:
            raise ReplayError(f'Event {event.id} ({event.kind!r}) references unknown pending input {fulfills!r}')
        self.pending_inputs.remove(matched)

    def skill_choices(
        self,
        skill_types: list[type[Skill]],
        level: int | None,
    ) -> list[AnySkill]:
        choices: list[AnySkill] = []
        for skill_cls in skill_types:
            existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
            fields = level_fields(skill_cls)
            _cls: Any = skill_cls
            if len(fields) == 1 and fields[0] == 'level':
                # Non-specialised skill
                current = getattr(existing, fields[0]).value if existing is not None else None
                if level is None:
                    if current is None or current < 4:
                        new_level = 1 if current is None else current + 1
                        choices.append(cast(AnySkill, _cls(level=Level(value=new_level))))
                else:
                    actual = current if current is not None else -1
                    if actual < level:
                        choices.append(cast(AnySkill, _cls(level=Level(value=level))))
            # Specialised skill
            elif level == 0:
                # Level-0 grant adds the whole type if absent
                if existing is None:
                    choices.append(cast(AnySkill, _cls()))
            elif level is None:
                # Increment — one choice per specialization field
                for field in fields:
                    current = getattr(existing, field).value if existing is not None else 0
                    if current < 4:
                        choices.append(cast(AnySkill, _cls(**{field: Level(value=current + 1)})))
            else:
                # Fixed level > 0 — one choice per spec currently below target
                for field in fields:
                    current = getattr(existing, field).value if existing is not None else 0
                    if current < level:
                        choices.append(cast(AnySkill, _cls(**{field: Level(value=level)})))
        return choices

    def grant_skill(self, skill: AnySkill) -> None:
        skill_cls = type(skill)
        existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
        if existing is None:
            self.summary.skills.append(skill_cls())
            existing = self.summary.skills[-1]
        for field in level_fields(skill_cls):
            given = getattr(skill, field).value
            if given > 0:
                current = getattr(existing, field).value
                getattr(existing, field).set(max(current, given))

    def increment_skill(self, skill: AnySkill) -> None:
        skill_cls = type(skill)
        existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
        fields = level_fields(skill_cls)
        active_field = next((f for f in fields if getattr(skill, f).value > 0), None)
        target_field = active_field or (fields[0] if fields else None)
        if existing is None:
            new_skill = skill_cls()
            if target_field:
                getattr(new_skill, target_field).set(1)
            self.summary.skills.append(new_skill)
            return
        if (active_field is not None or len(fields) == 1) and target_field:
            current = getattr(existing, target_field).value
            if current < 4:
                getattr(existing, target_field).set(current + 1)

    def check_skill_choice(
        self,
        skill_types: list[type[Skill]],
        level: int | None,
        choice: AnySkill,
    ) -> bool:
        return choice in self.skill_choices(skill_types, level)


def diff_summaries(before: CharacterSummary, after: CharacterSummary) -> list[str]:
    return before.diff(after)
