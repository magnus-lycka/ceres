from functools import cache

from ceres.character.careers.career_data import (
    CareerEventEntry,
    CharCheck,
    GainAllyEffect,
    GainConnectionsRolledEffect,
    GainEnemyEffect,
    GainRivalEffect,
    GainSkillEffect,
    LifeEventEffect,
    SkillChoiceEffect,
    SkillTableEntry,
)
from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.precareers.precareer_data import PreCareerData

_PRECAREER_EVENTS = {
    2: CareerEventEntry(text='Approached by an illegal psionic group.', effects=[]),
    3: CareerEventEntry(text='Your time in education is not happy and you fail to graduate.', effects=[]),
    4: CareerEventEntry(text='A prank goes wrong and someone gets hurt.', effects=[]),
    5: CareerEventEntry(
        text='Taking advantage of youth, you party as much as you study.',
        effects=[GainSkillEffect(skill='Carouse')],
    ),
    6: CareerEventEntry(
        text='You become involved in a tightly knit clique or group.',
        effects=[GainConnectionsRolledEffect(connection_type=ConnectionKind.ALLY, dice='d3')],
    ),
    7: CareerEventEntry(text='Life Event.', effects=[LifeEventEffect()]),
    8: CareerEventEntry(
        text='You join a political movement.',
        effects=[GainAllyEffect(), GainEnemyEffect()],
    ),
    9: CareerEventEntry(
        text='You develop a healthy interest in a hobby or other area of study.',
        effects=[SkillChoiceEffect(options=[], level=0)],
    ),
    10: CareerEventEntry(
        text='A tutor rubs you up the wrong way and you overturn their conclusions.',
        effects=[GainRivalEffect()],
    ),
    11: CareerEventEntry(text='War comes and a wide-ranging draft is instigated.', effects=[]),
    12: CareerEventEntry(text='You gain wide-ranging recognition.', effects=[]),
}

_UNIVERSITY_SKILLS = [
    SkillTableEntry(skill='Admin'),
    SkillTableEntry(skill='Advocate'),
    SkillTableEntry(skill='Animals', choices=['Animals']),
    SkillTableEntry(skill='Art'),
    SkillTableEntry(skill='Astrogation'),
    SkillTableEntry(skill='Electronics'),
    SkillTableEntry(skill='Engineer'),
    SkillTableEntry(skill='Language'),
    SkillTableEntry(skill='Medic'),
    SkillTableEntry(skill='Navigation'),
    SkillTableEntry(skill='Profession'),
    SkillTableEntry(skill='Science'),
]

_COLONIAL_SKILLS = [
    SkillTableEntry(skill='Animals', level=0),
    SkillTableEntry(skill='Athletics', level=0),
    SkillTableEntry(skill='Drive', level=0),
    SkillTableEntry(skill='Gun Combat', level=0),
    SkillTableEntry(skill='Mechanic', level=0),
    SkillTableEntry(skill='Medic', level=0),
    SkillTableEntry(skill='Navigation', level=0),
    SkillTableEntry(skill='Recon', level=0),
    SkillTableEntry(skill='Profession', level=0),
    SkillTableEntry(skill='Seafarer', level=0),
    SkillTableEntry(skill='Survival', level=1),
]

_SCHOOL_OF_HARD_KNOCKS_SKILLS = [
    SkillTableEntry(skill='Streetwise', level=1),
    SkillTableEntry(skill='Athletics', level=0),
    SkillTableEntry(skill='Deception', level=0),
    SkillTableEntry(skill='Drive', level=0),
    SkillTableEntry(skill='Gambler', level=0),
    SkillTableEntry(skill='Melee', level=0),
    SkillTableEntry(skill='Persuade', level=0),
    SkillTableEntry(skill='Stealth', level=0),
]

_SPACER_COMMUNITY_SKILLS = [
    SkillTableEntry(skill='Vacc Suit', level=1),
    SkillTableEntry(skill='Astrogation', level=0),
    SkillTableEntry(skill='Electronics', level=0),
    SkillTableEntry(skill='Engineer', level=0),
    SkillTableEntry(skill='Profession', level=0),
]


def _military_academy(name: str, tied_career: str, entry: CharCheck) -> PreCareerData:
    return PreCareerData(
        name=name,
        source='Core',
        entry=entry,
        entry_term_dms={2: -2, 3: -4},
        service_skills_from=tied_career,
        tied_career=tied_career,
        graduation=CharCheck(characteristic=Chars.INT, target=7),
        graduation_dms={'END_8+': 1, 'SOC_8+': 1},
        honours_target=11,
        graduation_benefits=[
            'If entering the tied military career, select any three Service Skills and increase them to level 1',
            'Increase EDU by +1',
            'If graduating with honours, increase SOC by +1',
            'Automatic entry into the tied military career if it is first attempted after graduation',
            'Commission roll before first term of a military career, with DM+2; honours makes it automatic',
        ],
        events=_PRECAREER_EVENTS,
    )


