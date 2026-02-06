"""
Example demonstrating fingerprint utilities.

Uses BrowserForge (optional) to:
- Generate consistent fingerprints
- Validate fingerprint consistency
- Get realistic screen sizes

Install: pip install abrasio[fingerprint]
"""

import asyncio
from abrasio import Abrasio

# Try to import fingerprint utilities
try:
    from abrasio.utils import (
        generate_fingerprint,
        validate_fingerprint_consistency,
        get_realistic_screen,
        get_realistic_locale,
    )
    FINGERPRINT_AVAILABLE = True
except ImportError:
    FINGERPRINT_AVAILABLE = False
    print("Fingerprint utilities not available.")
    print("Install with: pip install abrasio[fingerprint]")


async def check_browser_fingerprint(page):
    """Check browser fingerprint and validate consistency."""
    # Get fingerprint from browser
    result = await page.evaluate("""
        () => ({
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory,
            screenWidth: screen.width,
            screenHeight: screen.height,
            colorDepth: screen.colorDepth,
            webglVendor: (() => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl');
                    const ext = gl.getExtension('WEBGL_debug_renderer_info');
                    return ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : null;
                } catch { return null; }
            })(),
            webglRenderer: (() => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl');
                    const ext = gl.getExtension('WEBGL_debug_renderer_info');
                    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : null;
                } catch { return null; }
            })(),
        })
    """)

    print("\n=== Browser Fingerprint ===")
    print(f"User-Agent: {result['userAgent'][:80]}...")
    print(f"Platform: {result['platform']}")
    print(f"Language: {result['language']}")
    print(f"Hardware Concurrency: {result['hardwareConcurrency']}")
    print(f"Device Memory: {result['deviceMemory']} GB")
    print(f"Screen: {result['screenWidth']}x{result['screenHeight']}")
    print(f"Color Depth: {result['colorDepth']}")
    print(f"WebGL Vendor: {result['webglVendor']}")
    print(f"WebGL Renderer: {result['webglRenderer']}")

    # Validate consistency
    if FINGERPRINT_AVAILABLE:
        warnings = validate_fingerprint_consistency(
            user_agent=result['userAgent'],
            platform=result['platform'],
            screen_width=result['screenWidth'],
            screen_height=result['screenHeight'],
            webgl_vendor=result['webglVendor'],
            webgl_renderer=result['webglRenderer'],
        )

        if warnings:
            print("\n=== Consistency Warnings ===")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("\n=== Fingerprint is consistent ===")

    return result


async def main():
    print("=== Fingerprint Check Example ===\n")

    if FINGERPRINT_AVAILABLE:
        # Show realistic values
        print("Realistic screen (by market share):")
        for _ in range(3):
            screen = get_realistic_screen()
            print(f"  {screen['width']}x{screen['height']}")

        print("\nRealistic locale/timezone:")
        for _ in range(3):
            locale, tz = get_realistic_locale()
            print(f"  {locale} ({tz})")

        print("\nGenerating BrowserForge fingerprint...")
        try:
            fp = generate_fingerprint(browser="chrome", os="windows")
            print(f"  UA: {fp['navigator']['userAgent'][:60]}...")
            print(f"  Screen: {fp['screen']['width']}x{fp['screen']['height']}")
            if 'webgl' in fp:
                print(f"  WebGL: {fp['webgl']['vendor']} / {fp['webgl']['renderer']}")
        except Exception as e:
            print(f"  Error generating fingerprint: {e}")
            print("  Run: python -m browserforge update")

    # Check actual browser fingerprint
    print("\n=== Starting Browser ===")
    async with Abrasio(headless=False) as browser:
        page = await browser.new_page()
        await page.goto("about:blank")

        await check_browser_fingerprint(page)

        # Check against detection sites
        print("\n=== Testing Detection Sites ===")

        print("\n2. Testing browserscan...")
        await page.goto("https://browserscan.net")
        await asyncio.sleep(5)
        await page.screenshot(path="creepjs_result.png")
        print("   Screenshot saved to creepjs_result.png")

        print("\n1. Testing bot.sannysoft.com...")
        await page.goto("https://demo.fingerprint.com/playground")
        await asyncio.sleep(3)
        await page.screenshot(path="sannysoft_result.png")
        print("   Screenshot saved to sannysoft_result.png")

        print("\n2. Testing CreepJS...")
        await page.goto("https://abrahamjuliot.github.io/creepjs/")
        await asyncio.sleep(5)
        await page.screenshot(path="creepjs_result.png")
        print("   Screenshot saved to creepjs_result.png")


        input("\nPress Enter to close browser...")


if __name__ == "__main__":
    asyncio.run(main())
