"""Typed failures exposed by the reasoning-context boundary."""


class ReasoningContextError(ValueError):
    code = "reasoning_context_error"

    def to_dict(self):
        return {"error": {"code": self.code, "message": str(self)}}


class InvalidReasoningRequest(ReasoningContextError):
    code = "invalid_reasoning_request"


class ReasoningSnapshotError(ReasoningContextError):
    code = "reasoning_snapshot_error"

