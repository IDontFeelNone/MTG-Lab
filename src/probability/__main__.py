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
    args = parser.parse_args(argv)
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
