"""Exact PR #220 preservation for the append-only land owner decision.

The tests retain original input bytes and historical report contracts. A real
expanded publication catalog must reject; no positive historical fixture is used.
"""
import hashlib
from pathlib import Path
import unittest

import proposed_spell_packet_analysis_preservation as guard
import proposed_spell_packet_authoring_preservation as previous
from card_rules_pilot import contract as c, land
from land_test_support import ROOT, arguments, consumer, current_catalog_intact

CANONICAL_MAIN = "399016f2f69d709a8a50fd16f94b94432a093524"
CANONICAL_TREE = "5db2265fae343400b17ae67dcf461a1266e83e1f"
PROTECTED = {'.github/workflows/automatic-canonical-update.yml': '042d3597a1a0c2a440fe63387fdfc7b7af67d56b0182c7c65ef8bf677986ae6b',
 '.github/workflows/deck-usage-acquisition.yml': '066f6b49c70b458e2faf731d1868d0c64d41f5e869760ee2ebeec12aba209d67',
 '.github/workflows/market-acquisition.yml': '3d02c563339ac7f35af80a6cc44bd260be1be36ac9aac6d9f463e82f7385828c',
 '.github/workflows/mtgjson-production-ingestion.yml': '9fb7ea7116fc92722446d5c1e6a1587bdaf15516312b3a89ca2b27a45c5c067e',
 '.github/workflows/pilot-printing-acquisition.yml': 'b87f1f4664829ac0a684e3d51ab45194adecff2ac9cc62101455f34e47b4374e',
 '.github/workflows/production-evidence-intake.yml': '7f38dcc084e6f61cc07680783f8ab90964e8bf37a37baee181cf5f4cef3085a8',
 '.github/workflows/python-validation.yml': '4c4c7e42ff96c59e6edbe2c4d204c50a464d907153d9caf9df9564b03430b6a2',
 'docs/ARCHITECTURE.md': 'c4651ad45e47ff9a247151a9c4ca54e8e7dd18b23725cec0571039ef676284b3',
 'docs/DECISIONS.md': '47e1fc0e4353f251dde4fb316ec79642a3ab3d51fc0dcc6613b49a795ead73db',
 'docs/LAND_MANA_UTILITY_INTELLIGENCE.md': 'd29bc8ee9f801e818cc62f0d6f18d5bbe308eb045979bcecfa8177134e6cdf8c',
 'src/card_rules_pilot/__init__.py': '2093c7424b37f6106539fd705bd5f92fad3265e57f91f70b78f6f77b85a25feb',
 'src/card_rules_pilot/__main__.py': 'c8caad5badb9da31d6db5a8b45457a5c4bee4e26b63c333fa77e856b990d427d',
 'src/card_rules_pilot/authored.py': '4b6284d25add2069a34b6d6dda37be944296c22d14409a1920225bd719881e88',
 'src/card_rules_pilot/behavior.py': 'aa7f9399a6aca318ec24696ffe1fffb7b85899716ef8eebb278cabf444bb7f84',
 'src/card_rules_pilot/behavior_cli.py': '6af12074fa42af9fabb0682e0c43af6ae2a1917eb7ba7173651aa56c082a12f4',
 'src/card_rules_pilot/behavior_context.py': 'aabe91a493e36a3e459fca6a3619d15c60fd5d036fdaedfc46e538b8f68ee7fa',
 'src/card_rules_pilot/behavior_policy.py': 'ac67f056df9889afe377decc13d6d54fb0c741e101e67f5f718021b0e35c6d27',
 'src/card_rules_pilot/cards.py': '02311cfad0339836064c2235237853c0e3fc39c48db3bb901d37b02e58ccc70c',
 'src/card_rules_pilot/contract.py': '6ab87a46c13d91b799e1c30e96323898feb08d05ec80d486c4204784d27334e5',
 'src/card_rules_pilot/land.py': 'a7ef77e1c23a7b204f86c68fa298af0a1ac7fe9419d58be7b12944d9e9513864',
 'src/card_rules_pilot/land_authored.py': '224bcfa1db7dc7c7eac4aadb06dd0f4e4c35eba5a180e1864fd9bb799107601b',
 'src/card_rules_pilot/land_cards.py': 'db265f897b3549e920c5f2e5185fcfc7643fd209ad73e563d25c8caebb20244a',
 'src/card_rules_pilot/land_cli.py': '5420217b53d51c85aad79580f7bb14cb03533aefc42f51f6476c12542e4f6b74',
 'src/card_rules_pilot/land_context.py': '45b6ee3346e8c41c86732fb2f4a670b862106d22a4160e35a39c466090794d9a',
 'src/card_rules_pilot/land_effects.py': '9aebc93fd0f478cb0ea653c2876e813f16fc19291719aa912682dc0325d80baa',
 'src/card_rules_pilot/pilot.py': '4556628ec9e4be09b69b0f11434a3bd1c370c3744dac1f283811d51aaa3e4c31',
 'src/card_rules_pilot/reasoning.py': 'b01435e8180923cef545b19fa713afa153eb634e3a47f950455c01bb8d324f20',
 'src/card_rules_pilot/reasoning_policy.py': '4ebb431fb265fe37223aafe7a8c6829a027019ba1cd0d5abe54f94709a9465bf',
 'src/card_rules_pilot/reassessment.py': 'a98cbc8dd8a59567cbb4a4557f189456533055181726e39ef58e61b296788892',
 'src/card_rules_pilot/reassessment_cli.py': '7a75d87676ca94fe24232498ca36a7712f4b198a47615780d7586cd730d528c1',
 'src/card_rules_pilot/rules.py': 'fb07585c48cb7ca303de57e13ff0817dac34ee5472b6fdd91208670a453d15d7'}
