# Bounded hypothetical mana context v1

This read-only successor starts at canonical main
`5cbe0425e7ff8d9d6f0c7f4859f48fea5bfe8cab`, tree
`1fd9796a564fbf46a6e30bbd43c8084950eff2cb`. Merged #222 has ordered parents
`15b04687a11b1204bd8e7eb21e6b41a8b0ccb373` and reviewed head
`cf2c027953cb803f1b4efd80c70b8fd5576e3908`, with that same tree.
Architecture v13 remains ACTIVE APPROVED, Decision 017 ACCEPTED; repository-first
governance is unchanged.

Only the existing six lands and nine accepted subjects are supported. Admission
calls the actual existing explanation consumer, which calls the actual decision
consumer and validates retained catalog, Card evidence, original interpretations,
rule packages and exact owner decision. No hypothetical input supplies semantic
or source authority. One admission is shared for subsequent subject/comparison
calls. Each new public admission revalidates current evidence. No historical
positive fixture replaces incompatible current evidence.

Accepted owner decision:
`sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075`.
Collection: `sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e`.
Plan: `sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5`.
Context: `sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478`.
The nine accepted candidates and all original explanation, assessment, behavior,
composition and source identities are bound into the new reports or their exact
references. Original reports and records are not rewritten.

## Explicit contract and states

Input schema/domain: `card-rules-hypothetical-mana-input-v1`.
`make_scenario(assumptions)` seals a canonical record containing schema_version,
assumptions, input_authority and scenario_id. Identity uses the existing
domain-separated canonical content hash, excluding only its own identity field.
`validate_scenario` reproduces it exactly; `parse_scenario` accepts canonical
UTF-8 bytes with final LF and rejects duplicate keys, floats, unknown fields and
incorrect identities. Input bound is 4,096 bytes.

Each assumption has exactly `dimension` and `value`. Only:

- `controlled_swamp_count`: an exact integer from 0 through 1,000,000 inclusive;
  booleans, strings, negatives and fractional values reject. This is supplied
  arithmetic context, never independent land counting or Swamp recognition.
- `commander_color_identity`: an explicit list of distinct strings in canonical
  W, U, B, R, G order. Empty `[]` is valid. Foreign colors, duplicates and
  noncanonical order reject. No commander, format, real identity or actual
  palette is inferred.

At most four entries and two per dimension are permitted. An identical duplicate
entry rejects. Two different valid values for one dimension are `CONFLICTING`;
no value is selected and no dependent consequence is emitted. Submitted premises
and their order remain bound in the input identity.

`UNSPECIFIED` means no required hypothetical input was supplied. Missing remains
unknown rather than zero or an empty identity. Fixed output and explainable-only
subjects need no new hypothetical input; their state stays UNSPECIFIED with an
empty required-input list, while the accepted written capability remains visible.
`SUPPLIED` means an explicit valid assumption, never actual availability.
`UNSUPPORTED` is an explicit public error for foreign selectors, out-of-scope
inputs or unsupported claims. Such errors do not emit a partial report.
`CONFLICTING` is a report state retaining contradictory assumptions and a conflict
finding, with no dependent output. CLI returns exit 3 with that complete report;
unsupported/invalid inputs return exit 2 with empty stdout.

## Deterministic policy and public use

The generic calculation receives only a closed structured descriptor and validated
scenario. It routes by accepted output pattern/dependency, never by Card names,
subject IDs, free-form text parsing or provider annotations. Its pure policy tests
are synthetic conditional calculations, not observed games or new approved Card
interpretations. The public adapter is the evidence admission boundary.

A supplied count N substitutes into the accepted per-Swamp written instruction as
quantity N of B. The entire `{2}, {T}` cost stays separate. No net benefit,
break-even calculation, access to payment, or assumption that Coffers is a Swamp
is introduced. A supplied commander identity supplies only its members as the
written color-choice possibilities. An explicit empty set supplies no possible
colors within that assumption; it establishes no general actual-unusability claim.
Fixed colorless output and unrestricted any-color choices remain source-bound
written descriptions, without invented game-state inputs.

Port's paid targeted utility stays separate from its mana activation. City's
triggered damage stays separate from its mana activation, with general triggered
procedure unresolved. Citadel's color-choice ability retains its conditional
same-ability damage clause; the colorless ability does not inherit it. No target,
event, tapping action, trigger, damage, prevention or response sequence is executed.

API modules: `card_rules_pilot.mana_scenario` and `mana_scenario_policy`.
Use `load_mana_scenarios(**decision_arguments)` with the same required independent
roots/pins as the existing explanation/decision consumers. The immutable consumer
exposes `evaluate(subject_id, scenario=None)`, `compare(group, scenario=None)`,
`provenance(subject_id)`, `check()`, `validate_report`, `parse_report`, and
`detailed(reference)`. Decoded views are independent. Validation regenerates the
expected calculations and report from privately owned admitted premises.

