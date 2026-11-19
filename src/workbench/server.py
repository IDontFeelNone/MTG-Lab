"""Loopback-only, fixed-route local transport. No file, shell or storage API."""
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets

from probability.draw_access import canonical_json
from .adapter import MAX_INPUT_BYTES, WorkbenchError, assess_workbench, parse_workbench

ASSETS = Path(__file__).parent / 'assets'
ROUTES = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/app.css': ('app.css', 'text/css; charset=utf-8')}


class LocalServer(HTTPServer):
    """One bounded request at a time; socket and per-launch capability stay local."""
    def server_bind(self):
        if self.server_address[0] != '127.0.0.1':
            raise ValueError('only IPv4 loopback binding is supported')
        super().server_bind()

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


class Handler(BaseHTTPRequestHandler):
    server_version = 'MTGLabLocal/1'
    sys_version = ''

    def log_message(self, *_):
        pass  # No labels, deck contents, paths or access records are persisted.

    def send_error(self, code, message=None, explain=None):
        self._refuse(code, 'unsupported or malformed local request')

    def _reply(self, status, body, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        for key, value in {
            'Content-Type': content_type, 'Content-Length': str(len(body)),
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        }.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _refuse(self, status, reason):
        self._reply(status, canonical_json(WorkbenchError(reason).as_dict()).encode())

    def _boundary(self, *, post=False):
        expected = '127.0.0.1:' + str(self.server.server_port)
        if self.headers.get_all('Host') != [expected]:
            self._refuse(403, 'local Host required'); return False
        origins = self.headers.get_all('Origin')
        if (post and origins != ['http://' + expected]) or (origins and origins != ['http://' + expected]):
            self._refuse(403, 'same Origin required'); return False
        sites = self.headers.get_all('Sec-Fetch-Site')
        if sites and sites not in (['same-origin'], ['none']):
            self._refuse(403, 'cross-origin request refused'); return False
        return True

    def do_GET(self):
        if not self._boundary(): return
        if self.path not in ROUTES:
            self._refuse(404, 'unknown local route'); return
        name, kind = ROUTES[self.path]
        body = (ASSETS / name).read_bytes()
        if name == 'index.html': body = body.replace(b'__TOKEN__', self.server.capability.encode())
        self._reply(200, body, kind)

    def do_POST(self):
        if not self._boundary(post=True): return
        if self.path != '/assess':
            self._refuse(404, 'unknown local route'); return
        tokens = self.headers.get_all('X-MTG-Lab-Token')
        if not tokens or len(tokens) != 1 or not tokens[0].isascii() or not hmac.compare_digest(tokens[0], self.server.capability):
            self._refuse(403, 'local launch token required'); return
        if self.headers.get_all('Content-Type') != ['application/json']:
            self._refuse(415, 'JSON content type required'); return
        lengths = self.headers.get_all('Content-Length')
        if self.headers.get_all('Transfer-Encoding') or not lengths or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self._refuse(400, 'one bounded Content-Length required'); return
        if len(lengths[0]) > 6 or int(lengths[0]) > MAX_INPUT_BYTES:
            self._refuse(413, 'request byte budget exceeded'); return
        try:
            raw = self.rfile.read(int(lengths[0]))
            if len(raw) != int(lengths[0]): raise WorkbenchError('incomplete request body')
            report = assess_workbench(parse_workbench(raw))
        except WorkbenchError as error:
            self._refuse(422, str(error)); return
        except (TimeoutError, OSError):
            self._refuse(408, 'request body unavailable'); return
        self._reply(200, (canonical_json(report) + '\n').encode())


def create_server(port=0):
    """Bind exclusively to IPv4 loopback. Port zero selects an unused local port."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('port must be an integer from 0 through 65535')
    server = LocalServer(('127.0.0.1', port), Handler)
    server.capability = secrets.token_hex(32)
    return server
