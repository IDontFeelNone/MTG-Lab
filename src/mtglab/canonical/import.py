"""Command line entry point for reviewed canonical imports."""
import argparse
import json
from pathlib import Path

from canonical_import import CSVSource, JSONSource, ImportError, import_dataset

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="reviewed JSON file or CSV directory")
    parser.add_argument("--game", required=True)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--report", type=Path, help="optional JSON report destination")
    args = parser.parse_args(argv)
    adapter = JSONSource(args.source) if args.format == "json" else CSVSource(args.source)
    try:
        report = import_dataset(adapter, args.game, dry_run=args.dry_run,
                                validation_only=args.validation_only)
    except ImportError as error:
        parser.error(str(error))
    output = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.report: args.report.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0

if __name__ == "__main__": raise SystemExit(main())
