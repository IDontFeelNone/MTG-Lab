"""Bounded, metadata-only intake of explicitly selected official source URLs.

This adapter uses the existing acquisition provider seam, but deliberately does
not use its raw-payload store or normalization pipeline.  Response bytes exist
only transiently for an exact hash and bounded source-designation metadata.
They never enter ``ProviderResponse.payload`` or a retained report.  Retrieval
is neither a source-permission decision nor selection of a current rules release.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from html.parser import HTMLParser
from http.client import HTTPException
import hashlib
import math
import re
import socket
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from acquisition.framework import (
    AcquisitionError, AcquisitionProvider, ProviderRequest, ProviderResponse,
)


ALLOWED_WIZARDS_HOSTS = frozenset({
    "magic.wizards.com", "www.magic.wizards.com", "media.wizards.com",
})
ALLOWED_MEDIA_TYPES = frozenset({"text/html", "text/plain", "application/pdf"})
MAX_RESPONSE_BYTES = 5_000_000
MAX_REDIRECTS = 5
MAX_TIMEOUT_SECONDS = 30
MAX_DESIGNATED_LINKS = 24
MAX_METADATA_TEXT = 160
MAX_URL_LENGTH = 2048
_DATASET = "rules-source"


def _official_url(value: Any) -> str:
    """Validate an explicit credential-free HTTPS URL; never infer a host."""
    if not isinstance(value, str) or not value or len(value) > MAX_URL_LENGTH or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        raise AcquisitionError("official source URL must be an explicit safe HTTPS URL")
    if "\\" in value or re.search(r"%(?:00|0a|0d)", value, re.IGNORECASE):
        raise AcquisitionError("official source URL contains an ambiguous path")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise AcquisitionError("official source URL is malformed") from error
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_WIZARDS_HOSTS
            or parsed.username is not None or parsed.password is not None
            or port not in {None, 443} or parsed.query or parsed.fragment):
        raise AcquisitionError("official source URL is outside the explicit credential-free HTTPS policy")
    return urlunsplit(("https", parsed.hostname, parsed.path or "/", "", ""))


def _observed_at(value: Any) -> str:
    if not isinstance(value, str):
        raise AcquisitionError("observed_at must be an explicit timestamp with timezone")
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AcquisitionError("observed_at must be an explicit timestamp with timezone") from error
    if observed.tzinfo is None:
        raise AcquisitionError("observed_at must include a timezone")
    return value


def _bounded_text(value: str) -> str:
    return " ".join(value.split())[:MAX_METADATA_TEXT]


@dataclass(frozen=True, slots=True)
class MetadataTransportResponse:
    """Ephemeral transport result; never serialize or retain its body."""

    status: int
    url: str
    content_type: str
    body: bytes = field(repr=False)
    location: str | None = None
    content_encoding: str = "identity"


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


class UrllibMetadataTransport:
    """Use system proxy/CA configuration with cookies and redirects disabled."""

    def fetch(self, url: str, *, max_response_bytes: int, timeout_seconds: float) -> MetadataTransportResponse:
        # build_opener retains urllib's normal ProxyHandler and TLS CA behavior.
        # No cookie jar, authorization handler, custom trust bypass or redirect
        # handler is installed.  Redirect targets are reviewed by the provider.
        opener = build_opener(_NoRedirects())
        request = Request(url, headers={
            "Accept": "text/html, text/plain, application/pdf",
            "Accept-Encoding": "identity",
            "User-Agent": "MTG-Lab-source-metadata-review/1.0",
        }, method="GET")
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                media_type = response.headers.get_content_type()
                encoding = response.headers.get("Content-Encoding", "identity")
                body = response.read(max_response_bytes + 1) if media_type in ALLOWED_MEDIA_TYPES and encoding.lower() in {"identity", ""} else b""
                return MetadataTransportResponse(
                    response.status, response.geturl(), media_type, body,
                    content_encoding=encoding,
                )
        except HTTPError as error:
            # Even an HTTP failure may carry a copyrighted page or sensitive
            # challenge content.  Do not read or retain the error body/headers.
            try:
                return MetadataTransportResponse(
                    error.code, url, error.headers.get_content_type() if error.headers else "",
                    b"", location=error.headers.get("Location") if error.headers else None,
                )
            finally:
                error.close()
        except URLError as error:
            if isinstance(error.reason, (socket.timeout, TimeoutError)):
                raise TimeoutError("official source metadata retrieval timed out") from None
            raise OSError("official source metadata retrieval unavailable") from None
        except (HTTPException, ValueError):
            raise OSError("official source metadata retrieval unavailable") from None


class _SourcePageMetadata(HTMLParser):
    """Extract only bounded explicit metadata and document-designation links."""

    def __init__(self, url: str):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.fields: dict[str, str] = {}
        self.links: list[dict[str, str | None]] = []
        self._title = False
        self._title_parts: list[str] = []
        self._anchor: str | None = None
        self._anchor_parts: list[str] = []
        self._captured_characters = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "title":
            self._title = True
        elif tag == "meta":
            raw_name = attributes.get("name", "")
            name = raw_name.lower() if isinstance(raw_name, str) else ""
            if name in {"rules-effective-date", "rules-version"}:
                content = attributes.get("content")
                if not isinstance(content, str) or not content.strip() or len(content) > MAX_METADATA_TEXT:
                    raise ValueError("invalid explicit source metadata")
                key = "effective_date" if name == "rules-effective-date" else "rules_version"
                value = _bounded_text(content)
                if key == "effective_date" and date.fromisoformat(value).isoformat() != value:
                    raise ValueError("invalid explicit effective date")
                if key in self.fields and self.fields[key] != value:
                    raise ValueError("contradictory explicit source metadata")
                self.fields[key] = value
        elif tag == "a":
            self._anchor = attributes.get("href")
            self._anchor_parts = []

    def handle_data(self, data):
        # Body prose is never accumulated.  Title/anchor text is bounded even
        # when a source emits a pathological number of separate data chunks.
        if self._captured_characters >= MAX_METADATA_TEXT * (MAX_DESIGNATED_LINKS + 2):
            return
        if self._title:
            retained = data[:MAX_METADATA_TEXT]
            self._title_parts.append(retained)
            self._captured_characters += len(retained)
        elif self._anchor is not None:
            retained = data[:MAX_METADATA_TEXT]
            self._anchor_parts.append(retained)
            self._captured_characters += len(retained)

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
            value = _bounded_text(" ".join(self._title_parts))
            if value:
                self.fields["title"] = value
        elif tag == "a":
            href, self._anchor = self._anchor, None
            if not isinstance(href, str) or len(self.links) >= MAX_DESIGNATED_LINKS:
                return
            title = _bounded_text(" ".join(self._anchor_parts))
            # This reports a designation, never follows it or selects a release.
            if not (re.search(r"\b(?:rules|comprehensive|cr|pdf|txt)\b", title, re.IGNORECASE)
                    or urlsplit(href).path.lower().endswith((".pdf", ".txt"))):
                return
            try:
                target = _official_url(urljoin(self.url, href))
            except (AcquisitionError, ValueError):
                return
            media_type = "application/pdf" if urlsplit(target).path.lower().endswith(".pdf") else "text/plain" if urlsplit(target).path.lower().endswith(".txt") else None
            item = {"url": target, "title": title or None, "media_type": media_type}
            if item not in self.links:
                self.links.append(item)


def _metadata_from_body(url: str, media_type: str, body: bytes):
    if media_type == "application/pdf":
        # No PDF executable hooks, decompression, text extraction or parsing.
        return {}, []
    text = body.decode("utf-8")
    if media_type == "text/html":
        parser = _SourcePageMetadata(url)
        parser.feed(text)
        parser.close()
        return parser.fields, sorted(parser.links, key=lambda item: item["url"])
    fields = {}
    # Only deliberately labeled metadata is accepted, never a guessed date or
    # version from filenames, prose, HTTP headers, or publication chronology.
    for line in text.splitlines():
        match = re.fullmatch(r"rules-(effective-date|version):\s*(.{1,160})", line, re.IGNORECASE)
        if match:
            key = "effective_date" if match.group(1).lower() == "effective-date" else "rules_version"
            value = _bounded_text(match.group(2))
            if key == "effective_date" and date.fromisoformat(value).isoformat() != value:
                raise ValueError("invalid explicit effective date")
            if key in fields and fields[key] != value:
                raise ValueError("contradictory explicit source metadata")
            fields[key] = value
    return fields, []


class WizardsRulesMetadataProvider(AcquisitionProvider):
    """Explicit metadata-only official-source request; no crawling or storage."""

    provider_id = "wizards-rules-metadata"
    __slots__ = ("_transport", "_max_response_bytes", "_max_redirects", "_timeout_seconds", "_frozen")

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError("rules-source intake configuration is immutable")
        object.__setattr__(self, name, value)

    def __init__(self, transport=None, *, max_response_bytes=2_000_000,
                 max_redirects=3, timeout_seconds=15):
        if type(max_response_bytes) is not int or not 0 < max_response_bytes <= MAX_RESPONSE_BYTES:
            raise AcquisitionError("metadata response byte limit is outside the bounded policy")
        if type(max_redirects) is not int or not 0 <= max_redirects <= MAX_REDIRECTS:
            raise AcquisitionError("metadata redirect limit is outside the bounded policy")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise AcquisitionError("metadata timeout is outside the bounded policy")
        chosen = UrllibMetadataTransport() if transport is None else transport
        if not callable(getattr(chosen, "fetch", None)):
            raise AcquisitionError("metadata transport must provide an explicit fetch method")
        self._transport = chosen
        self._max_response_bytes = max_response_bytes
        self._max_redirects = max_redirects
        self._timeout_seconds = timeout_seconds
        self._frozen = True

    def build_request(self, dataset: str, parameters: Mapping[str, Any]) -> ProviderRequest:
        if dataset != _DATASET or not isinstance(parameters, Mapping) or set(parameters) != {"url", "observed_at"}:
            raise AcquisitionError("metadata requests require only rules-source URL and explicit observed_at")
        return ProviderRequest(dataset, {
            "url": _official_url(parameters["url"]), "observed_at": _observed_at(parameters["observed_at"]),
        })

    def retrieve(self, request: ProviderRequest) -> ProviderResponse:
        if not isinstance(request, ProviderRequest):
            raise AcquisitionError("an explicit provider request is required")
        checked = self.build_request(request.dataset, request.parameters)
        requested_url = checked.parameters["url"]
        current_url = requested_url
        metadata = {
            "requested_url": requested_url, "resolved_url": None,
            "observed_at": checked.parameters["observed_at"], "accessibility": "ACCESS_UNAVAILABLE",
            "http_status": None, "media_type": None, "byte_length": None,
            "artifact_sha256": None, "designated_links": [], "metadata_fields": {},
            "body_retained": False,
        }

        def result(outcome):
            metadata["accessibility"] = outcome
            return ProviderResponse(
                payload=b"", content_type="application/json",
                status="succeeded" if outcome == "AVAILABLE" else "unavailable",
                metadata=metadata,
                provenance={"provider_id": self.provider_id, "metadata_only": True,
                            "automatic_document_following": False, "release_selected": False},
            )

        for redirects in range(self._max_redirects + 1):
            try:
                response = self._transport.fetch(current_url,
                    max_response_bytes=self._max_response_bytes, timeout_seconds=self._timeout_seconds)
            except (TimeoutError, socket.timeout):
                return result("TIMEOUT")
            except (OSError, URLError):
                return result("ACCESS_UNAVAILABLE")
            if not isinstance(response, MetadataTransportResponse) or type(response.status) is not int or not 100 <= response.status <= 599 or not isinstance(response.body, bytes):
                return result("ACCESS_UNAVAILABLE")
            try:
                actual_url = _official_url(response.url)
            except AcquisitionError:
                return result("REDIRECT_BLOCKED")
            if actual_url != current_url:
                return result("REDIRECT_BLOCKED")
            metadata["resolved_url"] = actual_url
            metadata["http_status"] = response.status
            if response.status in {301, 302, 303, 307, 308}:
                if redirects == self._max_redirects or not isinstance(response.location, str):
                    return result("REDIRECT_BLOCKED")
                try:
                    current_url = _official_url(urljoin(current_url, response.location))
                except (AcquisitionError, ValueError):
                    return result("REDIRECT_BLOCKED")
                continue
            if response.status == 403:
                return result("HTTP_403")
            if response.status == 404:
                return result("HTTP_404")
            if response.status != 200:
                return result("ACCESS_UNAVAILABLE")
            if not isinstance(response.content_type, str) or not isinstance(response.content_encoding, str):
                return result("CONTENT_TYPE_UNSUPPORTED")
            media_type = response.content_type.split(";", 1)[0].strip().lower()
            metadata["media_type"] = media_type if media_type in ALLOWED_MEDIA_TYPES else None
            if media_type not in ALLOWED_MEDIA_TYPES or response.content_encoding.lower() not in {"", "identity"}:
                return result("CONTENT_TYPE_UNSUPPORTED")
            if len(response.body) > self._max_response_bytes:
                return result("ARTIFACT_TOO_LARGE")
            metadata["byte_length"] = len(response.body)
            metadata["artifact_sha256"] = "sha256:" + hashlib.sha256(response.body).hexdigest()
            try:
                fields, links = _metadata_from_body(actual_url, media_type, response.body)
            except (UnicodeDecodeError, ValueError, TypeError):
                return result("PARSE_METADATA_FAILED")
            metadata["metadata_fields"] = fields
            metadata["designated_links"] = links
            return result("AVAILABLE")
        return result("REDIRECT_BLOCKED")

    def validate_response(self, response: ProviderResponse) -> None:
        if not isinstance(response, ProviderResponse) or response.payload != b"" or response.content_type != "application/json" or response.metadata.get("body_retained") is not False:
            raise AcquisitionError("rules-source intake may expose metadata only")

    def emit_records(self, payload: bytes, content_type: str) -> Iterable[Mapping[str, Any]]:
        raise AcquisitionError("metadata-only rules-source intake does not normalize or store source content")
