"""
Fingerprint utilities using BrowserForge.

BrowserForge generates browser fingerprints that match real-world traffic
distributions. This module provides utilities for:
- Generating consistent fingerprints
- Validating fingerprint consistency
- Getting realistic screen sizes
- Getting realistic locales/timezones

Note: Fingerprint INJECTION is deprecated in BrowserForge (use Camoufox).
We use BrowserForge only for GENERATION and VALIDATION.

References:
- https://github.com/daijro/browserforge
- https://camoufox.com/

Install: pip install abrasio[fingerprint]
"""

from typing import Optional, Dict, Any, List, Tuple
import random
import logging

logger = logging.getLogger("abrasio.fingerprint")

# Try to import browserforge
try:
    from browserforge.fingerprints import FingerprintGenerator, Screen
    from browserforge.headers import HeaderGenerator
    BROWSERFORGE_AVAILABLE = True
except ImportError:
    BROWSERFORGE_AVAILABLE = False
    FingerprintGenerator = None
    Screen = None
    HeaderGenerator = None


def _check_browserforge():
    """Check if browserforge is available."""
    if not BROWSERFORGE_AVAILABLE:
        raise ImportError(
            "browserforge is required for fingerprint utilities. "
            "Install with: pip install abrasio[fingerprint]"
        )


# Common screen resolutions by market share (2024)
COMMON_SCREENS = [
    {"width": 1920, "height": 1080, "weight": 23},  # Most common
    {"width": 1366, "height": 768, "weight": 15},
    {"width": 1536, "height": 864, "weight": 10},
    {"width": 1440, "height": 900, "weight": 7},
    {"width": 1280, "height": 720, "weight": 6},
    {"width": 2560, "height": 1440, "weight": 5},
    {"width": 1600, "height": 900, "weight": 4},
    {"width": 1280, "height": 800, "weight": 3},
    {"width": 3840, "height": 2160, "weight": 3},  # 4K
    {"width": 1680, "height": 1050, "weight": 2},
]

# Common locales by usage
COMMON_LOCALES = [
    ("en-US", "America/New_York", 30),
    ("en-GB", "Europe/London", 8),
    ("de-DE", "Europe/Berlin", 5),
    ("fr-FR", "Europe/Paris", 4),
    ("es-ES", "Europe/Madrid", 3),
    ("pt-BR", "America/Sao_Paulo", 3),
    ("ja-JP", "Asia/Tokyo", 3),
    ("zh-CN", "Asia/Shanghai", 5),
    ("ko-KR", "Asia/Seoul", 2),
    ("it-IT", "Europe/Rome", 2),
]

