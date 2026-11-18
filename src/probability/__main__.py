"""Bounded, read-only exact card-access analysis: python -m probability draw-access."""
import argparse
from pathlib import Path
import sys

from .draw_access import (MAX_INPUT_BYTES, DrawAccessError, assess_draw_access,
                          canonical_json, parse_draw_access)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    draw = commands.add_parser('draw-access', help='exact probabilities over declared disjoint groups')
    draw.add_argument('--input', required=True, help='UTF-8 JSON file, or - for stdin')
    odds = commands.add_parser('pack-target-odds', help='exact at-least-one odds from an admitted pack model')
    odds.add_argument('--input', required=True, help='UTF-8 JSON file, or - for stdin')
    odds.add_argument('--game', default='magic')
    odds.add_argument('--data-root', type=Path)
    odds.add_argument('--product-id', required=True)
    odds.add_argument('--definition-id', required=True)
    args = parser.parse_args(argv)
    if args.command == 'pack-target-odds':
        from simulation import load_pack_simulator, PackSimulationError
        from .pack_odds import PackOddsError, parse_pack_odds, assess_pack_target
        try:
            if args.input == '-':
                raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            else:
                with Path(args.input).open('rb') as stream:
                    raw = stream.read(MAX_INPUT_BYTES + 1)
            request = parse_pack_odds(raw)
            view = load_pack_simulator(args.game, data_root=args.data_root).inspect(
                args.product_id, pack_definition_id=args.definition_id)
            result = assess_pack_target(view, request)
        except (PackOddsError, PackSimulationError, OSError) as error:
            if isinstance(error, PackOddsError): failure = error
            elif isinstance(error, PackSimulationError):
                failure = PackOddsError('MODEL_NOT_READY', ', '.join(error.requirements))
            else: failure = PackOddsError('INVALID_INPUT', 'input file unavailable')
            print(canonical_json(failure.as_dict()))
            return 2
        print(canonical_json(result))
        return 0
    try:
        if args.input == '-':
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            with Path(args.input).open('rb') as stream:
                raw = stream.read(MAX_INPUT_BYTES + 1)
        result = assess_draw_access(parse_draw_access(raw))
    except (DrawAccessError, OSError) as error:
        failure = error if isinstance(error, DrawAccessError) else DrawAccessError('input file unavailable')
        print(canonical_json(failure.as_dict()))
        return 2
    print(canonical_json(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
