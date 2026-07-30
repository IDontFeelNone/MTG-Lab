"""Provider interface and lifecycle enforcement for AI model execution."""
from abc import ABC, abstractmethod

from reasoning import ReasoningContextResult

from .errors import InvalidAIRequest, InvalidAIResponse, InvalidReasoningContext
from .models import AIModelRequest, AIModelResponse, AIProviderCapabilities, AIProviderMetadata


class AIModelProvider(ABC):
    """A provider boundary; implementations receive reasoning contexts, never repositories."""

    @abstractmethod
    def metadata(self) -> AIProviderMetadata: raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> AIProviderCapabilities: raise NotImplementedError

    @abstractmethod
    def validate_request(self, request: AIModelRequest) -> None: raise NotImplementedError

    @abstractmethod
    def validate_context(self, context: ReasoningContextResult) -> None: raise NotImplementedError

    @abstractmethod
    def execute(self, request: AIModelRequest, context: ReasoningContextResult) -> AIModelResponse: raise NotImplementedError


class AIModelAdapter:
    """Validates the complete provider lifecycle around a supplied context package."""

    def __init__(self, registry): self._registry = registry

    def execute(self, request: AIModelRequest, context: ReasoningContextResult) -> AIModelResponse:
        if not isinstance(request, AIModelRequest): raise InvalidAIRequest("request must be AIModelRequest")
        if not isinstance(context, ReasoningContextResult):
            raise InvalidReasoningContext("context must be ReasoningContextResult")
        provider = self._registry.validate_request(request)
        if context.context_id != request.reasoning_context_identifier:
            raise InvalidReasoningContext("request reasoning context identifier does not match supplied context")
        provider.validate_request(request); provider.validate_context(context)
        response = provider.execute(request, context)
        if not isinstance(response, AIModelResponse): raise InvalidAIResponse("provider must return AIModelResponse")
        expected = (request.provider_identifier, request.provider_version, request.model_identifier,
                    request.reasoning_context_identifier, request.execution_identifier)
        actual = (response.provider_identifier, response.provider_version, response.model_identifier,
                  response.reasoning_context_identifier, response.execution_identifier)
        if actual != expected: raise InvalidAIResponse("response identity does not match request")
        return response
