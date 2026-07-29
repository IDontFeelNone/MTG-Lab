# Research Log Architecture

**Tier:** Tier 0 (Architectural Constitution)

**Architectural Status:** Approved design; not implemented

## Purpose

The Research Log is MTG Lab's scientific notebook and institutional memory for domain research. It records questions, hypotheses, experiments, datasets, simulations, observations, conclusions, findings, and their supporting evidence in a reproducible, searchable, and versioned form.

The subsystem exists so research knowledge survives individual sessions, tools, contributors, and changing interpretations. A conclusion must never exist without traceable evidence, methods, and context. The Research Log is a first-class platform component alongside the Database, Import Pipeline, Validation Engine, Simulation Engine, Analytics Engine, Market Intelligence, and AI Advisor.

## Architectural Principles

- **Reproducibility:** A contributor can reconstruct an experiment or simulation from recorded inputs, versions, configuration, and seeds.
- **Provenance:** Every derived statement traces through observations and transformations to its sources.
- **Versioning:** Research state evolves through retained versions rather than destructive replacement.
- **Evidence preservation:** Original evidence remains available independently of later interpretation.
- **Searchability:** Structured metadata makes research discoverable across entities, projects, and time.
- **Explainability:** Findings expose the reasoning, assumptions, confidence, and evidence behind them.
- **AI grounding:** AI retrieves cited research records instead of relying on conversational memory.
- **Long-term institutional memory:** Knowledge remains intelligible after its original contributors and tools are gone.

## Architectural Position

The Research Log is a distinct domain subsystem, not a feature hidden inside analytics, AI, or persistence. It owns the lifecycle and relationships of research knowledge while delegating source acquisition, validation, computation, storage, and presentation to the systems responsible for those concerns.

The Git repository owns this architectural contract and future versioned data contracts. A database may provide generated persistence and search indexes, but it is not the architectural source of truth. No Research Log application module, schema, migration, or database table is currently implemented; those require separately approved milestones.

## Research Lifecycle

```text
Research Project
      ↓
Research Question
      ↓
Hypothesis
      ↓
Experiments
      ↓
Datasets
      ↓
Simulation Runs
      ↓
Observations
      ↓
Conclusions (Versioned)
      ↓
Published Findings
```

- **Research Project:** Defines a bounded research program, its objective, scope, participants, status, and linked domain entities.
- **Research Question:** States a specific answerable question within a project and supplies the context against which results are interpreted.
- **Hypothesis:** Records a testable proposed explanation or prediction, including assumptions and expected evidence.
- **Experiments:** Define repeatable procedures, inputs, controls, configurations, and success or evaluation criteria.
- **Datasets:** Identify versioned inputs and outputs used by experiments, including lineage, validation state, and content identity.
- **Simulation Runs:** Record deterministic executions with simulator and data versions, configuration, random seed, timestamps, and outputs.
- **Observations:** Capture what was measured or noticed without silently elevating it to a general conclusion.
- **Conclusions (Versioned):** Interpret accumulated observations with confidence, limitations, citations, and supersession relationships.
- **Published Findings:** Present reviewed conclusions for broader consumption while retaining links to the underlying research graph.

Stages may iterate. New evidence can create a new hypothesis, experiment, observation, or conclusion version without erasing earlier work.

## Core Entities

- **ResearchProject:** Aggregate root for related research questions and activity; links scope, contributors, domain subjects, and publication state.
- **ResearchEntry:** A common chronological entry point for notes, questions, hypotheses, experiment activity, observations, decisions, and links within a project without weakening their more specific entity contracts.
- **ResearchQuestion:** An answerable question belonging to a project; may have multiple competing hypotheses.
- **Hypothesis:** A versioned, testable claim linked to a question; evaluated by one or more experiments and observations.
- **Experiment:** A reproducible procedure that tests hypotheses and consumes or produces datasets and simulation runs.
- **Methodology:** The versioned procedure, controls, assumptions, tools, and evaluation criteria applied by an experiment.
- **ParameterSet:** Content-identified inputs and settings, including simulation configuration and random seeds, used for a reproducible execution.
- **Dataset:** A content-identified, versioned collection used or produced by research; records lineage and validation status.
- **SimulationRun:** A reproducible execution linked to an experiment, input datasets, engine version, seed, configuration, and results.
- **Observation:** A recorded measurement or qualitative result derived from evidence, a dataset, an experiment, a simulation, or a market event.
- **Result:** Structured experiment or simulation output with units, uncertainty, and links to the producing method, parameters, and datasets.
- **Conclusion:** A versioned interpretation addressing a question or hypothesis; cites observations and evidence and may supersede a prior conclusion.
- **Finding:** A reviewed, publishable research statement derived from one or more conclusion versions.
- **Evidence:** A traceable source or artifact supporting or contradicting hypotheses, observations, conclusions, or findings.
- **Attachment:** A content-identified file associated with research records, such as a chart, notebook export, image, or report.
- **Chart:** A reproducible visualization linked to its source dataset, query or transformation, configuration, and attachment rendition.
- **Tag:** A controlled or curated label supporting discovery across research types and domain subjects.
- **Version:** An immutable revision identity with authorship, timestamp, predecessor, change reason, and content identity.
- **Citation:** A precise reference from a research claim to internal evidence or an external source, including locator and access metadata.

Relationships form a navigable research graph rather than a flat journal. Entities use stable IDs; many-to-many links preserve competing hypotheses, shared datasets, contradictory evidence, and conclusions spanning multiple experiments.

Related-research links connect projects, questions, hypotheses, and findings without merging their identity or history. These links state their relationship type, such as extends, reproduces, contradicts, depends on, or supersedes.

## Metadata

