# Event and Pending Input Rethink

## Background

The current system for handling the events in ceres.character
is confusing to code and understand, and prittle, with much
information encoded in string literals in such a way that it's
very difficult to humans, AI or other tools to verify that
things work as intended.

If we use Citizen career Event 8 as an example, the rules say
this:

*You learn something you should not have – a corporate secret, a political scandal – which you can
profit from illegally. If you choose to do so, then you gain DM+1 to a Benefit roll from this career and
gain Streetwise 1, Deception 1 or a criminal Contact. If you refuse, you gain nothing.*

As a testament to the state of confusion in this system, Claude
has read this text and implemented someting completely different
but it still shows how messy this is. The Relevant parts of the
citizen.py code is:

```python
class PendingCitizenEvent8(CareerChoicePendingBase):
    kind: Literal['citizen_event_8'] = 'citizen_event_8'

    def on_choice(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        if event.choice == 'refuse':
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger=EffectTrigger.ADVANCEMENT,
                    source_event_id=event.id,
                    effect={'type': EffectType.DM, 'amount': 2},
                )
            )
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
        else:
            projection.pending_inputs.append(
                PendingCitizenEvent8SkillRoll(
                    id=f'{event.id}.0',
                    instruction='Roll Streetwise 8+: success = extra Benefit roll; fail = ejected, gain Rival',
                    options=[Streetwise()],
                )
            )


class PendingCitizenEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['citizen_event_8_skill_roll'] = 'citizen_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _apply_mishap_ejection

        if event.modified_roll >= 8:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger=EffectTrigger.MUSTER_OUT_ADD,
                    source_event_id=event.id,
                    effect={'type': EffectType.ADD, 'value': 1},
                )
            )
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            career = projection.get_current_career()
            projection.summary.connections.append(Rival(source='Illegal information leak (Citizen event 8)'))
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class CitizenEvent8Handler(CareerHandlerBase):
    type: Literal['citizen_event_8'] = 'citizen_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCitizenEvent8(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Use the illegal information (roll Streetwise 8+: success = extra Benefit roll, '
                    'fail = ejected, gain Rival) or refuse (DM+2 to next advancement)?'
                ),
                options=['use_it', 'refuse'],
            )
        )
        return pending_idx + 1


CAREER_DATA = CitizenCareerData(
    ...
    events={
        ...
        8: CareerEventEntry(
            text='You learn something illegal but profitable.',
            effects=[CitizenEvent8Handler()],
        ),
        ...
    },
)

```

Three fairly trivial sentences turn into 60 lines of code which is difficult
enough for it to be difficult to get right and easy to break. I'd much rather
prefer it look something like this:


```python
class CitizenEvent8DoSo(CareerChoice):
    kind: Literal['citizen_event_8_do_so'] = 'citizen_event_8_do_so'

    def on_choice(self, projection: CharacterProjection, event) -> None:
        '''
        Code to enable selection of Streetwise 1, Deception 1 or a criminal Contact
        '''

class CitizenEvent8Refuse(CareerChoice):
    kind: Literal['citizen_event_8_refuse'] = 'citizen_event_8_refuse'

    def on_choice(self, projection: CharacterProjection, event) -> None:
        # Do nothing
        pass



class PendingCitizenEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['citizen_event_8_skill_roll'] = 'citizen_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _apply_mishap_ejection

        if event.modified_roll >= 8:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger=EffectTrigger.MUSTER_OUT_ADD,
                    source_event_id=event.id,
                    effect={'type': EffectType.ADD, 'value': 1},
                )
            )
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            career = projection.get_current_career()
            projection.summary.connections.append(Rival(source='Illegal information leak (Citizen event 8)'))
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class CitizenEvent8Handler(CareerHandlerBase):
    type: Literal['citizen_event_8'] = 'citizen_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCitizenEvent8(
                id=pending_id(event_id, pending_idx),
                options=[CitizenEvent8DoSo(), CitizenEvent8Refuse()],
            )
        )
        return pending_idx + 1


CAREER_DATA = CitizenCareerData(
    ...
    events={
        ...
        8: CareerEventEntry(
            text=(
                'You learn something you should not have – a corporate secret, a political scandal '
                '– which you can profit from illegally. If you choose to do so, then you gain DM+1 '
                'to a Benefit roll from this career and gain Streetwise 1, Deception 1 or a criminal '
                'Contact. If you refuse, you gain nothing.'
            ),
            effects=[CitizenEvent8Handler()],
        ),
        ...
    },
)

```
