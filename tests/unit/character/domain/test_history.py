"""The displayed account of an occurrence develops as its decisions resolve."""

from ceres.character.domain.history import CreationHistory


def test_occurrence_is_visible_before_any_outcome_is_known():
    history = CreationHistory()

    history.start(1, 'You are offered advanced training.')

    assert history.render() == ['You are offered advanced training.']


def test_outcome_enriches_the_same_occurrence_without_losing_its_story():
    history = CreationHistory()
    history.start(1, 'You are offered advanced training.')

    history.record(1, 'Passed the EDU check.')

    assert history.render() == ['You are offered advanced training. Passed the EDU check.']


def test_outstanding_instructions_are_replaced_then_removed_without_removing_facts():
    history = CreationHistory()
    history.start(1, 'Training.')
    history.pending(1, ['Roll EDU 8+.'])
    assert history.render() == ['Training. In progress: Roll EDU 8+.']

    history.record(1, 'Passed the EDU check.')
    history.pending(1, ['Choose a skill.'])
    assert history.render() == ['Training. Passed the EDU check. In progress: Choose a skill.']

    history.record(1, 'Admin increased from 0 to 1.')
    history.pending(1, [])
    assert history.render() == ['Training. Passed the EDU check. Admin increased from 0 to 1.']


def test_identical_occurrences_keep_separate_outcomes_and_positions():
    history = CreationHistory()
    history.start(1, 'Training.')
    history.start(2, 'Training.')
    history.record(2, 'Failed the EDU check.')
    history.pending(1, ['Choose a skill.'])

    assert history.render() == [
        'Training. In progress: Choose a skill.',
        'Training. Failed the EDU check.',
    ]


def test_recovery_preserves_the_injury_even_when_the_changes_cancel_out():
    history = CreationHistory()
    history.start(1, 'Injured during a feud.')
    history.record(1, 'STR reduced from 7 to 5.')
    history.record(1, 'Treatment restored STR from 5 to 7.')

    assert history.render() == ['Injured during a feud. STR reduced from 7 to 5. Treatment restored STR from 5 to 7.']
