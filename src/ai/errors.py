"""Typed failures exposed by the AI model adapter boundary."""


class AIAdapterError(ValueError):
    code = "ai_adapter_error"

    def to_dict(self):
        return {"error": {"code": self.code, "message": str(self)}}


class InvalidAIRequest(AIAdapterError):
    code = "invalid_ai_request"


class InvalidReasoningContext(AIAdapterError):
    code = "invalid_reasoning_context"


class InvalidProvider(AIAdapterError):
    code = "invalid_ai_provider"


class DuplicateProvider(AIAdapterError):
    code = "duplicate_ai_provider"


class ProviderNotFound(AIAdapterError):
    code = "ai_provider_not_found"


class UnsupportedCapability(AIAdapterError):
    code = "unsupported_ai_capability"


class IncompatibleProviderVersion(AIAdapterError):
    code = "incompatible_ai_provider_version"


class InvalidAIResponse(AIAdapterError):
    code = "invalid_ai_response"
