"""Creation history through real career decisions and replay."""

from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, Engineer, Level, Mechanic, Pilot
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, MOCK_WORLD_2, CharacterDriver


def merchant(ucp='7869A5'):
    return (
        CharacterDriver()
        .start(VILANI, MOCK_WORLD)
        .ucp(ucp)
        .background_skills([Admin(), Athletics(), Carouse(), Drive()])
        .career('Merchant', 'Merchant Marine', roll=9)
    )


def merchant_in_term(number, ucp='7869A5'):
    character = merchant(ucp)
    for term in range(1, number):
        character.survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7).advancement(max(5, term + 1))
        if term >= 4:
            character.aging_roll(12)
        character.reenlist(True)
    return character


def merchant_at_ageing(ucp='7869A5'):
    return merchant_in_term(4, ucp).survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7).advancement(5)


def test_training_history_shows_the_story_and_outstanding_check():
    character = merchant().survive(7).term_event(9)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): You are given advanced training in a specialist field. '
        'In progress: Roll EDU 8+ to increase any one skill you already have by one level'
    ]


def test_failed_training_records_the_check_result_and_has_no_outstanding_choice():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): You are given advanced training in a specialist field. '
        'Failed the EDU check (7 against 8+).'
    ]


def test_successful_training_keeps_the_check_result_while_awaiting_the_skill():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=8)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): You are given advanced training in a specialist field. '
        'Passed the EDU check (8 against 8+). '
        'In progress: Advanced training: increase any existing skill by one level'
    ]


def test_completed_training_records_the_actual_skill_in_the_same_entry():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=8)
    character.choose_skill(Admin(level=Level(value=1)))

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): You are given advanced training in a specialist field. '
        'Passed the EDU check (8 against 8+). Admin increased from 0 to 1.'
    ]


def test_skill_award_records_the_chosen_speciality():
    character = merchant().survive(7).term_event(4)
    character.choose_skill(Engineer(m_drive=Level(value=1)))

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Gain any one of these skills, reflecting your time spent dealing '
        'with suppliers and spacers. Engineer (M-Drive) increased from 0 to 1.'
    ]


def test_repeated_training_keeps_distinct_occurrences_and_speciality_levels():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=8)
    character.choose_skill(Engineer(m_drive=Level(value=1))).advancement(5).reenlist(True)
    character.survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=8)
    character.choose_skill(Engineer(j_drive=Level(value=1)))

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): You are given advanced training in a specialist field. '
        'Passed the EDU check (8 against 8+). Engineer (M-Drive) increased from 0 to 1.',
        'Term 2 event (Merchant): You are given advanced training in a specialist field. '
        'Passed the EDU check (8 against 8+). Engineer (J-Drive) increased from 0 to 1.',
    ]


def navy_at_muster_out():
    return (
        CharacterDriver()
        .start(VILANI, MOCK_WORLD)
        .ucp('7869A5')
        .background_skills([Admin(), Athletics(), Carouse(), Drive()])
        .career('Navy', 'Line/Crew', roll=9)
        .survive(7)
        .term_event(4)
        .commission(False)
        .advancement(4)
        .reenlist(False)
    )


def test_muster_out_choice_remains_pending_until_the_actual_benefit_is_chosen():
    character = navy_at_muster_out().muster_out('benefits', 1)
    assert character.projection.creation_history[-1] == (
        'Muster out (Navy). In progress: Choose one benefit: Personal Vehicle or Ship Share'
    )
    character.benefit_choice(1)
    assert character.projection.creation_history[-1] == 'Muster out (Navy). Gained Ship Share.'


def test_chosen_characteristic_benefit_records_the_actual_increase():
    character = navy_at_muster_out().muster_out('benefits', 3).benefit_choice(0)

    assert character.projection.creation_history[-1] == 'Muster out (Navy). EDU increased from 10 to 11.'


def test_automatic_promotion_records_rank_and_reward_while_training_remains_outstanding():
    character = merchant().survive(7).term_event(12)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Your business or ship thrives. You are automatically promoted. '
        'Promoted to rank 1 Senior Crewman. Mechanic increased from 0 to 1. '
        'In progress: Choose a skill table and roll 1D'
    ]


