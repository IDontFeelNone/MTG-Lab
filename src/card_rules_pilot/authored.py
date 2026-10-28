"""Fixed engineer-authored review plan. No text parsing or classification occurs here.

Every reading below is pending semantic review. Bindings are supplied and checked
by the separate Card and retained-rule evidence readers.
"""

CRITERIA = [{'criterion_id': 'activated_kind', 'label': 'Activated ability kind', 'rule_refs': ['605.1a']},
 {'criterion_id': 'no_target', 'label': 'No target requirement', 'rule_refs': ['605.1a', '115.6']},
 {'criterion_id': 'potential_mana',
  'label': 'Potential to add mana on resolution',
  'rule_refs': ['605.1a', '605.2']},
 {'criterion_id': 'not_loyalty',
  'label': 'Not a loyalty ability',
  'rule_refs': ['605.1a', '606.1', '606.2']},
 {'criterion_id': 'no_library_cost_movement',
  'label': 'Costs do not move a card into or out of a library',
  'rule_refs': ['605.1a']},
 {'criterion_id': 'no_library_effect_movement',
  'label': 'Effect does not move a card into or out of a library',
  'rule_refs': ['605.1a']},
 {'criterion_id': 'self_replacement_considered',
  'label': 'Consider self-replacement effects in classification',
  'rule_refs': ['605.1a']},
 {'criterion_id': 'other_replacements_disregarded',
  'label': 'Disregard other applicable replacement effects in classification',
  'rule_refs': ['605.1a']},
 {'criterion_id': 'triggered_kind', 'label': 'Triggered ability kind', 'rule_refs': ['605.1b']},
 {'criterion_id': 'trigger_no_target',
  'label': 'Triggered candidate has no target requirement',
  'rule_refs': ['605.1b', '115.6']},
 {'criterion_id': 'trigger_potential_mana',
  'label': 'Triggered candidate could add mana on resolution',
  'rule_refs': ['605.1b', '605.2']},
 {'criterion_id': 'qualifying_trigger_relationship',
  'label': 'Trigger tied to activated mana-ability activation/resolution or mana entering a pool',
  'rule_refs': ['605.1b', '605.1a']}]