@cache
def load_precareers() -> dict[str, PreCareerData]:
    precareers = [
        PreCareerData(
            name='University',
            source='Core',
            entry=CharCheck(characteristic=Chars.EDU, target=6),
            entry_term_dms={2: -1, 3: -2},
            entry_soc_bonus_min=9,
            entry_soc_bonus=1,
            skill_choices=_UNIVERSITY_SKILLS,
            graduation=CharCheck(characteristic=Chars.INT, target=6),
            honours_target=10,
            graduation_benefits=[
                'Increase both chosen skills by one level',
                'Increase EDU by an additional +1',
                'DM+1, or DM+2 with honours, to qualify for listed careers',
                'Commission roll before first term of a military career after university',
            ],
            events=_PRECAREER_EVENTS,
        ),
        _military_academy('Army Academy', 'Army', CharCheck(characteristic=Chars.END, target=7)),
        _military_academy('Marine Academy', 'Marines', CharCheck(characteristic=Chars.END, target=8)),
        _military_academy('Navy Academy', 'Navy', CharCheck(characteristic=Chars.INT, target=8)),
        PreCareerData(
            name='Colonial Upbringing',
            source='Companion',
            entry_requirement='Automatic if homeworld is TL8-',
            skill_choices=_COLONIAL_SKILLS,
            graduation=CharCheck(characteristic=Chars.INT, target=8),
            graduation_dms={'END_8+': 1},
            honours_target=12,
            graduation_benefits=[
                'Increase one skill already gained at level 0 to level 1',
                'Gain any two other listed skills at level 1 or increase one skill already possessed',
                'Gain Jack-of-all-Trades 1',
                'Honours graduates gain Leadership 1 and may increase another level 0 skill to level 1',
                'Increase END by +1 and decrease EDU by -D3',
                'Age is 22+2D3 when entering the first career',
            ],
            events=_PRECAREER_EVENTS,
        ),
        PreCareerData(
            name='Merchant Academy',
            source='Companion',
            entry=CharCheck(characteristic=Chars.INT, target=9),
            entry_soc_bonus_min=8,
            entry_soc_bonus=1,
            curricula=['Business', 'Shipboard'],
            graduation=CharCheck(characteristic=Chars.INT, target=7),
            graduation_dms={'EDU_8+': 1, 'SOC_8+': 1},
            honours_target=11,
            graduation_benefits=[
                'Increase one skill from the chosen Broker or Merchant Marine table to level 1',
                'Increase EDU by +1',
                'Automatic entry into Merchant or Citizen at rank 1 if first career and appropriate branch',
                'Honours graduates may enter those careers at rank 2',
                'DM+1 to advancement checks in Merchant or Citizen; DM+2 with honours',
            ],
            events=_PRECAREER_EVENTS,
        ),
        PreCareerData(
            name='Psionic Community',
            source='Companion',
            entry_requirement='PSI 8+, DM+1 if INT 8+',
            skill_choices=[
                SkillTableEntry(skill='Profession', level=0),
                SkillTableEntry(skill='Science', level=0),
                SkillTableEntry(skill='Streetwise', level=0),
            ],
            graduation_requirement='PSI 6+, DM+1 if INT 8+',
            honours_target=12,
            graduation_benefits=[
                'Increase PSI by +1',
                'Skill level 1 in any one talent possessed',
                'Science (psionicology) 1',
                'Honours graduates gain all acquired talents at level 1 and may advance one to level 2',
                'Automatic enlistment in Psion career, even after intervening careers',
                'Gain a Rival, or an Enemy with honours',
            ],
            events=_PRECAREER_EVENTS,
        ),
        PreCareerData(
            name='School of Hard Knocks',
            source='Companion',
            entry_requirement='Automatic if SOC 6-',
            skill_choices=_SCHOOL_OF_HARD_KNOCKS_SKILLS,
            graduation=CharCheck(characteristic=Chars.INT, target=7),
            graduation_dms={'END_9+': 1},
            honours_target=11,
            graduation_benefits=[
                'Gain any three other listed skills at level 0',
                'Gain Gun Combat 0',
                'Honours graduates gain Carouse 1 and may increase another level 0 skill to level 1',
                'Decrease SOC by -1',
                'DM-2 on promotion or commission checks in first career unless leaving by choice',
            ],
            events=_PRECAREER_EVENTS,
        ),
        PreCareerData(
            name='Spacer Community',
            source='Companion',
            entry_requirement='Automatic if homeworld size code 0; INT 4+, DM+1 if DEX 8+',
            skill_choices=_SPACER_COMMUNITY_SKILLS,
            graduation=CharCheck(characteristic=Chars.INT, target=8),
            graduation_dms={'DEX_6+': 1},
            honours_target=12,
            graduation_benefits=[
                'Gain any two other listed skills at level 0',
                'Gain any listed skill at level 1',
                'Gain Pilot 0',
                'Honours graduates gain Jack-of-all-Trades 1',
                'Increase DEX by +1 and decrease SOC by -2',
                'DM+1 to enlist, gain commission or promotion in Merchant (Free Trader)',
            ],
            events=_PRECAREER_EVENTS,
        ),
    ]
    return {precareer.name: precareer for precareer in precareers}


__all__ = ['load_precareers']
