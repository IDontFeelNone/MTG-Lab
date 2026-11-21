"""Original caller-declared demonstration; contains no real Card source facts."""
from copy import deepcopy
from .investigations import append_revision, create_investigation


def example_request(copies=3, *, compare=False):
    deck = dict(deck_id='baseline', identity_authority='CALLER_DECLARED', complete=True,
        draw_population=dict(section='main', declared_size=60),
        entries=[dict(card_id='local:target', section='main', quantity=3),
                 dict(card_id='local:other', section='main', quantity=57)],
        groups=[dict(group_id='declared-target', members=['local:target'], minimum=1)],
        schedule=[dict(label='Seven seen assumption', cards_seen=7)],
        assumptions=dict(sampling='uniform-without-replacement', group_disjointness='caller_declared'))
    candidate = deepcopy(deck)
    candidate['deck_id'] = 'candidate' if compare else 'baseline'
    candidate['entries'][0]['quantity'] = copies
    candidate['entries'][1]['quantity'] = 60 - copies
    return dict(schema_version='deck-workbench-input-v1', labels=[
        dict(card_id='local:target', label='Authored target'), dict(card_id='local:other', label='Authored remainder')],
        analysis=dict(schema_version='supplied-deck-consistency-input-v1', decks=[deck, candidate] if compare else [candidate]))


def example_metadata(second=0, **changes):
    value = dict(created_at='2026-11-20T00:00:' + str(second).zfill(2) + 'Z',
        hypothesis='', outcome='exploring', assumptions=[], notes=[], counterexamples=[],
        rejected_alternatives=[], unresolved_questions=[], evidence_references=[])
    value.update(changes)
    return value


def example_investigation():
    artifact = create_investigation(key='original-copy-count-investigation',
        question='Does increasing a declared target from three copies to four improve seven-card access?',
        created_at='2026-11-20T00:00:00Z')
    artifact = append_revision(artifact, branch_id='baseline', parent_id=None,
        metadata=example_metadata(notes=['Explore access first; no claim about casting or deck strength.']))
    artifact = append_revision(artifact, branch_id='baseline', parent_id=artifact['revisions'][-1]['revision_id'],
        metadata=example_metadata(1, hypothesis='Three copies provide the baseline.',
            assumptions=['Uniform sampling without replacement; seven cards seen.']),
        analytical_input=example_request(), calculate=True)
    baseline = artifact['revisions'][-1]['revision_id']
    artifact = append_revision(artifact, branch_id='four-copy-test', parent_id=baseline,
        metadata=example_metadata(2, hypothesis='Four copies improve this exact access event.',
            outcome='supported_under_declared_assumptions',
            evidence_references=[dict(relation='supporting', label='Baseline experiment', reference=baseline)],
            unresolved_questions=['No claim about strategic costs of replacing another card.']),
        analytical_input=example_request(4, compare=True), calculate=True)
    return append_revision(artifact, branch_id='rejected-two-copy-test', parent_id=baseline,
        metadata=example_metadata(3, hypothesis='Two copies could improve access.', outcome='rejected',
            evidence_references=[dict(relation='contradicting', label='Baseline access experiment', reference=baseline)],
            counterexamples=['The exact two-copy access result is lower than the baseline.'],
            rejected_alternatives=['Rejected only for the stated access hypothesis, not as a deck ranking.']),
        analytical_input=example_request(2, compare=True), calculate=True)
