from tests.approval.snapshot import AnnotatedSnapshot


def pending_summary(projection) -> list[dict]:
    result = []
    for p in projection.pending_inputs:
        item: dict = {'type': type(p).__name__, 'kind': p.kind}
        if hasattr(p, 'level'):
            item['level'] = p.level
        if hasattr(p, 'options'):
            item['option_count'] = len(p.options)
            item['option_types'] = sorted({type(o).__name__ for o in p.options})
        result.append(item)
    return result


def projection_snap(projection) -> AnnotatedSnapshot:
    return AnnotatedSnapshot(
        {
            'summary': projection.summary.model_dump(mode='json'),
            'pending_inputs': pending_summary(projection),
        }
    )
