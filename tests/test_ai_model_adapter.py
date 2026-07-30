import json
import unittest
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
from io import StringIO
from types import MappingProxyType

from ai import (AIExecutionMetadata, AIModelAdapter, AIModelProvider, AIModelRequest,
                AIModelResponse, AIProviderCapabilities, AIProviderMetadata,
                AIProviderRegistry)
from ai.errors import (DuplicateProvider, IncompatibleProviderVersion, InvalidAIRequest,
                       InvalidAIResponse, InvalidProvider, ProviderNotFound,
                       UnsupportedCapability)
from mtglab.__main__ import main
from reasoning import ReasoningContextResult


def context():
    return ReasoningContextResult("sha256:" + "1" * 64, "sha256:" + "2" * 64,
                                  {}, (), (), (), {}, {}, {}, {}, {}, {}, ())


class StubProvider(AIModelProvider):
    def __init__(self, identifier="test-provider", version="1.2.3", capabilities=("structured-response",)):
        self._metadata = AIProviderMetadata(identifier, version, ("test-model",))
        self._capabilities = AIProviderCapabilities(capabilities)
        self.calls = []

    def metadata(self): return self._metadata
    def capabilities(self): return self._capabilities
    def validate_request(self, request): self.calls.append("request")
    def validate_context(self, supplied): self.calls.append("context")
    def execute(self, request, supplied):
        self.calls.append("execute")
        execution = AIExecutionMetadata(request.execution_identifier, "2026-07-30T00:00:00Z",
                                        "2026-07-30T00:00:01Z")
        return AIModelResponse(request.provider_identifier, request.provider_version,
                               request.model_identifier, supplied.context_id, execution,
                               {"status": "structured"})


class BadResponseProvider(StubProvider):
    def execute(self, request, supplied): return {"not": "a response"}


class AIModelAdapterTests(unittest.TestCase):
    def request(self, **changes):
        values = {"provider_identifier": "test-provider", "provider_version": "1.2.3",
                  "model_identifier": "test-model", "reasoning_context_identifier": context().context_id,
                  "execution_identifier": "execution-1", "created_at": "2026-07-30T00:00:00Z"}
        values.update(changes); return AIModelRequest(**values)

    def test_contracts_are_immutable_and_recursively_frozen(self):
        response = StubProvider().execute(self.request(), context())
        with self.assertRaises(FrozenInstanceError): response.provider_identifier = "other"
        self.assertIsInstance(response.structured_response, MappingProxyType)
        with self.assertRaises(TypeError): response.structured_response["x"] = 1

    def test_serialization_is_deterministic_and_has_token_placeholders(self):
        request = self.request(required_capabilities=("structured-response", "structured-response"))
        self.assertEqual(request.to_json(), request.to_json())
        self.assertEqual(request.to_json(), json.dumps(request.to_dict(), sort_keys=True,
                                                       ensure_ascii=False, separators=(",", ":")))
        execution = AIExecutionMetadata("execution-1", "2026-07-30T00:00:00Z")
        self.assertIsNone(execution.to_dict()["input_tokens"])

    def test_registration_lookup_discovery_and_versions_are_deterministic(self):
        registry = AIProviderRegistry(); provider = StubProvider()
        registry.register(provider)
        self.assertIs(registry.lookup("test-provider"), provider)
        self.assertEqual(registry.versions(), {"test-provider": "1.2.3"})
        self.assertEqual(registry.capability_discovery("structured-response")[0][0], provider.metadata())

    def test_duplicate_missing_and_version_errors_are_typed(self):
        registry = AIProviderRegistry(); registry.register(StubProvider())
        with self.assertRaises(DuplicateProvider): registry.register(StubProvider())
        with self.assertRaises(ProviderNotFound): registry.lookup("missing")
        with self.assertRaises(IncompatibleProviderVersion): registry.lookup("test-provider", "2.0.0")

    def test_provider_and_capability_validation(self):
        with self.assertRaises(InvalidProvider): AIProviderRegistry().register(StubProvider("Bad Provider"))
        with self.assertRaises(InvalidProvider): AIProviderRegistry().register(StubProvider(version="latest"))
        with self.assertRaises(UnsupportedCapability):
            AIProviderRegistry().register(StubProvider(capabilities=("embeddings",)))

    def test_malformed_request_and_schema_are_rejected(self):
        registry = AIProviderRegistry(); registry.register(StubProvider())
        with self.assertRaises(InvalidAIRequest): registry.validate_request(self.request(reasoning_context_identifier=""))
        with self.assertRaises(InvalidAIRequest): registry.validate_request(self.request(model_identifier="missing"))
        with self.assertRaises(ValueError): self.request(schema_version="ai-model-adapter-v2")
        with self.assertRaises(ValueError): self.request(created_at="yesterday")

    def test_lifecycle_is_ordered_and_repeated_execution_is_structured(self):
        registry = AIProviderRegistry(); provider = StubProvider(); registry.register(provider)
        first = AIModelAdapter(registry).execute(self.request(), context())
        second = AIModelAdapter(registry).execute(self.request(), context())
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(provider.calls, ["request", "context", "execute"] * 2)

    def test_bad_response_is_typed(self):
        registry = AIProviderRegistry(); registry.register(BadResponseProvider())
        with self.assertRaises(InvalidAIResponse): AIModelAdapter(registry).execute(self.request(), context())

    def test_cli_json_for_empty_provider_framework(self):
        for command in ("providers", "capabilities", "validate"):
            out = StringIO()
            with redirect_stdout(out): self.assertEqual(main(["ai", command]), 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["schema_version"], "ai-model-adapter-v1")
        out = StringIO()
        with redirect_stdout(out): self.assertEqual(main(["ai", "validate", "--provider", "absent"]), 2)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"], "ai_provider_not_found")


if __name__ == "__main__": unittest.main()