PLAN_BODY = {'schema_version': 'card-rules-mana-pilot-plan-v1',
 'prepared_at': '2026-10-26T23:20:00Z',
 'authority': 'ENGINEER_AUTHORED_PENDING_INTERPRETATIONS_ONLY',
 'subjects': [{'subject_id': 'sol-ring-tap',
               'card_id': '6ad8011d-3471-4369-9d68-b264cc027487',
               'proposed_kind': 'proposed_activated_ability',
               'proposed_classification': 'proposed_activated_mana_ability',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the selected tap ability as one activation '
                                          'with its own tap cost and mana-producing effect.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'no_target',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:115.6'],
                             'rationale': 'The engineer reads the complete selected cost and effect as '
                                          'requiring no target. This expressly authored absence reading uses '
                                          'the whole passage rather than a target count.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:605.2'],
                             'rationale': 'The engineer reads the selected Add instruction as potential mana '
                                          'production on resolution, separate from present output or '
                                          'eligibility.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': 'The engineer reads the entire selected activation cost as a tap '
                                          'cost rather than a loyalty-symbol cost; retained 606.1-606.2 '
                                          'supply only classification context.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.',
                                             'Broad 606 remains partially represented; loyalty execution is '
                                             'unavailable.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the complete selected cost as tapping this '
                                          'object, without moving a card into or out of a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the complete selected effect as mana addition, '
                                          'without moving a card into or out of a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'unknown',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'full_oracle_field'],
                             'rationale': 'The engineer has selected the complete ability and full Card '
                                          'context, but cannot establish a complete self-replacement '
                                          'assessment from the retained semantic representation.',
                             'limitations': ['The retained rules require considering self-replacement, but '
                                             'no self-replacement recognition or evaluation is implemented.',
                                             'Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The authored proposal follows the retained classification '
                                          'qualification by disregarding other applicable replacement '
                                          'effects in this assessment.',
                             'limitations': ['This policy annotation does not establish which external '
                                             'replacement effects exist, how they apply, or actual mana '
                                             'output.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.2'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']}],
               'classification_rationale': 'An engineer proposes the activated-mana reading under retained '
                                           '605.1a; the unresolved self-replacement assessment prevents '
                                           'describing the proposal as fully supported or semantically '
                                           'approved.',
               'classification_evidence_refs': ['selected_passage',
                                                'full_oracle_field',
                                                'rule:605.1a',
                                                'rule:605.2',
                                                'rule:606.1',
                                                'rule:606.2'],
               'counterevidence': ['The complete passage supports a proposed mana-producing activation, but '
                                   'does not supply formal Card semantics, current eligibility or actual '
                                   'mana output.'],
               'missing_requirements': ['Human review of subject-kind and criterion readings.',
                                        'Complete self-replacement semantics and any externally supplied '
                                        'ability/effect changes.',
                                        'Current activation eligibility and actual output remain '
                                        'unassessed.'],
               'comparison_note': 'A mana-related strategic role is separately authored context; it does not '
                                  'establish the rules category. Classification does not establish present '
                                  'activation eligibility or output.'},
              {'subject_id': 'basalt-monolith-tap',
               'card_id': '6b8cf2a0-b045-4d91-9d91-c602d40c6237',
               'proposed_kind': 'proposed_activated_ability',
               'proposed_classification': 'proposed_activated_mana_ability',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the selected tap ability as one activation '
                                          'with its own tap cost and mana-producing effect.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'no_target',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:115.6'],
                             'rationale': 'The engineer reads the complete selected cost and effect as '
                                          'requiring no target. This expressly authored absence reading uses '
                                          'the whole passage rather than a target count.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:605.2'],
                             'rationale': 'The engineer reads the selected Add instruction as potential mana '
                                          'production on resolution, separate from present output or '
                                          'eligibility.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': 'The engineer reads the entire selected activation cost as a tap '
                                          'cost rather than a loyalty-symbol cost; retained 606.1-606.2 '
                                          'supply only classification context.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.',
                                             'Broad 606 remains partially represented; loyalty execution is '
                                             'unavailable.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the complete selected cost as tapping this '
                                          'object, without moving a card into or out of a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the complete selected effect as mana addition, '
                                          'without moving a card into or out of a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'unknown',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'full_oracle_field'],
                             'rationale': 'The engineer has selected the complete ability and full Card '
                                          'context, but cannot establish a complete self-replacement '
                                          'assessment from the retained semantic representation.',
                             'limitations': ['The retained rules require considering self-replacement, but '
                                             'no self-replacement recognition or evaluation is implemented.',
                                             'Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The authored proposal follows the retained classification '
                                          'qualification by disregarding other applicable replacement '
                                          'effects in this assessment.',
                             'limitations': ['This policy annotation does not establish which external '
                                             'replacement effects exist, how they apply, or actual mana '
                                             'output.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.2'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as an activated ability, so the '
                                          'triggered criteria family is outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']}],
               'classification_rationale': 'An engineer proposes the activated-mana reading under retained '
                                           '605.1a; the unresolved self-replacement assessment prevents '
                                           'describing the proposal as fully supported or semantically '
                                           'approved.',
               'classification_evidence_refs': ['selected_passage',
                                                'full_oracle_field',
                                                'rule:605.1a',
                                                'rule:605.2',
                                                'rule:606.1',
                                                'rule:606.2'],
               'counterevidence': ['The complete passage supports a proposed mana-producing activation, but '
                                   'does not supply formal Card semantics, current eligibility or actual '
                                   'mana output.',
                                   'The static untap restriction and separate paid untap activation remain '
                                   'full-field surrounding context; neither is a cost or effect of this '
                                   'selected tap subject.'],
               'missing_requirements': ['Human review of subject-kind and criterion readings.',
                                        'Complete self-replacement semantics and any externally supplied '
                                        'ability/effect changes.',
                                        'Current activation eligibility and actual output remain '
                                        'unassessed.'],
               'comparison_note': 'A mana-related strategic role is separately authored context; it does not '
                                  'establish the rules category. Classification does not establish present '
                                  'activation eligibility or output.'},
              {'subject_id': 'basalt-monolith-untap',
               'card_id': '6b8cf2a0-b045-4d91-9d91-c602d40c6237',
               'proposed_kind': 'proposed_activated_ability',
               'proposed_classification': 'proposed_exclusion',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads this complete paid untap passage as its own '
                                          'activation, separate from the tap-for-mana activation.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'no_target',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:115.6'],
                             'rationale': 'The complete selected cost and untap effect are expressly read as '
                                          'requiring no target, scoped only to this passage.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'proposed_not_satisfied',
                             'evidence_refs': ['selected_passage',
                                               'rule:605.1a',
                                               'rule:605.2',
                                               'full_oracle_field',
                                               'rule:605.5'],
                             'rationale': 'The selected effect untaps this artifact; paying mana in the '
                                          'selected cost is not potentially adding mana on resolution. The '
                                          "separate tap ability cannot supply this subject's effect.",
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': 'The complete selected cost is read as a mana payment rather than '
                                          'a loyalty-symbol cost.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.',
                                             '606.1-606.2 do not provide full loyalty execution.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The complete selected cost is read as paying mana, without a card '
                                          'transfer into or out of a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The complete selected effect is read as untapping this artifact, '
                                          'without a card transfer into or out of a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'unknown',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'full_oracle_field'],
                             'rationale': 'No complete self-replacement semantic assessment is available for '
                                          'this selected untap effect.',
                             'limitations': ['The retained rules require considering self-replacement, but '
                                             'no self-replacement recognition or evaluation is implemented.',
                                             'Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'Other applicable replacement effects are disregarded in the '
                                          'authored classification assessment, as required by retained '
                                          '605.1a.',
                             'limitations': ['Unknown external replacement effects remain unknown; no '
                                             'execution occurs.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'The selected subject is proposed as an activated ability; '
                                          'triggered criteria are outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'The selected subject is proposed as an activated ability; '
                                          'triggered criteria are outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.2'],
                             'rationale': 'The selected subject is proposed as an activated ability; '
                                          'triggered criteria are outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as an activated ability; '
                                          'triggered criteria are outside that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']}],
               'classification_rationale': "The authored exclusion rests on the selected activation's "
                                           'proposed lack of potential mana production, under 605.1a and '
                                           '605.5. Its paid mana cost does not meet the output criterion.',
               'classification_evidence_refs': ['selected_passage',
                                                'full_oracle_field',
                                                'rule:605.1a',
                                                'rule:605.5'],
               'counterevidence': ['The host has a separate mana-producing activation; borrowing that effect '
                                   'would change the selected subject.',
                                   'The static untap restriction is surrounding context, not a third '
                                   'classified subject.'],
               'missing_requirements': ['Human review of the selected activation and exclusion.',
                                        'Self-replacement semantics remain unresolved.',
                                        'No cost payment, untap execution or repeatable sequence is '
                                        'evaluated.'],
               'comparison_note': 'Paying mana differs from potentially producing mana. The two Basalt '
                                  'activations remain distinct; no loop or infinite-mana conclusion '
                                  'follows.'},
              {'subject_id': 'deathrite-shaman-first',
               'card_id': '22f1a4a4-c423-4d1c-8775-0ed604a9fa51',
               'proposed_kind': 'proposed_activated_ability',
               'proposed_classification': 'proposed_exclusion',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The engineer reads the complete first ability as a tap-cost '
                                          'activation with a targeted exile instruction followed by mana '
                                          'addition.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'no_target',
                             'state': 'proposed_not_satisfied',
                             'evidence_refs': ['selected_passage',
                                               'rule:605.1a',
                                               'rule:115.6',
                                               'rule:605.5a'],
                             'rationale': 'The selected complete passage expressly requires a target land '
                                          'card from a graveyard. That requirement conflicts with the '
                                          'no-target criterion independently of the number of targets chosen '
                                          'in any imagined state.',
                             'limitations': ['No target choice, target legality or present activation '
                                             'eligibility is evaluated.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:605.2'],
                             'rationale': "The engineer reads the first ability's mana-addition instruction "
                                          'as potential output; this does not remove the target requirement.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': "The selected activation's complete cost is read as tapping rather "
                                          'than a loyalty-symbol cost.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.',
                                             '606.1-606.2 are classification context only.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The complete selected activation cost is read as tapping; the '
                                          'exile instruction belongs to its effect and names a graveyard '
                                          'source rather than a library.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The complete effect is read as exile from a graveyard and mana '
                                          'addition, without library transfer. The exile instruction is '
                                          'preserved, not omitted.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'unknown',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'full_oracle_field'],
                             'rationale': 'The selected first ability and all surrounding abilities are '
                                          'retained, but a complete self-replacement assessment is '
                                          'unavailable.',
                             'limitations': ['The retained rules require considering self-replacement, but '
                                             'no self-replacement recognition or evaluation is implemented.',
                                             'Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The authored classification assessment disregards other '
                                          'applicable replacement effects without evaluating them.',
                             'limitations': ['This does not establish whether external effects exist or '
                                             'change actual resolution.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'This exact first subject is proposed as an activated ability; the '
                                          'triggered criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'This exact first subject is proposed as an activated ability; the '
                                          'triggered criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.2'],
                             'rationale': 'This exact first subject is proposed as an activated ability; the '
                                          'triggered criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.1a'],
                             'rationale': 'This exact first subject is proposed as an activated ability; the '
                                          'triggered criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']}],
               'classification_rationale': 'The engineer proposes exclusion because the first complete '
                                           'activation requires a target, citing retained 605.1a, 115.6 and '
                                           'the actual targeted-exclusion record 605.5a.',
               'classification_evidence_refs': ['selected_passage',
                                                'full_oracle_field',
                                                'rule:605.1a',
                                                'rule:115.6',
                                                'rule:605.5a'],
               'counterevidence': ['Mana production is present in the selected effect but cannot cancel its '
                                   'target requirement.',
                                   'Both other host abilities remain source context and are outside this '
                                   "pilot's assessment."],
               'missing_requirements': ['Human review of first-ability ownership and target-requirement '
                                        'reading.',
                                        'Self-replacement and other real Card semantics remain unavailable.',
                                        'No target-count substitution, legal-target determination or '
                                        'activation ruling.'],
               'comparison_note': 'Target requirement differs from chosen-target count; potential mana '
                                  'output alone does not establish the mana-ability category.'},
              {'subject_id': 'dark-ritual-spell',
               'card_id': '53f7c868-b03e-4fc2-8dcf-a75bbfa3272b',
               'proposed_kind': 'proposed_spell_instruction',
               'proposed_classification': 'proposed_exclusion',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:115.6'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:605.2'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as a spell instruction bound to '
                                          'the retained Instant type line, not an activated ability; 605.5b '
                                          'supplies separate spell-exclusion context.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'The selected subject is proposed as a spell instruction, not a '
                                          'triggered ability; mana production does not change that kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'The selected subject is proposed as a spell instruction, not a '
                                          'triggered ability; mana production does not change that kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.2'],
                             'rationale': 'The selected subject is proposed as a spell instruction, not a '
                                          'triggered ability; mana production does not change that kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:605.1a'],
                             'rationale': 'The selected subject is proposed as a spell instruction, not a '
                                          'triggered ability; mana production does not change that kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']}],
               'classification_rationale': 'The engineer reads the complete Oracle instruction together with '
                                           'the retained Instant type line as a mana-producing spell '
                                           'instruction. The actual retained spell-exclusion record is '
                                           '605.5b, with general exclusion context 605.5.',
               'classification_evidence_refs': ['selected_passage', 'type_line', 'rule:605.5', 'rule:605.5b'],
               'counterevidence': ['The instruction proposes mana production; it does not establish '
                                   'activated or triggered ability kind.',
                                   'Ability criteria marked inapplicable are not successful findings.'],
               'missing_requirements': ['Human review of the spell/instruction distinction.',
                                        'Casting, spell resolution and actual mana production remain '
                                        'unavailable.'],
               'comparison_note': 'A mana-producing spell differs from an activated or triggered mana '
                                  'ability. No immediate-ability or no-stack behavior is transferred to this '
                                  'spell instruction.'},
              {'subject_id': 'mana-flare-trigger',
               'card_id': '97159138-c34b-416e-b079-5c952383a243',
               'proposed_kind': 'proposed_triggered_ability',
               'proposed_classification': 'interpretation_unresolved',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:115.6'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:605.2'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'The engineer reads the complete selected event-and-effect passage '
                                          'as one host-owned triggered ability.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'The engineer expressly reads the complete host passage as '
                                          'requiring no target, scoped to that selected passage and '
                                          'independent of any chosen-target count.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage',
                                               'rule:605.1b',
                                               'rule:605.2',
                                               'full_oracle_field'],
                             'rationale': 'The engineer reads the complete triggered effect as a potential '
                                          'additional mana instruction. No quantity, type, recipient state '
                                          'or actual output is calculated.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'unknown',
                             'evidence_refs': ['selected_passage',
                                               'rule:605.1b',
                                               'rule:605.1a',
                                               'full_oracle_field',
                                               'rule:605.5a'],
                             'rationale': 'The engineer proposes a relationship between tapping a land for '
                                          'mana and activation or resolution of an activated mana ability. '
                                          'Retained 605.1b separately permits activation, resolution or mana '
                                          'entering a pool; the selected wording does not itself bind a '
                                          'concrete land ability or prove its 605.1a category. Formal '
                                          'relationship and cause semantics remain unresolved.',
                             'limitations': ['A relationship annotation supplies no event matching, cause '
                                             'detection or activation/resolution engine.',
                                             'All three retained qualifying alternatives remain distinct.']}],
               'classification_rationale': 'A triggered-mana interpretation is proposed for review, but the '
                                           'qualifying relationship to an activated mana ability or mana '
                                           'entering a pool remains materially unresolved. The machine '
                                           'classification state therefore remains '
                                           'interpretation_unresolved.',
               'classification_evidence_refs': ['selected_passage',
                                                'full_oracle_field',
                                                'rule:605.1b',
                                                'rule:605.1a',
                                                'rule:605.5a'],
               'counterevidence': ['The full trigger and effect are retained together; a downstream '
                                   'association with mana alone is insufficient.',
                                   'A concrete underlying land ability and its pending 605.1a reading are '
                                   'not selected by this pilot.'],
               'missing_requirements': ['Human review of trigger-kind and proposed qualifying relationship.',
                                        'Formal activation/resolution/mana-added relationship and cause '
                                        'semantics are unavailable.',
                                        'No event detection, trigger causality, resolution, priority or mana '
                                        'output execution.'],
               'comparison_note': 'The trigger relationship needs its own evidence; a mana-related event or '
                                  'output word is insufficient. Activated priority-return context cannot be '
                                  'transferred to this triggered subject.'},
              {'subject_id': 'pitiless-plunderer-host-trigger',
               'card_id': 'a784481f-eccb-4112-bb38-04a659319660',
               'proposed_kind': 'proposed_triggered_ability',
               'proposed_classification': 'proposed_exclusion',
               'criteria': [{'criterion_id': 'activated_kind',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_target',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:115.6'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'potential_mana',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:605.2'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'not_loyalty',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a', 'rule:606.1', 'rule:606.2'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_library_cost_movement',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'no_library_effect_movement',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'self_replacement_considered',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'other_replacements_disregarded',
                             'state': 'inapplicable',
                             'evidence_refs': ['selected_passage', 'rule:605.1a'],
                             'rationale': 'The selected host subject is proposed as a triggered ability; the '
                                          'activated criteria family does not apply to that proposed kind.',
                             'limitations': ['Wrong proposed subject kind for this criteria family; this is '
                                             'not a successful criterion finding.']},
                            {'criterion_id': 'triggered_kind',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1b'],
                             'rationale': 'The engineer reads the complete selected event-and-effect passage '
                                          'as one host-owned triggered ability.',
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'trigger_no_target',
                             'state': 'proposed_satisfied',
                             'evidence_refs': ['selected_passage', 'rule:605.1b', 'rule:115.6'],
                             'rationale': 'The engineer expressly reads the complete host passage as '
                                          'requiring no target, scoped to that selected passage and '
                                          'independent of any chosen-target count.',
                             'limitations': ['Expressly authored absence reading scoped to the complete '
                                             'selected passage; unknown external effects and state remain '
                                             'unknown.']},
                            {'criterion_id': 'trigger_potential_mana',
                             'state': 'proposed_not_satisfied',
                             'evidence_refs': ['selected_passage',
                                               'rule:605.1b',
                                               'rule:605.2',
                                               'full_oracle_field'],
                             'rationale': 'The selected host effect creates a Treasure token. The engineer '
                                          'does not read that host effect as directly adding mana on '
                                          'resolution; the quoted activation belongs to the created object '
                                          "and cannot supply the host subject's output.",
                             'limitations': ['Formal ability/effect semantics and current game state are '
                                             'unavailable; this authored reading remains pending semantic '
                                             'review.']},
                            {'criterion_id': 'qualifying_trigger_relationship',
                             'state': 'proposed_not_satisfied',
                             'evidence_refs': ['selected_passage',
                                               'rule:605.1b',
                                               'rule:605.1a',
                                               'full_oracle_field',
                                               'rule:605.5a'],
                             'rationale': 'The complete selected host trigger is another controlled creature '
                                          'dying. The engineer proposes that this is not '
                                          'activation/resolution of an activated mana ability or mana '
                                          'entering a pool. A possible later use of a created object is only '
                                          'a downstream connection.',
                             'limitations': ['A relationship annotation supplies no event matching, cause '
                                             'detection or activation/resolution engine.',
                                             'All three retained qualifying alternatives remain distinct.']}],
               'classification_rationale': 'The engineer proposes exclusion under retained 605.1b and '
                                           '605.5a: this host trigger has a death relationship and '
                                           'token-creation effect, while the quoted mana activation has a '
                                           'different owner.',
               'classification_evidence_refs': ['selected_passage',
                                                'full_oracle_field',
                                                'rule:605.1b',
                                                'rule:605.1a',
                                                'rule:605.5a'],
               'counterevidence': ['The parenthetical quoted token ability is retained as full-field source '
                                   'context with a separate owner; it is not selected as a pilot subject.',
                                   'A strategic mana-related payoff interpretation does not establish the '
                                   'host trigger as a mana ability.'],
               'missing_requirements': ['Human review of host/token ownership and the proposed exclusions.',
                                        "Token semantics and the created object's activation are outside "
                                        'scope; no canonical Treasure entity is created.',
                                        'No death-event detection, trigger execution, token creation or '
                                        'later mana production is evaluated.'],
               'comparison_note': 'Host-card text differs from an ability belonging to a created object. The '
                                  'parenthetical token description remains visible without attributing its '
                                  'activation to Plunderer.'}],
 'scope_notes': ['Exactly six Cards and seven local review subjects. Subject IDs are not canonical ability '
                 'identities.',
                 'All criterion readings are authored interpretations of selected retained text, never '
                 'established semantic facts.',
                 'All candidates require review, null human attestation, no canonical admission and blocked '
                 'execution.',
                 'Card evidence observation 2026-08-02 and CR release 2026-09-25 are distinct time bindings; '
                 'no current Oracle verification or official ruling is claimed.',
                 'No generic classifier, parser, model, fictional evaluator input or execution authority is '
                 'supplied.']}
