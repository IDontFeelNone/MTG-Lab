"""Exact reversible adapters for five composition seams and finite test adapters.

The immutable design and all historical source pins retain their original
identities. Only these precise successor bytes can reconstruct each original;
no data, report, policy, workflow, timeout or arbitrary future source is exempt.
"""
import hashlib

COMPOSITION_SOURCE_PINS = {'src/card_rules_pilot/land.py': {'composition_seam': {'bytes': 13600,
                                                       'sha256': '822eff89e94f6c8f8c46885f09b9e616fcec4d9bf9ad7083ecb8806939002026'},
                                  'historical': {'bytes': 13531,
                                                 'sha256': 'a7ef77e1c23a7b204f86c68fa298af0a1ac7fe9419d58be7b12944d9e9513864'}},
 'src/card_rules_pilot/land_cards.py': {'composition_seam': {'bytes': 13257,
                                                             'sha256': 'ea5dfcec2cae5f4b35eb79912b72a040c3351769352678c3fe27329f6a7afd03'},
                                        'historical': {'bytes': 12470,
                                                       'sha256': 'db265f897b3549e920c5f2e5185fcfc7643fd209ad73e563d25c8caebb20244a'}},
 'src/card_rules_pilot/land_decision.py': {'composition_seam': {'bytes': 19807,
                                                                'sha256': '613fa07ec91f6fb07a5e4fc2b74515dc871dc0534355afb1d273775e48728acf'},
                                           'historical': {'bytes': 19547,
                                                          'sha256': '68a46f0836ec26f1421be73c2383ecb40d6516b1f206ab96ab4b997141fa61c2'}},
 'src/card_rules_pilot/land_explanation.py': {'composition_seam': {'bytes': 9096,
                                                                   'sha256': 'd6384d6d852ed02b2e23603eed5581ebeed5a7adc4658d9e91b793f8ff78bfa1'},
                                              'historical': {'bytes': 8458,
                                                             'sha256': 'e6e5ab70412ef231e78f88db78d489824845566de94eaaaf43c33073f88c8060'}},
 'src/card_rules_pilot/mana_scenario.py': {'composition_seam': {'bytes': 10704,
                                                                'sha256': '27e59d48739438d91aca16a3090aed1d49a8dea5a2a0df4de28bd96e380cab7a'},
                                           'historical': {'bytes': 10437,
                                                          'sha256': '309b5673db3ffb6e4438d4eb8e5b7884bd28c368f679d6430e952a39270db960'}},
 'tests/proposed_spell_packet_analysis_preservation.py': {'composition_seam': {'bytes': 78983,
                                                                               'sha256': 'c0e0341674db7a2699b86fe5fedc39df574f0bd49d593eb0be9a77bc4b8e1255'},
                                                          'historical': {'bytes': 78787,
                                                                         'sha256': 'a90468ad63907348ef1a576d570e444c6906e6982956414eab0f196075ebb3b9'}},
 'tests/test_land_decision_preservation.py': {'composition_seam': {'bytes': 10408,
                                                                   'sha256': '8f650b699986b5399be1e9f9658bf39acb540e109df43c29694e21ec8b54873a'},
                                              'historical': {'bytes': 10312,
                                                             'sha256': '5050c20733483d52829e5f79c4efaee178d4e51f309b6b17759077b0d96965cc'}},
 'tests/test_mana_scenario_preservation.py': {'composition_seam': {'bytes': 4990,
                                                                   'sha256': '4e6bce4a47fde1ddded3fe84529137d00f24d1fafeb2e1f26198daf2787d9473'},
                                              'historical': {'bytes': 4813,
                                                             'sha256': '4c9de755b8996413d393a6a814074fbb6ce25044b773b8fb54c5eebb8dc9be3a'}},
 'tests/test_real_rules_execution_design_boundaries.py': {'composition_seam': {'bytes': 20203,
                                                                               'sha256': 'e611f6c4c321e4fe8f5b80302d980618a4f380559d376a697b60ef299a90ba34'},
                                                          'historical': {'bytes': 19996,
                                                                         'sha256': '82cc01bbcd6bdf84fc111f40f34c16e12a12f3a319110b7666fd1b24f41641a0'}},
 'tests/test_rules_card_integration_design.py': {'composition_seam': {'bytes': 14885,
                                                                      'sha256': 'db2915d39afb73fa028a8c568dd1ff265a7564e2bb89c1e933705cb084635b40'},
                                                 'historical': {'bytes': 14894,
                                                                'sha256': 'd70e07121c32fc0b80ab2722da4aa1e41d392b7fc2088705fa71ef8c1fbda2f9'}}}
