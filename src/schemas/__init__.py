"""Versioned JSON Schema contracts for MTG Lab canonical data."""
from pathlib import Path
SCHEMA_VERSION="v1"
SCHEMA_NAMES=("card","product","printing","slot","print-sheet","source-record","acquisition-manifest")
def schema_path(name:str,version:str=SCHEMA_VERSION)->Path:
 if name not in SCHEMA_NAMES: raise ValueError(f"Unknown schema: {name}")
 return Path(__file__).parent/version/f"{name}.schema.json"
