"""
IP-based geolocation for automatic locale and timezone detection.

This module detects the user's location based on their public IP address
and returns appropriate locale and timezone settings for browser configuration.

Used only in LOCAL mode (no API key) to ensure browser settings match the user's
actual location, improving stealth by avoiding mismatches between IP geolocation
and browser locale/timezone.

In CLOUD mode, the cloud browser handles this automatically based on the proxy's location.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from functools import lru_cache
import urllib.request
import json

from .fingerprint import REGION_CONFIG

logger = logging.getLogger("abrasio.geolocation")

# IP Geolocation APIs (free, no API key required)
GEOLOCATION_APIS = [
    "http://ip-api.com/json/?fields=status,countryCode,timezone,query",
    "https://ipapi.co/json/",
]

# Cache duration (in function calls, not time - using lru_cache)
CACHE_SIZE = 1


@dataclass
class GeoLocation:
    """Geolocation result from IP lookup."""
    ip: str
    country_code: str
    timezone: str
    locale: str
    success: bool = True
    error: Optional[str] = None


@lru_cache(maxsize=CACHE_SIZE)
def _fetch_geolocation() -> Optional[dict]:
    """
    Fetch geolocation data from IP API.

    Cached to avoid repeated API calls.

    Returns:
        Dict with geolocation data or None if all APIs fail
    """
    for api_url in GEOLOCATION_APIS:
        try:
            logger.debug(f"Fetching geolocation from {api_url}")

            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

                # Handle ip-api.com format
                if "status" in data:
                    if data.get("status") == "success":
                        return {
                            "ip": data.get("query", ""),
                            "country_code": data.get("countryCode", ""),
                            "timezone": data.get("timezone", ""),
                        }
                    else:
                        logger.warning(f"ip-api.com returned error: {data}")
                        continue

                # Handle ipapi.co format
                if "country_code" in data:
                    return {
                        "ip": data.get("ip", ""),
                        "country_code": data.get("country_code", ""),
                        "timezone": data.get("timezone", ""),
                    }

                logger.warning(f"Unexpected API response format: {data}")

        except Exception as e:
            logger.debug(f"Geolocation API {api_url} failed: {e}")
            continue

    return None


def detect_geolocation() -> GeoLocation:
    """
    Detect user's geolocation from their public IP address.

    Returns:
        GeoLocation object with country_code, timezone, locale, and IP

    Example:
        >>> geo = detect_geolocation()
        >>> print(f"Country: {geo.country_code}, Timezone: {geo.timezone}, Locale: {geo.locale}")
        Country: BR, Timezone: America/Sao_Paulo, Locale: pt-BR
    """
    data = _fetch_geolocation()

    if not data:
        logger.warning("Could not detect geolocation. Using defaults (en-US, America/New_York)")
        return GeoLocation(
            ip="unknown",
            country_code="US",
            timezone="America/New_York",
            locale="en-US",
            success=False,
            error="All geolocation APIs failed"
        )

    country_code = data.get("country_code", "US").upper()
    timezone = data.get("timezone", "America/New_York")
    ip = data.get("ip", "unknown")

    # Get locale from our region config
    if country_code in REGION_CONFIG:
        locale = REGION_CONFIG[country_code]["locale"]
    else:
        # Fallback: construct locale from country code
        # e.g., "AR" -> "es-AR", "NL" -> "nl-NL"
        locale = f"en-{country_code}"
        logger.debug(f"Unknown country code {country_code}, using fallback locale {locale}")

    logger.info(f"Detected geolocation: {country_code} ({timezone}, {locale})")

    return GeoLocation(
        ip=ip,
        country_code=country_code,
        timezone=timezone,
        locale=locale,
        success=True
    )


def get_locale_timezone_from_ip() -> Tuple[str, str, str]:
    """
    Get locale and timezone based on the user's public IP.

    Convenience function for SDK configuration.

    Returns:
        Tuple of (locale, timezone, country_code)

    Example:
        >>> locale, timezone, country = get_locale_timezone_from_ip()
        >>> print(f"locale={locale}, timezone={timezone}, country={country}")
        locale=pt-BR, timezone=America/Sao_Paulo, country=BR
    """
    geo = detect_geolocation()
    return (geo.locale, geo.timezone, geo.country_code)


def clear_geolocation_cache():
    """Clear the geolocation cache to force a fresh lookup."""
    _fetch_geolocation.cache_clear()


__all__ = [
    "detect_geolocation",
    "get_locale_timezone_from_ip",
    "clear_geolocation_cache",
    "GeoLocation",
]
