"""
Example demonstrating human-like behavior simulation.

Features inspired by Camoufox:
- Bezier curve mouse movements (distance-aware)
- Variable typing speed with occasional mistakes
- Smooth scrolling with momentum
- Random pauses and delays

These behaviors help avoid bot detection that analyzes
user interaction patterns.
"""

import asyncio
from abrasio import Abrasio
from abrasio.utils import (
    human_click,
    human_type,
    human_scroll,
    human_move_to,
    human_wait,
    simulate_reading,
    random_delay,
)


async def main():
    async with Abrasio(headless=False) as browser:
        page = await browser.new_page()

        print("Navigating to example form...")
        await page.goto("https://www.google.com")

        # Wait like a human would
        await human_wait(1.0, 2.0)

        # Move mouse naturally to search box
        search_box = await page.query_selector('textarea[name="q"], input[name="q"]')
        if search_box:
            box = await search_box.bounding_box()
            if box:
                print("Moving mouse to search box with Bezier curve...")
                await human_move_to(
                    page,
                    box["x"] + box["width"] / 2,
                    box["y"] + box["height"] / 2,
                )

            # Click with natural movement
            print("Clicking search box...")
            await human_click(page, 'textarea[name="q"], input[name="q"]')

            # Type with human-like speed (variable delays, occasional mistakes)
            print("Typing with human-like behavior...")
            await human_type(
                page,
                "patchright undetected browser automation",
                mistake_probability=0.03,  # 3% chance of typo
                think_pause_probability=0.05,  # 5% chance of pause
            )

            # Wait a bit before pressing enter
            await human_wait(0.5, 1.5)

            # Press enter
            await page.keyboard.press("Enter")

        # Wait for results
        await page.wait_for_load_state("networkidle")

        # Simulate reading the results page
        print("Simulating reading behavior...")
        await simulate_reading(page, min_seconds=3.0, max_seconds=6.0)

        # Scroll down naturally
        print("Scrolling with momentum...")
        await human_scroll(page, "down", 400, smooth=True)
        await human_wait(1.0, 2.0)

        await human_scroll(page, "down", 300, smooth=True)
        await human_wait(0.5, 1.0)

        # Scroll back up
        await human_scroll(page, "up", 200, smooth=True)

        print("\nDone! Mouse movements used Bezier curves with:")
        print("- Distance-aware timing (Fitts's Law)")
        print("- Ease-in-out acceleration")
        print("- Micro-jitter for natural feel")
        print("\nTyping included:")
        print("- Variable speed based on character frequency")
        print("- Occasional burst typing")
        print("- Random thinking pauses")

        # Keep browser open for inspection
        input("\nPress Enter to close...")


if __name__ == "__main__":
    asyncio.run(main())
