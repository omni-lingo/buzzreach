"""Shared application error base (CFG-002).

All service-layer errors inherit from AppError and carry a machine-readable
``code`` plus a human-readable ``message``. API routes translate these into
structured JSON error responses (BUILD_RULES section 9).
"""


class AppError(Exception):
    """Base application error with a machine-readable error code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
