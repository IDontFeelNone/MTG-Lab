#!/usr/bin/env python3
"""Regenerate the deterministic Phase 137 read-only audit report."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from card_intelligence import build_phase137_audit, report_bytes
path=ROOT/'data/reviews/phase-137/printing-history-audit.json'; path.parent.mkdir(parents=True,exist_ok=True)
path.write_bytes(report_bytes(build_phase137_audit(ROOT/'data'))); print(path.relative_to(ROOT))