SOURCE_EDITS = {'src/card_rules_pilot/land.py': [(9693,
                                   9800,
                                   b'               expected_profile_id, expected_query_snapshot_'
                                   b'id, expected_plan_id):\n',
                                   b'               expected_profile_id, expected_query_snapshot_'
                                   b'id, expected_plan_id, mechanical_reader=None):\n'),
                                  (9980,
                                   10129,
                                   b'        expected_profile_id=expected_profile_id, expected_qu'
                                   b'ery_snapshot_id=expected_query_snapshot_id)\n',
                                   b'        expected_profile_id=expected_profile_id, expected_qu'
                                   b'ery_snapshot_id=expected_query_snapshot_id,\n        mechanic'
                                   b'al_reader=mechanical_reader)\n')],
 'src/card_rules_pilot/land_cards.py': [(4483,
                                         4605,
                                         b'               expected_profile_id: str, expected_query_'
                                         b'snapshot_id: str) -> dict:\n',
                                         b'               expected_profile_id: str, expected_query_'
                                         b'snapshot_id: str,\n               mechanical_reader=N'
                                         b'one) -> dict:\n'),
                                        (5468,
                                         6481,
                                         b'    mechanical = MechanicalCardIntelligence.from_attachm'
                                         b'ent(\n        attachment, data_root=mechanical_root /'
                                         b' "data",\n        source_directory=mechanical_root / '
                                         b'"data/market/acquisitions" / ACQUISITION,\n        ex'
                                         b'pected_query_snapshot_id=expected_query_snapshot_id)\n',
                                         b'    if mechanical_reader is None:\n        mechanical'
                                         b' = MechanicalCardIntelligence.from_attachment(\n     '
                                         b'       attachment, data_root=mechanical_root / "data'
                                         b'",\n            source_directory=mechanical_root / "d'
                                         b'ata/market/acquisitions" / ACQUISITION,\n            '
                                         b'expected_query_snapshot_id=expected_query_snapshot_i'
                                         b'd)\n    else:\n        # Public batch-composition seam'
                                         b'. Revalidate both selected roots; never\n        # ac'
                                         b'cept a dossier dictionary, stale reader, or unbound lega'
                                         b'cy reader.\n        mechanical = mechanical_reader\n  '
                                         b'      if type(mechanical) is not MechanicalCardIntellige'
                                         b'nce:\n            raise CardBindingError("actual atta'
                                         b'ched mechanical reader required")\n        mechanical'
                                         b'.verify_inputs()\n        if (mechanical.data_root !='
                                         b' (mechanical_root / "data").resolve()\n              '
                                         b'  or mechanical.catalog_binding != attachment.bindin'
                                         b'g\n                or mechanical.query.snapshot().sna'
                                         b'pshot_id != expected_query_snapshot_id):\n           '
                                         b' raise CardBindingError("shared mechanical reader bindin'
                                         b'g mismatch")\n')],
 'src/card_rules_pilot/land_decision.py': [(10782,
                                            10981,
                                            b'',
                                            b'    def verify_evidence(self):\n        """Reproduce '
                                            b'the exact decision and original evidence for composi'
                                            b'tion."""\n        self.validate_record(json.loads(sel'
                                            b'f._decision))\n        return self.check()\n\n'),
                                           (15717,
                                            15790,
                                            b'        expected_plan_id, expected_decision_id):\n',
                                            b'        expected_plan_id, expected_decision_id, mech'
                                            b'anical_reader=None):\n'),
                                           (16442,
                                            16522,
                                            b'        expected_plan_id=expected_plan_id)\n',
                                            b'        expected_plan_id=expected_plan_id, mechanica'
                                            b'l_reader=mechanical_reader)\n')],
 'src/card_rules_pilot/land_explanation.py': [(456,
                                               494,
                                               b'',
                                               b'    _decision: d.LandDecisionConsumer\n'),
                                              (3613,
                                               3882,
                                               b'',
                                               b'    def verify_evidence(self):\n        """Recomp'
                                               b'ute all explanation evidence from its owning acc'
                                               b'epted consumer."""\n        expected = from_decis'
                                               b'ion(self._decision)\n        c.exact(json.loads(s'
                                               b'elf._snapshot), json.loads(expected._snapshot))\n'
                                               b'        return self.check()\n\n'),
                                              (5190,
                                               5516,
                                               b'    accepted = d.load_land_decision(**arguments)'
                                               b'\n',
                                               b'    return from_decision(d.load_land_decision(**'
                                               b'arguments))\n\n\ndef from_decision(accepted):\n '
                                               b'   """Compose an actually admitted decision; no '
                                               b'dictionary admission route."""\n    if type(accep'
                                               b'ted) is not d.LandDecisionConsumer:\n        rais'
                                               b"e c.PilotError('admitted land decision consumer "
                                               b"required')\n    accepted.verify_evidence()\n"),
                                              (7277,
                                               7331,
                                               b'',
                                               b"    object.__setattr__(result, '_decision', acce"
                                               b'pted)\n')],
 'src/card_rules_pilot/mana_scenario.py': [(5860,
                                            6240,
                                            b'    explanations = e.load_land_explanations(**argume'
                                            b"nts)\n    detail = explanations.check().to_dict()['de"
                                            b"tailed']\n",
                                            b'    return from_explanations(e.load_land_explanation'
                                            b's(**arguments))\n\n\ndef from_explanations(explanat'
                                            b'ions):\n    """Reuse an actually admitted, privately '
                                            b'owned explanation batch."""\n    if type(explanations'
                                            b') is not e.LandExplanationConsumer:\n        raise c.'
                                            b"PilotError('admitted land explanation consumer requi"
                                            b"red')\n    detail = explanations.verify_evidence().to"
                                            b"_dict()['detailed']\n")],
 'tests/proposed_spell_packet_analysis_preservation.py': [(561,
                                                           1022,
                                                           b'    return path.relative_to(root).as'
                                                           b'_posix() in NEW_SOURCE_PATHS | CONDI'
                                                           b'TIONAL_SOURCE_PATHS | SENSITIVITY_SO'
                                                           b'URCE_PATHS | ALTERNATIVES_SOURCE_PAT'
                                                           b'HS | COMPOUND_SOURCE_PATHS | CARD_RU'
                                                           b'LES_PILOT_SOURCE_PATHS | MANA_REASON'
                                                           b'ING_SOURCE_PATHS | MANA_CONTEXT_SOUR'
                                                           b'CE_PATHS | MANA_CONTEXT_REVIEW_PATHS'
                                                           b' | MANA_BEHAVIOR_SOURCE_PATHS | LAND'
                                                           b'_MANA_SOURCE_PATHS | LAND_DECISION_S'
                                                           b'OURCE_PATHS | LAND_EXPLANATION_SOURC'
                                                           b'E_PATHS | MANA_SCENARIO_SOURCE_PATHS'
                                                           b'\n',
                                                           b'    return path.relative_to(root).as'
                                                           b'_posix() in NEW_SOURCE_PATHS | CONDI'
                                                           b'TIONAL_SOURCE_PATHS | SENSITIVITY_SO'
                                                           b'URCE_PATHS | ALTERNATIVES_SOURCE_PAT'
                                                           b'HS | COMPOUND_SOURCE_PATHS | CARD_RU'
                                                           b'LES_PILOT_SOURCE_PATHS | MANA_REASON'
                                                           b'ING_SOURCE_PATHS | MANA_CONTEXT_SOUR'
                                                           b'CE_PATHS | MANA_CONTEXT_REVIEW_PATHS'
                                                           b' | MANA_BEHAVIOR_SOURCE_PATHS | LAND'
                                                           b'_MANA_SOURCE_PATHS | LAND_DECISION_S'
                                                           b'OURCE_PATHS | LAND_EXPLANATION_SOURC'
                                                           b'E_PATHS | MANA_SCENARIO_SOURCE_PATHS'
                                                           b' | LAND_OVERLAY_SOURCE_PATHS\n'),
                                                          (78815,
                                                           78983,
                                                           b'',
                                                           b'\nLAND_OVERLAY_SOURCE_PATHS = frozens'
                                                           b'et({"src/card_intelligence/land_over'
                                                           b'lay.py", "src/card_intelligence/land'
                                                           b'_overlay_cli.py", "src/projection/hi'
                                                           b'storical_evidence.py"})\n')],
 'tests/test_land_decision_preservation.py': [(251,
                                               316,
                                               b'',
                                               b'from overlay_preservation_support import histori'
                                               b'cal_source_bytes\n'),
                                              (7722,
                                               7841,
                                               b'                self.assertEqual(hashlib.sha256('
                                               b'path.read_bytes()).hexdigest(), digest)\n',
                                               b'                self.assertEqual(hashlib.sha256('
                                               b'historical_source_bytes(name, path.read_bytes())'
                                               b').hexdigest(), digest)\n')],
 'tests/test_mana_scenario_preservation.py': [(100,
                                               165,
                                               b'',
                                               b'from overlay_preservation_support import histori'
                                               b'cal_source_bytes\n'),
                                              (3496,
                                               3617,
                                               b'            self.assertEqual(hashlib.sha256(path'
                                               b'.read_bytes()).hexdigest(), digest, name)\n',
                                               b'            self.assertEqual(hashlib.sha256(hist'
                                               b'orical_source_bytes(name, path.read_bytes())).he'
                                               b'xdigest(), digest, name)\n'),
                                              (4303,
                                               4475,
                                               b"        raw = (ROOT / 'tests/proposed_spell_pack"
                                               b"et_analysis_preservation.py').read_bytes()\n",
                                               b"        raw = historical_source_bytes('tests/pro"
                                               b"posed_spell_packet_analysis_preservation.py', (R"
                                               b"OOT / 'tests/proposed_spell_packet_analysis_pres"
                                               b"ervation.py').read_bytes())\n")],
 'tests/test_real_rules_execution_design_boundaries.py': [(6411,
                                                           6618,
                                                           b'',
                                                           b'        from overlay_preservation_su'
                                                           b'pport import is_overlay_addition, as'
                                                           b'sert_overlay_addition\n        if is_'
                                                           b'overlay_addition(path, ROOT):\n      '
                                                           b'      assert_overlay_addition(path, '
                                                           b'ROOT)\n            continue\n')],
 'tests/test_rules_card_integration_design.py': [(8139,
                                                  8256,
                                                  b"            self.assertEqual(len(raw),pin['b"
                                                  b"ytes'],name);self.assertEqual(hashlib.sha256"
                                                  b"(raw).hexdigest(),pin['sha256'],name)\n",
                                                  b'            from overlay_preservation_suppor'
                                                  b't import verify_source_pin\n            verif'
                                                  b'y_source_pin(name, raw, pin)\n')]}