# Comprehensive region to locale/timezone mapping
# Maps ISO 3166-1 alpha-2 country codes to (locale, timezone, valid_timezones)
REGION_CONFIG = {
    # North America
    "US": {"locale": "en-US", "timezone": "America/New_York", "valid_timezones": [
        "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
        "America/Phoenix", "America/Anchorage", "Pacific/Honolulu"
    ]},
    "CA": {"locale": "en-CA", "timezone": "America/Toronto", "valid_timezones": [
        "America/Toronto", "America/Vancouver", "America/Edmonton", "America/Winnipeg"
    ]},
    "MX": {"locale": "es-MX", "timezone": "America/Mexico_City", "valid_timezones": [
        "America/Mexico_City", "America/Cancun", "America/Tijuana"
    ]},

    # South America
    "BR": {"locale": "pt-BR", "timezone": "America/Sao_Paulo", "valid_timezones": [
        "America/Sao_Paulo", "America/Rio_Branco", "America/Manaus", "America/Recife"
    ]},
    "AR": {"locale": "es-AR", "timezone": "America/Buenos_Aires", "valid_timezones": [
        "America/Buenos_Aires", "America/Argentina/Buenos_Aires"
    ]},
    "CL": {"locale": "es-CL", "timezone": "America/Santiago", "valid_timezones": ["America/Santiago"]},
    "CO": {"locale": "es-CO", "timezone": "America/Bogota", "valid_timezones": ["America/Bogota"]},
    "PE": {"locale": "es-PE", "timezone": "America/Lima", "valid_timezones": ["America/Lima"]},

    # Europe
    "GB": {"locale": "en-GB", "timezone": "Europe/London", "valid_timezones": ["Europe/London"]},
    "DE": {"locale": "de-DE", "timezone": "Europe/Berlin", "valid_timezones": ["Europe/Berlin"]},
    "FR": {"locale": "fr-FR", "timezone": "Europe/Paris", "valid_timezones": ["Europe/Paris"]},
    "ES": {"locale": "es-ES", "timezone": "Europe/Madrid", "valid_timezones": ["Europe/Madrid"]},
    "IT": {"locale": "it-IT", "timezone": "Europe/Rome", "valid_timezones": ["Europe/Rome"]},
    "PT": {"locale": "pt-PT", "timezone": "Europe/Lisbon", "valid_timezones": ["Europe/Lisbon"]},
    "NL": {"locale": "nl-NL", "timezone": "Europe/Amsterdam", "valid_timezones": ["Europe/Amsterdam"]},
    "BE": {"locale": "nl-BE", "timezone": "Europe/Brussels", "valid_timezones": ["Europe/Brussels"]},
    "AT": {"locale": "de-AT", "timezone": "Europe/Vienna", "valid_timezones": ["Europe/Vienna"]},
    "CH": {"locale": "de-CH", "timezone": "Europe/Zurich", "valid_timezones": ["Europe/Zurich"]},
    "PL": {"locale": "pl-PL", "timezone": "Europe/Warsaw", "valid_timezones": ["Europe/Warsaw"]},
    "SE": {"locale": "sv-SE", "timezone": "Europe/Stockholm", "valid_timezones": ["Europe/Stockholm"]},
    "NO": {"locale": "nb-NO", "timezone": "Europe/Oslo", "valid_timezones": ["Europe/Oslo"]},
    "DK": {"locale": "da-DK", "timezone": "Europe/Copenhagen", "valid_timezones": ["Europe/Copenhagen"]},
    "FI": {"locale": "fi-FI", "timezone": "Europe/Helsinki", "valid_timezones": ["Europe/Helsinki"]},
    "RU": {"locale": "ru-RU", "timezone": "Europe/Moscow", "valid_timezones": [
        "Europe/Moscow", "Europe/Kaliningrad", "Asia/Yekaterinburg", "Asia/Vladivostok"
    ]},
    "UA": {"locale": "uk-UA", "timezone": "Europe/Kiev", "valid_timezones": ["Europe/Kiev", "Europe/Kyiv"]},
    "CZ": {"locale": "cs-CZ", "timezone": "Europe/Prague", "valid_timezones": ["Europe/Prague"]},
    "GR": {"locale": "el-GR", "timezone": "Europe/Athens", "valid_timezones": ["Europe/Athens"]},
    "TR": {"locale": "tr-TR", "timezone": "Europe/Istanbul", "valid_timezones": ["Europe/Istanbul"]},

    # Asia
    "JP": {"locale": "ja-JP", "timezone": "Asia/Tokyo", "valid_timezones": ["Asia/Tokyo"]},
    "CN": {"locale": "zh-CN", "timezone": "Asia/Shanghai", "valid_timezones": ["Asia/Shanghai", "Asia/Hong_Kong"]},
    "KR": {"locale": "ko-KR", "timezone": "Asia/Seoul", "valid_timezones": ["Asia/Seoul"]},
    "IN": {"locale": "hi-IN", "timezone": "Asia/Kolkata", "valid_timezones": ["Asia/Kolkata", "Asia/Calcutta"]},
    "SG": {"locale": "en-SG", "timezone": "Asia/Singapore", "valid_timezones": ["Asia/Singapore"]},
    "HK": {"locale": "zh-HK", "timezone": "Asia/Hong_Kong", "valid_timezones": ["Asia/Hong_Kong"]},
    "TW": {"locale": "zh-TW", "timezone": "Asia/Taipei", "valid_timezones": ["Asia/Taipei"]},
    "TH": {"locale": "th-TH", "timezone": "Asia/Bangkok", "valid_timezones": ["Asia/Bangkok"]},
    "VN": {"locale": "vi-VN", "timezone": "Asia/Ho_Chi_Minh", "valid_timezones": ["Asia/Ho_Chi_Minh", "Asia/Saigon"]},
    "ID": {"locale": "id-ID", "timezone": "Asia/Jakarta", "valid_timezones": ["Asia/Jakarta"]},
    "MY": {"locale": "ms-MY", "timezone": "Asia/Kuala_Lumpur", "valid_timezones": ["Asia/Kuala_Lumpur"]},
    "PH": {"locale": "fil-PH", "timezone": "Asia/Manila", "valid_timezones": ["Asia/Manila"]},
    "AE": {"locale": "ar-AE", "timezone": "Asia/Dubai", "valid_timezones": ["Asia/Dubai"]},
    "SA": {"locale": "ar-SA", "timezone": "Asia/Riyadh", "valid_timezones": ["Asia/Riyadh"]},
    "IL": {"locale": "he-IL", "timezone": "Asia/Jerusalem", "valid_timezones": ["Asia/Jerusalem", "Asia/Tel_Aviv"]},

    # Oceania
    "AU": {"locale": "en-AU", "timezone": "Australia/Sydney", "valid_timezones": [
        "Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane", "Australia/Perth"
    ]},
    "NZ": {"locale": "en-NZ", "timezone": "Pacific/Auckland", "valid_timezones": ["Pacific/Auckland"]},

    # Africa
    "ZA": {"locale": "en-ZA", "timezone": "Africa/Johannesburg", "valid_timezones": ["Africa/Johannesburg"]},
    "EG": {"locale": "ar-EG", "timezone": "Africa/Cairo", "valid_timezones": ["Africa/Cairo"]},
    "NG": {"locale": "en-NG", "timezone": "Africa/Lagos", "valid_timezones": ["Africa/Lagos"]},
    "KE": {"locale": "en-KE", "timezone": "Africa/Nairobi", "valid_timezones": ["Africa/Nairobi"]},
}


