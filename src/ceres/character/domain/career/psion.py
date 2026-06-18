from typing import Any, ClassVar, Literal, cast

from ceres.character.domain.benefits import (
    COMBAT_IMPLANT,
    CONTACT,
    GUN,
    SHIP_SHARE,
    TAS_MEMBERSHIP,
)
from ceres.character.domain.career.career_data import (
    AdvancementDmEffect,
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    CareerData,
    CareerEventEntry,
    CareerHandlerBase,
    CareerSkillOption,
    CareerSkillTables,
    CharCheck,
    DecreaseCharacteristicEffect,
    GainAllyEffect,
    GainContactEffect,
    LifeEventEffect,
    MishapEntry,
    MusterOutData,
    MusterOutRow,
    RankBonus,
    RankEntry,
    RollMishapEffect,
    SkillChoiceEffect,
    SkillTable,
    _blank_ranks,
)
from ceres.character.domain.career.career_events import (
    PendingChoices,
    PendingSkillChoice,
    _advancement_pending,
    _apply_mishap_ejection,
)
from ceres.character.domain.career.common import CommonMishap1Handler
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection import Ally, Contact, make_connection
from ceres.character.domain.health.health_events import (
    PendingInjuryTable,
)
from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeOffered
from ceres.character.domain.psionics import (
    Awareness,
    Clairvoyance,
    Psi,
    Telekinesis,
    Telepathy,
    Teleportation,
    psionic_talent_instances,
    queue_psionic_institute_training,
)
from ceres.character.domain.skills import (
    AnySkill,
    ArtSkill,
    Athletics,
    Deception,
    Electronics,
    GunCombat,
    JackOfAllTrades,
    LanguageSkill,
    Leadership,
    Level,
    LifeScience,
    Mechanic,
    Medic,
    Melee,
    Persuade,
    Recon,
    ScienceSkill,
    Stealth,
    Streetwise,
    Survival,
    Tactics,
    VaccSuit,
    skill_instances,
)
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import ChoiceBase, PendingInputBase

_TALENTS: list[Psi] = [Psi(talent) for talent in psionic_talent_instances()]
_ALL_NON_JOT_SKILLS: list[AnySkill] = [
    cast(AnySkill, skill) for skill in skill_instances(AnySkill) if not isinstance(skill, JackOfAllTrades)
]


class PsionIncreasePsiHandler(CareerHandlerBase):
    type: Literal['psion_increase_psi'] = 'psion_increase_psi'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        psi = projection.summary.characteristics.get(Chars.PSI, 0)
        projection.summary.characteristics[Chars.PSI] = psi + 1
        career = projection.get_current_career()
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment, event_id, pending_idx)
        )
        return pending_idx + 1


class PendingPsionAdvancedTraining(CareerSkillRollPendingBase):
    kind: Literal['psion_advanced_training'] = 'psion_advanced_training'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction='Choose any skill except Jack-of-All-Trades to gain at level 1',
                    options=_ALL_NON_JOT_SKILLS,
                )
            )


class PsionAdvancedTrainingHandler(CareerHandlerBase):
    type: Literal['psion_advanced_training_request'] = 'psion_advanced_training_request'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPsionAdvancedTraining(
                pending_id=(event_id, pending_idx),
                instruction='Roll EDU 8+ to gain any skill except Jack-of-All-Trades',
                options=[Chars.EDU],
            )
        )
        return pending_idx + 1


class PsionMishap4Accept(ChoiceBase):
    kind: Literal['psion_mishap_4_accept'] = 'psion_mishap_4_accept'
    label: str = 'Accept (continue in Psion career and gain an Enemy)'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.add_connection(ConnectionKind.ENEMY, origin='Unethical psionic work')
        career = projection.get_current_career()
        projection.pending_inputs.append(_advancement_pending(career, projection.summary.current_assignment, event.id))


