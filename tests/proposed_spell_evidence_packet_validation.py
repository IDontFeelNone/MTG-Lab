"""Compatibility entry point for the single shared PR #209 packet checker.

Aliasing preserves historical test imports and patches of module globals; the
implementation lives in tooling, never in tests.
"""
import sys

from proposed_spell_packets import validation as _validation

if __name__ == "__main__":
    _validation.main()
else:
    sys.modules[__name__] = _validation
