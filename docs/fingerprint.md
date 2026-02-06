# Fingerprint Config & Utilities

Guide to configuring browser fingerprint protections and using fingerprint utilities.

## FingerprintConfig (Local Mode)

`FingerprintConfig` controls browser fingerprint protections in **local mode only**. In cloud mode, the cloud browser handles all fingerprinting automatically with real collected fingerprints.

### Basic Usage

```python
from abrasio import Abrasio, FingerprintConfig

async with Abrasio(
    headless=False,
    fingerprint=FingerprintConfig(
        webgl=True,          # Keep WebGL enabled (default)
        webrtc=False,        # Block WebRTC IP leak
        canvas_noise=True,   # Add noise to canvas fingerprint
        audio_noise=True,    # Add noise to audio fingerprint
    ),
) as browser:
    page = await browser.new_page()
    await page.goto("https://example.com")
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `webgl` | `True` | Enable WebGL APIs. Disabling is a strong bot signal - only disable if you specifically need to hide GPU info. |
| `webrtc` | `True` | Enable WebRTC. Set `False` when using a proxy to prevent real IP leaks. |
| `canvas_noise` | `False` | Add imperceptible noise to canvas fingerprint reads. Makes canvas fingerprint unique per session. |
| `audio_noise` | `False` | Add noise to AudioContext fingerprint reads. Makes audio fingerprint unique per session. |

### Recommendations

```python
# With proxy - block WebRTC to prevent IP leak
FingerprintConfig(webrtc=False)

# High privacy - randomize fingerprints
FingerprintConfig(
    canvas_noise=True,
    audio_noise=True,
    webrtc=False,
)

# Default - minimal footprint, maximum stealth
FingerprintConfig()  # All defaults
```

> **Cloud mode**: `FingerprintConfig` is completely ignored. The cloud browser uses real collected fingerprints 

## What is Browser Fingerprinting?

Browser fingerprinting identifies users by collecting device and browser characteristics:

| Category | Attributes |
|----------|------------|
| **Navigator** | User-Agent, platform, language, hardware concurrency |
| **Screen** | Width, height, color depth, pixel ratio |
| **WebGL** | GPU vendor, renderer, extensions |
| **Canvas** | Rendered image hash |
| **Audio** | AudioContext properties |
| **Fonts** | Installed system fonts |

Anti-bot systems check for **consistency** - if your User-Agent says Windows but WebGL shows Apple GPU, you're detected.

## Why Patchright Doesn't Need Fingerprint Injection

Unlike tools that inject fake fingerprints (which can be detected), Patchright:

1. Uses **real Chrome** browser (`channel="chrome"`)
2. Uses **real system GPU** for WebGL
3. Uses **real screen** dimensions
4. Doesn't modify JavaScript APIs

This means your fingerprint is **naturally consistent** because it's the real browser's fingerprint. `FingerprintConfig` adds optional noise on top of the real fingerprint rather than replacing it.

## Fingerprint Generation Utilities

*Requires: `pip install abrasio[fingerprint]`*

### generate_fingerprint()

Generate a consistent fingerprint using BrowserForge:

```python
from abrasio.utils import generate_fingerprint

# Generate random consistent fingerprint
fp = generate_fingerprint()

print(fp["navigator"]["userAgent"])
print(fp["screen"]["width"], "x", fp["screen"]["height"])
```

### Options

```python
fp = generate_fingerprint(
    browser="chrome",     # "chrome", "firefox", "safari", "edge"
    os="windows",         # "windows", "macos", "linux", None (random)
    device="desktop",     # "desktop", "mobile"
    locale="en-US",       # Locale string
    screen={              # Screen constraints
        "min_width": 1280,
        "max_width": 1920,
        "min_height": 720,
        "max_height": 1080,
    },
)
```

## Validate Consistency

### validate_fingerprint_consistency()

Check if fingerprint attributes are internally consistent:

```python
from abrasio.utils import validate_fingerprint_consistency

warnings = validate_fingerprint_consistency(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    platform="Win32",
    screen_width=1920,
    screen_height=1080,
    webgl_vendor="Apple Inc.",           # Mismatch!
    webgl_renderer="Apple M1",           # Mismatch!
)

if warnings:
    print("Inconsistencies detected:")
    for w in warnings:
        print(f"  - {w}")
else:
    print("Fingerprint is consistent!")
```

### Detected Inconsistencies

| Check | Example Issue |
|-------|--------------|
| OS mismatch | Windows UA + Mac platform |
| Mobile vs Desktop | Mobile UA + 1920x1080 screen |
| GPU mismatch | Apple GPU + Windows OS |
| Screen size | Too small or too large |
| Aspect ratio | Unrealistic ratio |

## Region Auto-Configuration

### get_realistic_locale()

Get locale/timezone by region:

```python
from abrasio.utils import get_realistic_locale

# By region
locale, timezone = get_realistic_locale(region="BR")
print(f"{locale} ({timezone})")  # pt-BR (America/Sao_Paulo)
```

**Supported Regions:**

| Region | Locale | Timezone |
|--------|--------|----------|
| US | en-US | America/New_York |
| BR | pt-BR | America/Sao_Paulo |
| GB | en-GB | Europe/London |
| DE | de-DE | Europe/Berlin |
| FR | fr-FR | Europe/Paris |
| ES | es-ES | Europe/Madrid |
| JP | ja-JP | Asia/Tokyo |
| CN | zh-CN | Asia/Shanghai |
| KR | ko-KR | Asia/Seoul |
| IT | it-IT | Europe/Rome |

50+ regions supported total.

## Testing Fingerprint

Test your browser against detection sites:

```python
import asyncio
from abrasio import Abrasio

async def test_fingerprint():
    async with Abrasio(headless=False) as browser:
        page = await browser.new_page()

        # BrowserLeaks - comprehensive fingerprint test
        await page.goto("https://browserleaks.com/")
        await page.screenshot(path="browserleaks.png")

        # Sannysoft - bot detection test
        await page.goto("https://bot.sannysoft.com/")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="sannysoft.png")

        # CreepJS - advanced fingerprint analysis
        await page.goto("https://abrahamjuliot.github.io/creepjs/")
        await page.wait_for_timeout(5000)
        await page.screenshot(path="creepjs.png")

asyncio.run(test_fingerprint())
```

## Common Fingerprint Detection Patterns

### 1. OS Mismatch

```
Detected:
User-Agent: Windows NT 10.0
Platform: MacIntel
```

### 2. GPU Mismatch

```
Detected:
User-Agent: Windows NT 10.0
WebGL: Apple M1 GPU
```

### 3. Screen Mismatch

```
Detected:
User-Agent: iPhone
Screen: 1920x1080
```

### 4. Language Mismatch

```
Detected:
IP: Brazil
Language: ru-RU
Timezone: Europe/Moscow
```

## When to Use What

| Use Case | Recommendation |
|----------|----------------|
| Local mode (default) | Let Patchright use real fingerprint |
| Local mode with proxy | `FingerprintConfig(webrtc=False)` |
| Local mode high privacy | `FingerprintConfig(canvas_noise=True, audio_noise=True, webrtc=False)` |
| Cloud mode | FingerprintConfig ignored - real fingerprints automatic |
| Checking consistency | Use `validate_fingerprint_consistency()` |
| Multiple local profiles | Use different `user_data_dir` paths |