def get_realistic_screen(
    min_width: Optional[int] = None,
    max_width: Optional[int] = None,
    min_height: Optional[int] = None,
    max_height: Optional[int] = None,
) -> Dict[str, int]:
    """
    Get a realistic screen resolution based on market share.

    Args:
        min_width: Minimum screen width
        max_width: Maximum screen width
        min_height: Minimum screen height
        max_height: Maximum screen height

    Returns:
        Dict with width and height
    """
    # Filter screens by constraints
    valid_screens = []
    for screen in COMMON_SCREENS:
        if min_width and screen["width"] < min_width:
            continue
        if max_width and screen["width"] > max_width:
            continue
        if min_height and screen["height"] < min_height:
            continue
        if max_height and screen["height"] > max_height:
            continue
        valid_screens.append(screen)

    if not valid_screens:
        # Fallback to most common
        return {"width": 1920, "height": 1080}

    # Weighted random selection
    total_weight = sum(s["weight"] for s in valid_screens)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for screen in valid_screens:
        cumulative += screen["weight"]
        if r <= cumulative:
            return {"width": screen["width"], "height": screen["height"]}

    return {"width": valid_screens[0]["width"], "height": valid_screens[0]["height"]}


def get_realistic_locale(region: Optional[str] = None) -> Tuple[str, str]:
    """
    Get a realistic locale and timezone combination.

    Args:
        region: Optional region hint (e.g., "US", "BR", "DE")

    Returns:
        Tuple of (locale, timezone)
    """
    if region:
        # Map region to locale
        region_map = {
            "US": ("en-US", "America/New_York"),
            "BR": ("pt-BR", "America/Sao_Paulo"),
            "GB": ("en-GB", "Europe/London"),
            "DE": ("de-DE", "Europe/Berlin"),
            "FR": ("fr-FR", "Europe/Paris"),
            "ES": ("es-ES", "Europe/Madrid"),
            "JP": ("ja-JP", "Asia/Tokyo"),
            "CN": ("zh-CN", "Asia/Shanghai"),
            "KR": ("ko-KR", "Asia/Seoul"),
            "IT": ("it-IT", "Europe/Rome"),
        }
        if region.upper() in region_map:
            return region_map[region.upper()]

    # Weighted random selection
    total_weight = sum(l[2] for l in COMMON_LOCALES)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for locale, timezone, weight in COMMON_LOCALES:
        cumulative += weight
        if r <= cumulative:
            return (locale, timezone)

    return COMMON_LOCALES[0][:2]


