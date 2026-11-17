# MTG Lab Vision

MTG Lab is an evidence-driven, reproducible decision-intelligence and research
platform for collectible card games. It aims to help people understand cards,
products and decisions, inspect the basis of an answer, and distinguish what is
known from what remains uncertain.

Magic: The Gathering is the initial game. Mystery Booster 2 is the reference
product for demonstrating reusable product infrastructure. The architecture is
intended to support additional collectible card games over time, with each
game's identities, evidence and rules kept explicit.

This document is the authoritative long-term product vision. It describes desired
capabilities, not present implementation or permission to build them. Approved
architecture and accepted decisions remain in [ARCHITECTURE](docs/ARCHITECTURE.md)
and [DECISIONS](docs/DECISIONS.md). [GOVERNANCE](docs/GOVERNANCE.md) explains scope
approval and the responsibilities of current-state documents.

## First useful release

The first useful MTG Lab release should provide a practical, evidence-backed
experience offering useful product, card, collection or acquisition analysis
within verified data and implemented capabilities. It should make limitations
and uncertainty visible and provide reproducible, inspectable results.

Its exact feature set, acceptance criteria, delivery schedule and implementation
authorization require separate Project Owner approval. A useful first release
does not need to realize every research ambition below.

## Ultimate research vision

The long-term goal combines the following capabilities into an explainable
laboratory. Their inclusion here neither changes the approved roadmap nor
authorizes engineering work.

### Real-Card and Rules Intelligence

Understand actual cards, Oracle text, game mechanics, timing, legality, costs,
exceptions, procedures, interactions and strategic implications. Keep verified
rules evidence, reviewed semantic understanding and executable gameplay as
distinct achievements. Card text or a rule citation alone cannot establish a
complete procedure or interaction.

### Product and Pack Simulation

Represent products through generic definitions and support statistically validated
pack opening, reproducible seeded simulation, displays, cases, distributions,
print sheets and probability analysis. Separate declared mathematical models
from demonstrated physical collation and communicate unsupported assumptions.

### Collection Intelligence

Track ownership, exact Printings, finishes, treatments, storage, acquisition
history, value and usefulness. Support reassessment as evidence and personal
objectives change, while separating private holdings and preferences from
canonical facts.

### Deck Intelligence

Support deck construction, archetype analysis, synergy, competitive relevance,
upgrades, legality, collection-aware recommendations and strategic comparison.
Distinguish rules legality, observed performance and strategic hypotheses, with
explicit objectives, alternatives and evidence.

### Market and Acquisition Intelligence

Analyze prices, historical trends, sealed products, singles, supply, expected
value, presale premiums, transaction costs, risk and acquisition timing. Preserve
provider, currency, date and methodology, and distinguish observations from
valuations, forecasts and recommendations.

### AI Tutoring and Interactive Laboratory

Help users learn Magic rules, cards, strategies and interactions through
explanations, questions, hypothetical scenarios and interactive experimentation.
AI should reason over attributable evidence and supported procedures, disclose
uncertainty and refuse to invent missing facts or authority.

### Research and Experimentation

Preserve hypotheses, evidence, experiments, outcomes, counterexamples and
reproducible validation. Keep domain research in the established
[Research Log](docs/RESEARCH_LOG_ARCHITECTURE.md), with engineering documentation
and temporary conversation context serving their separate purposes.

### Evidence-Backed Discovery

The ultimate research benchmark is to independently identify a genuinely powerful
overlooked card or interaction before widespread recognition, explain its rules
and strategic basis, and evaluate that hypothesis against subsequent real-world
evidence. This is an aspirational research benchmark, not a claim of present
predictive capability or a guarantee of future discovery.

## Enduring boundaries

Repository-owned contracts, accepted decisions and explicitly admitted evidence
govern conclusions. Generated databases, indexes, reports and model context do
not create competing authority. Source verification, source-use permissions,
semantic review, admission and execution remain independent gates.

Capability breadth must preserve explainability, privacy, historical integrity
and honest uncertainty. Neither this vision nor its first-release description
silently expands the approved roadmap.
