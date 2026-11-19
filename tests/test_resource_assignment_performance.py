"""Small production-envelope checks in isolated, strictly limited workers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = '''import json,resource,sys
resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
resource.setrlimit(resource.RLIMIT_CPU,(59,60))
from probability.resource_assignment import assess_resource_assignment,ResourceAssignmentError
try: result=assess_resource_assignment(json.load(sys.stdin))
except ResourceAssignmentError as error: result=error.as_dict()
print(json.dumps(result))
'''


@unittest.skipUnless(sys.platform.startswith('linux'), 'resource-limited production envelope requires Linux rlimits')
class ResourceAssignmentPerformanceTests(unittest.TestCase):
    def test_representative_adversarial_and_refusal_cases_under_enforced_limits(self):
        cases = json.loads((ROOT / 'tests/fixtures/resource_assignment_v1/benchmarks.json').read_bytes())
        for name, request in cases.items():
            with self.subTest(name=name):
                process = subprocess.run([sys.executable, '-B', '-c', WORKER], input=json.dumps(request),
                                         capture_output=True, text=True, cwd=ROOT,
                                         env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')}, timeout=60)
                self.assertEqual(process.returncode, 0, process.stderr)
                report = json.loads(process.stdout)
                if name.endswith('refusal'):
                    self.assertEqual(report['status'], 'REFUSED')
                    self.assertEqual(report['code'], 'RESOURCE_BUDGET_REFUSAL')
                    self.assertNotIn('probability', report)
                else:
                    self.assertEqual(report['status'], 'CALCULATED')
                    self.assertGreater(int(report['probability']['numerator']), 0)


if __name__ == '__main__':
    unittest.main()
