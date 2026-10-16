# Fictional gameplay contract proof

These files are original project-authored fictional test inputs for the bounded
`fictional-two-player-v1` interpreter. They contain no real Card records, provider
facts, copied Oracle text, or Comprehensive Rules corpus. The four invented Card
identities are `pebble-resource`, `ember-scroll`, `swift-lantern`, and `moss-plot`.

`rules-snapshot.json` pins the source metadata, rule definitions and their hashes,
coverage manifest, explicit rules version/effective date, and semantic rules
snapshot identity. Each `*.semantics.json` pins authored structured semantics to
that exact rules snapshot. `game-state.json` pins the initial two-player state;
the hidden library object's identity remains unknown. No rules document or
natural-language text is parsed into executable behavior.

`tests/gameplay_rules_fixture.py::write_fixture` deterministically reproduces all
six JSON files from the same authored inputs. Regeneration is a test-authoring
action, never a fallback for missing or corrupt retained fixtures. Ordinary tests
load the retained IDs and require exact agreement with the authored proof.

The fixture establishes only fictional contract behavior. It is not production
eligibility, human admission approval, source-policy clearance, real-game
completeness, format legality, strategy, or gameplay simulation. Its authorship
metadata grants no permission concerning any real third-party rules or dataset.