HISTORICAL_INPUTS = {'data/review/card-rules-mana-pilot/manifest.json': 'f60ff2cfdd49715fd1cbcc62a999e5095fb77473a0eda3f04b8a3bf7986c0e64',
 'data/review/card-rules-mana-pilot/plan.json': '92dff0b55af5c9906963b871a0cbfd5122a8f8a737b4402a6067bb742137d1fb',
 'data/review/land-mana-utility/interpretations.json': '6376abbc89497ced3b399dc4606361b1eca7621df3b6ececeb60fdec0ae3df11',
 'data/review/land-mana-utility/manifest.json': 'e148fcce3c92a445d61305c488f63b5fecd83efda2a677c0355e31b13252166f',
 'data/review/land-mana-utility/plan.json': 'bed5e94c18b6145a139557a53b8d0af8ae38fbe243e4027da4e8ee9033ab2b3c',
 'data/review/mana-context-reassessment/manifest.json': 'e03711421c665d9bea2457f713e3343d74e162897c1646f26f7f105e33d204c0',
 'data/review/mana-context-reassessment/reassessments.json': '00ab500f0a618b811d558496c3c1cebebe8c6adb54993f449795b7df8db91bcc'}


class LandDecisionPreservationTests(unittest.TestCase):
    def test_finite_consumer_additions_reject_future_or_source_paths(self):
        names = {"src/card_rules_pilot/land_decision.py",
                 "src/card_rules_pilot/land_decision_cli.py"}
        self.assertEqual(guard.LAND_DECISION_SOURCE_PATHS, names)
        for name in names:
            self.assertTrue(guard.is_packet_analysis_addition(ROOT / name))
            self.assertTrue(previous.is_packet_authoring_addition(ROOT / name))
            self.assertFalse(guard.is_packet_analysis_addition(ROOT / (name + ".future")))
        for name in ("src/card_rules_pilot/land_decision_future.py",
                     "src/card_rules_pilot/semantic_approval_service.py",
                     "src/gameplay_rules/projection/land_decision.py",
                     "reference-reviews/land-decision/projection.json"):
            self.assertFalse(guard.is_packet_analysis_addition(ROOT / name))

    def test_exact_document_suffixes_reconstruct_pr220_and_reject_drift(self):
        self.assertEqual(set(guard.LAND_DECISION_DOCUMENT_APPENDICES),
                         set(guard.DOCUMENT_APPENDICES))
        for name, pin in guard.LAND_DECISION_DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = (ROOT / name).read_bytes()
                inherited = guard.historical_document_before_land_decision_append(name, raw)
                self.assertEqual(len(raw), pin["baseline_bytes"] + pin["appendix_bytes"])
                self.assertEqual(hashlib.sha256(inherited).hexdigest(), pin["baseline_sha256"])
                self.assertEqual(guard.historical_document_before_land_decision_append(name, inherited),
                                 inherited)
                self.assertEqual(guard.historical_document_before_land_mana_append(name, raw),
                                 guard.historical_document_before_land_mana_append(name, inherited))
                for changed in (raw + b"future\n", raw[:-1], b"X" + raw[1:],
                                inherited + b"X" + raw[len(inherited)+1:], bytearray(raw), True):
                    with self.assertRaises(AssertionError):
                        guard.historical_document_before_land_decision_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_land_decision_append("docs/future.md", b"")

    def test_historical_sources_architecture_and_all_hosted_workflows_are_exact(self):
        for name, digest in PROTECTED.items():
            with self.subTest(path=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.stat().st_mode & 0o111, 0)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_original_data_bytes_own_identities_and_pending_status_are_preserved(self):
        if not current_catalog_intact(self):
            # The real publication writer changes the attachment and intentionally
            # omits pending review data. Its actual public reader must reject.
            with self.assertRaises(ValueError):
                land.load_lands(**arguments())
            return
        for name, digest in HISTORICAL_INPUTS.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)
        actual = consumer()
        overview = actual.overview()
        value = overview.to_dict()
        for candidate in value["context"]["interpretations"]["candidates"]:
            self.assertEqual(c.identity(candidate["schema_version"], candidate, "candidate_id"),
                             candidate["candidate_id"])
            self.assertEqual(candidate["semantic_review_status"], "PENDING_NOT_ESTABLISHED")
            self.assertEqual(candidate["review"], {"status": "requires_review",
                "human_attestation": None, "canonical_admission": False})
            self.assertEqual(candidate["execution_authority"], "BLOCKED")
        for doc, identity, length, digest in (
            (overview, "sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd",
             689253, "0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515"),
            (actual.check(), "sha256:d6725c1479882549479a76a3a30e52871d5fbedb77ac5abd105f527e9eeca4cd",
             596487, "c71633d26a13d2ad8f0bc6db1a0b561d9df824cdad5eeba9880b953bbc9f2d4a")):
            raw = doc.to_json().encode()
            self.assertEqual(c.identity(doc.to_dict()["schema_version"], doc.to_dict(), "report_id"), identity)
            self.assertEqual(doc.to_dict()["report_id"], identity)
            self.assertEqual(len(raw), length)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            actual.validate_report(doc.to_dict())
        retained = value["context"]["retained_rules"]
        self.assertEqual(retained["context_count"], 24)
        self.assertEqual((retained["global_source_units"], retained["global_projections"]), (104, 16))
        self.assertEqual(retained["source_inspection_allowlist"], [])
        self.assertEqual(retained["source_projection_allowlist"], [])
        self.assertEqual((retained["new_source_units"], retained["new_projections"]), (0, 0))


if __name__ == "__main__":
    unittest.main()
