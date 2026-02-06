"""Custom exceptions for Abrasio SDK."""


class AbrasioError(Exception):
    """Base exception for all Abrasio errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(AbrasioError):
    """Raised when API authentication fails."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)


class SessionError(AbrasioError):
    """Raised when session creation or management fails."""

    def __init__(self, message: str, session_id: str = None):
        super().__init__(message, {"session_id": session_id})
        self.session_id = session_id


class BrowserError(AbrasioError):
    """Raised when browser operations fail."""

    pass


class TimeoutError(AbrasioError):
    """Raised when an operation times out."""

    def __init__(self, message: str = "Operation timed out", timeout_ms: int = None):
        super().__init__(message, {"timeout_ms": timeout_ms})
        self.timeout_ms = timeout_ms


class InsufficientFundsError(AbrasioError):
    """Raised when user has insufficient balance (cloud mode)."""

    def __init__(self, balance: float = None):
        message = "Insufficient funds in your Abrasio account"
        if balance is not None:
            message += f" (current balance: ${balance:.2f})"
        super().__init__(message, {"balance": balance})
        self.balance = balance


class RateLimitError(AbrasioError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, {"retry_after": retry_after})
        self.retry_after = retry_after


class BlockedError(AbrasioError):
    """Raised when the target site blocks the request."""

    def __init__(self, url: str = None, status_code: int = None):
        message = "Request was blocked by the target site"
        if url:
            message += f" ({url})"
        if status_code:
            message += f" - Status: {status_code}"
        super().__init__(message, {"url": url, "status_code": status_code})
        self.url = url
        self.status_code = status_code