class PsionMishap4Refuse(ChoiceBase):
    kind: Literal['psion_mishap_4_refuse'] = 'psion_mishap_4_refuse'
    label: str = 'Refuse (leave Psion career)'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class PsionMishap4Handler(CareerHandlerBase):
    type: Literal['psion_mishap_4'] = 'psion_mishap_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Use your psionic powers unethically?',
                choices=[PsionMishap4Accept(), PsionMishap4Refuse()],
            )
        )
        return pending_idx + 1


class PsionMishap3RollHandler(EventHandlerBase):
    kind: Literal['psion_mishap_3_roll_result'] = 'psion_mishap_3_roll_result'
    roll: int

    def apply(self, projection: CharacterProjection, event: Event, fulfilled_pending: Any = None) -> None:
        pending_idx = 0
        if self.roll <= 2:
            projection.pending_inputs.append(
                PendingInjuryTable(pending_id=(event.id, pending_idx), instruction='Roll 1D on Injury table')
            )
            pending_idx += 1
        elif self.roll <= 4:
            projection.summary.characteristics[Chars.SOC] = max(
                0, projection.summary.characteristics.get(Chars.SOC, 0) - 1
            )
        _apply_mishap_ejection(projection, event.id, pending_idx, lose_current_term=True)


class PendingPsionMishap3Roll(PendingInputBase):
    kind: Literal['psion_mishap_3_roll'] = 'psion_mishap_3_roll'

    def event_from_form(self, form: Any) -> Event:
        return Event(fulfills=self.pending_id, handler=PsionMishap3RollHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D anti-psi attack result', min=1, max=6)]


class PsionMishap3Handler(CareerHandlerBase):
    type: Literal['psion_mishap_3'] = 'psion_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPsionMishap3Roll(
                pending_id=(event_id, pending_idx),
                instruction='Roll 1D for the result of the anti-psi attack',
            )
        )
        return pending_idx + 1


class PsionConnectionConvertedHandler(EventHandlerBase):
    kind: Literal['psion_connection_converted'] = 'psion_connection_converted'
    connection_index: int
    new_kind: ConnectionKind
    continue_term: bool = False

    def apply(self, projection: CharacterProjection, event: Event, fulfilled_pending: Any = None) -> None:
        connections = projection.summary.connections
        if 0 <= self.connection_index < len(connections) and isinstance(
            connections[self.connection_index], (Contact, Ally)
        ):
            old = connections[self.connection_index]
            connections[self.connection_index] = make_connection(
                self.new_kind, term=old.term, origin=old.origin, name=old.name, note=old.note
            )
        else:
            projection.add_connection(self.new_kind, origin='Psion career')
        if self.continue_term and projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id)
            )


class PendingPsionConnectionConversion(PendingInputBase):
    kind: Literal['psion_connection_conversion'] = 'psion_connection_conversion'
    new_kind: ConnectionKind
    continue_term: bool = False

    def event_from_form(self, form: Any) -> Event:
        return Event(
            fulfills=self.pending_id,
            handler=PsionConnectionConvertedHandler(
                connection_index=form_int(form, 'connection_index', -1),
                new_kind=self.new_kind,
                continue_term=self.continue_term,
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [
            (f'{connection.display_name}: {connection.origin}', str(index))
            for index, connection in enumerate(projection.summary.connections)
            if isinstance(connection, (Contact, Ally))
        ]
        if not options:
            options = [('No represented Contact or Ally; add new connection', '-1')]
        return [Select(name='connection_index', label='Connection to change', options=options)]


class PsionMishap6Handler(CareerHandlerBase):
    type: Literal['psion_mishap_6'] = 'psion_mishap_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPsionConnectionConversion(
                pending_id=(event_id, pending_idx),
                instruction='Choose the former friend who becomes an Enemy',
                new_kind=ConnectionKind.ENEMY,
            )
        )
        return pending_idx + 1


class PsionEvent3Handler(CareerHandlerBase):
    type: Literal['psion_event_3'] = 'psion_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPsionConnectionConversion(
                pending_id=(event_id, pending_idx),
                instruction='Choose the Contact or Ally who becomes a Rival',
                new_kind=ConnectionKind.RIVAL,
                continue_term=True,
            )
        )
        return pending_idx + 1


