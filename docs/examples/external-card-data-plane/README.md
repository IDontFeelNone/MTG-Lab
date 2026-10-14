# Fictional snapshot contract example

This is an original, unrelated fictional dataset for documentation and public
tests. It is not a provider dataset, production snapshot, real admission decision,
source-policy clearance or user inventory. No new runtime loader is implemented.
The tiny JSON Schema applies only to this example, outside the runtime registry.

`fictional-snapshot/` contains one Card and one Printing using today's v1 schemas,
a source record and original evidence, a fixture-only policy, schema bindings,
source/content/release manifests and an **illustrative** validation report. Its
`unrun_production_checks` and `production_eligible=false` prevent representing the
example as a production acceptance receipt. The report states expected fixture
checks; actual test results are separately recorded by unittest, not manufactured
as a retained production report.

The supplied `created_at` is a fixed fictional authoring input, not a provider
publication time. The source is a local original fixture URN; no network request
is made. The example has no actual reviewer or admission decision.

## Reproduce the identities

Read JSON and serialize with UTF-8, sorted keys, compact separators, no trailing
newline, `ensure_ascii=False` and `allow_nan=False`. Reject duplicate keys. For
each semantic identity hash this exact wrapper:

```python
payload = {"identity_domain": "mtg-lab:" + kind + ":design-v1", "document": body}
identity = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False, allow_nan=False).encode()).hexdigest()
```

| Kind | Body |
| --- | --- |
| `source-manifest` | source-manifest.json except source_manifest_id |
| `content-manifest` | content-manifest.json except content_id |
| `validation-input` | release-manifest.json's complete validation_input object |
| `release-manifest` | release-manifest.json except snapshot_id |
| `schema-set` | complete schema-bindings.json |
| `policy` | complete policy.json |

Exact file hashes instead hash retained bytes, including their trailing LF.
Each file entry carries a relative path, byte length and SHA-256. Content file
entries are sorted; source/content/report/release control documents are separately
bound to avoid self-referential hashes. All files in the example bundle must be
accounted for, including the source-manifest and validation report.

The outer fictional snapshot identity is
`804d640a305579ad81bbac8b5c40850ec80e5b1b96374e3ca5b798731a35fc65`.
It is not the existing query snapshot identity and never replaces old hash recipes.

`baseline-audit.json` binds the architecture documents inspected at canonical main
`ec8fcbf97c84d24337503c81dd1c31a31e163d44`; it records that API_CONTRACT.md was
absent. It is an audit inventory, not permission evidence or a runtime dependency.
Accepted architecture/decision text is preserved as an exact prefix before the
new proposed notes.

## What the tests demonstrate

Run `PYTHONPATH=src python -m unittest discover -s tests -p
'test_external_card_data_plane_design.py' -v`. Checks cover the proposed example's
identity/hash/inventory closure, tampering, safe paths, repeated metadata, authority
separation, documentation links and preserved accepted text. They also relocate
this fictional data and call the **existing** CanonicalQueryEngine and
CanonicalCollectionResolver with explicit data roots.

Those reader checks demonstrate useful current seams and stable IDs across roots.
They do not demonstrate a new production loader, complete typed materialization,
protected integration CI, authenticated snapshot activation, real admission,
permission to process MB2, or successful replay of unretained upstream bytes.
