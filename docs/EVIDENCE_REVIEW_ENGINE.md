# Evidence Review Engine

**Status:** Implemented, product-agnostic pre-promotion control

## Purpose and boundary

The Evidence Review Engine evaluates an external evidence handoff before the
handoff may enter the Rule Claim Matrix workflow. It assesses only evidence
quality, completeness, provenance, and internal consistency. It does not infer
rules, decide whether a domain claim is true, populate canonical repositories,
or perform product-specific parsing, generation, probability, or simulation.

The engine is distinct from the Evidence Repository loader. The review engine
examines a possibly incomplete external delivery and produces findings. A later
workflow may archive accepted evidence under `data/sources/`; archive admission
and canonical promotion remain separate controlled decisions.

## Handoff contract

An external handoff is a directory containing `manifest.json` and files beneath
`artifacts/`. The versioned `evidence-handoff` schema requires:

- stable handoff identity, title, creation time, and schema version;
- source identities and non-empty external references;
- a declared list of required artifact identities;
- artifact paths, media types, byte sizes, SHA-256 hashes, and source identities;
- explicit claims with stable identities, topics, literal values, statements,
  artifact references, and source references.

The `topic` and literal `value` fields permit mechanical conflict detection. The
engine reports different declared values for the same topic; it does not choose
between them or derive a replacement value.

## Workflow

1. `load_handoff` parses the manifest, confines paths to the handoff directory,
   and reads available artifact bytes. Missing, unreadable, and path-escaping
   artifacts become review findings where possible.
2. `validate_handoff` checks the versioned manifest contract, declared source
   references, required-artifact references, byte sizes, and SHA-256 hashes.
3. Duplicate detection compares artifact identities, paths, and content hashes.
   Conflict detection groups only explicitly declared claim topics and values.
4. Completeness assessment classifies supported and unsupported claims, missing
   required artifacts, and artifacts not cited by any claim. Its score is the
   rounded percentage of required artifacts present with verified integrity and
   claims backed by valid artifact and source references. An empty assessment
   scores zero rather than implying sufficiency.
5. `review_handoff` deterministically sorts inventories and findings and assigns
   one recommendation:
   - **Ready for verification**: integrity and consistency checks pass, all
     claims are supported, all required artifacts are present, and no artifact
     is orphaned.
   - **Needs additional evidence**: structural and integrity checks pass, but
     evidence is missing, a claim is unsupported, or an artifact is orphaned.
   - **Reject**: the manifest is invalid, an artifact fails integrity or safe
     loading, a source/required-artifact reference is invalid, artifacts are
     duplicated, or explicit claims conflict.
6. The returned report is validated against the version selected by its own
   `schema_version` before either JSON or Markdown is rendered.

## Reports

The `evidence-review-report` schema covers the evidence inventory, supported and
unsupported claim identities, conflicts, missing evidence, orphaned and
duplicate artifacts, completeness score, provenance summary, validation
findings, and recommendation. `render_json_report` emits sorted, indented JSON
with a trailing newline. `render_markdown_report` emits the same reviewed facts
as a stable human-readable document. Rendering never mutates or promotes data.

## Responsibilities and repository integration

Evidence providers are responsible for supplying artifact bytes, hashes,
metadata, explicit claims, and resolvable source references. Reviewers are
responsible for inspecting the generated report and the underlying artifacts;
`Ready for verification` means the handoff is mechanically reviewable, not that
its claims have been accepted as canonical truth.

The engine belongs before Rule Claim Matrix creation and before any controlled
promotion boundary:

```text
external handoff
      |
      v
Evidence Review Engine -- JSON + Markdown review reports
      |
      v (human decision and separate archive admission)
Evidence Repository --> Rule Claim Matrix --> controlled promotion
```

Application code imports the public functions from `evidence_review`. Report
files, when retained by a future workflow, are intermediate review artifacts and
must not be stored as canonical domain data. This subsystem introduces no
product, Slot, Print Sheet, generator, probability, or simulation behavior and
does not alter Tier 0 architecture.