class PsionEvent5Benefit(ChoiceBase):
    kind: Literal['psion_event_5_benefit'] = 'psion_event_5_benefit'
    label: str = 'Gain an extra Benefit roll'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.summary.career_terms[-1].require_muster_out().extra_rolls += 1
        career = projection.get_current_career()
        projection.pending_inputs.append(_advancement_pending(career, projection.summary.current_assignment, event.id))


class PsionEvent5Soc(ChoiceBase):
    kind: Literal['psion_event_5_soc'] = 'psion_event_5_soc'
    label: str = 'Gain SOC +1'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.summary.characteristics[Chars.SOC] = min(
            15, projection.summary.characteristics.get(Chars.SOC, 0) + 1
        )
        career = projection.get_current_career()
        projection.pending_inputs.append(_advancement_pending(career, projection.summary.current_assignment, event.id))


class PendingPsionEvent5Roll(CareerSkillRollPendingBase):
    kind: Literal['psion_event_5_roll'] = 'psion_event_5_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingChoices(
                    pending_id=(event.id, 0),
                    instruction='Choose the reward for successfully using your powers',
                    choices=[PsionEvent5Benefit(), PsionEvent5Soc()],
                )
            )
        else:
            projection.summary.characteristics[Chars.SOC] = max(
                0, projection.summary.characteristics.get(Chars.SOC, 0) - 1
            )


class PsionEvent5Accept(ChoiceBase):
    kind: Literal['psion_event_5_accept'] = 'psion_event_5_accept'
    label: str = 'Accept (roll PSI 8+)'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.pending_inputs.append(
            PendingPsionEvent5Roll(
                pending_id=(event.id, 0),
                instruction='Roll PSI 8+ to improve your standing',
                options=[Chars.PSI],
            )
        )


class PsionEvent5Refuse(ChoiceBase):
    kind: Literal['psion_event_5_refuse'] = 'psion_event_5_refuse'
    label: str = 'Refuse'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(_advancement_pending(career, projection.summary.current_assignment, event.id))


class PsionEvent5Handler(CareerHandlerBase):
    type: Literal['psion_event_5'] = 'psion_event_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Use your powers unethically to better your standing?',
                choices=[PsionEvent5Accept(), PsionEvent5Refuse()],
            )
        )
        return pending_idx + 1


