"""
Stealth HTTP client with TLS fingerprinting.

Implements browser-like HTTP requests using curl_cffi to match:
- TLS fingerprint (JA3/JA4)
- HTTP/2 SETTINGS frame
- Header order
- Cipher suite ordering

Why this matters:
- Many anti-bot systems fingerprint TLS connections
- Python's requests/httpx have distinct TLS fingerprints
- curl_cffi uses BoringSSL to match real browser fingerprints

References:
- https://curl-cffi.readthedocs.io/
- https://scrapfly.io/blog/how-to-avoid-ja3-fingerprinting/
- https://lwthiker.com/networks/2022/06/17/ja3.html
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

try:
    from curl_cffi import requests as curl_requests
    from curl_cffi.requests import AsyncSession, Session, Response
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    curl_requests = None
    AsyncSession = None
    Session = None
    Response = None


class BrowserImpersonation(str, Enum):
    """
    Browser impersonation profiles for TLS fingerprinting.

    Each profile matches the exact TLS/HTTP fingerprint of that browser version.
    """
    # Chrome (most common, recommended for most sites)
    CHROME_120 = "chrome120"
    CHROME_119 = "chrome119"
    CHROME_118 = "chrome118"
    CHROME_117 = "chrome117"
    CHROME_116 = "chrome116"
    CHROME_110 = "chrome110"
    CHROME_107 = "chrome107"
    CHROME_104 = "chrome104"
    CHROME_101 = "chrome101"
    CHROME_100 = "chrome100"
    CHROME_99 = "chrome99"

    # Chrome Android
    CHROME_99_ANDROID = "chrome99_android"

    # Edge (good for Microsoft-related sites)
    EDGE_101 = "edge101"
    EDGE_99 = "edge99"

    # Safari (good for Apple-related sites)
    SAFARI_15_5 = "safari15_5"
    SAFARI_15_3 = "safari15_3"

    # Safari iOS
    SAFARI_IOS_15_5 = "safari_ios15_5"
    SAFARI_IOS_15_6 = "safari_ios15_6"

    # Default (latest stable Chrome)
    DEFAULT = "chrome120"

    @classmethod
    def random_chrome(cls) -> "BrowserImpersonation":
        """Get a random Chrome version."""
        chrome_versions = [
            cls.CHROME_120, cls.CHROME_119, cls.CHROME_118,
            cls.CHROME_117, cls.CHROME_116, cls.CHROME_110,
        ]
        return random.choice(chrome_versions)

    @classmethod
    def for_region(cls, region: str) -> "BrowserImpersonation":
        """
        Get recommended impersonation for a region.

        - US/EU: Chrome (most common)
        - Asia: Chrome/Edge mix
        - Apple-centric regions: Safari option
        """
        region = (region or "US").upper()

        if region in ("JP", "KR", "CN", "TW", "HK", "SG"):
            # Asia - Chrome is dominant
            return cls.random_chrome()

        # Most regions - Chrome
        return cls.random_chrome()


@dataclass
class StealthResponse:
    """
    Response wrapper with useful properties.

    Provides a clean interface regardless of underlying HTTP library.
    """
    status_code: int
    headers: Dict[str, str]
    content: bytes
    url: str
    encoding: str = "utf-8"

    @property
    def text(self) -> str:
        """Decode response content as text."""
        return self.content.decode(self.encoding, errors="replace")

    @property
    def ok(self) -> bool:
        """Check if response was successful (2xx)."""
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        """Parse response as JSON."""
        import json
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        """Raise exception if response indicates an error."""
        if not self.ok:
            raise HTTPError(f"HTTP {self.status_code}: {self.url}")


class HTTPError(Exception):
    """HTTP request error."""
    pass


class TLSFingerprintError(Exception):
    """TLS fingerprint library not available."""
    pass


@dataclass
class StealthClientConfig:
    """Configuration for stealth HTTP client."""

    # Browser impersonation (TLS fingerprint)
    impersonate: BrowserImpersonation = BrowserImpersonation.DEFAULT

    # Timeout in seconds
    timeout: float = 30.0

    # Follow redirects
    allow_redirects: bool = True
    max_redirects: int = 10

    # Proxy (format: "http://user:pass@host:port")
    proxy: Optional[str] = None

    # Verify SSL certificates
    verify: bool = True

    # Default headers (merged with request headers)
    headers: Dict[str, str] = field(default_factory=dict)

    # Cookies
    cookies: Dict[str, str] = field(default_factory=dict)

    # Region for auto-configuration
    region: Optional[str] = None

    # Auto-rotate impersonation on each request
    rotate_impersonation: bool = False


class StealthClient:
    """
    Async HTTP client with TLS fingerprinting.

    Uses curl_cffi to make requests that match real browser TLS fingerprints.
    This bypasses JA3/JA4 fingerprint detection used by anti-bot systems.

    Example:
        async with StealthClient() as client:
            # Simple GET
            response = await client.get("https://example.com")
            print(response.text)

            # POST with JSON
            response = await client.post(
                "https://api.example.com/data",
                json={"key": "value"}
            )

            # With custom headers
            response = await client.get(
                "https://example.com",
                headers={"Authorization": "Bearer token"}
            )
    """

    def __init__(
        self,
        impersonate: Union[BrowserImpersonation, str] = BrowserImpersonation.DEFAULT,
        timeout: float = 30.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        region: Optional[str] = None,
        rotate_impersonation: bool = False,
        verify: bool = True,
    ):
        """
        Initialize stealth HTTP client.

        Args:
            impersonate: Browser to impersonate (affects TLS fingerprint)
            timeout: Request timeout in seconds
            proxy: Proxy URL (http://user:pass@host:port)
            headers: Default headers for all requests
            cookies: Default cookies for all requests
            region: Region for auto-configuring Accept-Language etc.
            rotate_impersonation: Rotate browser version on each request
            verify: Verify SSL certificates
        """
        if not CURL_CFFI_AVAILABLE:
            raise TLSFingerprintError(
                "curl_cffi is required for TLS fingerprinting. "
                "Install with: pip install curl_cffi"
            )

        if isinstance(impersonate, str):
            impersonate = BrowserImpersonation(impersonate)

        self.config = StealthClientConfig(
            impersonate=impersonate,
            timeout=timeout,
            proxy=proxy,
            headers=headers or {},
            cookies=cookies or {},
            region=region,
            rotate_impersonation=rotate_impersonation,
            verify=verify,
        )

        self._session: Optional[AsyncSession] = None

    async def __aenter__(self) -> "StealthClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start(self) -> None:
        """Initialize the HTTP session."""
        impersonate = self._get_impersonation()

        self._session = AsyncSession(
            impersonate=impersonate,
            timeout=self.config.timeout,
            proxies={"http": self.config.proxy, "https": self.config.proxy} if self.config.proxy else None,
            verify=self.config.verify,
            headers=self._build_default_headers(),
        )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_impersonation(self) -> str:
        """Get browser impersonation string."""
        if self.config.rotate_impersonation:
            return BrowserImpersonation.random_chrome().value
        return self.config.impersonate.value

    def _build_default_headers(self) -> Dict[str, str]:
        """Build default headers based on configuration."""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": self._get_accept_language(),
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": self._get_sec_ch_ua(),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        # Merge with custom headers (custom takes precedence)
        headers.update(self.config.headers)
        return headers

    def _get_accept_language(self) -> str:
        """Get Accept-Language header based on region."""
        region = (self.config.region or "US").upper()

        # Common Accept-Language values by region
        languages = {
            "US": "en-US,en;q=0.9",
            "BR": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "GB": "en-GB,en;q=0.9,en-US;q=0.8",
            "DE": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "FR": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "ES": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "IT": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "JP": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "KR": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "CN": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        return languages.get(region, "en-US,en;q=0.9")

    def _get_sec_ch_ua(self) -> str:
        """Get Sec-Ch-Ua header based on impersonation."""
        imp = self.config.impersonate.value

        if "chrome120" in imp:
            return '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        if "chrome119" in imp:
            return '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
        if "chrome118" in imp:
            return '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"'
        if "edge" in imp:
            return '"Microsoft Edge";v="101", "Chromium";v="101", "Not A;Brand";v="99"'

        # Default Chrome
        return '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

    def _wrap_response(self, response: Response) -> StealthResponse:
        """Wrap curl_cffi response in our response class."""
        return StealthResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
            encoding=response.encoding or "utf-8",
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, bytes, Dict]] = None,
        json: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        allow_redirects: Optional[bool] = None,
    ) -> StealthResponse:
        """
        Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            headers: Additional headers (merged with defaults)
            params: URL query parameters
            data: Request body (form data or raw)
            json: Request body as JSON (sets Content-Type automatically)
            cookies: Additional cookies
            timeout: Request timeout (overrides default)
            allow_redirects: Follow redirects (overrides default)

        Returns:
            StealthResponse with response data
        """
        if not self._session:
            raise HTTPError("Client not started. Use 'async with' or call start().")

        # Merge headers
        req_headers = dict(self._build_default_headers())
        if headers:
            req_headers.update(headers)

        # Merge cookies
        req_cookies = dict(self.config.cookies)
        if cookies:
            req_cookies.update(cookies)

        # Rotate impersonation if enabled
        if self.config.rotate_impersonation:
            impersonate = BrowserImpersonation.random_chrome().value
        else:
            impersonate = None  # Use session default

        response = await self._session.request(
            method=method.upper(),
            url=url,
            headers=req_headers,
            params=params,
            data=data,
            json=json,
            cookies=req_cookies if req_cookies else None,
            timeout=timeout or self.config.timeout,
            allow_redirects=allow_redirects if allow_redirects is not None else self.config.allow_redirects,
            impersonate=impersonate,
        )

        return self._wrap_response(response)

    async def get(self, url: str, **kwargs) -> StealthResponse:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> StealthResponse:
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> StealthResponse:
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> StealthResponse:
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> StealthResponse:
        """Make a HEAD request."""
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs) -> StealthResponse:
        """Make an OPTIONS request."""
        return await self.request("OPTIONS", url, **kwargs)


class StealthClientSync:
    """
    Synchronous HTTP client with TLS fingerprinting.

    Same as StealthClient but for synchronous code.

    Example:
        with StealthClientSync() as client:
            response = client.get("https://example.com")
            print(response.text)
    """

    def __init__(
        self,
        impersonate: Union[BrowserImpersonation, str] = BrowserImpersonation.DEFAULT,
        timeout: float = 30.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        region: Optional[str] = None,
        rotate_impersonation: bool = False,
        verify: bool = True,
    ):
        if not CURL_CFFI_AVAILABLE:
            raise TLSFingerprintError(
                "curl_cffi is required for TLS fingerprinting. "
                "Install with: pip install curl_cffi"
            )

        if isinstance(impersonate, str):
            impersonate = BrowserImpersonation(impersonate)

        self.config = StealthClientConfig(
            impersonate=impersonate,
            timeout=timeout,
            proxy=proxy,
            headers=headers or {},
            cookies=cookies or {},
            region=region,
            rotate_impersonation=rotate_impersonation,
            verify=verify,
        )

        self._session: Optional[Session] = None

    def __enter__(self) -> "StealthClientSync":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def start(self) -> None:
        """Initialize the HTTP session."""
        impersonate = self._get_impersonation()

        self._session = Session(
            impersonate=impersonate,
            timeout=self.config.timeout,
            proxies={"http": self.config.proxy, "https": self.config.proxy} if self.config.proxy else None,
            verify=self.config.verify,
            headers=self._build_default_headers(),
        )

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def _get_impersonation(self) -> str:
        """Get browser impersonation string."""
        if self.config.rotate_impersonation:
            return BrowserImpersonation.random_chrome().value
        return self.config.impersonate.value

    def _build_default_headers(self) -> Dict[str, str]:
        """Build default headers based on configuration."""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": self._get_accept_language(),
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": self._get_sec_ch_ua(),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        headers.update(self.config.headers)
        return headers

    def _get_accept_language(self) -> str:
        """Get Accept-Language header based on region."""
        region = (self.config.region or "US").upper()

        languages = {
            "US": "en-US,en;q=0.9",
            "BR": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "GB": "en-GB,en;q=0.9,en-US;q=0.8",
            "DE": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "FR": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "ES": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "IT": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "JP": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "KR": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "CN": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        return languages.get(region, "en-US,en;q=0.9")

    def _get_sec_ch_ua(self) -> str:
        """Get Sec-Ch-Ua header based on impersonation."""
        imp = self.config.impersonate.value

        if "chrome120" in imp:
            return '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        if "chrome119" in imp:
            return '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
        if "chrome118" in imp:
            return '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"'
        if "edge" in imp:
            return '"Microsoft Edge";v="101", "Chromium";v="101", "Not A;Brand";v="99"'

        return '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

    def _wrap_response(self, response: Response) -> StealthResponse:
        """Wrap curl_cffi response in our response class."""
        return StealthResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
            encoding=response.encoding or "utf-8",
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, bytes, Dict]] = None,
        json: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        allow_redirects: Optional[bool] = None,
    ) -> StealthResponse:
        """Make an HTTP request."""
        if not self._session:
            raise HTTPError("Client not started. Use 'with' or call start().")

        req_headers = dict(self._build_default_headers())
        if headers:
            req_headers.update(headers)

        req_cookies = dict(self.config.cookies)
        if cookies:
            req_cookies.update(cookies)

        if self.config.rotate_impersonation:
            impersonate = BrowserImpersonation.random_chrome().value
        else:
            impersonate = None

        response = self._session.request(
            method=method.upper(),
            url=url,
            headers=req_headers,
            params=params,
            data=data,
            json=json,
            cookies=req_cookies if req_cookies else None,
            timeout=timeout or self.config.timeout,
            allow_redirects=allow_redirects if allow_redirects is not None else self.config.allow_redirects,
            impersonate=impersonate,
        )

        return self._wrap_response(response)

    def get(self, url: str, **kwargs) -> StealthResponse:
        """Make a GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> StealthResponse:
        """Make a POST request."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> StealthResponse:
        """Make a PUT request."""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> StealthResponse:
        """Make a DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs) -> StealthResponse:
        """Make a HEAD request."""
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs) -> StealthResponse:
        """Make an OPTIONS request."""
        return self.request("OPTIONS", url, **kwargs)


# Convenience functions for one-off requests
async def get(url: str, **kwargs) -> StealthResponse:
    """Make a one-off GET request with TLS fingerprinting."""
    async with StealthClient(**kwargs) as client:
        return await client.get(url)


async def post(url: str, **kwargs) -> StealthResponse:
    """Make a one-off POST request with TLS fingerprinting."""
    async with StealthClient(**kwargs) as client:
        return await client.post(url, **kwargs)


def get_sync(url: str, **kwargs) -> StealthResponse:
    """Make a one-off synchronous GET request with TLS fingerprinting."""
    with StealthClientSync(**kwargs) as client:
        return client.get(url)


def post_sync(url: str, **kwargs) -> StealthResponse:
    """Make a one-off synchronous POST request with TLS fingerprinting."""
    with StealthClientSync(**kwargs) as client:
        return client.post(url, **kwargs)
