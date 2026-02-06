"""
Example: TLS Fingerprinting with curl_cffi

This example demonstrates how to use the StealthClient for HTTP requests
that match real browser TLS fingerprints (JA3/JA4).

Why TLS fingerprinting matters:
- Anti-bot systems like Cloudflare, Akamai, PerimeterX fingerprint TLS connections
- Python's requests/httpx have distinct TLS fingerprints (easily detected)
- curl_cffi uses BoringSSL to match Chrome's exact TLS fingerprint

Use cases:
1. API requests that need to bypass TLS fingerprinting
2. Pre-checking pages before opening in browser (detect CAPTCHAs)
3. Lightweight scraping without full browser overhead
4. Cookie/session harvesting for later use in browser

Install:
    pip install curl_cffi
"""

import asyncio
from abrasio.http import StealthClient, StealthClientSync, BrowserImpersonation


async def example_async():
    """Async HTTP client with TLS fingerprinting."""
    print("=" * 60)
    print("Async StealthClient Example")
    print("=" * 60)

    # Basic usage - impersonates Chrome 120
    async with StealthClient() as client:
        response = await client.get("https://httpbin.org/headers")
        print("\n1. Basic request headers seen by server:")
        print(response.json()["headers"])

    # With specific browser impersonation
    async with StealthClient(impersonate=BrowserImpersonation.CHROME_119) as client:
        response = await client.get("https://httpbin.org/user-agent")
        print("\n2. User-Agent with Chrome 119 impersonation:")
        print(response.json()["user-agent"])

    # With region configuration (auto-sets Accept-Language)
    async with StealthClient(region="BR") as client:
        response = await client.get("https://httpbin.org/headers")
        print("\n3. Accept-Language with region=BR:")
        print(f"Accept-Language: {response.json()['headers'].get('Accept-Language')}")

    # With proxy
    # async with StealthClient(proxy="http://user:pass@proxy.example.com:8080") as client:
    #     response = await client.get("https://httpbin.org/ip")
    #     print(response.json())

    # POST request with JSON
    async with StealthClient() as client:
        response = await client.post(
            "https://httpbin.org/post",
            json={"key": "value", "items": [1, 2, 3]}
        )
        print("\n4. POST request with JSON:")
        print(response.json()["json"])

    # Rotate impersonation on each request (anti-fingerprinting)
    async with StealthClient(rotate_impersonation=True) as client:
        for i in range(3):
            response = await client.get("https://httpbin.org/headers")
            sec_ch_ua = response.json()["headers"].get("Sec-Ch-Ua", "N/A")
            print(f"\n5.{i+1} Rotated impersonation - Sec-Ch-Ua: {sec_ch_ua[:50]}...")


def example_sync():
    """Synchronous HTTP client with TLS fingerprinting."""
    print("\n" + "=" * 60)
    print("Sync StealthClientSync Example")
    print("=" * 60)

    # Basic usage
    with StealthClientSync() as client:
        response = client.get("https://httpbin.org/ip")
        print("\n1. Your IP (as seen by server):")
        print(response.json()["origin"])

    # Check TLS fingerprint (use a JA3 checker service)
    with StealthClientSync(impersonate=BrowserImpersonation.CHROME_120) as client:
        # Note: ja3er.com shows your JA3 fingerprint
        response = client.get("https://tls.browserleaks.com/json")
        if response.ok:
            data = response.json()
            print("\n2. TLS Fingerprint info:")
            print(f"   JA3 Hash: {data.get('ja3_hash', 'N/A')}")
            print(f"   JA3 Text: {data.get('ja3_text', 'N/A')[:80]}...")


async def example_check_cloudflare():
    """
    Example: Check if a site has Cloudflare protection.

    This is useful to pre-check before opening in browser.
    """
    print("\n" + "=" * 60)
    print("Cloudflare Detection Example")
    print("=" * 60)

    async with StealthClient(region="US") as client:
        # Sites known to use Cloudflare
        test_sites = [
            "https://www.cloudflare.com",
            "https://httpbin.org",
        ]

        for site in test_sites:
            try:
                response = await client.get(site, timeout=10.0)

                # Check for Cloudflare headers
                cf_ray = response.headers.get("cf-ray")
                cf_cache = response.headers.get("cf-cache-status")
                server = response.headers.get("server", "")

                has_cloudflare = (
                    cf_ray is not None or
                    cf_cache is not None or
                    "cloudflare" in server.lower()
                )

                print(f"\n{site}")
                print(f"  Status: {response.status_code}")
                print(f"  Cloudflare detected: {has_cloudflare}")
                if has_cloudflare:
                    print(f"  CF-Ray: {cf_ray}")

            except Exception as e:
                print(f"\n{site}")
                print(f"  Error: {e}")


async def example_session_persistence():
    """
    Example: Cookie/session persistence across requests.

    Useful for login flows or maintaining state.
    """
    print("\n" + "=" * 60)
    print("Session Persistence Example")
    print("=" * 60)

    async with StealthClient() as client:
        # First request - get cookies
        response = await client.get("https://httpbin.org/cookies/set/session_id/abc123")
        print("\n1. Set cookie via redirect:")
        print(f"   URL after redirect: {response.url}")

        # The session maintains cookies automatically
        response = await client.get("https://httpbin.org/cookies")
        print("\n2. Cookies in session:")
        print(f"   {response.json()}")


async def main():
    """Run all examples."""
    await example_async()
    example_sync()
    await example_check_cloudflare()
    await example_session_persistence()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
