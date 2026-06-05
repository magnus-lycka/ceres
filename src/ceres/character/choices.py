"""Registry of all concrete ChoiceBase subclasses; assembles the AnyChoice discriminated union."""

from typing import Annotated

from pydantic import Field

from ceres.character.careers.agent import (
    AgentMishap2Accept,
    AgentMishap2Refuse,
    AgentMishap5Ally,
    AgentMishap5Contact,
    AgentMishap5Family,
)
from ceres.character.careers.army import (
    ArmyMishap4Cooperate,
    ArmyMishap4JoinRing,
)
from ceres.character.careers.citizen import (
    CitizenEvent8DoSo,
    CitizenEvent8GainContact,
    CitizenEvent8GainDeception,
    CitizenEvent8GainStreetwise,
    CitizenEvent8Refuse,
    CitizenMishap4Cooperate,
    CitizenMishap4Resist,
)
from ceres.character.careers.drifter import (
    DrifterEvent3Accept,
    DrifterEvent3Decline,
    DrifterEvent9Accept,
    DrifterEvent9Decline,
    DrifterEvent9Injury,
    DrifterEvent9Prison,
)
from ceres.character.careers.entertainer import (
    EntertainerEvent8Accept,
    EntertainerEvent8Refuse,
)
from ceres.character.careers.marines import (
    MarinesEvent9Protect,
    MarinesEvent9Report,
    MarinesMishap4Accept,
    MarinesMishap4Refuse,
)
from ceres.character.careers.merchant import (
    MerchantEvent3Accept,
    MerchantEvent3Refuse,
)
from ceres.character.careers.navy import (
    NavyEvent10Profit,
    NavyEvent10Refuse,
    NavyMishap4NotResponsible,
    NavyMishap4Responsible,
)
from ceres.character.careers.noble import (
    NobleEvent8Accept,
    NobleEvent8Refuse,
)
from ceres.character.careers.prisoner import (
    PrisonerEvent3Attempt,
    PrisonerEvent3Stay,
    PrisonerEvent7Gang,
    PrisonerEvent7GoodBehaviour,
    PrisonerEvent7ParoleHearing,
    PrisonerEvent7Riot,
    PrisonerEvent7Transfer,
    PrisonerEvent7Visitation,
    PrisonerEvent9Decline,
    PrisonerEvent9Level1,
    PrisonerEvent9Level2,
    PrisonerEvent9Level3,
    PrisonerEvent12Refuse,
    PrisonerEvent12TakeRisk,
    PrisonerMishap3Fight,
    PrisonerMishap3Submit,
)
from ceres.character.careers.rogue import (
    RogueEvent3Defend,
    RogueEvent3Lawyer,
    RogueEvent6Backstab,
    RogueEvent6Refuse,
    RogueMishap3RollOther,
    RogueMishap3RollTwo,
)
from ceres.character.careers.scholar import (
    ScholarEvent3Accept,
    ScholarEvent3Decline,
    ScholarEvent8Accept,
    ScholarEvent8Refuse,
    ScholarMishap3Openly,
    ScholarMishap3Secretly,
    ScholarMishap5GiveUp,
    ScholarMishap5StartAgain,
)

type AnyChoice = Annotated[
    AgentMishap2Accept
    | AgentMishap2Refuse
    | AgentMishap5Ally
    | AgentMishap5Contact
    | AgentMishap5Family
    | ArmyMishap4Cooperate
    | ArmyMishap4JoinRing
    | CitizenEvent8DoSo
    | CitizenEvent8GainContact
    | CitizenEvent8GainDeception
    | CitizenEvent8GainStreetwise
    | CitizenEvent8Refuse
    | CitizenMishap4Cooperate
    | CitizenMishap4Resist
    | DrifterEvent3Accept
    | DrifterEvent3Decline
    | DrifterEvent9Accept
    | DrifterEvent9Decline
    | DrifterEvent9Injury
    | DrifterEvent9Prison
    | EntertainerEvent8Accept
    | EntertainerEvent8Refuse
    | MarinesEvent9Protect
    | MarinesEvent9Report
    | MarinesMishap4Accept
    | MarinesMishap4Refuse
    | MerchantEvent3Accept
    | MerchantEvent3Refuse
    | NavyEvent10Profit
    | NavyEvent10Refuse
    | NavyMishap4NotResponsible
    | NavyMishap4Responsible
    | NobleEvent8Accept
    | NobleEvent8Refuse
    | PrisonerEvent12Refuse
    | PrisonerEvent12TakeRisk
    | PrisonerEvent3Attempt
    | PrisonerEvent3Stay
    | PrisonerEvent7Gang
    | PrisonerEvent7GoodBehaviour
    | PrisonerEvent7ParoleHearing
    | PrisonerEvent7Riot
    | PrisonerEvent7Transfer
    | PrisonerEvent7Visitation
    | PrisonerEvent9Decline
    | PrisonerEvent9Level1
    | PrisonerEvent9Level2
    | PrisonerEvent9Level3
    | PrisonerMishap3Fight
    | PrisonerMishap3Submit
    | RogueEvent3Defend
    | RogueEvent3Lawyer
    | RogueEvent6Backstab
    | RogueEvent6Refuse
    | RogueMishap3RollOther
    | RogueMishap3RollTwo
    | ScholarEvent3Accept
    | ScholarEvent3Decline
    | ScholarEvent8Accept
    | ScholarEvent8Refuse
    | ScholarMishap3Openly
    | ScholarMishap3Secretly
    | ScholarMishap5GiveUp
    | ScholarMishap5StartAgain,
    Field(discriminator='kind'),
]
