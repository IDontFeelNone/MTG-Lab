# Accepted land explanations v1

This bounded read-only presentation milestone starts at main
`15b04687a11b1204bd8e7eb21e6b41a8b0ccb373`, tree
`4cc8dfd108c6dd365af65a19fdfc8d3dfa800513`. It admits only the exact
owner decision `sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075`
through `load_land_decision`, including its actual catalog, retained evidence,
original interpretation and decision reproduction. Collection:
`sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e`.
No pending record is promoted or rewritten.

`card_rules_pilot.land_explanation.load_land_explanations` accepts the same
keyword arguments as `load_land_decision`. One admission loads the catalog and
rule packages once. Subsequent calls use privately owned immutable bytes. Each
new public admission validates current sources again. Supported methods:
`explain_subject`, `explain_card`, `compare`, `provenance`, `check`,
`validate_report`, `parse_report`, and `detailed(reference)`.
The latter verifies the complete original overview's identity, bytes and SHA-256.
Reports carry that exact route; detailed evidence remains complete.

The separately versioned policy uses explicit output patterns, dependencies,
costs, ownership states and original computed consequences. Every finding has a
finite template ID and candidate/assessment JSON pointers. No name, subject ID,
substring, LLM, embedding, network or external API selects a conclusion.
Comparisons group equal or differing structured dimensions and shared potential
mana findings. A capability difference supplies no strategic ranking.

Report schema: `card-rules-accepted-land-explanation-report-v1`.
Canonical JSON is bounded to 65,536 bytes and readable UTF-8 to 32,768 bytes for
all views. Individual explanations are normally about 5–8 KB including exact
references; comparison bounds allow all material uncertainty. Readable output
contains findings and references without full dossiers, rule packages or raw
historical aggregate JSON. `to_dict` returns independent decoded views.
Exact recomputation rejects unknown fields, wrong types, foreign selectors and
coherently rehashed report changes; canonical parsing rejects duplicate keys.

CLI: `python -m card_rules_pilot.land_explanation_cli --review-root reference-reviews`
followed by `subject SUBJECT`, `card 'CARD NAME'`, `compare GROUP`,
`provenance SUBJECT` or `check`. Each command requires the same root and
independent identity options as `land_decision_cli`; add `--json` for canonical
output. Closed selectors expose precisely nine existing subjects, six exact
Card names and four original comparison groups. Unsupported requests explicitly
fail with exit 2 and no partial stdout. There are no mutation commands.

Historical sources, data, decision, permissions, architecture and workflows are
unchanged. The sole inherited code change enumerates three new source paths in
the preservation adapter. Coverage stays 104 CR units / 16 projections and a
24-unit retained land context. New projections and Cards: zero.
Architecture v13 ACTIVE APPROVED and Decision 017 ACCEPTED remain binding.
Canonical gameplay admission is false; execution BLOCKED; semantic closure OPEN;
all ten activation responsibilities OPEN / EXECUTION_BLOCKED. Source clearance
is not_granted. Private retention, redistribution, free service, commercial
service and AI export remain NOT_ESTABLISHED. Tier A remains non-production.

Port abilities remain separate; City damage belongs to its separate trigger with
broad-603 procedure unresolved; Citadel color-choice owns its damage while its
colorless ability does not. Coffers lacks Swamp count and payment context;
Tower lacks commander identity and palette. No actual or net output, legal action
or successful payment follows. Stronger conclusions need those inputs and
additional rule/source authority. Next recommended capability is a separately
reviewed context-input contract, without executing gameplay.

Stop for independent PM review and owner approval. Future milestone authorized:
false. Future source projection authorized: false. Future milestone begun: false.

## Measured report identities and UTF-8 sizes

Policy: `sha256:4eefb8ceb34fb5799823d4a2881c897e6903f7eb2f3a2c5c4596ca7f854d2d6c`.

