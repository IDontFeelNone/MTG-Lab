# AI Model Adapter Framework v1

> **Status: Current — Phase 95. Architecture v12 is unchanged.**

## Architecture assessment

Phase 95 adds the next downstream boundary in Architecture v12:

```text
Canonical Repository -> Query -> Analytics -> Semantic -> Reasoning Context
  -> AI Model Adapter -> future provider implementations
```

The milestone changes no Tier 0 architecture or canonical contract. It relies on the
Constitution's single-source-of-truth, AI-is-not-the-repository, derived-knowledge,
explicit-boundary, and human-accountability laws. The Reasoning Context Layer remains the
only source of model reasoning context. The adapter accepts a `ReasoningContextResult`; it
has no canonical, query, analytics, semantic, persistence, filesystem, or repository
dependency. Providers receive that same context contract through the abstract interface and
therefore cannot use this framework to bypass the reasoning boundary.

No architectural defect was found. The merged Phase 94 baseline is present in
`src/reasoning/`, its CLI, tests, documentation, and merge commit `73c4b15` before this work.

## Provider boundary and contracts

`src/ai/models.py` defines immutable `ai-model-adapter-v1` contracts:

* `AIModelRequest` identifies provider/version, model, reasoning context, execution, creation
  time, and required provider-neutral capabilities.
* `AIModelResponse` binds recursively immutable structured output to the same identities and
  execution metadata.
* `AIProviderCapabilities` reports only framework-recognized capabilities.
* `AIProviderMetadata` reports provider/version and supported model identifiers.
* `AIExecutionMetadata` reports lifecycle timestamps and nullable, non-negative token
  accounting placeholders.

Every contract serializes deterministically as sorted JSON. Identifiers and timestamps are
caller/provider supplied: the framework performs no inference and does not manufacture
nondeterministic current times.

## Lifecycle

1. Application code obtains an immutable context from `ReasoningContextBuilder`.
2. It explicitly selects a registered provider and constructs a request bound to the
   context's content identifier.
3. `AIModelAdapter` validates request, registry compatibility, and exact context identity.
4. The provider validates the request and supplied reasoning context.
5. The provider returns `AIModelResponse`; the adapter validates response type and all
   request/response identities before returning it.

No provider exists in v1, so no model execution, prompt construction, or network request is
possible in the shipped application.

## Registry and validation

`AIProviderRegistry` is an in-memory, explicit registry. Registration, sorted lookup and
capability discovery, duplicate detection, exact version reporting, and request validation
are deterministic. Registration rejects malformed lowercase provider/model identifiers,
non-semantic versions, unknown schemas, invalid contracts, and unsupported capabilities.
Request validation rejects absent/content-invalid context identifiers, missing identities,
unsupported models or capabilities, and incompatible exact provider versions with typed
errors.

There is intentionally no dynamic plugin loading, reflection, entry-point processing, or
filesystem discovery. The CLI's empty registry accurately reports no implementations:
`mtg-lab ai providers`, `mtg-lab ai capabilities`, and `mtg-lab ai validate` emit JSON and
expose no provider-specific operations.

## Future provider integration

A future separately reviewed provider implements `AIModelProvider`, declares only supported
framework contracts, and is registered explicitly by composition-root code. It must consume
the supplied `ReasoningContextResult`; direct persistence access is outside the interface and
architecturally forbidden. Provider implementations belong downstream of `src/ai` and must
not add provider-specific code to canonical, query, analytics, semantic, or reasoning
packages.

## Exclusions

This phase adds no OpenAI, Anthropic, Gemini, Ollama, or other provider; no SDK or runtime
dependency; no embeddings, vector search, prompts, inference, natural-language answers, or
canonical mutations. It does not redesign repository boundaries or canonical contracts.