def test_promotion_training_finishes_with_the_chosen_speciality_not_the_next_term():
    character = merchant().survive(7).term_event(12).skill_table('advanced_education', 1)
    assert character.projection.creation_history[-1].endswith('In progress: Choose a specialization for Engineer')
    character.skill_table_choice(Engineer(power=Level(value=1)))

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Your business or ship thrives. You are automatically promoted. '
        'Promoted to rank 1 Senior Crewman. Mechanic increased from 0 to 1. '
        'Engineer (Power) increased from 0 to 1.'
    ]


def test_rank_reward_does_not_claim_an_increase_when_the_skill_is_already_known():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=8)
    character.choose_skill(Mechanic(level=Level(value=1))).advancement(5).reenlist(True)
    character.survive(7).term_event(12)

    assert character.projection.creation_history[-1] == (
        'Term 2 event (Merchant): Your business or ship thrives. You are automatically promoted. '
        'Promoted to rank 1 Senior Crewman. Mechanic remains at 1. '
        'In progress: Choose a skill table and roll 1D'
    )


def test_contact_name_completes_the_occurrence_even_though_naming_is_nonblocking():
    character = merchant().survive(7).term_event(6)
    assert 'In progress: Name this Contact' in character.projection.creation_history[-1]
    character.name_connection('Vessa', 'A supplier')

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): You make an unexpected connection outside your normal circles. '
        'Gain a Contact. Contact: Vessa — A supplier.'
    ]


def test_contact_without_a_note_does_not_leave_an_empty_annotation():
    character = merchant().survive(7).term_event(6).name_connection('Vessa')

    assert character.projection.creation_history[-1].endswith('Contact: Vessa.')


def test_deferred_benefit_bonus_is_already_a_completed_award():
    character = merchant().survive(7).term_event(10)
    expected = [
        'Term 1 event (Merchant): A good deal ensures you are living the high life for a few years. '
        'Gain DM+1 to any one Benefit roll. Awarded DM+1 to one future Benefit roll.'
    ]
    assert character.projection.creation_history == expected
    character.advancement(5)
    assert character.projection.creation_history == expected


def test_cash_award_records_the_amount_as_a_separate_completed_occurrence():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7)
    character.advancement(5).reenlist(False).muster_out('cash', 1)

    assert character.projection.creation_history[-1] == 'Muster out (Merchant): Gained Cr1,000.'


def test_direct_item_benefit_is_a_completed_history_occurrence():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7)
    character.advancement(5).reenlist(False).muster_out('benefits', 5)

    assert character.projection.creation_history[-1] == 'Muster out (Merchant): Gained Ship Share.'


def test_characteristic_benefit_records_the_actual_increase():
    character = merchant().survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7)
    character.advancement(5).reenlist(False).muster_out('benefits', 2)

    assert character.projection.creation_history[-1] == 'Muster out (Merchant): INT increased from 9 to 10.'


def test_characteristic_benefit_at_the_limit_does_not_claim_an_increase():
    character = merchant('786FA5').survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7)
    character.advancement(5).reenlist(False).muster_out('benefits', 2)

    assert character.projection.creation_history[-1] == 'Muster out (Merchant): INT remains at 15 (maximum reached).'


def test_multiple_benefits_from_one_roll_are_all_recorded_in_one_entry():
    character = (
        CharacterDriver()
        .start(VILANI, MOCK_WORLD)
        .ucp('7869A5')
        .background_skills([Admin(), Athletics(), Carouse(), Drive()])
        .career('Citizen', 'Corporate', roll=9)
        .survive(7)
        .term_event(7)
        .life_event(3)
        .advancement(4)
        .reenlist(False)
        .muster_out('benefits', 6)
    )

    assert character.projection.creation_history[-1] == 'Muster out (Citizen): Gained Ship Share. Gained Ship Share.'


def test_war_mishap_shows_ejection_while_the_skill_choice_is_still_outstanding():
    character = merchant().survive(2).mishap(3)

    assert character.projection.creation_history == [
        'Automatic mishap (rolled natural 2) in term 1',
        'Term 1 mishap (Merchant): A sudden war destroys your trade routes and contacts, '
        'forcing you to flee that region of space. Gain Gun Combat 1 or Pilot 1. '
        'Left Merchant. In progress: Choose one skill at level 1',
    ]