def generate_fingerprint(
    browser: str = "chrome",
    os: Optional[str] = None,
    device: str = "desktop",
    locale: Optional[str] = None,
    screen: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Generate a consistent browser fingerprint using BrowserForge.

    All fingerprint attributes are internally consistent (e.g., Windows UA
    won't have Apple M1 GPU).

    Args:
        browser: Browser type ("chrome", "firefox", "safari", "edge")
        os: Operating system ("windows", "macos", "linux") - random if None
        device: Device type ("desktop", "mobile")
        locale: Locale string (e.g., "en-US") - random if None
        screen: Screen constraints {"min_width", "max_width", etc.}

    Returns:
        Dict with fingerprint data including:
        - navigator: Navigator properties
        - screen: Screen properties
        - headers: HTTP headers
        - webgl: WebGL properties (if available)

    Raises:
        ImportError: If browserforge is not installed
    """
    _check_browserforge()

    # Set up screen constraints
    screen_obj = None
    if screen:
        screen_obj = Screen(
            min_width=screen.get("min_width"),
            max_width=screen.get("max_width"),
            min_height=screen.get("min_height"),
            max_height=screen.get("max_height"),
        )

    # Generate fingerprint
    generator = FingerprintGenerator(
        browser=browser,
        os=os,
        device=device,
    )

    fp = generator.generate(screen=screen_obj)

    # Generate matching headers
    header_gen = HeaderGenerator(
        browser=browser,
        os=os,
        device=device,
    )
    headers = header_gen.generate()

    # Build result
    result = {
        "navigator": {
            "userAgent": fp.navigator.userAgent if hasattr(fp, 'navigator') else None,
            "platform": fp.navigator.platform if hasattr(fp, 'navigator') else None,
            "language": locale or (fp.navigator.language if hasattr(fp, 'navigator') else "en-US"),
            "hardwareConcurrency": fp.navigator.hardwareConcurrency if hasattr(fp, 'navigator') else 8,
            "deviceMemory": fp.navigator.deviceMemory if hasattr(fp, 'navigator') else 8,
        },
        "screen": {
            "width": fp.screen.width if hasattr(fp, 'screen') else 1920,
            "height": fp.screen.height if hasattr(fp, 'screen') else 1080,
            "colorDepth": fp.screen.colorDepth if hasattr(fp, 'screen') else 24,
            "pixelRatio": fp.screen.pixelRatio if hasattr(fp, 'screen') else 1,
        },
        "headers": dict(headers) if headers else {},
    }

    # Add WebGL if available
    if hasattr(fp, 'webgl') and fp.webgl:
        result["webgl"] = {
            "vendor": fp.webgl.vendor,
            "renderer": fp.webgl.renderer,
        }

    logger.debug(f"Generated fingerprint: {result['navigator']['userAgent']}")
    return result


def validate_fingerprint_consistency(
    user_agent: str,
    platform: str,
    screen_width: int,
    screen_height: int,
    webgl_vendor: Optional[str] = None,
    webgl_renderer: Optional[str] = None,
) -> List[str]:
    """
    Validate that fingerprint attributes are internally consistent.

    Checks for common mismatches that can trigger bot detection:
    - Windows UA with macOS platform
    - Mobile UA with desktop resolution
    - Apple GPU with Windows/Linux OS
    - Unrealistic screen sizes

    Args:
        user_agent: Browser User-Agent string
        platform: Navigator platform
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        webgl_vendor: WebGL vendor string (optional)
        webgl_renderer: WebGL renderer string (optional)

    Returns:
        List of inconsistency warnings (empty if all consistent)
    """
    warnings = []
    ua_lower = user_agent.lower()
    platform_lower = platform.lower()

    # Check OS consistency
    if "windows" in ua_lower and "mac" in platform_lower:
        warnings.append("UA says Windows but platform says Mac")
    if "mac os" in ua_lower and "win" in platform_lower:
        warnings.append("UA says macOS but platform says Windows")
    if "linux" in ua_lower and ("mac" in platform_lower or "win" in platform_lower):
        warnings.append("UA says Linux but platform doesn't match")

    # Check mobile vs desktop
    if any(m in ua_lower for m in ["mobile", "android", "iphone"]):
        if screen_width > 1024 or screen_height > 1024:
            warnings.append("Mobile UA but desktop-sized screen")
    else:
        if screen_width < 800 and screen_height < 600:
            warnings.append("Desktop UA but very small screen")

    # Check WebGL consistency
    if webgl_vendor and webgl_renderer:
        vendor_lower = webgl_vendor.lower()
        renderer_lower = webgl_renderer.lower()

        # Apple GPU should only appear on macOS/iOS
        if "apple" in vendor_lower or "apple" in renderer_lower:
            if "windows" in ua_lower or "linux" in ua_lower:
                warnings.append("Apple GPU with non-Apple OS")

        # NVIDIA/AMD typically not on iOS
        if any(g in renderer_lower for g in ["nvidia", "amd", "radeon", "geforce"]):
            if "iphone" in ua_lower or "ipad" in ua_lower:
                warnings.append("Desktop GPU with iOS device")

    # Check for unrealistic screen sizes
    if screen_width < 320 or screen_height < 240:
        warnings.append("Screen too small to be realistic")
    if screen_width > 7680 or screen_height > 4320:  # Beyond 8K
        warnings.append("Screen too large to be realistic")
    if screen_width > screen_height * 4:
        warnings.append("Unrealistic aspect ratio (too wide)")

    return warnings


def validate_region_consistency(
    region: Optional[str] = None,
    locale: Optional[str] = None,
    timezone: Optional[str] = None,
) -> List[str]:
    """
    Validate that region, locale, and timezone are consistent.

    This is important for anti-detection as mismatches between IP geolocation,
    browser locale, and timezone are a common detection vector.

    Args:
        region: ISO 3166-1 alpha-2 country code (e.g., "US", "BR", "DE")
        locale: Browser locale string (e.g., "en-US", "pt-BR")
        timezone: Timezone string (e.g., "America/New_York", "America/Sao_Paulo")

    Returns:
        List of inconsistency warnings (empty if all consistent)

    Example:
        >>> warnings = validate_region_consistency(region="BR", timezone="America/New_York")
        >>> print(warnings)
        ['Timezone America/New_York does not match region BR (expected America/Sao_Paulo or similar)']
    """
    warnings = []

    if not region:
        return warnings

    region_upper = region.upper()

    if region_upper not in REGION_CONFIG:
        logger.warning(f"Unknown region: {region}. Skipping validation.")
        return warnings

    config = REGION_CONFIG[region_upper]
    expected_locale = config["locale"]
    expected_timezone = config["timezone"]
    valid_timezones = config["valid_timezones"]

    # Check timezone consistency
    if timezone:
        if timezone not in valid_timezones:
            warnings.append(
                f"Timezone '{timezone}' does not match region '{region}' "
                f"(expected one of: {', '.join(valid_timezones)})"
            )

    # Check locale consistency (less strict - just check language prefix)
    if locale:
        expected_lang = expected_locale.split("-")[0]
        actual_lang = locale.split("-")[0]

        # Allow some flexibility for multilingual countries
        multilingual_regions = {"CA", "CH", "BE", "SG", "IN"}
        if region_upper not in multilingual_regions:
            if actual_lang != expected_lang:
                warnings.append(
                    f"Locale '{locale}' language does not match region '{region}' "
                    f"(expected language: {expected_lang})"
                )

    return warnings


def auto_configure_region(
    region: str,
    locale: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Tuple[str, str, List[str]]:
    """
    Automatically configure locale and timezone based on region.

    Returns the best locale/timezone combination for the given region,
    using provided values if they are consistent, or defaults if not.

    Args:
        region: ISO 3166-1 alpha-2 country code (e.g., "US", "BR", "DE")
        locale: Optional locale override (validated for consistency)
        timezone: Optional timezone override (validated for consistency)

    Returns:
        Tuple of (locale, timezone, warnings)
        - locale: The locale to use (provided or auto-detected)
        - timezone: The timezone to use (provided or auto-detected)
        - warnings: List of any inconsistency warnings

    Example:
        >>> locale, timezone, warnings = auto_configure_region("BR")
        >>> print(locale, timezone)
        pt-BR America/Sao_Paulo

        >>> locale, timezone, warnings = auto_configure_region("BR", timezone="America/New_York")
        >>> print(warnings)
        ['Timezone mismatch: using America/New_York but region BR expects America/Sao_Paulo']
    """
    warnings = []
    region_upper = region.upper()

    if region_upper not in REGION_CONFIG:
        logger.warning(f"Unknown region: {region}. Using defaults.")
        return (locale or "en-US", timezone or "America/New_York", warnings)

    config = REGION_CONFIG[region_upper]
    default_locale = config["locale"]
    default_timezone = config["timezone"]
    valid_timezones = config["valid_timezones"]

    # Determine final locale
    final_locale = locale if locale else default_locale

    # Determine final timezone
    final_timezone = timezone if timezone else default_timezone

    # Validate and warn if mismatches
    if timezone and timezone not in valid_timezones:
        warnings.append(
            f"Timezone mismatch: using '{timezone}' but region '{region}' "
            f"expects one of: {', '.join(valid_timezones)}"
        )
        logger.warning(warnings[-1])

    if locale:
        expected_lang = default_locale.split("-")[0]
        actual_lang = locale.split("-")[0]
        multilingual_regions = {"CA", "CH", "BE", "SG", "IN"}
        if region_upper not in multilingual_regions and actual_lang != expected_lang:
            warnings.append(
                f"Locale mismatch: using '{locale}' but region '{region}' "
                f"typically uses '{default_locale}'"
            )
            logger.warning(warnings[-1])

    return (final_locale, final_timezone, warnings)


def get_region_config(region: str) -> Optional[Dict[str, Any]]:
    """
    Get the full configuration for a region.

    Args:
        region: ISO 3166-1 alpha-2 country code

    Returns:
        Dict with locale, timezone, and valid_timezones, or None if unknown region
    """
    return REGION_CONFIG.get(region.upper())


def list_supported_regions() -> List[str]:
    """
    List all supported region codes.

    Returns:
        List of ISO 3166-1 alpha-2 country codes
    """
    return sorted(REGION_CONFIG.keys())


__all__ = [
    "generate_fingerprint",
    "validate_fingerprint_consistency",
    "validate_region_consistency",
    "auto_configure_region",
    "get_region_config",
    "list_supported_regions",
    "get_realistic_screen",
    "get_realistic_locale",
    "BROWSERFORGE_AVAILABLE",
    "REGION_CONFIG",
]
