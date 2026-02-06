"""Synchronous wrapper for Abrasio SDK."""

import asyncio
from typing import Optional, Union, TYPE_CHECKING

from .._api import Abrasio as AsyncAbrasio
from .._config import AbrasioConfig

if TYPE_CHECKING:
    from patchright.sync_api import Browser, BrowserContext, Page


def _run_sync(coro):
    """Run an async coroutine synchronously.

    Compatible with Python 3.8+ including 3.10+ where
    get_event_loop() emits DeprecationWarning without a running loop.
    """
    try:
        asyncio.get_running_loop()
        # Already inside an event loop (e.g. Jupyter notebooks).
        # Run in a separate thread to avoid blocking.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        # No running loop — safe to create one
        return asyncio.run(coro)


class Abrasio:
    """
    Synchronous interface for Abrasio SDK.

    Usage:
        with Abrasio() as browser:
            page = browser.new_page()
            page.goto("https://example.com")
            print(page.title())
    """

    def __init__(
        self,
        config: Optional[Union[AbrasioConfig, str]] = None,
        *,
        api_key: Optional[str] = None,
        headless: bool = True,
        proxy: Optional[str] = None,
        stealth: bool = True,
        **kwargs,
    ):
        self._async_abrasio = AsyncAbrasio(
            config=config,
            api_key=api_key,
            headless=headless,
            proxy=proxy,
            stealth=stealth,
            **kwargs,
        )

    def __enter__(self) -> "Abrasio":
        """Context manager entry."""
        _run_sync(self._async_abrasio.start())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        _run_sync(self._async_abrasio.close())

    def start(self) -> "Abrasio":
        """Start the browser."""
        _run_sync(self._async_abrasio.start())
        return self

    def close(self) -> None:
        """Close the browser."""
        _run_sync(self._async_abrasio.close())

    def new_page(self) -> "Page":
        """Create a new page."""
        # Returns async page - works with sync wrapper
        return _run_sync(self._async_abrasio.new_page())

    def new_context(self, **kwargs) -> "BrowserContext":
        """Create a new browser context."""
        return _run_sync(self._async_abrasio.new_context(**kwargs))

    @property
    def browser(self) -> "Browser":
        """Get the underlying browser."""
        return self._async_abrasio.browser

    @property
    def is_cloud(self) -> bool:
        """Check if running in cloud mode."""
        return self._async_abrasio.is_cloud

    @property
    def is_local(self) -> bool:
        """Check if running in local mode."""
        return self._async_abrasio.is_local