Every research entity records metadata appropriate to its lifecycle, including:

- Stable, globally unique IDs.
- Creation and update timestamps, plus observation or execution time where distinct.
- Human or system authors and responsible reviewers.
- Explicit lifecycle status, such as proposed, active, blocked, completed, superseded, reviewed, or published.
- Confidence using a documented scale and rationale where the entity makes an interpretive claim.
- Tags and controlled classifications.
- Links to relevant products, cards, and sets by stable repository IDs.
- Version, predecessor, content hash, and change reason where versioned.
- Source, tool, engine, repository, schema, and dataset versions needed for audit or reproduction.

Missing metadata remains explicit. Unknown values must not be silently inferred.

## Versioning

Nothing is overwritten. Corrections, reinterpretations, and status changes create retained versions with authorship, timestamps, reasons, and predecessor links. Every conclusion is versioned so contributors can reconstruct what was believed, why it was believed, and what evidence caused it to change.

Every experiment remains reproducible: its method, inputs, dataset versions, configuration, software versions, and random seeds are immutable or content-addressed. Superseded records remain searchable and are clearly marked rather than deleted from history.

## Reproducibility

A research claim is reproducible only when another contributor can identify the exact evidence, methodology version, parameter set, input datasets, repository and engine versions, environment assumptions, and—where randomness is involved—random seed. Structured results and charts retain the query or transformation that produced them.

Reproduction attempts are new linked experiments or runs, not edits to the original. They record whether results confirmed, contradicted, or qualified earlier observations. External sources that cannot be archived must retain citations, access timestamps, content hashes where possible, and documented limitations.

## Evidence Model

```text
Raw evidence
      ↓
Parsed evidence
      ↓
Normalized evidence
      ↓
Research conclusions
```

Raw evidence preserves acquired source material exactly. Parsed evidence records extracted source facts and locations. Normalized evidence reconciles representations while retaining field-level provenance. Research conclusions interpret validated evidence through documented observations and methods.

Evidence links may support, contradict, qualify, or invalidate a claim. They record content identity, source, acquisition context, transformation lineage, validation state, and precise locators. AI and human contributors must always be able to trace a conclusion or finding back through observations and transformations to preserved evidence.

## AI Integration

The AI Advisor retrieves Research Log entities and their citations to answer questions such as:

- Have we researched Goblin Storm?
- Summarize all Mystery Booster 2 work.
- Show contradictory findings.
- Which hypotheses changed over time?

AI output must distinguish **facts**, **observations**, **inference**, **hypotheses**, and **published conclusions**. It must expose confidence, limitations, version state, contradictions, and citations rather than collapsing them into a single unsupported answer.

AI may assist with retrieval, comparison, summarization, tagging, and proposed hypotheses. It may not silently publish conclusions, rewrite evidence, replace deterministic analytics, or treat conversational memory as research data.

## Search

Research must be searchable and filterable by:

- Products, cards, and sets.
- Tags and controlled classifications.
- Confidence range.
- Authors and reviewers.
- Research status and publication state.
- Creation, observation, execution, and publication date.
- Datasets and dataset versions.
- Experiments and simulation runs.
- Conclusions, conclusion versions, and findings.
- Supporting, contradictory, or superseding relationships.

Search results must retain entity type, status, version, confidence, and provenance context so discovery does not misrepresent a draft hypothesis as a published finding.

## Database Integration

The persistence layer will conceptually provide tables for projects, entries, questions, hypotheses, experiments, methodologies, parameter sets, datasets, simulation runs, observations, structured results, conclusions, findings, evidence, attachments, charts, tags, versions, and citations. Association tables will represent authorship, tagging, domain and related-research links, evidence relationships, experiment inputs and outputs, hypothesis evaluation, conclusion support, contradiction, and supersession.

These are conceptual storage responsibilities, not schema definitions. Physical tables, columns, indexes, migrations, and ORM models require a separately approved design. The database is a query and persistence layer derived from versioned contracts; it does not replace repository-owned architecture or preserved evidence.

## Future Enhancements

- Peer review and approval workflows.
- Multi-contributor collaboration and discussion.
- Citation generation and export.
- Scheduled re-analysis against new data or engine versions.
- Automatic experiment and simulation capture.
- Market-triggered re-evaluation.
- AI-generated summaries with cited sources.
- Automated contradiction detection.
- Cross-project knowledge graphs.

## Relationship to Other Systems

- **Database:** Persists and queries structured Research Log entities, versions, and relationships without becoming the authority for raw evidence.
- **Import Pipeline:** Supplies immutable raw, parsed, and normalized evidence with source and transformation provenance.
- **Validation:** Verifies structural, referential, domain, and statistical integrity before evidence or results support conclusions.
- **Simulation:** Produces reproducible runs and datasets linked to experiments, configuration, versions, and seeds.
- **Analytics:** Produces documented derived metrics and observations from validated data.
- **Market Intelligence:** Supplies timestamped market observations and triggers re-evaluation when material conditions change.
- **AI Advisor:** Retrieves, compares, explains, and cites research while preserving epistemic distinctions and uncertainty.
- **Collection Manager:** Supplies scoped collection facts and consumes reviewed findings without embedding research conclusions as untraceable state.

Systems exchange stable IDs and versioned contracts. The Research Log references their outputs; it does not absorb their responsibilities.

## Architectural Importance

The Research Log is a **Tier 0 architectural subsystem** because it preserves the institutional memory of MTG Lab's research. Without it, hypotheses, experiments, contradictory evidence, and evolving conclusions would be scattered across conversations and transient artifacts. With it, the platform can accumulate trustworthy domain knowledge that remains reproducible, searchable, explainable, and grounded over the lifetime of the project.
