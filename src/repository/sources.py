"""Generic loading for canonical source records and acquisition manifests."""
from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any,Mapping
from validation import SchemaValidationError,validate_document
_ROOT=Path(__file__).resolve().parents[2]/"data"/"canonical"/"games"; _ID=re.compile(r"^[a-z0-9][a-z0-9._-]*$")
class SourceLoadError(ValueError): pass
def _path(game,product_id,name,root): 
 if not all(_ID.fullmatch(x) for x in (game,product_id,name)): raise ValueError("identifiers must be stable lowercase identifiers")
 return (Path(root) if root else _ROOT)/game/"products"/product_id/"sources"/f"{name}.json"
def load_source_record(game,product_id,source_id,*,games_root=None):
 root=Path(games_root) if games_root else _ROOT
 product_path=_path(game,product_id,source_id,root)
 global_path=root/game/"sources"/f"{source_id}.json"
 p=product_path if product_path.exists() else global_path
 try: d=json.loads(p.read_text(encoding="utf-8"))
 except FileNotFoundError as e: raise SourceLoadError(f"Source record not found: {p}") from e
 except json.JSONDecodeError as e: raise SourceLoadError(f"Malformed source record: {p}") from e
 try: validate_document(d,"source-record")
 except SchemaValidationError as e: raise SourceLoadError(str(e)) from e
 if d["id"]!=source_id: raise SourceLoadError("Source identifier does not match canonical path")
 return d
def load_acquisition_manifest(game,product_id,manifest_id,*,games_root=None):
 p=_path(game,product_id,manifest_id,games_root).with_name(f"{manifest_id}.manifest.json")
 try: d=json.loads(p.read_text(encoding="utf-8"))
 except (FileNotFoundError,json.JSONDecodeError) as e: raise SourceLoadError(f"Cannot load manifest: {p}") from e
 try: validate_document(d,"acquisition-manifest")
 except SchemaValidationError as e: raise SourceLoadError(str(e)) from e
 if d["id"]!=manifest_id or d["product_id"]!=product_id: raise SourceLoadError("Manifest identifiers do not match canonical path")
 for source_id in d["source_ids"]: load_source_record(game,product_id,source_id,games_root=games_root)
 return d
