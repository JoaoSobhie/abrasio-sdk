"""
HTTP client with TLS fingerprinting for stealth requests.

Uses curl_cffi to impersonate real browsers at the TLS/HTTP level:
- JA3/JA4 TLS fingerprint matching
- HTTP/2 SETTINGS frame matching
- Header order matching
- Cipher suite ordering

This is useful for:
- Pre-fetching pages to check for CAPTCHAs
- API requests that need browser-like fingerprints
- Lightweight scraping without full browser overhead

Usage:
    from abrasio.http import StealthClient

    async with StealthClient() as client:
        response = await client.get("https://example.com")
        print(response.text)

    # Sync version
    from abrasio.http import StealthClientSync

    with StealthClientSync() as client:
        response = client.get("https://example.com")
        print(response.text)
"""

from .client import (
    StealthClient,
    StealthClientSync,
    StealthResponse,
    BrowserImpersonation,
)

__all__ = [
    "StealthClient",
    "StealthClientSync",
    "StealthResponse",
    "BrowserImpersonation",
]