| View | Selector | JSON bytes | Readable bytes | Report ID |
|---|---|---:|---:|---|
| subject | snow-wastes-mana | 5764 | 4849 | `sha256:b685480e56593929adb221f806e65b90ff2f8070bcfea446ca132c49d91b9a80` |
| subject | port-mana | 5770 | 4862 | `sha256:74e283e8c7046749c9e737d780cdec139ee0bace3b0331b303405b53df1526d9` |
| subject | port-utility | 6002 | 5005 | `sha256:151937966f075a9a0a21ad3d72279f0098eb308ae9ad0730c78c8d1ba3cb3d13` |
| subject | city-mana | 5935 | 5017 | `sha256:4df49e66ec8689f85fdf5e8a655047b5241844db1ea299a5cd710b024282ae6a` |
| subject | city-damage-trigger | 6338 | 5272 | `sha256:c6bb34713ac38e7fa896838df37e180f40848cf268753dd855319dacd4000bc7` |
| subject | citadel-colorless | 5847 | 4931 | `sha256:fd301c6a35925bf94b3d24e52eaada2859e9cd21f78bf7f3e06e93facd8c83f7` |
| subject | citadel-color-choice | 6121 | 5181 | `sha256:a556fc6a90ae11dc748db26c4282c7ab815819ec2056e3cb94e82efbf953d077` |
| subject | coffers-mana | 6640 | 5503 | `sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7` |
| subject | tower-mana | 6456 | 5413 | `sha256:0adf34087f64ee465ec850c0e38f2b2cac820c898dbe9b240758808b8401764b` |
| card | Snow-Covered Wastes | 5764 | 4849 | `sha256:55448674fd551d65a2da40d9c027ffd95c1e7720143cfca06607a57cb14cbff4` |
| card | Rishadan Port | 10726 | 9017 | `sha256:75611a551cb8ceb8fb60c2d81f01a24eed8bc50ec1a2950185b366280d8ed7f3` |
| card | City of Brass | 11220 | 9439 | `sha256:a3a0f5acbc3dcc6eef0ff9dd5e83049c78c3964e5846a8f0a3c56d43b8548179` |
| card | Tarnished Citadel | 10910 | 9262 | `sha256:688cf4321e6578f3f2850429272ac5c4b501038048913fc6a4f2f42c08828382` |
| card | Cabal Coffers | 6638 | 5503 | `sha256:567e9a7c8d15603d9978a55a278ca4b25b4b8677a171623b1dc23714d267812e` |
| card | Command Tower | 6456 | 5413 | `sha256:abe76e354015fadff9e4952dd4255af08a889fa276434d0287831b109fcbface` |
| comparison | mana-and-utility | 16929 | 14444 | `sha256:d3020a92127d058feaafec09cf29bae5ea742a25d0b940f8e125196e537103cd` |
| comparison | damage-ownership | 23004 | 19737 | `sha256:c6143671b243abc158f64cda2da34c89ae902dcf5fbe2c53380dfe38a6118503` |
| comparison | variable-output | 12582 | 10647 | `sha256:474eb3b04e7302c391b9f2414306490e564e1f7ff30e8edf734713c6d34a8f05` |
| comparison | color-context | 12521 | 10664 | `sha256:381c0e3aec1f33d565f098edbad1ead2327523a9ab1a0c892151feb5c3f53275` |

## Actual public CLI demonstrations

Command selector: `subject coffers-mana`; exit 0.