def historical_source_bytes(name, raw):
    if type(raw) is not bytes: raise AssertionError('exact source bytes required')
    pair = COMPOSITION_SOURCE_PINS.get(name)
    if pair is None: return raw
    actual = dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    if actual == pair['historical']: return raw
    if actual != pair['composition_seam']: raise AssertionError('unreviewed source change: ' + name)
    for start,end,old,new in reversed(SOURCE_EDITS[name]):
        if raw[start:end] != new: raise AssertionError('exact source seam changed')
        raw = raw[:start] + old + raw[end:]
    if dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) != pair['historical']:
        raise AssertionError('original source not reproduced')
    return raw


def verify_source_pin(name, raw, historical_pin):
    old = historical_source_bytes(name, raw)
    if len(old) != historical_pin['bytes'] or hashlib.sha256(old).hexdigest() != historical_pin['sha256']:
        raise AssertionError('exact historical source pin changed: ' + name)

OVERLAY_ADDITIONS = {'src/card_intelligence/land_overlay.py': {'bytes': 29232,
                                           'sha256': 'eed4fce6dc632ccc724dbb5d2809cc69196f7d72a3598abde0f4b4663697f56b'},
 'src/card_intelligence/land_overlay_cli.py': {'bytes': 4021,
                                               'sha256': '702f23ec582cbcb141c0c517e539bef22873da88b74f1ab3af8ea66581f214ec'},
 'src/projection/historical_evidence.py': {'bytes': 3755,
                                           'sha256': '5aae30565f70f67a33cee43caf4b4720ef74cbb13ca1c5a5728e682143d21725'}}


def is_overlay_addition(path, root):
    return path.relative_to(root).as_posix() in OVERLAY_ADDITIONS


def assert_overlay_addition(path, root):
    name = path.relative_to(root).as_posix()
    if name not in OVERLAY_ADDITIONS or path.is_symlink() or path.stat().st_mode & 0o111:
        raise AssertionError('unsupported overlay source path/mode')
    raw = path.read_bytes()
    if dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) != OVERLAY_ADDITIONS[name]:
        raise AssertionError('exact overlay source bytes required')
