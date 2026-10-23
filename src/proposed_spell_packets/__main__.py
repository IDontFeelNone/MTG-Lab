"""Explicit offline CLI for fictional packet drafts and immutable records."""
import argparse
import json
import sys

from gameplay_rules.errors import GameplayContractError
from .authoring import Workspace
from .validation import PACKET_NAMES


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Existing local pilot directory outside the repository")
    commands = parser.add_subparsers(dest="command", required=True)
    draft = commands.add_parser("draft", help="Copy an explicitly selected fictional example or revise a recorded packet")
    source = draft.add_mutually_exclusive_group(required=True)
    source.add_argument("--example", choices=PACKET_NAMES)
    source.add_argument("--base", help="Exact recorded parent packet identity")
    draft.add_argument("--output", required=True, help="New editable draft file outside the repository")
    record = commands.add_parser("record", help="Validate and explicitly record canonical immutable bytes")
    source = record.add_mutually_exclusive_group(required=True)
    source.add_argument("--draft", help="Editable v1 draft envelope; derive its identity")
    source.add_argument("--sealed", help="Existing canonical packet; verify its supplied identity")
    for name in ("inspect", "history"):
        command = commands.add_parser(name, help="Read validated authored explanations" + (" with ancestors" if name == "history" else ""))
        command.add_argument("packet_id")
    args = parser.parse_args(argv)
    try:
        workspace = Workspace(args.workspace)
        if args.command == "draft":
            result = workspace.draft(example=args.example, base=args.base, output=args.output)
        elif args.command == "record":
            result = workspace.record(draft=args.draft, sealed=args.sealed)
        else:
            print(workspace.inspect(args.packet_id, history=args.command == "history"))
            return 0
        print(json.dumps(result, sort_keys=True))
        return 0
    except (GameplayContractError, OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(json.dumps({"status": "REJECTED", "error": str(error), "execution_authority": "BLOCKED"}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
