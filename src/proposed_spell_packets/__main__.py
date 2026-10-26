"""Explicit offline CLI for fictional packet drafts and immutable records."""
import argparse
import json
import sys

from gameplay_rules.errors import GameplayContractError
from .authoring import Workspace
from .analysis import analyze, compare, render
from .validation import PACKET_NAMES
from .conditions import evaluate, read_model, render as render_condition
from .sensitivity import analyze as analyze_sensitivity, render as render_sensitivity
from .alternatives import evaluate as evaluate_alternatives, read_definition, render as render_alternatives


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
    analysis = commands.add_parser("analyze", help="Trace declared evidence dependencies; no sufficiency or gameplay verdict")
    analysis.add_argument("packet_id", help="Exact recorded packet identity")
    analysis.add_argument("--json", action="store_true", help="Emit deterministic derived-report bytes")
    comparison = commands.add_parser("compare", help="Compare an explicit ancestor and descendant; no latest selection")
    comparison.add_argument("ancestor_id")
    comparison.add_argument("descendant_id")
    comparison.add_argument("--json", action="store_true", help="Emit deterministic derived-report bytes")
    evaluation = commands.add_parser("evaluate", help="Compute one explicitly authored fictional condition under selected assertions")
    evaluation.add_argument("packet_id", help="Exact recorded packet identity")
    evaluation.add_argument("--model", required=True, help="Separate explicit versioned condition-model JSON file")
    evaluation.add_argument("--json", action="store_true", help="Emit canonical immutable computed-result bytes")
    sensitivity = commands.add_parser("sensitivity", help="Examine independent Boolean hypotheses for selected UNKNOWN assertion groups")
    sensitivity.add_argument("packet_id", help="Exact recorded packet identity")
    sensitivity.add_argument("--model", required=True, help="Exact explicit versioned condition-model JSON file")
    sensitivity.add_argument("--json", action="store_true", help="Emit canonical hypothetical-report bytes")
    alternatives = commands.add_parser("evaluate-alternatives", help="Compare explicitly listed fictional alternatives against shared authored requirements")
    alternatives.add_argument("packet_id", help="Exact recorded packet identity")
    alternatives.add_argument("--requirements", required=True, help="Explicit versioned shared-requirement definition JSON file")
    alternatives.add_argument("--json", action="store_true", help="Emit canonical computed comparison-report bytes")
    args = parser.parse_args(argv)
    try:
        workspace = Workspace(args.workspace)
        if args.command == "draft":
            result = workspace.draft(example=args.example, base=args.base, output=args.output)
        elif args.command == "record":
            result = workspace.record(draft=args.draft, sealed=args.sealed)
        elif args.command == "evaluate-alternatives":
            report = evaluate_alternatives(workspace, args.packet_id, read_definition(args.requirements))
            if args.json:
                sys.stdout.buffer.write(report.canonical_bytes)
            else:
                print(render_alternatives(report))
            return 0
        elif args.command == "sensitivity":
            report = analyze_sensitivity(workspace, args.packet_id, read_model(args.model))
            if args.json:
                sys.stdout.buffer.write(report.canonical_bytes)
            else:
                print(render_sensitivity(report))
            return 0
        elif args.command == "evaluate":
            report = evaluate(workspace, args.packet_id, read_model(args.model))
            if args.json:
                sys.stdout.buffer.write(report.canonical_bytes)
            else:
                print(render_condition(report))
            return 0
        elif args.command in ("analyze", "compare"):
            report = (analyze(workspace, args.packet_id) if args.command == "analyze"
                      else compare(workspace, args.ancestor_id, args.descendant_id))
            if args.json:
                sys.stdout.buffer.write(report.canonical_bytes)
            else:
                print(render(report))
            return 0
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
