#!/usr/bin/env python3
"""Acquire and immutably retain the bounded Phase 135 MTGJSON projection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import socket
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from production_evidence.pilot_printings import PilotPrintingRetention


USER_AGENT = "MTG-Lab/Phase-135B (GitHub-Actions bounded printing acquisition)"
SOURCE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/gzip, application/octet-stream;q=0.9",
    "Accept-Encoding": "identity",
}
CHECKSUM_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/plain, application/octet-stream;q=0.9",
    "Accept-Encoding": "identity",
}
ALLOWED_HOSTS = frozenset({"mtgjson.com", "www.mtgjson.com"})
MAX_REDIRECTS = 5


def safe_url_descriptor(url: str) -> str:
    """Return a URL without credentials, query data, or fragments."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    port = f":{parts.port}" if parts.port and parts.port != 443 else ""
    return urlunsplit((parts.scheme.lower(), host + port, parts.path, "", ""))


class AcquisitionTransportError(RuntimeError):
    """A sanitized, classified provider transport failure."""

    def __init__(self, failure_type: str, message: str, metadata: dict | None = None):
        super().__init__(message)
        self.failure_type = failure_type
        self.safe_message = message
        self.metadata = dict(metadata or {})


class SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_hosts: frozenset[str]):
        super().__init__()
        self.allowed_hosts = allowed_hosts
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if parts.scheme.lower() != "https":
            raise AcquisitionTransportError("unsafe_redirect", "redirect destination was not HTTPS")
        if (parts.hostname or "").lower() not in self.allowed_hosts:
            raise AcquisitionTransportError("unsafe_redirect", "redirect destination host was not approved")
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise AcquisitionTransportError("redirect_limit", "provider redirect limit exceeded")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MTGJSONDownloader:
    """Fetch one checksum sidecar and exactly one large MTGJSON source response."""

    def __init__(self, *, timeout: int = 120, opener_factory=build_opener):
        self.timeout = timeout
        self.opener_factory = opener_factory
        self.diagnostic: dict[str, object] = {}
        self.source_requests = 0
        self.checksum_requests = 0

    @staticmethod
    def _validate_url(url: str) -> None:
        parts = urlsplit(url)
        if parts.scheme.lower() != "https" or (parts.hostname or "").lower() not in ALLOWED_HOSTS:
            raise AcquisitionTransportError("invalid_url", "provider URL was not an approved HTTPS URL")
        if parts.username or parts.password:
            raise AcquisitionTransportError("invalid_url", "provider URL contained forbidden credentials")

    def _request(self, url: str, headers: dict[str, str], kind: str):
        self._validate_url(url)
        redirector = SafeRedirectHandler(ALLOWED_HOSTS)
        opener = self.opener_factory(redirector)
        if kind == "source":
            self.source_requests += 1
        else:
            self.checksum_requests += 1
        try:
            response = opener.open(Request(url, headers=headers), timeout=self.timeout)
            final_url = response.geturl()
            self._validate_url(final_url)
            status = getattr(response, "status", response.getcode())
            content_type = response.headers.get_content_type()
            self.diagnostic.update({
                f"{kind}_http_status": status,
                f"{kind}_final_host": (urlsplit(final_url).hostname or "").lower(),
                f"{kind}_final_url_descriptor": safe_url_descriptor(final_url),
                f"{kind}_content_type": content_type,
                f"{kind}_redirect_count": redirector.redirect_count,
            })
            if status != 200:
                response.close()
                raise AcquisitionTransportError("http_status", f"{kind} response returned HTTP {status}")
            return response
        except AcquisitionTransportError:
            self.diagnostic[f"{kind}_redirect_count"] = redirector.redirect_count
            raise
        except HTTPError as error:
            error_url = error.geturl()
            error_host = (urlsplit(error_url).hostname or "").lower()
            self.diagnostic.update({f"{kind}_http_status": error.code,
                                    f"{kind}_final_host": error_host if error_host in ALLOWED_HOSTS else "unapproved",
                                    f"{kind}_final_url_descriptor": safe_url_descriptor(error_url),
                                    f"{kind}_content_type": error.headers.get_content_type() if error.headers else None,
                                    f"{kind}_redirect_count": redirector.redirect_count})
            failure = "http_403" if error.code == 403 else "http_status"
            raise AcquisitionTransportError(failure, f"{kind} response returned HTTP {error.code}") from None
        except (TimeoutError, socket.timeout):
            self.diagnostic[f"{kind}_redirect_count"] = redirector.redirect_count
            raise AcquisitionTransportError("timeout", f"{kind} request timed out") from None
        except (URLError, ssl.SSLError, OSError) as error:
            self.diagnostic[f"{kind}_redirect_count"] = redirector.redirect_count
            reason = getattr(error, "reason", None)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise AcquisitionTransportError("timeout", f"{kind} request timed out") from None
            raise AcquisitionTransportError("transport_error", f"{kind} transport failed") from None

    @staticmethod
    def parse_checksum(payload: bytes) -> str:
        if len(payload) > 4096:
            raise AcquisitionTransportError("malformed_checksum", "checksum sidecar was too large")
        try:
            line = payload.decode("ascii").strip()
        except UnicodeDecodeError:
            raise AcquisitionTransportError("malformed_checksum", "checksum sidecar was not ASCII") from None
        fields = line.split()
        if len(fields) != 2 or fields[1].lstrip("*") != "AllPrintings.json.gz":
            raise AcquisitionTransportError("malformed_checksum", "checksum sidecar named an unexpected file")
        digest = fields[0].lower()
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise AcquisitionTransportError("malformed_checksum", "checksum sidecar did not contain a SHA-256")
        return digest

    def __call__(self, url: str, target: Path) -> dict:
        checksum_url = url + ".sha256"
        self.diagnostic.update({"requested_source_descriptor": safe_url_descriptor(url),
                                "checksum_descriptor": safe_url_descriptor(checksum_url)})
        with self._request(checksum_url, CHECKSUM_HEADERS, "checksum") as response:
            expected = self.parse_checksum(response.read(4097))
        digest = hashlib.sha256()
        byte_count = 0
        with self._request(url, SOURCE_HEADERS, "source") as response, target.open("xb") as output:
            while chunk := response.read(1024 * 1024):
                byte_count += len(chunk)
                digest.update(chunk)
                output.write(chunk)
            transport = {"status": response.status, "content_type": response.headers.get_content_type(),
                         "final_url_descriptor": safe_url_descriptor(response.geturl()),
                         "final_host": (urlsplit(response.geturl()).hostname or "").lower(),
                         "redirect_count": self.diagnostic.get("source_redirect_count", 0)}
        if byte_count == 0:
            raise AcquisitionTransportError("empty_source", "provider source response was empty")
        actual = digest.hexdigest()
        if actual != expected:
            raise AcquisitionTransportError("checksum_mismatch", "provider source SHA-256 did not match sidecar")
        transport.update({"expected_sha256": expected, "source_sha256": actual, "source_byte_count": byte_count})
        return transport


