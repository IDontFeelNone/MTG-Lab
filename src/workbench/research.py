"""Launch the additive portable research page: python -m workbench.research."""
import argparse
import hmac
import json
import secrets

from probability.draw_access import canonical_json
from .server import ASSETS, Handler, LocalServer
from .investigations import (MAX_BYTES, InvestigationError, append_revision, create_investigation,
                             export_handoff, open_investigation, replay_investigation)

MAX_REQUEST_BYTES = 2 * MAX_BYTES + 8192


def dispatch(request):
    """Closed, finite same-process operations. Never dispatch caller code or paths."""
    if type(request) is not dict or type(request.get('operation')) is not str:
        raise InvestigationError('INVALID_REQUEST', 'closed research request required')
    operation = request['operation']
    fields = {
        'create': {'operation', 'key', 'question', 'created_at'},
        'append': {'operation', 'artifact', 'branch_id', 'parent_id', 'metadata', 'analytical_input', 'calculate'},
        'open': {'operation', 'artifact'}, 'replay': {'operation', 'artifact'},
        'export': {'operation', 'artifact', 'revision_ids'}, 'example': {'operation'},
    }
    if operation not in fields or request.keys() != fields[operation]:
        raise InvestigationError('INVALID_REQUEST', 'unsupported operation or request fields')
    arguments = {k: v for k, v in request.items() if k != 'operation'}
    if operation == 'create':
        return {'artifact': create_investigation(**arguments)}
    if operation == 'append':
        artifact = arguments.pop('artifact')
        return {'artifact': append_revision(artifact, **arguments)}
    if operation == 'open':
        artifact = request['artifact']
        if type(artifact) is str:
            try:
                artifact = artifact.encode('utf-8')
            except UnicodeError:
                raise InvestigationError('INVALID_REQUEST', 'invalid artifact Unicode') from None
        return {'artifact': open_investigation(artifact)}
    if operation == 'replay':
        return replay_investigation(request['artifact'])
    if operation == 'export':
        return {'handoff': export_handoff(**arguments)}
    from .research_example import example_investigation
    return {'artifact': example_investigation()}


def parse_request(raw):
    if type(raw) is not bytes or len(raw) > MAX_REQUEST_BYTES:
        raise InvestigationError('BUDGET_EXCEEDED', 'research request byte budget exceeded')
    def unique(pairs):
        value = {}
        for k, v in pairs:
            if k in value:
                raise InvestigationError('INVALID_REQUEST', 'duplicate JSON key')
            value[k] = v
        return value
    def invalid(_):
        raise InvestigationError('INVALID_REQUEST', 'noninteger JSON numbers unsupported')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                          parse_constant=invalid, parse_float=invalid)
    except (ValueError, UnicodeError, RecursionError):
        raise InvestigationError('INVALID_REQUEST', 'invalid bounded UTF-8 JSON') from None


class ResearchHandler(Handler):
    def do_GET(self):
        if self.path not in ('/research', '/research.js', '/research.css'):
            return super().do_GET()
        if not self._boundary():
            return
        if self.path == '/research.js':
            return self._reply(200, (ASSETS / 'research.js').read_bytes(), 'text/javascript; charset=utf-8')
        if self.path == '/research.css':
            return self._reply(200, (ASSETS / 'research.css').read_bytes(), 'text/css; charset=utf-8')
        # Compose the existing editor unchanged; the additive script uses its
        # request/render boundary. No historical browser asset is rewritten.
        body = (ASSETS / 'index.html').read_bytes().replace(b'__TOKEN__', self.server.capability.encode())
        panel = (ASSETS / 'research-panel.html').read_bytes()
        body = body.replace(b'</header>', b'</header>' + panel, 1)
        body = body.replace(b'</head>', b'<link rel="stylesheet" href="/research.css"><script src="/research.js" defer></script></head>', 1)
        self._reply(200, body, 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path != '/research':
            return super().do_POST()
        if not self._boundary(post=True):
            return
        tokens = self.headers.get_all('X-MTG-Lab-Token')
        if not tokens or len(tokens) != 1 or not tokens[0].isascii() or not hmac.compare_digest(tokens[0], self.server.capability):
            return self._refuse(403, 'local launch token required')
        if self.headers.get_all('Content-Type') != ['application/json']:
            return self._refuse(415, 'JSON content type required')
        lengths = self.headers.get_all('Content-Length')
        if self.headers.get_all('Transfer-Encoding') or not lengths or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            return self._refuse(400, 'one bounded Content-Length required')
        if len(lengths[0]) > 7 or int(lengths[0]) > MAX_REQUEST_BYTES:
            return self._refuse(413, 'research request byte budget exceeded')
        try:
            raw = self.rfile.read(int(lengths[0]))
            if len(raw) != int(lengths[0]):
                raise InvestigationError('INVALID_REQUEST', 'incomplete request')
            result = dispatch(parse_request(raw))
        except InvestigationError as error:
            return self._reply(422, canonical_json(error.as_dict()).encode())
        except (TimeoutError, OSError):
            return self._refuse(408, 'request unavailable')
        self._reply(200, (canonical_json(result) + '\n').encode())


def create_research_server(port=0):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('bounded integer port required')
    server = LocalServer(('127.0.0.1', port), ResearchHandler)
    server.capability = secrets.token_hex(32)
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        server = create_research_server(args.port)
    except (ValueError, OSError):
        parser.exit(2, 'Unable to bind the requested loopback port.\n')
    print('MTG Lab research — open http://127.0.0.1:' + str(server.server_port) + '/research', flush=True)
    print('Memory only. Save explicitly to keep history; Ctrl+C stops the application.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