Comparisons retain the four existing groups and original comparison identity.
Only inputs belonging to a selected dependency are permitted. They are filtered
to that dependency's subject; they do not leak into another subject. Costs,
ownership, conditional outputs, missing inputs and limitations remain separate.
No strategic ranking or general superiority follows.

CLI: `PYTHONPATH=src python -m card_rules_pilot.mana_scenario_cli --review-root
reference-reviews subject coffers-mana ... --swamp-count 5`. Replace `...` with
the existing decision CLI's required catalog/mechanical/cohort/decision roots and
expected profile/query/plan/decision pins. Other commands are `compare GROUP`,
`provenance SUBJECT` and `check`; `--json` selects canonical JSON. Tower uses
`--colors WB`; explicit empty identity is `--colors ''`. Repeated different
`--swamp-count` or `--colors` options submit conflicting premises. There is no
natural-language parser, arbitrary game-state object, persistence or mutation API.

Report schema/domain: `card-rules-hypothetical-mana-report-v1`.
Calculation schema/domain: `card-rules-hypothetical-mana-calculation-v1`.
Canonical report bound is 65,536 bytes; readable UTF-8 bound 32,768 bytes. No
inherited bound or timeout changes. Full original 689,253-byte evidence is retained
once privately and available through its integrity-checked route, never embedded
in each result. Reports bind precise input/scenario identities, accepted candidate
and decision/source identities, original explanation/behavior/composition evidence,
new policy/calculation identities, hypothetical consequences, unknowns and blocked
execution. Detailed reference equality, byte count and SHA-256 are verified.

## Preservation and limits

All prior Card data, interpretations, owner decisions, rule projections, original
calculations, explanation modules/reports, publication implementation and workflows
remain unchanged. The only inherited edit enumerates exactly three new source paths
in the finite preservation adapter. Historical pending records stay pending. No
new Cards, acquisitions, interpretations, CR inspections or source projections.
Coverage remains 104 CR units / 16 projections / 24 retained land-context units.

Canonical admission=false; execution_authority=BLOCKED; semantic closure OPEN;
all ten activation responsibilities OPEN / EXECUTION_BLOCKED. Source clearance is
not_granted. Private retention, redistribution, free service, commercial service and
AI export remain NOT_ESTABLISHED. Tier A remains non-production. No payment solver,
combat, stack, priority, trigger or general mana accounting engine is introduced.

A justified future capability would be an independently reviewed context-evidence
provenance contract distinguishing hypothetical assumptions from independently
verified observations. It is not authorized or begun by this milestone.

Future milestone authorized: false
Future source projection authorized: false
Future milestone begun: false

## Actual public demonstrations and measurements

Policy identity: `sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149`. One actual admission: 3.004424 seconds. Wall times below measure actual report calculation plus canonical and readable rendering, reusing the one admitted consumer.

### Coffers zero

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: SUPPLIED
Explicit assumptions (not observations): [{"dimension": "controlled_swamp_count", "value": 0}]
Scenario: sha256:c1b4012f84500b9a11507f897bb6dcc1113633377b749c5803074afd58a3ac94
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:253950bb5b4649230a31dd7ccb9689100d6b7421b953779e62e8d2a1528604c9