def test_disaster_keeps_its_nested_mishap_and_skill_without_ejecting_the_character():
    character = merchant().survive(7).term_event(2).mishap(3, stay_in_career=True)
    character.choose_skill(Pilot(spacecraft=Level(value=1)))

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Disaster! Roll on the Mishap table but you are not ejected from this career. '
        'Term 1 mishap (Merchant): A sudden war destroys your trade routes and contacts, '
        'forcing you to flee that region of space. Gain Gun Combat 1 or Pilot 1. '
        'Pilot (Spacecraft) increased from 0 to 1.'
    ]
    assert character.projection.summary.current_career.name == 'Merchant'


def test_nested_narrative_only_event_is_a_completed_account_not_an_empty_outcome():
    character = merchant().survive(7).term_event(7).life_event(12).unusual_event(4)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: unusual event — see sub-table Unusual event: amnesia'
    ]


def test_travel_records_the_new_world_and_retains_the_future_qualification_bonus():
    character = merchant().survive(7).term_event(7).life_event(9)
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: travel (qualification DM ahead) '
        'Gained DM+2 to the next qualification roll. '
        'In progress: You move to another world. Select your new homeworld.'
    ]
    character.move_homeworld(MOCK_WORLD_2)
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: travel (qualification DM ahead) '
        'Gained DM+2 to the next qualification roll. Moved to Regina.'
    ]


def test_life_event_injury_is_visible_while_awaiting_the_injury_roll():
    character = merchant().survive(7).term_event(7).life_event(2)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: sickness or injury '
        'In progress: Roll 1D on Injury table (sickness/injury)'
    ]


def test_relationship_life_event_keeps_the_named_ally_in_the_same_entry():
    character = merchant().survive(7).term_event(7).life_event(5)
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: relationship strengthened (ally gained) '
        'In progress: Name this Ally (Life event: improved relationship)'
    ]
    character.name_connection('Vessa', 'Spouse')
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: relationship strengthened (ally gained) Ally: Vessa — Spouse.'
    ]


def test_contact_life_event_keeps_the_name_with_its_story():
    character = merchant().survive(7).term_event(7).life_event(7).name_connection('Dara')

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: new contact made Contact: Dara.'
    ]


def test_good_fortune_records_the_deferred_bonus_amount():
    character = merchant().survive(7).term_event(7).life_event(10)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: good fortune (benefit roll bonus) '
        'Awarded DM+2 to one future Benefit roll.'
    ]


def test_ended_relationship_keeps_the_choice_and_name_with_the_story():
    character = merchant().survive(7).term_event(7).life_event(4)
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: ending of a relationship '
        'In progress: Ending relationship: gain a rival or enemy?'
    ]
    character.life_event_connection(ConnectionKind.ENEMY).name_connection('Vessa')
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: ending of a relationship '
        'Life event: relationship ended, gained an enemy Enemy: Vessa.'
    ]


def test_life_event_injury_records_the_chosen_characteristic_loss():
    character = merchant().survive(7).term_event(7).life_event(2).injury_roll(4)
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: sickness or injury '
        'Injury roll 4. In progress: Scarred: choose STR, DEX, or END to reduce by 2'
    ]
    character.choose_characteristic(Chars.STR, amount=2)
    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: sickness or injury Injury roll 4. STR reduced from 7 to 5.'
    ]


def test_nearly_fatal_injury_records_all_three_characteristic_losses():
    character = merchant().survive(7).term_event(7).life_event(2).injury_roll(1)
    character.nearly_killed(Chars.STR, roll=3)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: sickness or injury Injury roll 1. '
        'STR reduced from 7 to 4. DEX reduced from 8 to 6. END reduced from 6 to 4.'
    ]


def test_minor_injury_records_recovery_without_inventing_a_characteristic_loss():
    character = merchant().survive(7).term_event(7).life_event(2).injury_roll(6)

    assert character.projection.creation_history == [
        'Term 1 event (Merchant): Life Event. Life event: sickness or injury '
        'Injury roll 6. Lightly injured; no permanent damage.'
    ]


def test_ageing_is_its_own_occurrence_visible_before_the_roll():
    character = merchant_at_ageing()

    assert character.projection.creation_history[-1] == ('Ageing at age 34. In progress: Roll 2D on Aging table')
    assert character.projection.creation_history[-2] == (
        'Term 4 event (Merchant): You are given advanced training in a specialist field. '
        'Failed the EDU check (7 against 8+).'
    )


def test_ageing_without_deterioration_is_a_completed_outcome():
    character = merchant_at_ageing().aging_roll(7)

    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 7 − 4 terms = 3. No deterioration.'
    )