def write_diagnostic(path: Path | None, value: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--canonical-snapshot", required=True)
    parser.add_argument("--acquired-at", required=True)
    parser.add_argument("--repository", type=Path, default=Path("data/evidence/phase-135"))
    parser.add_argument("--source-url", default="https://mtgjson.com/api/v5/AllPrintings.json.gz")
    parser.add_argument("--diagnostics", type=Path)
    args = parser.parse_args()
    diagnostic: dict[str, object] = {
        "schema_version": "mtgjson-pilot-transport-diagnostic-v1", "run_id": args.run_id,
        "acquisition_timestamp": args.acquired_at,
        "requested_source_descriptor": safe_url_descriptor(args.source_url),
        "checksum_descriptor": safe_url_descriptor(args.source_url + ".sha256"),
    }
    downloader = MTGJSONDownloader()
    try:
        args.repository.mkdir(parents=True, exist_ok=True)
        result = PilotPrintingRetention(args.repository, downloader).acquire(
            run_id=args.run_id, source_url=args.source_url,
            canonical_snapshot=args.canonical_snapshot, acquired_at=args.acquired_at)
        diagnostic.update(downloader.diagnostic)
        diagnostic.update({"failure_type": None, "message": "acquisition completed",
                           "source_requests": downloader.source_requests,
                           "checksum_requests": downloader.checksum_requests})
        write_diagnostic(args.diagnostics, diagnostic)
        print(json.dumps(result["report"], indent=2, sort_keys=True))
        return 0
    except Exception as error:
        diagnostic.update(downloader.diagnostic)
        if isinstance(error, AcquisitionTransportError):
            diagnostic.update(error.metadata)
            failure_type, message = error.failure_type, error.safe_message
        else:
            failure_type, message = "acquisition_error", str(error)
        diagnostic.update({"failure_type": failure_type, "message": message,
                           "source_requests": downloader.source_requests,
                           "checksum_requests": downloader.checksum_requests})
        write_diagnostic(args.diagnostics, diagnostic)
        print(json.dumps(diagnostic, indent=2, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