Cabal Coffers / coffers-mana — SUPPLIED
Accepted written capability: Add {B} for each Swamp you control.
Local assumptions: [{"dimension": "controlled_swamp_count", "value": 0}]
Conditional written output: {"kind": "HYPOTHETICAL_WRITTEN_QUANTITY", "mana_symbol": "B", "quantity": 0}
Written cost (separate): {2}, {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: controlled_swamp_count
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Controlled Swamp count, available payment, actual output and net benefit remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:3871be23ee4ab4bca6ff3bd1254f4e35da588d1ae4684ae534181cced76defb5
Local scenario: sha256:c1b4012f84500b9a11507f897bb6dcc1113633377b749c5803074afd58a3ac94
Accepted explanation: sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7; SHA-256 83e5fe774e476cf51e9e24935c23973a08d1accaa80cd46b6adc9842ffa6c137
Evidence: {"assessment_id": "sha256:33ff8a2bd0b83dfdf0430e463a8719701fdee1f7c319fef493a95a7cf93e3e61", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48", "composition_id": "sha256:354ceb308b58b00500dbc662dfbcc11215d8c02deff457ff192dbc3cbf52180c", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "provider_record_id": "0b1cbebd-9552-4628-bbb7-e235a812063e", "record_content_identity": "sha256:ae0532e0593f09c2d2a3d484902fd53d01f4a5140a1a2113db6c538eef16c9e5", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7"}}
Pointers: {"assessment": "/assessments/7", "candidate": "/context/interpretations/candidates/7", "descriptor": "/context/interpretations/candidates/7/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Coffers five

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: SUPPLIED
Explicit assumptions (not observations): [{"dimension": "controlled_swamp_count", "value": 5}]
Scenario: sha256:347daa51afdf52f52e1e805e0cbbf09e25fdb2ec4ae15b4ca957d40a1dbf2bcd
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:5d924efddc420db71a3c6b5eb5b81337a9cd83ee0295df5dde9471760849e1cb

Cabal Coffers / coffers-mana — SUPPLIED
Accepted written capability: Add {B} for each Swamp you control.
Local assumptions: [{"dimension": "controlled_swamp_count", "value": 5}]
Conditional written output: {"kind": "HYPOTHETICAL_WRITTEN_QUANTITY", "mana_symbol": "B", "quantity": 5}
Written cost (separate): {2}, {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: controlled_swamp_count
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Controlled Swamp count, available payment, actual output and net benefit remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:5fff567accdbc2984f195b15f7f7708fa1da3e3cf61a914e9047467a09b11d22
Local scenario: sha256:347daa51afdf52f52e1e805e0cbbf09e25fdb2ec4ae15b4ca957d40a1dbf2bcd
Accepted explanation: sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7; SHA-256 83e5fe774e476cf51e9e24935c23973a08d1accaa80cd46b6adc9842ffa6c137
Evidence: {"assessment_id": "sha256:33ff8a2bd0b83dfdf0430e463a8719701fdee1f7c319fef493a95a7cf93e3e61", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48", "composition_id": "sha256:354ceb308b58b00500dbc662dfbcc11215d8c02deff457ff192dbc3cbf52180c", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "provider_record_id": "0b1cbebd-9552-4628-bbb7-e235a812063e", "record_content_identity": "sha256:ae0532e0593f09c2d2a3d484902fd53d01f4a5140a1a2113db6c538eef16c9e5", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7"}}
Pointers: {"assessment": "/assessments/7", "candidate": "/context/interpretations/candidates/7", "descriptor": "/context/interpretations/candidates/7/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Coffers unspecified

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: UNSPECIFIED
Explicit assumptions (not observations): []
Scenario: sha256:e1e0474bfcf71dca210faaa931a1e5fa947b47a3092bff9215156c7a6749d639
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:717b8a8ae27ea49ba2c40ad95e4c062537c28414c0b912d36eeb388846641e94

Cabal Coffers / coffers-mana — UNSPECIFIED
Accepted written capability: Add {B} for each Swamp you control.
Local assumptions: []
Conditional written output: null
Written cost (separate): {2}, {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: controlled_swamp_count
Missing inputs: controlled_swamp_count
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Controlled Swamp count, available payment, actual output and net benefit remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:a894affd2ea345919f9cb379ab8ff1138c5fa05d3da35d97097fe73f263be952
Local scenario: sha256:e1e0474bfcf71dca210faaa931a1e5fa947b47a3092bff9215156c7a6749d639
Accepted explanation: sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7; SHA-256 83e5fe774e476cf51e9e24935c23973a08d1accaa80cd46b6adc9842ffa6c137
Evidence: {"assessment_id": "sha256:33ff8a2bd0b83dfdf0430e463a8719701fdee1f7c319fef493a95a7cf93e3e61", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48", "composition_id": "sha256:354ceb308b58b00500dbc662dfbcc11215d8c02deff457ff192dbc3cbf52180c", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "provider_record_id": "0b1cbebd-9552-4628-bbb7-e235a812063e", "record_content_identity": "sha256:ae0532e0593f09c2d2a3d484902fd53d01f4a5140a1a2113db6c538eef16c9e5", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7"}}
Pointers: {"assessment": "/assessments/7", "candidate": "/context/interpretations/candidates/7", "descriptor": "/context/interpretations/candidates/7/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Tower WB

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: SUPPLIED
Explicit assumptions (not observations): [{"dimension": "commander_color_identity", "value": ["W", "B"]}]
Scenario: sha256:9d47b0066c10b1c620a2c34afe683d78f553cb73286c0b3ab9bd55eff6bee864
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:6b06de463953b89f6c63169e5aa5381071aca53cef7aaa66d0310fdcf075d938

Command Tower / tower-mana — SUPPLIED
Accepted written capability: Add one mana of any color in your commander's color identity.
Local assumptions: [{"dimension": "commander_color_identity", "value": ["W", "B"]}]
Conditional written output: {"colors": ["W", "B"], "empty_set_does_not_establish_actual_unusability": true, "kind": "HYPOTHETICAL_WRITTEN_COLOR_CHOICES", "quantity": 1}
Written cost (separate): {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: commander_color_identity
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Commander identity, commander color identity, permitted palette and actual output remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:9d43ad2c228f2368f7190e0424b6e0e3de49139243fffcb95fccd6957abd4db3
Local scenario: sha256:9d47b0066c10b1c620a2c34afe683d78f553cb73286c0b3ab9bd55eff6bee864
Accepted explanation: sha256:0adf34087f64ee465ec850c0e38f2b2cac820c898dbe9b240758808b8401764b; SHA-256 d711c1d588ef8ffa60fb16175a813aafe189a6eb87d15df172d21361dde499a9
Evidence: {"assessment_id": "sha256:58a66761889c6d7ef2f1006e97aa3a9352c2fb2f0381f8adb0fe33b7fdca38cf", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc", "composition_id": "sha256:e9f771703619821debe9764684dffb0958eceaffd1da6cb313a089b89b61dbc3", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "mechanical_dossier_id": "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432", "provider_record_id": "99eed556-06b8-4063-8d72-24f010dd372e", "record_content_identity": "sha256:33e27370c407f4db5911261c8a297e8c73981da10544b0f760f561c62779e2ed", "source_field_identity": "sha256:0083dc0fcf214ffeb96b30c72e680c32b5c34fd3afb8a76a982d5241c5b4ebea"}}
Pointers: {"assessment": "/assessments/8", "candidate": "/context/interpretations/candidates/8", "descriptor": "/context/interpretations/candidates/8/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Tower unspecified

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: UNSPECIFIED
Explicit assumptions (not observations): []
Scenario: sha256:e1e0474bfcf71dca210faaa931a1e5fa947b47a3092bff9215156c7a6749d639
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:0a219bf97e7abddf4e80947ea6d95ed0cd8341e284137c4746b4ef8f17a3d540

Command Tower / tower-mana — UNSPECIFIED
Accepted written capability: Add one mana of any color in your commander's color identity.
Local assumptions: []
Conditional written output: null
Written cost (separate): {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: commander_color_identity
Missing inputs: commander_color_identity
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Commander identity, commander color identity, permitted palette and actual output remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:875a289ecdfc89e3d4c93a84dd086e789e344206d81da3b9e136d4838892e639
Local scenario: sha256:e1e0474bfcf71dca210faaa931a1e5fa947b47a3092bff9215156c7a6749d639
Accepted explanation: sha256:0adf34087f64ee465ec850c0e38f2b2cac820c898dbe9b240758808b8401764b; SHA-256 d711c1d588ef8ffa60fb16175a813aafe189a6eb87d15df172d21361dde499a9
Evidence: {"assessment_id": "sha256:58a66761889c6d7ef2f1006e97aa3a9352c2fb2f0381f8adb0fe33b7fdca38cf", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc", "composition_id": "sha256:e9f771703619821debe9764684dffb0958eceaffd1da6cb313a089b89b61dbc3", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "mechanical_dossier_id": "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432", "provider_record_id": "99eed556-06b8-4063-8d72-24f010dd372e", "record_content_identity": "sha256:33e27370c407f4db5911261c8a297e8c73981da10544b0f760f561c62779e2ed", "source_field_identity": "sha256:0083dc0fcf214ffeb96b30c72e680c32b5c34fd3afb8a76a982d5241c5b4ebea"}}
Pointers: {"assessment": "/assessments/8", "candidate": "/context/interpretations/candidates/8", "descriptor": "/context/interpretations/candidates/8/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Tower explicit empty

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: SUPPLIED
Explicit assumptions (not observations): [{"dimension": "commander_color_identity", "value": []}]
Scenario: sha256:84be758a66648ac296d5afd0b17aabaa05976a3efce13d9370549d934e30c24a
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:9ea3db2ae6dd43591bb58c9bb010ea787d863a8df722d57b1b3b242a73186ef6

Command Tower / tower-mana — SUPPLIED
Accepted written capability: Add one mana of any color in your commander's color identity.
Local assumptions: [{"dimension": "commander_color_identity", "value": []}]
Conditional written output: {"colors": [], "empty_set_does_not_establish_actual_unusability": true, "kind": "HYPOTHETICAL_WRITTEN_COLOR_CHOICES", "quantity": 1}
Written cost (separate): {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: commander_color_identity
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Commander identity, commander color identity, permitted palette and actual output remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:040b62f8c225904e0701a3c1019f40fe73c2bff673c48ac3d7d963072fe97b9a
Local scenario: sha256:84be758a66648ac296d5afd0b17aabaa05976a3efce13d9370549d934e30c24a
Accepted explanation: sha256:0adf34087f64ee465ec850c0e38f2b2cac820c898dbe9b240758808b8401764b; SHA-256 d711c1d588ef8ffa60fb16175a813aafe189a6eb87d15df172d21361dde499a9
Evidence: {"assessment_id": "sha256:58a66761889c6d7ef2f1006e97aa3a9352c2fb2f0381f8adb0fe33b7fdca38cf", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc", "composition_id": "sha256:e9f771703619821debe9764684dffb0958eceaffd1da6cb313a089b89b61dbc3", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "mechanical_dossier_id": "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432", "provider_record_id": "99eed556-06b8-4063-8d72-24f010dd372e", "record_content_identity": "sha256:33e27370c407f4db5911261c8a297e8c73981da10544b0f760f561c62779e2ed", "source_field_identity": "sha256:0083dc0fcf214ffeb96b30c72e680c32b5c34fd3afb8a76a982d5241c5b4ebea"}}
Pointers: {"assessment": "/assessments/8", "candidate": "/context/interpretations/candidates/8", "descriptor": "/context/interpretations/candidates/8/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Coffers versus Wastes

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: SUPPLIED
Explicit assumptions (not observations): [{"dimension": "controlled_swamp_count", "value": 5}]
Scenario: sha256:347daa51afdf52f52e1e805e0cbbf09e25fdb2ec4ae15b4ca957d40a1dbf2bcd
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:48c5f16aa7cbe9f67915d1e0085d5113eeb0932f7e485725c423cb9b4cac3f5c

Snow-Covered Wastes / snow-wastes-mana — UNSPECIFIED
Accepted written capability: Add {C}.
Local assumptions: []
Conditional written output: {"kind": "FIXED_WRITTEN_OUTPUT", "mana_symbol": "C", "quantity": 1}
Written cost (separate): {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs:
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Available untapped resource, current activation permission and payment feasibility remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:0ca5def62732cb546d919efd7058f945705257b94568bc1e365641eb77d17e00
Local scenario: sha256:e1e0474bfcf71dca210faaa931a1e5fa947b47a3092bff9215156c7a6749d639
Accepted explanation: sha256:b685480e56593929adb221f806e65b90ff2f8070bcfea446ca132c49d91b9a80; SHA-256 751eec0321f5d064db16680a2836f04ac3d24b43215f976546c4f482f320a38c
Evidence: {"assessment_id": "sha256:918b73b22f1d41eabbfc282c86c52663346467a803721ffbbeec0c160d8c47de", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:7ce81b50485c09cb3ed789db287142253b55541c067d275f6750f1c9a2bc02e5", "composition_id": "sha256:fac1de82d3d366c6dcc64f0f61b24726fe0904ebeecd46da90e4ef99af069b50", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "46a07b53-ff58-4bd6-80dd-ded2eb0e29a3", "mechanical_dossier_id": "sha256:025c47309f73d623564ef6aa3b1ba6a646ea9e5acc84df9089387269345b6d91", "provider_record_id": "3bce79b7-f964-4442-b3db-3ecffbba8d92", "record_content_identity": "sha256:8533ca89d03b32fe0abd09860aeca37eee182ef77076b44df60f0875ebb40f58", "source_field_identity": "sha256:0c53f7694000b2c4298fadbf11a0607ad5f8972bc66c38fbb798e7051f33ee3f"}}
Pointers: {"assessment": "/assessments/0", "candidate": "/context/interpretations/candidates/0", "descriptor": "/context/interpretations/candidates/0/descriptive_readings"}

Cabal Coffers / coffers-mana — SUPPLIED
Accepted written capability: Add {B} for each Swamp you control.
Local assumptions: [{"dimension": "controlled_swamp_count", "value": 5}]
Conditional written output: {"kind": "HYPOTHETICAL_WRITTEN_QUANTITY", "mana_symbol": "B", "quantity": 5}
Written cost (separate): {2}, {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: controlled_swamp_count
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Controlled Swamp count, available payment, actual output and net benefit remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:5fff567accdbc2984f195b15f7f7708fa1da3e3cf61a914e9047467a09b11d22
Local scenario: sha256:347daa51afdf52f52e1e805e0cbbf09e25fdb2ec4ae15b4ca957d40a1dbf2bcd
Accepted explanation: sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7; SHA-256 83e5fe774e476cf51e9e24935c23973a08d1accaa80cd46b6adc9842ffa6c137
Evidence: {"assessment_id": "sha256:33ff8a2bd0b83dfdf0430e463a8719701fdee1f7c319fef493a95a7cf93e3e61", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48", "composition_id": "sha256:354ceb308b58b00500dbc662dfbcc11215d8c02deff457ff192dbc3cbf52180c", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "provider_record_id": "0b1cbebd-9552-4628-bbb7-e235a812063e", "record_content_identity": "sha256:ae0532e0593f09c2d2a3d484902fd53d01f4a5140a1a2113db6c538eef16c9e5", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7"}}
Pointers: {"assessment": "/assessments/7", "candidate": "/context/interpretations/candidates/7", "descriptor": "/context/interpretations/candidates/7/descriptive_readings"}
Comparison: {"dimensions": ["conditional_written_output", "written_cost", "ownership", "missing_inputs"], "finding": "Compare the displayed written outputs, separate costs and ownership under the explicit assumptions. No actual usability, payment feasibility, net mana or strategic advantage follows.", "original_comparison_id": "sha256:b1e922fae256d2a0e73e919565e582a1a2395709dc41899f23c210efb7072764"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Tower versus City

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: SUPPLIED
Explicit assumptions (not observations): [{"dimension": "commander_color_identity", "value": ["W", "B"]}]
Scenario: sha256:9d47b0066c10b1c620a2c34afe683d78f553cb73286c0b3ab9bd55eff6bee864
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:2aff0103f842e5eee31c9f0b43593170b20c41fce68ac628e0954de872756a17

Command Tower / tower-mana — SUPPLIED
Accepted written capability: Add one mana of any color in your commander's color identity.
Local assumptions: [{"dimension": "commander_color_identity", "value": ["W", "B"]}]
Conditional written output: {"colors": ["W", "B"], "empty_set_does_not_establish_actual_unusability": true, "kind": "HYPOTHETICAL_WRITTEN_COLOR_CHOICES", "quantity": 1}
Written cost (separate): {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: commander_color_identity
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Commander identity, commander color identity, permitted palette and actual output remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:9d43ad2c228f2368f7190e0424b6e0e3de49139243fffcb95fccd6957abd4db3
Local scenario: sha256:9d47b0066c10b1c620a2c34afe683d78f553cb73286c0b3ab9bd55eff6bee864
Accepted explanation: sha256:0adf34087f64ee465ec850c0e38f2b2cac820c898dbe9b240758808b8401764b; SHA-256 d711c1d588ef8ffa60fb16175a813aafe189a6eb87d15df172d21361dde499a9
Evidence: {"assessment_id": "sha256:58a66761889c6d7ef2f1006e97aa3a9352c2fb2f0381f8adb0fe33b7fdca38cf", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc", "composition_id": "sha256:e9f771703619821debe9764684dffb0958eceaffd1da6cb313a089b89b61dbc3", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "mechanical_dossier_id": "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432", "provider_record_id": "99eed556-06b8-4063-8d72-24f010dd372e", "record_content_identity": "sha256:33e27370c407f4db5911261c8a297e8c73981da10544b0f760f561c62779e2ed", "source_field_identity": "sha256:0083dc0fcf214ffeb96b30c72e680c32b5c34fd3afb8a76a982d5241c5b4ebea"}}
Pointers: {"assessment": "/assessments/8", "candidate": "/context/interpretations/candidates/8", "descriptor": "/context/interpretations/candidates/8/descriptive_readings"}

City of Brass / city-mana — UNSPECIFIED
Accepted written capability: Add one mana of any color.
Local assumptions: []
Conditional written output: {"colors": ["W", "U", "B", "R", "G"], "kind": "WRITTEN_ANY_COLOR_CHOICE", "quantity": 1}
Written cost (separate): {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs:
Missing inputs:
Conflict: None
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Actual activation, mana choice/output and whether any tapped event or damage occurs remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:492d4c1053d479863a01a262fc19290d3d85bb6a4711c76ee4ad7273c16d5c29
Local scenario: sha256:e1e0474bfcf71dca210faaa931a1e5fa947b47a3092bff9215156c7a6749d639
Accepted explanation: sha256:4df49e66ec8689f85fdf5e8a655047b5241844db1ea299a5cd710b024282ae6a; SHA-256 f816c621f404323711d5ffad094a2448457c715ff5aeaa649a89f98e4705eb70
Evidence: {"assessment_id": "sha256:482ecd0cf1535254b57aba5f9e962a90d483a96738c9c1400d18afa9980d16da", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:75a3a8dd76a16138dfbd8528d2680109e3f9ca542538df6b0fe6298a63e84148", "composition_id": "sha256:a8c34fa5d9107d526973e771f5cffe9dc4e519913964010f0257b0003f02620b", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "f25351e3-539b-4bbc-b92d-6480acf4d722", "mechanical_dossier_id": "sha256:838daa12cfb53634aa9699e1109863d19ed8a3937406bd9f080021ba7ff356f2", "provider_record_id": "10eb8117-c009-4d50-b3fb-4879081f38be", "record_content_identity": "sha256:80ef84aabe386846245886a551dbc22a63224557840d2b009ec4ea9b575c12ea", "source_field_identity": "sha256:fc1205f58d5b528c7eb9ffe6291a2265cd46fdffac9a69642f71eee11c2b914f"}}
Pointers: {"assessment": "/assessments/3", "candidate": "/context/interpretations/candidates/3", "descriptor": "/context/interpretations/candidates/3/descriptive_readings"}
Comparison: {"dimensions": ["conditional_written_output", "written_cost", "ownership", "missing_inputs"], "finding": "Compare the displayed written outputs, separate costs and ownership under the explicit assumptions. No actual usability, payment feasibility, net mana or strategic advantage follows.", "original_comparison_id": "sha256:378a75ccd74039f7a5769cd58f9017807fa3611699023f3f882a14e5fc4528fe"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

### Explicit conflict

```text
MTG Lab — hypothetical mana context
Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.
State: CONFLICTING
Explicit assumptions (not observations): [{"dimension": "controlled_swamp_count", "value": 0}, {"dimension": "controlled_swamp_count", "value": 5}]
Scenario: sha256:e2858af41e32a43b8b0f9640620d26c7a1fac7d759f7460b68d866a7e4747c3d
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Plan: sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5
Context: sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478
Policy: sha256:e31393a947305efe46abe207ef951209dc47898ceb6ad917a1da5db900f15149
Report: sha256:2d3c3f96de2579c23b89dab3e607c5dcf76881a2c8ee733ece21002258931b22

Cabal Coffers / coffers-mana — CONFLICTING
Accepted written capability: Add {B} for each Swamp you control.
Local assumptions: [{"dimension": "controlled_swamp_count", "value": 0}, {"dimension": "controlled_swamp_count", "value": 5}]
Conditional written output: null
Written cost (separate): {2}, {T}
Ownership: no_additional_effect; conditional damage clause, not executed: None
Mode: WRITTEN_OUTPUT_ONLY
Required hypothetical inputs: controlled_swamp_count
Missing inputs:
Conflict: Different premises for the same dependency; no value selected.
Unknowns: No actual activation, untapped resource, legal action, payment or mana production is established. Actual Swamp count, commander identity, format legality, available resources and usable mana remain unevaluated. No net mana, break-even threshold, payment feasibility, spell affordability, target, tapping event, trigger firing, damage, prevention, stack or response sequence is calculated. Changed text, gained abilities, copies and external effects remain outside the accepted retained-text scope.
Retained unknowns: Controlled Swamp count, available payment, actual output and net benefit remain unknown.
Unsupported conclusions: actual mana production, net usable mana, payment feasibility, legal action, strategic superiority
Calculation: sha256:b8fa625bacacc904c1ef27dc30318139eb038a7b6ab4daab044c1ca8c47646a1
Local scenario: sha256:e2858af41e32a43b8b0f9640620d26c7a1fac7d759f7460b68d866a7e4747c3d
Accepted explanation: sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7; SHA-256 83e5fe774e476cf51e9e24935c23973a08d1accaa80cd46b6adc9842ffa6c137
Evidence: {"assessment_id": "sha256:33ff8a2bd0b83dfdf0430e463a8719701fdee1f7c319fef493a95a7cf93e3e61", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48", "composition_id": "sha256:354ceb308b58b00500dbc662dfbcc11215d8c02deff457ff192dbc3cbf52180c", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "provider_record_id": "0b1cbebd-9552-4628-bbb7-e235a812063e", "record_content_identity": "sha256:ae0532e0593f09c2d2a3d484902fd53d01f4a5140a1a2113db6c538eef16c9e5", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7"}}
Pointers: {"assessment": "/assessments/7", "candidate": "/context/interpretations/candidates/7", "descriptor": "/context/interpretations/candidates/7/descriptive_readings"}
Full evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.
Source clearance=not_granted; permissions={"ai_export": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED", "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED"}; Tier A non-production.
```

Actual unsupported-input demonstration: `UNSUPPORTED: input outside selected dependencies`. No partial report.

Actual coherent nested-calculation and enclosing-report rehash tamper rejection: `fixed authored contract or exact evidence binding mismatch`.

Actual canonical CLI `subject coffers-mana --swamp-count 0`: exit 0, report `sha256:253950bb5b4649230a31dd7ccb9689100d6b7421b953779e62e8d2a1528604c9`; exact JSON byte parity with API: verified.

Actual canonical CLI `subject tower-mana --colors WB`: exit 0, report `sha256:6b06de463953b89f6c63169e5aa5381071aca53cef7aaa66d0310fdcf075d938`; exact JSON byte parity with API: verified.

Actual canonical CLI `subject coffers-mana --swamp-count 0 --swamp-count 5`: exit 3, report `sha256:2d3c3f96de2579c23b89dab3e607c5dcf76881a2c8ee733ece21002258931b22`; exact JSON byte parity with API: verified.

| Scenario/view | Report identity | Canonical bytes | Readable bytes | Seconds |
|---|---|---:|---:|---:|
| Coffers zero | `sha256:253950bb5b4649230a31dd7ccb9689100d6b7421b953779e62e8d2a1528604c9` | 4847 | 4143 | 0.003248 |
| Coffers five | `sha256:5d924efddc420db71a3c6b5eb5b81337a9cd83ee0295df5dde9471760849e1cb` | 4847 | 4143 | 0.002900 |
| Coffers unspecified | `sha256:717b8a8ae27ea49ba2c40ad95e4c062537c28414c0b912d36eeb388846641e94` | 4714 | 3997 | 0.002908 |
| Tower WB | `sha256:6b06de463953b89f6c63169e5aa5381071aca53cef7aaa66d0310fdcf075d938` | 4956 | 4259 | 0.003012 |
| Tower unspecified | `sha256:0a219bf97e7abddf4e80947ea6d95ed0cd8341e284137c4746b4ef8f17a3d540` | 4744 | 4029 | 0.002906 |
| Tower explicit empty | `sha256:9ea3db2ae6dd43591bb58c9bb010ea787d863a8df722d57b1b3b242a73186ef6` | 4935 | 4235 | 0.002894 |
| Coffers versus Wastes | `sha256:48c5f16aa7cbe9f67915d1e0085d5113eeb0932f7e485725c423cb9b4cac3f5c` | 8148 | 7143 | 0.003125 |
| Tower versus City | `sha256:2aff0103f842e5eee31c9f0b43593170b20c41fce68ac628e0954de872756a17` | 8280 | 7286 | 0.003112 |
| Explicit conflict | `sha256:2d3c3f96de2579c23b89dab3e607c5dcf76881a2c8ee733ece21002258931b22` | 4944 | 4241 | 0.002903 |
| subject snow-wastes-mana | `sha256:f0e6234661496126a9d9a6d2bebb4685aadb133ce685b25febc83d6690a665e6` | 4716 | 4004 | 0.002872 |
| subject port-mana | `sha256:36cad3ef545a85b29bca372bfa53f6b6c05260e67e2ca75aada7aa01bb5ae4c1` | 4680 | 3975 | 0.002811 |
| subject port-utility | `sha256:6741de4e96e5031f9236a5c61142a65a75c7d1cedc9b7093a374ff658ce1b7fb` | 4655 | 3942 | 0.002835 |
| subject city-mana | `sha256:0559e1252a3d667fdee73ad9a144e9c19335907222ad9dd06b833d7efae3cd25` | 4732 | 4031 | 0.002800 |
| subject city-damage-trigger | `sha256:63581359fd47f6e28a4ccceab8feaf60309fa81c8c5db8868763a5af1b526e05` | 4726 | 4006 | 0.002817 |
| subject citadel-colorless | `sha256:8cac13b63734d51cb02832a50ea17a59cf3e783fba0af146d5ec22c56bd75e1a` | 4691 | 3978 | 0.002852 |
| subject citadel-color-choice | `sha256:a11f0d67e3a921ed92232a8915dba824bf8626aa7181bd009cde914a64820816` | 4789 | 4075 | 0.002798 |
| subject coffers-mana | `sha256:717b8a8ae27ea49ba2c40ad95e4c062537c28414c0b912d36eeb388846641e94` | 4714 | 3997 | 0.002862 |
| subject tower-mana | `sha256:0a219bf97e7abddf4e80947ea6d95ed0cd8341e284137c4746b4ef8f17a3d540` | 4744 | 4029 | 0.002838 |
| comparison mana-and-utility | `sha256:6a98a684bcdd76cad006b3fd699a90f24c61e676ced77ccbb83b43040e518ff5` | 10844 | 9509 | 0.003222 |
| comparison damage-ownership | `sha256:5f182cc23519b53b4db164c87daf6019cfbd4c151a488d7368e8462846d2ce01` | 13919 | 12270 | 0.003487 |
| comparison variable-output | `sha256:48c5f16aa7cbe9f67915d1e0085d5113eeb0932f7e485725c423cb9b4cac3f5c` | 8148 | 7143 | 0.003152 |
| comparison color-context | `sha256:2aff0103f842e5eee31c9f0b43593170b20c41fce68ac628e0954de872756a17` | 8280 | 7286 | 0.003178 |

Complete canonical-base preservation audit: 2986 inherited files / 91979016 original bytes. 2985 files byte-identical; every inherited mode preserved. The sole inherited edit is the finite three-source-path adapter, with exact reversal tested. No inherited document is edited.