def test_ageing_choice_keeps_the_roll_then_records_the_actual_reduction():
    character = merchant_at_ageing().aging_roll(4)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 4 − 4 terms = 0. In progress: Aging: choose STR, DEX, or END to reduce by 1'
    )
    character.aging_choice(Chars.DEX)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 4 − 4 terms = 0. DEX reduced from 8 to 7.'
    )


def test_ageing_remains_in_progress_after_only_one_of_two_choices():
    character = merchant_at_ageing().aging_roll(3).aging_choice(Chars.STR)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 3 − 4 terms = -1. STR reduced from 7 to 6. '
        'In progress: Aging: choose STR, DEX, or END to reduce by 1'
    )
    character.aging_choice(Chars.END)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 3 − 4 terms = -1. STR reduced from 7 to 6. END reduced from 6 to 5.'
    )


def test_mishap_and_ageing_started_by_the_same_event_have_separate_outcomes():
    character = merchant_in_term(4).survive(2).mishap(3)
    assert character.projection.creation_history[-2:] == [
        'Term 4 mishap (Merchant): A sudden war destroys your trade routes and contacts, '
        'forcing you to flee that region of space. Gain Gun Combat 1 or Pilot 1. '
        'Left Merchant. In progress: Choose one skill at level 1',
        'Ageing at age 34. In progress: Roll 2D on Aging table',
    ]


def test_ageing_records_all_three_automatic_reductions():
    character = merchant_at_ageing().aging_roll(2)

    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 2 − 4 terms = -2. '
        'STR reduced from 7 to 6. DEX reduced from 8 to 7. END reduced from 6 to 5.'
    )


def test_severe_ageing_records_two_points_lost_from_each_physical_characteristic():
    character = merchant_in_term(7).survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7).advancement(5)
    character.aging_roll(2)

    assert character.projection.creation_history[-1] == (
        'Ageing at age 46. Ageing roll 2 − 7 terms = -5. '
        'STR reduced from 7 to 5. DEX reduced from 8 to 6. END reduced from 6 to 4.'
    )


def test_severe_ageing_crisis_keeps_recovery_with_the_losses():
    character = (
        merchant_in_term(7, '2869A5').survive(7).term_event(9).skill_roll(Chars.EDU, modified_roll=7).advancement(8)
    )
    character.aging_roll(2).aging_crisis(paid=True, medical_roll=1)

    assert character.projection.creation_history[-1] == (
        'Ageing at age 46. Ageing roll 2 − 7 terms = -5. '
        'STR reduced from 2 to 0. DEX reduced from 8 to 6. END reduced from 6 to 4. '
        'Medical care restored STR from 0 to 1.'
    )


def test_automatic_ageing_losses_keep_the_crisis_outcome_in_the_same_entry():
    character = merchant_at_ageing('1869A5').aging_roll(2)
    assert character.projection.creation_history[-1].startswith(
        'Ageing at age 34. Ageing roll 2 − 4 terms = -2. '
        'STR reduced from 1 to 0. DEX reduced from 8 to 7. END reduced from 6 to 5. In progress:'
    )
    character.aging_crisis(paid=True, medical_roll=1)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 2 − 4 terms = -2. '
        'STR reduced from 1 to 0. DEX reduced from 8 to 7. END reduced from 6 to 5. '
        'Medical care restored STR from 0 to 1.'
    )


def test_unpaid_ageing_crisis_records_death_as_the_outcome():
    character = merchant_at_ageing('1869A5').aging_roll(4).aging_choice(Chars.STR)
    character.aging_crisis(paid=False, medical_roll=0)

    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 4 − 4 terms = 0. STR reduced from 1 to 0. Died in the ageing crisis.'
    )


def test_ageing_crisis_preserves_deterioration_and_subsequent_recovery():
    character = merchant_at_ageing('1869A5').aging_roll(4).aging_choice(Chars.STR)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 4 − 4 terms = 0. STR reduced from 1 to 0. '
        'In progress: Aging crisis: pay for medical care or die?'
    )
    character.aging_crisis(paid=True, medical_roll=1)
    assert character.projection.creation_history[-1] == (
        'Ageing at age 34. Ageing roll 4 − 4 terms = 0. STR reduced from 1 to 0. Medical care restored STR from 0 to 1.'
    )
