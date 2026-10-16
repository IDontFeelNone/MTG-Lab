"""Safe contract errors for Gameplay Rules & Interaction Intelligence."""


class GameplayContractError(ValueError):
    """Malformed, corrupt or incompatible input; never a legality verdict.

    Messages identify contract fields, not file contents or absolute paths.
    """

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")
