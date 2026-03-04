from contextlib import AbstractContextManager

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from shopper_google.config import GoogleComputerUseConfig


class BrowserEnvironment(AbstractContextManager["BrowserEnvironment"]):
    """Manage the Playwright browser used by the Google Computer Use loop."""

    def __init__(self, config: GoogleComputerUseConfig):
        self.config = config
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> "BrowserEnvironment":
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch(
                headless=self.config.headless
            )
        except Exception as exc:
            self.playwright.stop()
            self.playwright = None
            raise RuntimeError(
                "Playwright Chromium is not available. Run "
                "`uv run playwright install chromium` first."
            ) from exc
        self.context = self.browser.new_context(
            viewport={
                "width": self.config.screen_width,
                "height": self.config.screen_height,
            }
        )
        self.page = self.context.new_page()
        return self

    def close(self) -> None:
        if self.context is not None:
            self.context.close()
            self.context = None
        if self.browser is not None:
            self.browser.close()
            self.browser = None
        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None

    def screenshot(self) -> bytes:
        if self.page is None:
            raise RuntimeError("Browser page is not initialized")
        return self.page.screenshot(type="png")

    def current_url(self) -> str:
        if self.page is None:
            raise RuntimeError("Browser page is not initialized")
        return self.page.url

    def __enter__(self) -> "BrowserEnvironment":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
