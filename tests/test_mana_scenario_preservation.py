"""Exact predecessor preservation; incompatible live writer evidence must reject."""
import hashlib
from overlay_preservation_support import historical_source_bytes
from pathlib import Path
import unittest
from card_rules_pilot import mana_scenario
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments
import proposed_spell_packet_analysis_preservation as guard

PROTECTED = {'src/card_rules_pilot/land.py': 'a7ef77e1c23a7b204f86c68fa298af0a1ac7fe9419d58be7b12944d9e9513864', 'src/card_rules_pilot/land_authored.py': '224bcfa1db7dc7c7eac4aadb06dd0f4e4c35eba5a180e1864fd9bb799107601b', 'src/card_rules_pilot/land_cards.py': 'db265f897b3549e920c5f2e5185fcfc7643fd209ad73e563d25c8caebb20244a', 'src/card_rules_pilot/land_context.py': '45b6ee3346e8c41c86732fb2f4a670b862106d22a4160e35a39c466090794d9a', 'src/card_rules_pilot/land_effects.py': '9aebc93fd0f478cb0ea653c2876e813f16fc19291719aa912682dc0325d80baa', 'src/card_rules_pilot/land_decision.py': '68a46f0836ec26f1421be73c2383ecb40d6516b1f206ab96ab4b997141fa61c2', 'src/card_rules_pilot/land_decision_cli.py': '18456fdce9f2b8b0b325eca18bb8ff9934a11383511030b4417a4d74b8479447', 'src/card_rules_pilot/land_explanation.py': 'e6e5ab70412ef231e78f88db78d489824845566de94eaaaf43c33073f88c8060', 'src/card_rules_pilot/land_explanation_cli.py': '7c49f986a14764054dede4307c42c979522fd5e621666e07ada41c800e700ba1', 'src/card_rules_pilot/land_explanation_policy.py': '38b5bfd7a4508f91cf9f657f30b6959460988537965321146e0912f852e7a82c', 'src/card_rules_pilot/reasoning_policy.py': '4ebb431fb265fe37223aafe7a8c6829a027019ba1cd0d5abe54f94709a9465bf', 'src/card_rules_pilot/behavior_policy.py': 'ac67f056df9889afe377decc13d6d54fb0c741e101e67f5f718021b0e35c6d27', 'src/card_rules_pilot/contract.py': '6ab87a46c13d91b799e1c30e96323898feb08d05ec80d486c4204784d27334e5', '.github/workflows/python-validation.yml': '4c4c7e42ff96c59e6edbe2c4d204c50a464d907153d9caf9df9564b03430b6a2', 'tests/publication_validation_regression.py': 'f4562e15a35d4c9effeaebc3bb6a0fbe4723c6df2004ff4db9bf308ab9c57274', 'docs/ARCHITECTURE.md': 'c4651ad45e47ff9a247151a9c4ca54e8e7dd18b23725cec0571039ef676284b3', 'docs/DECISIONS.md': '47e1fc0e4353f251dde4fb316ec79642a3ab3d51fc0dcc6613b49a795ead73db', 'docs/ACCEPTED_LAND_EXPLANATIONS.md': '52dbaf6699d545303e6c2ef47003d2460ba202bebb1dbc71568123f6b7ba6eb9', 'data/review/land-semantic-decisions/owner-acceptance-v1.json': 'd842e14ba5609f21820c6a6ef9bd686d835169e2162d456911aacfe0b2ca6063', 'data/review/land-mana-utility/interpretations.json': '6376abbc89497ced3b399dc4606361b1eca7621df3b6ececeb60fdec0ae3df11', 'data/review/land-mana-utility/plan.json': 'bed5e94c18b6145a139557a53b8d0af8ae38fbe243e4027da4e8ee9033ab2b3c', 'data/review/land-mana-utility/manifest.json': 'e148fcce3c92a445d61305c488f63b5fecd83efda2a677c0355e31b13252166f'}
GUARD_BASE_SHA256 = '9f4c611146abf03dfbbff34363c6b01fc7f3200d7efc7edc718c225715b69723'

class ManaScenarioPreservationTests(unittest.TestCase):
    def test_historical_sources_documents_workflow_and_evidence_exact(self):
        intact = current_catalog_intact(self)
        for name, digest in PROTECTED.items():
            if name.startswith('data/') and not intact:
                with self.assertRaises(ValueError): mana_scenario.load_mana_scenarios(**decision_arguments())
                continue
            path = ROOT / name
            self.assertFalse(path.is_symlink())
            self.assertEqual(path.stat().st_mode & 0o111, 0)
            self.assertEqual(hashlib.sha256(historical_source_bytes(name, path.read_bytes())).hexdigest(), digest, name)

    def test_exact_three_source_additions_and_narrow_adapter_reversal(self):
        names = {"src/card_rules_pilot/mana_scenario.py", "src/card_rules_pilot/mana_scenario_policy.py", "src/card_rules_pilot/mana_scenario_cli.py"}
        self.assertEqual(guard.MANA_SCENARIO_SOURCE_PATHS, names)
        for name in names:
            self.assertTrue(guard.is_packet_analysis_addition(ROOT / name))
            self.assertFalse(guard.is_packet_analysis_addition(ROOT / (name + '.future')))
        for name in ('src/card_rules_pilot/mana_scenario_engine.py', 'src/gameplay_rules/projection/mana_scenario.py'):
            self.assertFalse(guard.is_packet_analysis_addition(ROOT / name))
        raw = historical_source_bytes('tests/proposed_spell_packet_analysis_preservation.py', (ROOT / 'tests/proposed_spell_packet_analysis_preservation.py').read_bytes())
        old = raw.replace(b'| LAND_EXPLANATION_SOURCE_PATHS | MANA_SCENARIO_SOURCE_PATHS\n', b'| LAND_EXPLANATION_SOURCE_PATHS\n', 1)
        suffix = b'\nMANA_SCENARIO_SOURCE_PATHS = frozenset({"src/card_rules_pilot/mana_scenario.py", "src/card_rules_pilot/mana_scenario_policy.py", "src/card_rules_pilot/mana_scenario_cli.py"})\n'
        self.assertTrue(old.endswith(suffix))
        self.assertEqual(hashlib.sha256(old[:-len(suffix)]).hexdigest(), GUARD_BASE_SHA256)

if __name__ == '__main__': unittest.main()
