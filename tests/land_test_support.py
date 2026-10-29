"""One shared actual admission for focused land routing and pure result checks.

The real disposable writer's expanded catalog is required to reject. This helper
never installs or selects historical positive catalog evidence.
"""
from functools import lru_cache
from pathlib import Path

from card_rules_pilot.cards import PROFILE_ID, QUERY_ID
from test_card_rules_pilot_cards import current_catalog_intact

ROOT = Path(__file__).resolve().parents[1]


def arguments(**changes):
    from card_rules_pilot.land_authored import PLAN_ID
    value = dict(catalog_root=ROOT, mechanical_root=ROOT,
        review_root=ROOT / 'reference-reviews',
        cohort_root=ROOT / 'data/review/land-mana-utility',
        expected_profile_id=PROFILE_ID, expected_query_snapshot_id=QUERY_ID,
        expected_plan_id=PLAN_ID)
    value.update(changes)
    return value


def common():
    selected = arguments()
    result = []
    for name in ('catalog_root', 'mechanical_root', 'cohort_root',
                 'expected_profile_id', 'expected_query_snapshot_id', 'expected_plan_id'):
        result.extend(['--' + name.replace('_', '-'), str(selected[name])])
    return result


@lru_cache(maxsize=1)
def consumer():
    from card_rules_pilot.land import load_lands
    return load_lands(**arguments())
