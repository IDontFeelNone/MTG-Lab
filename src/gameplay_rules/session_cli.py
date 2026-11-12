"""Bounded JSON-lines player actions for an explicit fictional gameplay session."""
import argparse
import json
from pathlib import Path
import sys

from .errors import GameplayContractError
from .models import GameAction
from .session import (decode_session_json, load_gameplay_session, replay_session,
                      render_session_view)
from .snapshots import MAX_CONTRACT_BYTES, load_card_semantics, load_rules_snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rules', required=True)
    parser.add_argument('--semantics', action='append', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--format', choices=('json', 'text'), default='json')
    parser.add_argument('--replay', help='Recompute a full-information session report; no action execution from prose')
    parser.add_argument('--expected-session-id')
    parser.add_argument('--history', action='store_true', help='Print full-information replay history, including hidden state')
    args = parser.parse_args(argv)
    if args.expected_session_id and not args.replay:
        parser.error('--expected-session-id requires --replay')

    def emit(value, text):
        print(text if args.format == 'text' else json.dumps(value, sort_keys=True, allow_nan=False), end='' if args.format == 'text' else '\n')

    try:
        session = load_gameplay_session(rules_path=args.rules, semantics_paths=args.semantics, state_path=args.state)
        if args.replay:
            path = Path(args.replay)
            if ('..' in path.parts or '\\' in str(path) or
                    any(p.is_symlink() for p in (path, *path.parents)) or path.stat().st_size > MAX_CONTRACT_BYTES):
                raise GameplayContractError('invalid_session', 'Unsafe or oversized replay report')
            report = decode_session_json(path.read_bytes())
            if type(report) is not dict:
                raise GameplayContractError('invalid_session', 'Complete session report required')
            if report.get('initial_state') != session.state.to_dict():
                raise GameplayContractError('session_binding', 'Replay must bind the selected initial-state file')
            session = replay_session(load_rules_snapshot(args.rules), [load_card_semantics(p) for p in args.semantics],
                                     report, expected_session_id=args.expected_session_id)
            emit(dict(type='replay_verified', session_id=session.report()['session_id'], view=session.view()),
                 'Replay verified: ' + session.report()['session_id'] + '\n' + render_session_view(session.view()))
        else:
            emit(dict(type='state', view=session.view()), render_session_view(session.view()))
            rejected = False
            while True:
                line = sys.stdin.readline(MAX_CONTRACT_BYTES + 1)
                if not line:
                    break
                if len(line) > MAX_CONTRACT_BYTES and not line.endswith('\n'):
                    emit(dict(type='error', code='session_bound', state_id=session.state.identity), 'session_bound\n')
                    return 2  # Never reinterpret the tail of one oversized action as another request.
                try:
                    entry = session.submit(GameAction.from_dict(decode_session_json(line)))
                    rejected |= entry['status'] != 'LEGAL'
                    emit(dict(type='action_result', sequence=entry['sequence'], status=entry['status'],
                              action_id=entry['request']['action_id'],
                              reasons=entry['legality']['explanation']['reason_codes'],
                              transition_ids=[t['transition_id'] for t in entry['transitions']], view=session.view()),
                         f"Attempt {entry['sequence']}: {entry['request']['kind']} — {entry['status']} " +
                         ', '.join(entry['legality']['explanation']['reason_codes']) + '\n' + render_session_view(session.view()))
                except GameplayContractError as error:
                    rejected = True
                    emit(dict(type='error', code=error.code, state_id=session.state.identity), str(error) + '\n')
            if args.history:
                print(json.dumps(session.report(), sort_keys=True, indent=2, allow_nan=False))
            return 2 if rejected else 0
        if args.history:
            print(json.dumps(session.report(), sort_keys=True, indent=2, allow_nan=False))
        return 0
    except (GameplayContractError, OSError) as error:
        code = error.code if isinstance(error, GameplayContractError) else 'unavailable_session_file'
        emit(dict(type='error', code=code), code + '\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
