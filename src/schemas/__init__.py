"""Versioned JSON Schema contracts for MTG Lab data artifacts."""
from pathlib import Path
SCHEMA_VERSION="v1"
SCHEMA_NAMES=("card","product","printing","slot","print-sheet","source-record","acquisition-manifest","evidence-manifest","parsed-record-artifact","normalized-candidate-artifact","promotion-audit","population-review-report")
def schema_path(name:str,version:str=SCHEMA_VERSION)->Path:
 if name not in SCHEMA_NAMES: raise ValueError(f"Unknown schema: {name}")
 return Path(__file__).parent/version/f"{name}.schema.json"
