# MTG Lab Vision

MTG Lab is an evidence-driven, reproducible decision-intelligence and research
platform for collectible card games. It aims to help people understand cards,
products and decisions, inspect the basis of an answer, and distinguish what is
known from what remains uncertain.

MTG Lab originated as an analytical foundation for ChatGPT, beginning with
booster-pack probability questions and Mystery Booster 2 simulation research.
Its intended experience is an accessible, AI-powered application through which
users can investigate cards, decks, collections, products, markets and research
hypotheses without programming knowledge.

The Project Owner's conceptual comparison is: “If ChatGPT, Untapped.gg, Moxfield,
and Collectr had a baby.” This describes an integrated experience, not a
requirement to reproduce those applications.

Magic: The Gathering is the initial game. Mystery Booster 2 is the reference
product for demonstrating reusable product infrastructure. The architecture is
intended to support additional collectible card games over time, with each
game's identities, evidence and rules kept explicit.
This ambition does not authorize expanding the present engineering scope.

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

Complete interactive gameplay, Arena feature parity and superhuman gameplay are
not prerequisites for the first useful release.

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

Expert-level strategic intelligence, autonomous gameplay and full-game simulation
remain long-term research ambitions. MTG Lab is not intended to recreate MTG Arena.
Rules understanding and gameplay simulation should primarily support analytical
questions: deck consistency, win-condition probabilities, disruption, matchup
analysis and strategy evaluation.

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

Tier classifications must be format-specific and supported by competitive
evidence. Early-turn consistency matters, but turn-six performance is not a
universal competitive benchmark.

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

Support both ChatGPT-accessible analytical capabilities and a built-in AI
research assistant. Both should reason over verified knowledge and analytical
tools rather than becoming a competing source of canonical truth. Interchangeable
model providers and orchestration architectures remain proposed technical
approaches, not approved implementation requirements.

### Proactive Research Intelligence

MTG Lab should eventually be an AI-powered research intelligence system that
recognizes important Magic developments, independently investigates promising
hypotheses, challenges its own findings, and brings meaningful discoveries to
the user before the user knows to ask. This is an enduring strategic product
requirement and a long-term research ambition, not a present capability, a
prerequisite for the first useful release, or implementation authorization.

From separately authorized sources, the system should eventually detect:

- New cards and set previews.
- Emerging interactions and strategies.
- Format and rules changes.
- Tournament results and metagame shifts.
- Reprints, product releases and market developments.
- Changes affecting previously recorded research hypotheses.

Its multi-step research should eventually support:

1. Detecting and verifying relevant developments.
2. Resolving supported Card identities, mechanics and evidence.
3. Generating testable hypotheses.
4. Selecting and invoking authorized analytical tools.
5. Comparing alternatives and investigating counterexamples.
6. Challenging its own preliminary conclusions.
7. Preserving evidence, experiments and reassessments through the established
   [Research Log architecture](docs/RESEARCH_LOG_ARCHITECTURE.md).
8. Proactively communicating meaningful findings and uncertainties.

The system should prioritize investigations according to their potential strategic significance, novelty, evidentiary strength, uncertainty, and expected value of further research, while recognizing when an investigation should be deferred, stopped, or revisited.

Research effort should be selective. Users should retain meaningful control over
research interests, notification preferences, frequency, significance thresholds,
privacy and authorized external actions.

AI-generated hypotheses must remain distinct from verified facts and supported
analytical conclusions. AI must not become a competing canonical authority or
override deterministic analytical results. Proactive research must operate within
separately approved source-use permissions, tool access, computational budgets,
privacy restrictions, stopping conditions and publication controls.

The long-term benchmark includes identifying genuinely powerful overlooked cards,
interactions or strategies before widespread recognition, supported by verifiable
evidence and later real-world validation. This ambition does not claim that the
capability already exists or authorize any implementation or external action.

### Research and Experimentation

Preserve dated hypotheses, original evidence, experiments, outcomes, counterexamples and
reproducible validation. Keep domain research in the established
[Research Log](docs/RESEARCH_LOG_ARCHITECTURE.md), with engineering documentation
and temporary conversation context serving their separate purposes.

Retain experiment versions and later validation so the historical record can
substantiate whether a sleeper-card discovery preceded widespread recognition.

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

Enduring product requirements guide desired outcomes; proposed technical
approaches require separate approval; deferred features remain outside
authorized work; aspirational research capabilities are benchmarks rather than
release prerequisites. Nothing in this vision authorizes implementation.

## iPhone-first Owner authorization

Owner authorization must be practical from an iPhone. MTG Lab presents the exact
operation or policy, scope, validation results, material risks and limitations.
The Owner authenticates and selects Approve or Reject. The system constructs and
verifies identity, role, timestamps, request bindings, replay protection and audit
evidence automatically. Routine approval must not require entering technical
authorization metadata. Independent initial enrollment may be required.

## Bounded standing authorization

MTG Lab must eventually support independently authenticated, explicitly approved,
bounded standing policies. Every execution must satisfy the active policy's
operation, source, material, capability, resource and lifecycle constraints and
retain exact policy, evidence and validation bindings. Out-of-policy operations
fail closed or escalate. The system cannot grant itself permissions or amend its
own authority. Standing policies do not establish source-use rights, factual
reliability, semantic correctness, legality or gameplay authority. No standing-policy
execution is currently implemented or authorized.

Within independently approved source-use, research and execution scopes, MTG Lab
should progressively detect relevant developments, prepare evidence-backed
hypotheses, test alternatives and counterexamples, and escalate meaningful findings
and unresolved conflicts. Routine qualifying operations should eventually proceed
under bounded standing policies. Verified observations, accepted interpretations,
rules-supported interactions, hypotheses, simulation results and competitive
validation remain distinct. Sleeper-card discovery remains a research benchmark
requiring verifiable evidence and eventual real-world validation.
