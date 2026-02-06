"""
Stealth module - mostly handled by Patchright natively.

Patchright provides built-in anti-detection that handles:
- Runtime.enable CDP leak prevention
- Console.enable serialization detection
- navigator.webdriver flag removal
- AutomationControlled blink feature disable

This module is kept for reference but most stealth is now
handled at the Patchright level for better consistency.

IMPORTANT: Do NOT add JavaScript patches that modify browser APIs.
This creates fingerprint inconsistencies that are easily detected.
Let Patchright and real Chrome handle the fingerprint naturally.
"""

__all__ = []
