import json
from pathlib import Path

import pytest

from mtglab.__main__ import main
from query import CanonicalQueryEngine, QueryError


ROOT = Path(__file__).parents[1]


@pytest.fixture
def engine():
    return CanonicalQueryEngine()


def test_entity_and_identifier_lookups(engine):
    card = engine.entity("magic.lightning-bolt")
    assert card.entity_type == "card"
    assert card.canonical_values["name"] == "Lightning Bolt"
    assert card.provenance_summary["source_ids"] == ["gatherer-lightning-bolt-lea"]
    assert card.confidence == 1.0
    assert card.uncertainty == "known"
    assert engine.entities(printing_id="magic.lea.161.en")[0].canonical_identity == "magic.lea.161.en"
    assert len(engine.entities(set_id="mb2")) == 4
    assert len(engine.entities(entity_type="card")) == 15


def test_relationships_and_provenance(engine):
    printings = engine.related("magic.lightning-bolt", "card_printings")
    assert [x.canonical_identity for x in printings] == ["magic.lea.161.en"]
    assert engine.related("magic.lea.161.en", "printing_card")[0].canonical_identity == "magic.lightning-bolt"
    assert engine.related("magic.lea.161.en", "printing_set") == ({
        "canonical_identity": "lea", "entity_type": "set",
        "printing_ids": ["magic.lea.161.en", "magic.lea.232.en", "magic.lea.262.en",
                         "magic.lea.263.en", "magic.lea.264.en", "magic.lea.265.en",
                         "magic.lea.266.en", "magic.lea.270.en", "magic.lea.47.en",
                         "magic.lea.83.en", "magic.lea.85.en"]},)
    provenance = engine.provenance("magic.lightning-bolt")
    assert provenance["canonical_identity"] == "magic.lightning-bolt"
    assert provenance["evidence_assertions"][0]["source_id"] == "gatherer-lightning-bolt-lea"


def test_search_is_deterministic_and_repeatable(engine):
    assert [x.canonical_identity for x in engine.search("Lightning Bolt")] == ["magic.lightning-bolt"]
    assert engine.search("lightning bolt", mode="normalized") == engine.search("LIGHTNING BOLT", case_insensitive=True)
    first = engine.search("mox", mode="prefix", case_insensitive=True)
    assert first == engine.search("mox", mode="prefix", case_insensitive=True)
    assert [x.canonical_identity for x in first] == sorted(x.canonical_identity for x in first)
    with pytest.raises(QueryError): engine.search("bolt", mode="fuzzy")


def test_promoted_dataset_review_audit_and_validation_states(tmp_path):
    games = ROOT / "data/canonical/games"
    state = {"card": {
        "magic.query-test": {"entity_type": "card", "values": {"name": "Query Test", "provider_id": "p-1", "external_id": "e-1"},
          "promotion_id": "promotion-test", "review_package_id": "review-test",
          "dataset_identity": [{"dataset_id": "dataset-test"}], "acquisition_lineage": {"run_id": "run-test"},
          "evidence_references": ["assertion-test"], "confidence": .75,
          "uncertainty_state": "unknowns_reviewed", "superseded_status": True}}}
    canonical = tmp_path / "canonical"; canonical.mkdir(); (canonical / "state.json").write_text(json.dumps(state))
    audit = {"promotion_id": "promotion-test", "promoted_entities": ["magic.query-test"], "rejected_entities": [],
             "validation_results": {"valid": True}, "review_package": {"review_package_id": "review-test",
             "provider": {"provider_id": "provider-test"}, "candidate_assertions": [{"id": "assertion-test",
             "source_id": "provider-test", "status": "candidate", "evidence_class": "unknown"}]}}
    audit_root = tmp_path / "audit"; audit_root.mkdir(); (audit_root / "promotion-test.json").write_text(json.dumps(audit))
    query = CanonicalQueryEngine(games_root=games, data_root=tmp_path)
    result = query.entity("magic.query-test")
    assert query.entities(provider_id="p-1") == (result,)
    assert query.entities(external_id="e-1") == (result,)
    assert query.dataset("dataset-test")["promoted_entities"][0]["canonical_identity"] == result.canonical_identity
    assert query.related("review-test", "review_package_entities") == (result,)
    assert query.related("promotion-test", "promotion_audits")[0]["promotion_id"] == "promotion-test"
    assert query.validation("unknown") == (result,)
    assert query.validation("superseded") == (result,)


def test_rejected_and_validation_failure_audits(tmp_path):
    audit = tmp_path / "audit"; audit.mkdir()
    value = {"promotion_id": "failed", "promoted_entities": [], "rejected_entities": ["bad"],
             "validation_results": {"valid": False}}
    (audit / "failed.json").write_text(json.dumps(value))
    query = CanonicalQueryEngine(games_root=ROOT / "data/canonical/games", data_root=tmp_path)
    assert query.validation("rejected")[0]["rejected_entities"] == ["bad"]
    assert query.validation("validation_failure")[0]["promotion_id"] == "failed"


def test_cli_query_operations(capsys):
    data_root = ROOT / "data"
    assert main(["--data-root", str(data_root), "query", "entity", "magic.lightning-bolt"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["canonical_identity"] == "magic.lightning-bolt"
    assert main(["--data-root", str(data_root), "query", "search", "light", "--mode", "prefix", "--case-insensitive"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["canonical_identity"] == "magic.lightning-bolt"
    assert main(["--data-root", str(data_root), "query", "provenance", "magic.lightning-bolt"]) == 0
    assert json.loads(capsys.readouterr().out)["source_ids"] == ["gatherer-lightning-bolt-lea"]
    assert main(["--data-root", str(data_root), "query", "validation", "superseded"]) == 0
    assert json.loads(capsys.readouterr().out) == []
    assert main(["--data-root", str(data_root), "query", "dataset", "missing-dataset"]) == 0
    assert json.loads(capsys.readouterr().out)["promoted_entities"] == []