```text
MTG Lab — accepted land explanation
Historical retained-text acceptance only; original pending records preserved. No current Oracle verification, current legal action, actual payment, output or damage is established.
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Policy: sha256:4eefb8ceb34fb5799823d4a2881c897e6903f7eb2f3a2c5c4596ca7f854d2d6c
Report: sha256:de313f93d6fe77a706620b1023a463f022e62de310e2f91ceac9e9172367aea7
Canonical admission=false; execution=BLOCKED.

Cabal Coffers / coffers-mana
{2}, {T}: Add {B} for each Swamp you control.
capability: Retained written capability: Add {B} for each Swamp you control.
  Evidence: /candidate/descriptive_readings/output/written_instruction; rules:
capability: Accepted premises conditionally support potential mana production; current or net output is not established.
  Evidence: /assessment/classification/satisfied_requirements, /candidate/descriptive_readings/output/actual_output; rules: 605.2
cost: Written activation cost: {2}, {T}. Payment feasibility remains unknown.
  Evidence: /candidate/descriptive_readings/cost/written_cost, /candidate/descriptive_readings/cost/payment_feasibility; rules:
restriction: Output depends on the controlled Swamp count, which is unknown. Potential production establishes neither actual nor net output.
  Evidence: /candidate/descriptive_readings/output/dependencies/0, /candidate/descriptive_readings/conditions/supplied_game_inputs; rules:
restriction: Available payment is unknown; the written cost does not establish payment feasibility.
  Evidence: /candidate/descriptive_readings/output/dependencies/1, /candidate/descriptive_readings/conditions/supplied_game_inputs; rules:
additional_effect: The accepted complete-subject reading assigns no additional effect to this selected ability. Costs, targets, output and damage from other abilities do not transfer.
  Evidence: /candidate/descriptive_readings/effect_ownership/state, /assessment/additional_effect_composition/status; rules:
procedure: Conditional procedure: That qualifying activation resolves immediately after activation without becoming a stack object. Its stack-object targeting, countering and response implications concern this ability only.
  Evidence: /assessment/behavior/consequences/0; rules: 605.3b
unknown: Pre-activation priority is unknown, so applicability of the conditional priority-return implication remains unknown.
  Evidence: /assessment/behavior/consequences/4; rules: 405.6c
unknown: Controlled Swamp count, available payment, actual output and net benefit remain unknown.
  Evidence: /candidate/unresolved/0; rules:
limitation: This is a capability explanation within accepted historical retained-text scope. It establishes no current legal action, completed payment, actual output, damage, or strategic advantage.
  Evidence: /candidate/classification_present_usability_distinct, /candidate/limitations, /assessment/behavior/scope_restrictions; rules:
Provenance: {"assessment_id": "sha256:33ff8a2bd0b83dfdf0430e463a8719701fdee1f7c319fef493a95a7cf93e3e61", "assessment_pointer": "/assessments/7", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48", "candidate_pointer": "/context/interpretations/candidates/7", "composition_id": "sha256:354ceb308b58b00500dbc662dfbcc11215d8c02deff457ff192dbc3cbf52180c", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "provider_record_id": "0b1cbebd-9552-4628-bbb7-e235a812063e", "record_content_identity": "sha256:ae0532e0593f09c2d2a3d484902fd53d01f4a5140a1a2113db6c538eef16c9e5", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7"}, "subject_binding": {"card_id": "7358e164-5704-4e78-9b21-6a9bf2a968ce", "complete_field_value": "{2}, {T}: Add {B} for each Swamp you control.", "identity_scope": "local_review_subject_only", "mechanical_dossier_id": "sha256:2c12e2c4f063e6d0f3f120ce9a4f2ba04a79565a8f6dedd4de277ccb07e3e4a2", "owner": "host_card", "ownership_and_context_limitations": "The complete written cost and stated Swamp-count output dependency remain attached. No count, subtype recognition, net output, break-even calculation or executable sequence is supplied.", "passage_end": 45, "passage_start": 0, "selected_passage": "{2}, {T}: Add {B} for each Swamp you control.", "source_field_identity": "sha256:23efd58b7cd64f2a51c94c1e72afb04897ab9a826509f2cf00532c53ec92f8d7", "source_field_pointer": "/oracle_text", "source_record_pointer": "/19/oracle_text", "subject_id": "coffers-mana", "surrounding_after": "", "surrounding_before": "", "type_line": {"field_identity": "sha256:4565c9fc2d223ca7a76a17ba57ce302c096ae0feeccddbfe1db021fe136c762d", "source_pointer": "/type_line", "status": "known", "value": "Land"}, "unselected_context_assessment": "outside_this_subject"}}
Detailed evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
```

Command selector: `compare color-context`; exit 0.

