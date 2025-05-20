import logging, random
from typing import Optional, Dict
from playwright.async_api import async_playwright
from ..utils.constants import PLAYWRIGHT_BROWSER_ARGS, PLAYWRIGHT_BROWSER_ARGS_DOCKER # Changed to relative
from ..utils.utils import is_running_in_docker # Changed to relative

class PlaywrightManager:
    """
    Manages Playwright browser lifecycle and configuration.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(
        self, 
        headless: bool, 
        user_agent: str | None = None,
        locale: str | None = None,
        timezone_id: str | None = None,
        proxy: Optional[Dict[str, str]] = None
    ):       
        """
        Initialize and start Playwright with a browser and page.

        Args:
            is_webdriver_headless (bool): Whether to start the browser in headless mode.
            proxy (Optional[Dict[str, str]]): Proxy configuration with keys 'server', 'username', and 'password'.
        """
        try:
            self.logger.info("Starting Playwright...")
            self.playwright = await async_playwright().start()

            browser_args = PLAYWRIGHT_BROWSER_ARGS_DOCKER if is_running_in_docker() else PLAYWRIGHT_BROWSER_ARGS

            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=browser_args, 
                proxy=proxy
            )

            self.context = await self.browser.new_context(
                locale=locale,
                timezone_id=timezone_id,
                user_agent=user_agent,
                viewport={"width": random.randint(1366, 1920), "height": random.randint(768, 1080)}
            )

            self.page = await self.context.new_page()
            self.logger.info("Playwright initialized successfully.")

        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright: {str(e)}")
            raise

    async def cleanup(self):
        """Properly closes Playwright instances."""
        self.logger.info("Cleaning up Playwright resources...")
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("Playwright resources cleanup complete.")