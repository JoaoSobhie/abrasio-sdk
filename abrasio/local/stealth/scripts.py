"""
Legacy stealth scripts - DEPRECATED.

Patchright handles anti-detection natively at the protocol level:
- Avoids Runtime.enable (the main detection vector)
- Executes JS in isolated ExecutionContexts
- Disables Console.enable

JavaScript API patches (like overriding navigator.webdriver) are
COUNTERPRODUCTIVE because:

1. They create fingerprint inconsistencies
   - Original function vs patched function have different signatures
   - toString() returns different results
   - Property descriptors reveal patches

2. Modern anti-bot systems check for:
   - Prototype chain inconsistencies
   - Function native code checks
   - Error stack analysis that reveals injected scripts

3. The best stealth is NO patches
   - Use real Chrome (channel="chrome")
   - Use Patchright for CDP leak prevention
   - Don't modify any browser APIs
   - Let the real browser fingerprint be natural

References:
- https://github.com/AntBat/patchright
- https://deviceandbrowserinfo.com/learning_zone/articles/detecting-headless-chrome-puppeteer-2024
- https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/
"""

# DEPRECATED - These patches are no longer used
# Kept for historical reference only
STEALTH_SCRIPTS = []

__all__ = ["STEALTH_SCRIPTS"]