```text
MTG Lab — accepted land explanation
Historical retained-text acceptance only; original pending records preserved. No current Oracle verification, current legal action, actual payment, output or damage is established.
Decision: sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075
Collection: sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e
Policy: sha256:4eefb8ceb34fb5799823d4a2881c897e6903f7eb2f3a2c5c4596ca7f854d2d6c
Report: sha256:381c0e3aec1f33d565f098edbad1ead2327523a9ab1a0c892151feb5c3f53275
Canonical admission=false; execution=BLOCKED.

Command Tower / tower-mana
{T}: Add one mana of any color in your commander's color identity.
capability: Retained written capability: Add one mana of any color in your commander's color identity.
  Evidence: /candidate/descriptive_readings/output/written_instruction; rules:
capability: Accepted premises conditionally support potential mana production; current or net output is not established.
  Evidence: /assessment/classification/satisfied_requirements, /candidate/descriptive_readings/output/actual_output; rules: 605.2
cost: Written activation cost: {T}. Payment feasibility remains unknown.
  Evidence: /candidate/descriptive_readings/cost/written_cost, /candidate/descriptive_readings/cost/payment_feasibility; rules:
restriction: The written color choice is restricted by commander color identity. No commander, color identity or permitted palette is supplied; unknown is not an empty palette.
  Evidence: /candidate/descriptive_readings/output/dependencies/0, /candidate/descriptive_readings/conditions/supplied_game_inputs; rules:
additional_effect: The accepted complete-subject reading assigns no additional effect to this selected ability. Costs, targets, output and damage from other abilities do not transfer.
  Evidence: /candidate/descriptive_readings/effect_ownership/state, /assessment/additional_effect_composition/status; rules:
procedure: Conditional procedure: That qualifying activation resolves immediately after activation without becoming a stack object. Its stack-object targeting, countering and response implications concern this ability only.
  Evidence: /assessment/behavior/consequences/0; rules: 605.3b
unknown: Pre-activation priority is unknown, so applicability of the conditional priority-return implication remains unknown.
  Evidence: /assessment/behavior/consequences/4; rules: 405.6c
unknown: Commander identity, commander color identity, permitted palette and actual output remain unknown.
  Evidence: /candidate/unresolved/0; rules:
limitation: This is a capability explanation within accepted historical retained-text scope. It establishes no current legal action, completed payment, actual output, damage, or strategic advantage.
  Evidence: /candidate/classification_present_usability_distinct, /candidate/limitations, /assessment/behavior/scope_restrictions; rules:
Provenance: {"assessment_id": "sha256:58a66761889c6d7ef2f1006e97aa3a9352c2fb2f0381f8adb0fe33b7fdca38cf", "assessment_pointer": "/assessments/8", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc", "candidate_pointer": "/context/interpretations/candidates/8", "composition_id": "sha256:e9f771703619821debe9764684dffb0958eceaffd1da6cb313a089b89b61dbc3", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "mechanical_dossier_id": "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432", "provider_record_id": "99eed556-06b8-4063-8d72-24f010dd372e", "record_content_identity": "sha256:33e27370c407f4db5911261c8a297e8c73981da10544b0f760f561c62779e2ed", "source_field_identity": "sha256:0083dc0fcf214ffeb96b30c72e680c32b5c34fd3afb8a76a982d5241c5b4ebea"}, "subject_binding": {"card_id": "0895c9b7-ae7d-4bb3-af17-3b75deb50a25", "complete_field_value": "{T}: Add one mana of any color in your commander's color identity.", "identity_scope": "local_review_subject_only", "mechanical_dossier_id": "sha256:b9c2ad7c634422e4938c016a0911eeb6c7f9663805edfb6f01224990e2531432", "owner": "host_card", "ownership_and_context_limitations": "The complete commander-color-identity restriction remains attached. No commander, palette or actual output is inferred from Card color identity or provider annotations; unknown context is not an empty palette.", "passage_end": 66, "passage_start": 0, "selected_passage": "{T}: Add one mana of any color in your commander's color identity.", "source_field_identity": "sha256:0083dc0fcf214ffeb96b30c72e680c32b5c34fd3afb8a76a982d5241c5b4ebea", "source_field_pointer": "/oracle_text", "source_record_pointer": "/230/oracle_text", "subject_id": "tower-mana", "surrounding_after": "", "surrounding_before": "", "type_line": {"field_identity": "sha256:4565c9fc2d223ca7a76a17ba57ce302c096ae0feeccddbfe1db021fe136c762d", "source_pointer": "/type_line", "status": "known", "value": "Land"}, "unselected_context_assessment": "outside_this_subject"}}

City of Brass / city-mana
{T}: Add one mana of any color.
capability: Retained written capability: Add one mana of any color.
  Evidence: /candidate/descriptive_readings/output/written_instruction; rules:
capability: Accepted premises conditionally support potential mana production; current or net output is not established.
  Evidence: /assessment/classification/satisfied_requirements, /candidate/descriptive_readings/output/actual_output; rules: 605.2
cost: Written activation cost: {T}. Payment feasibility remains unknown.
  Evidence: /candidate/descriptive_readings/cost/written_cost, /candidate/descriptive_readings/cost/payment_feasibility; rules:
additional_effect: The accepted complete-subject reading assigns no additional effect to this selected ability. Costs, targets, output and damage from other abilities do not transfer.
  Evidence: /candidate/descriptive_readings/effect_ownership/state, /assessment/additional_effect_composition/status; rules:
procedure: Conditional procedure: That qualifying activation resolves immediately after activation without becoming a stack object. Its stack-object targeting, countering and response implications concern this ability only.
  Evidence: /assessment/behavior/consequences/0; rules: 605.3b
unknown: Pre-activation priority is unknown, so applicability of the conditional priority-return implication remains unknown.
  Evidence: /assessment/behavior/consequences/4; rules: 405.6c
unknown: Actual activation, mana choice/output and whether any tapped event or damage occurs remain unknown.
  Evidence: /candidate/unresolved/0; rules:
limitation: This is a capability explanation within accepted historical retained-text scope. It establishes no current legal action, completed payment, actual output, damage, or strategic advantage.
  Evidence: /candidate/classification_present_usability_distinct, /candidate/limitations, /assessment/behavior/scope_restrictions; rules:
Provenance: {"assessment_id": "sha256:482ecd0cf1535254b57aba5f9e962a90d483a96738c9c1400d18afa9980d16da", "assessment_pointer": "/assessments/3", "behavior_calculation_id": "sha256:794b49138181f879dd9f77b901d438e12a1240ce9b211828d0427015a4ba92ad", "candidate_id": "sha256:75a3a8dd76a16138dfbd8528d2680109e3f9ca542538df6b0fe6298a63e84148", "candidate_pointer": "/context/interpretations/candidates/3", "composition_id": "sha256:a8c34fa5d9107d526973e771f5cffe9dc4e519913964010f0257b0003f02620b", "source_binding": {"canonical_snapshot_id": "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7", "card_id": "f25351e3-539b-4bbc-b92d-6480acf4d722", "mechanical_dossier_id": "sha256:838daa12cfb53634aa9699e1109863d19ed8a3937406bd9f080021ba7ff356f2", "provider_record_id": "10eb8117-c009-4d50-b3fb-4879081f38be", "record_content_identity": "sha256:80ef84aabe386846245886a551dbc22a63224557840d2b009ec4ea9b575c12ea", "source_field_identity": "sha256:fc1205f58d5b528c7eb9ffe6291a2265cd46fdffac9a69642f71eee11c2b914f"}, "subject_binding": {"card_id": "f25351e3-539b-4bbc-b92d-6480acf4d722", "complete_field_value": "Whenever this land becomes tapped, it deals 1 damage to you.\n{T}: Add one mana of any color.", "identity_scope": "local_review_subject_only", "mechanical_dossier_id": "sha256:838daa12cfb53634aa9699e1109863d19ed8a3937406bd9f080021ba7ff356f2", "owner": "host_card", "ownership_and_context_limitations": "The damage trigger remains a separately owned subject. Its becomes-tapped relationship is not imported as an additional effect of this activation.", "passage_end": 92, "passage_start": 61, "selected_passage": "{T}: Add one mana of any color.", "source_field_identity": "sha256:fc1205f58d5b528c7eb9ffe6291a2265cd46fdffac9a69642f71eee11c2b914f", "source_field_pointer": "/oracle_text", "source_record_pointer": "/29/oracle_text", "subject_id": "city-mana", "surrounding_after": "", "surrounding_before": "Whenever this land becomes tapped, it deals 1 damage to you.\n", "type_line": {"field_identity": "sha256:4565c9fc2d223ca7a76a17ba57ce302c096ae0feeccddbfe1db021fe136c762d", "source_pointer": "/type_line", "status": "known", "value": "Land"}, "unselected_context_assessment": "outside_this_subject"}}
Shared capabilities: [{"capability": "potential_mana", "subjects": ["tower-mana", "city-mana"], "support": "capability findings in each referenced subject"}]
shared written_cost: [{"subject_id": "tower-mana", "value": "{T}"}, {"subject_id": "city-mana", "value": "{T}"}]
shared ownership: [{"subject_id": "tower-mana", "value": "no_additional_effect"}, {"subject_id": "city-mana", "value": "no_additional_effect"}]
shared procedure: [{"subject_id": "tower-mana", "value": "CONDITIONAL_ACTIVATED_MANA"}, {"subject_id": "city-mana", "value": "CONDITIONAL_ACTIVATED_MANA"}]
differences output_pattern: [{"subject_id": "tower-mana", "value": "commander_color_context_dependent"}, {"subject_id": "city-mana", "value": "unrestricted_color_choice"}]
differences dependencies: [{"subject_id": "tower-mana", "value": ["commander_color_identity"]}, {"subject_id": "city-mana", "value": []}]
Capability differences establish no strategic advantage, ranking, score, deck recommendation or acquisition advice. Actual and net output, payment feasibility and game impact require additional context.
Detailed evidence: {"bytes": 689253, "report_id": "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd", "route": "LandExplanationConsumer.detailed(reference)", "sha256": "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"}
```

Command selector: `card Nykthos`; exit 2.

```text
accepted land explanation rejected: unsupported explanation selector or inference
```

Actual evidence-integrity rejection from `consumer.detailed(tampered_reference)`: `fixed authored contract or exact evidence binding mismatch`.

Preservation audit: 2981 inherited files, 91918222 current inherited bytes; every inherited mode and blob identical except the explicitly enumerated preservation-adapter source whitelist. No historical document suffix or data change.
