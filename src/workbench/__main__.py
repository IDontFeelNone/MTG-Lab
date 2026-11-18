"""Launch the local deck-consistency workbench; Ctrl+C stops it."""
import argparse
from .server import create_server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0, help='local port (default: select an unused port)')
    args = parser.parse_args(argv)
    try:
        server = create_server(args.port)
    except (ValueError, OSError):
        parser.exit(2, 'Unable to bind the requested loopback port.\n')
    print('MTG Lab — open http://127.0.0.1:' + str(server.server_port) + '/', flush=True)
    print('Local memory only; no automatic persistence. Stop with Ctrl+C.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