class Psion(CareerData):
    type: Literal['PSION_CAREER'] = 'PSION_CAREER'

    name: ClassVar[str] = 'Psion'
    description: ClassVar[str] = (
        'A career for Travellers who choose to focus on their '
        'psionic potential instead of more conventional lifestyles.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.PSI, target=6)
    allows_assignment_change: ClassVar[bool] = False

    def is_selectable(self, projection=None) -> bool:
        if projection is None:
            return False
        if projection.summary.psionics is None:
            return False
        if self.name in projection.auto_qualify_careers:
            return True
        return projection.summary.characteristics.get(Chars.PSI, 0) >= 9

    def qualification_failed(self, projection: CharacterProjection, event_id: int) -> None:
        from ceres.character.domain.career.career_events import queue_career_choice_indexed

        projection.summary.problems.append('Failed to qualify for Psion; choose another career for this term.')
        queue_career_choice_indexed(projection, event_id, 0, 'Psion qualification failed — choose another career')

    def _basic_training_table_name(self, assignment: AssignmentData) -> str:
        return f'assignment{self.assignment_index(assignment)}'

    def skill_table_option_is_available(
        self,
        projection: CharacterProjection,
        table_name: str,
        option: CareerSkillOption,
    ) -> bool:
        if not isinstance(option, Psi):
            return True
        psionics = projection.summary.psionics
        possessed = psionics is not None and psionics.talent_level(type(option.talent)) is not None
        return possessed or table_name == 'service_skills'

    def start_new_term(
        self,
        projection: CharacterProjection,
        assignment: AssignmentData,
        event_id: int,
        is_continuation: bool = False,
    ) -> None:
        insert_at = len(projection.pending_inputs)
        super().start_new_term(projection, assignment, event_id, is_continuation)
        training_queued = queue_psionic_institute_training(projection, event_id, len(projection.pending_inputs))
        if training_queued:
            insert_at = 1
        if projection.summary.homeworld.uwp.startswith('X'):
            return
        used_sub_ids = {int(p.pending_id[1]) for p in projection.pending_inputs if p.pending_id[0] == event_id}
        homeworld_idx = max(used_sub_ids, default=-1) + 1
        projection.pending_inputs.insert(
            insert_at,
            PendingHomeworldChangeOffered(
                pending_id=(event_id, homeworld_idx),
                instruction='You may relocate to another world. Select a new homeworld (optional).',
                reason='Psion career: you may change homeworld at the start of each '
                'term if your current world has a starport.',
                source_kind='career_entry',
                source_career='Psion',
            ),
        )

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Wild Talent',
            description='You developed your powers without formal training.',
            survival=CharCheck(characteristic=Chars.SOC, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=8),
        ),
        AssignmentData(
            name='Adept',
            description='You are a scholar of the psionic disciplines.',
            survival=CharCheck(characteristic=Chars.EDU, target=4),
            advancement=CharCheck(characteristic=Chars.EDU, target=8),
        ),
        AssignmentData(
            name='Psi-Warrior',
            description='You combine combat training with psionic warfare.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.END, target=6),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable([Chars.EDU, Chars.INT, Chars.STR, Chars.DEX, Chars.END, Chars.PSI]),
        service_skills=SkillTable(
            [
                Psi(Telepathy()),
                Psi(Clairvoyance()),
                Psi(Telekinesis()),
                Psi(Awareness()),
                Psi(Teleportation()),
                _TALENTS,
            ]
        ),
        advanced_education=SkillTable(
            [
                skill_instances(LanguageSkill),
                skill_instances(ArtSkill),
                Electronics(),
                Medic(),
                skill_instances(ScienceSkill),
                Mechanic(),
            ],
            min_edu=8,
        ),
        assignment1=SkillTable(
            [Psi(Telepathy()), Psi(Telekinesis()), Deception(), Stealth(), Streetwise(), [Melee(), GunCombat()]]
        ),
        assignment2=SkillTable(
            [
                Psi(Telepathy()),
                Psi(Clairvoyance()),
                Psi(Awareness()),
                Medic(),
                Persuade(),
                skill_instances(ScienceSkill),
            ]
        ),
        assignment3=SkillTable(
            [Psi(Telepathy()), Psi(Awareness()), Psi(Teleportation()), GunCombat(), VaccSuit(), Recon()]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = _blank_ranks()
    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
        1: {
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, title='Survivor', bonus=RankBonus(choices=[Survival(), Streetwise()], level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, title='Witch', bonus=RankBonus(skill=Deception(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6),
        },
        2: {
            0: RankEntry(rank=0),
            1: RankEntry(
                rank=1,
                title='Initiate',
                bonus=RankBonus(skill=LifeScience(psionicology=Level(value=1)), level=1),
            ),
            2: RankEntry(rank=2),
            3: RankEntry(
                rank=3,
                title='Acolyte',
                bonus=RankBonus(choices=cast(list[CareerSkillOption], _TALENTS), level=1),
            ),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5),
            6: RankEntry(
                rank=6,
                title='Master',
                bonus=RankBonus(choices=cast(list[CareerSkillOption], _TALENTS), level=1),
            ),
        },
        3: {
            0: RankEntry(rank=0, title='Psi-Soldier'),
            1: RankEntry(rank=1, bonus=RankBonus(choices=[GunCombat()], level=1)),
            2: RankEntry(rank=2, title='Knight', bonus=RankBonus(skill=Leadership(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, title='Master of Wills', bonus=RankBonus(choices=[Tactics()], level=1)),
            6: RankEntry(rank=6),
        },
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=1000, benefit=GUN),
            2: MusterOutRow(cash=2000, benefit=SHIP_SHARE, count=2),
            3: MusterOutRow(cash=4000, benefit=CONTACT),
            4: MusterOutRow(cash=4000, benefit=TAS_MEMBERSHIP),
            5: MusterOutRow(cash=8000, benefit=CONTACT),
            6: MusterOutRow(cash=8000, benefit=COMBAT_IMPLANT),
            7: MusterOutRow(cash=16000, benefit=SHIP_SHARE, count=10),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured (this is the same as a result of 2 on the Injury table). '
            'Alternatively, roll twice on the Injury table and take the lower result.',
            defer_ejection=True,
            effects=[CommonMishap1Handler()],
        ),
        2: MishapEntry(
            text='You telepathically contact something dangerous. Lose one PSI. '
            'You also suffer from persistent and terrifying nightmares.',
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.PSI)],
        ),
        3: MishapEntry(
            text='An anti-psi cult or gang attempts to expose or attack you. Roll 1D: on a 1–2, you are injured, '
            'roll on the Injury table (see page 49). On a 3–4, lose one SOC. On a 5–6, nothing else happens '
            'but you still must leave this career.',
            defer_ejection=True,
            effects=[PsionMishap3Handler()],
        ),
        4: MishapEntry(
            text='You are asked to use your psionic powers in an unethical fashion. Accept and you may continue in '
            'this career but gain an Enemy. Refuse and you must leave the career.',
            defer_ejection=True,
            effects=[PsionMishap4Handler()],
        ),
        5: MishapEntry(
            text='You are experimented on by a corporation, government or other organisation. '
            'You escape but are forced to leave this career.',
        ),
        6: MishapEntry(
            text='Your gift causes a former friend to turn on you and betray you. '
            'One Ally or Contact becomes an Enemy.',
            effects=[PsionMishap6Handler()],
        ),
    }

    events: ClassVar[dict[int, CareerEventEntry]] = {
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='Your psionic abilities make you uncomfortable to be around. One Contact or Ally becomes a Rival.',
            effects=[PsionEvent3Handler()],
        ),
        4: CareerEventEntry(
            text='Choose one of these skills, reflecting your time spent mastering mind and body. '
            'Gain one of Athletics 1, Stealth 1, Survival 1 or Art 1.',
            effects=[
                SkillChoiceEffect(options=[Athletics(), Stealth(), Survival(), *skill_instances(ArtSkill)], level=1)
            ],
        ),
        5: CareerEventEntry(
            text='You have a chance to use your powers unethically to better your standing. If you accept, '
            'roll PSI 8+ If you succeed, gain an extra Benefit roll or +1 SOC. If you fail, lose one SOC.',
            effects=[PsionEvent5Handler()],
        ),
        6: CareerEventEntry(
            text='You make an unexpected connection outside your normal circles. Gain a Contact.',
            effects=[GainContactEffect()],
        ),
        7: CareerEventEntry(text='Life Event. Roll on the Life Events table.', effects=[LifeEventEffect()]),
        8: CareerEventEntry(
            text='You achieve a new level of psionic strength. Increase your PSI by +1.',
            effects=[PsionIncreasePsiHandler()],
        ),
        9: CareerEventEntry(
            text='You are given advanced training in a specialist field. '
            'Roll EDU 8+ to gain any one skill except Jack-of-all-Trades.',
            effects=[PsionAdvancedTrainingHandler()],
        ),
        10: CareerEventEntry(
            text='You pick up potentially useful information using your '
            'psychic powers. Gain DM+1 to any one Benefit roll.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        11: CareerEventEntry(
            text='You gain a mentor. Gain an Ally and DM+4 to your next '
            'advancement roll (in any career) thanks to their aid.',
            effects=[GainAllyEffect(), AdvancementDmEffect(amount=4)],
        ),
        12: CareerEventEntry(
            text='You achieve a new level of discipline in your powers. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    }


PSION = Psion()
