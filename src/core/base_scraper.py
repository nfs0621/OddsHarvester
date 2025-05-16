import logging, re, json, asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError, Error
from .playwright_manager import PlaywrightManager
from .browser_helper import BrowserHelper
from .odds_portal_market_extractor import OddsPortalMarketExtractor
from utils.constants import ODDSPORTAL_BASE_URL, ODDS_FORMAT, SCRAPE_CONCURRENCY_TASKS
from utils.sport_market_constants import BaseballMarket # Added import

class BaseScraper:
    """
    Base class for scraping match data from OddsPortal.
    """

    def __init__(
        self, 
        playwright_manager: PlaywrightManager,
        browser_helper: BrowserHelper, 
        market_extractor: OddsPortalMarketExtractor
    ):
        """
        Args:
            playwright_manager (PlaywrightManager): Handles Playwright lifecycle.
            browser_helper (BrowserHelper): Helper class for browser interactions.
            market_extractor (OddsPortalMarketExtractor): Handles market scraping.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.playwright_manager = playwright_manager
        self.browser_helper = browser_helper
        self.market_extractor = market_extractor

    def _sanitize_bookmaker_name(self, name: str) -> str:
        """
        Sanitizes a bookmaker name to be used in a column header.
        Replaces spaces and special characters with underscores and converts to lowercase.
        """
        name = name.lower()
        name = re.sub(r'\\s+', '_', name)  # Replace spaces with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)  # Remove special characters except underscore
        return name

    async def set_odds_format(
        self, 
        page: Page, 
        odds_format: str = ODDS_FORMAT
    ):
        """
        Sets the odds format on the page.

        Args:
            page (Page): The Playwright page instance.
            odds_format (str): The desired odds format.
        """
        try:
            self.logger.info(f"Attempting to set odds format to: {odds_format}")
            button_selector = "div.group > button.gap-2"
            # Increased timeout for stability, ensure button is interactable
            await page.wait_for_selector(button_selector, state="visible", timeout=10000)
            dropdown_button = await page.query_selector(button_selector)

            if not dropdown_button:
                self.logger.error("Odds format dropdown button not found.")
                return

            current_format_text = await dropdown_button.inner_text()
            self.logger.info(f"Current odds format detected on button: {current_format_text}")

            # Normalize comparison
            if odds_format.lower() in current_format_text.lower():
                self.logger.info(f"Odds format already appears to be '{odds_format}'. Skipping change.")
                return

            await dropdown_button.click()
            # Wait for dropdown content to be visible
            dropdown_content_selector = "div.group > div.dropdown-content"
            await page.wait_for_selector(dropdown_content_selector, state="visible", timeout=5000)
            
            format_option_selector = f"{dropdown_content_selector} > ul > li > a"
            format_options = await page.query_selector_all(format_option_selector)

            found_option = False
            for option in format_options:
                option_text = await option.inner_text()
                if option_text and odds_format.lower() in option_text.lower():
                    self.logger.info(f"Found matching odds format option: {option_text}. Clicking.")
                    await option.click()
                    
                    # Wait for the dropdown to close by checking for its absence or invisibility
                    await page.wait_for_selector(dropdown_content_selector, state="hidden", timeout=5000)
                    # Add a small delay for the page to update the button text
                    await page.wait_for_timeout(1000) 

                    # Verify the change by re-checking the button text
                    updated_format_text = await dropdown_button.inner_text()
                    if odds_format.lower() in updated_format_text.lower():
                        self.logger.info(f"Odds format successfully changed to '{odds_format}'. Button text: {updated_format_text}")
                    else:
                        self.logger.warning(f"Attempted to change odds format to '{odds_format}', but button text is now '{updated_format_text}'.")
                    found_option = True
                    break
            
            if not found_option:
                self.logger.warning(f"Desired odds format '{odds_format}' not found in dropdown options.")

        except TimeoutError as e:
            self.logger.error(f"Timeout error during set_odds_format: {e}")
        except Exception as e:
            self.logger.error(f"General error in set_odds_format: {e}", exc_info=True)
    
    async def extract_match_links(
        self, 
        page: Page
    ) -> List[str]:
        """
        Extract and parse match links from the current page.

        Args:
            page (Page): A Playwright Page instance for this task.

        Returns:
            List[str]: A list of unique match links found on the page.
        """
        try:
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'lxml')
            event_rows = soup.find_all(class_=re.compile("^eventRow"))
            self.logger.info(f"Found {len(event_rows)} event rows.")

            match_links = {
                f"{ODDSPORTAL_BASE_URL}{link['href']}"
                for row in event_rows
                for link in row.find_all('a', href=True)
                if len(link['href'].strip('/').split('/')) > 3
            }

            self.logger.info(f"Extracted {len(match_links)} unique match links.")
            return list(match_links)

        except Exception as e:
            self.logger.error(f"Error extracting match links: {e}", exc_info=True)
            return []

    async def extract_match_odds(
        self, 
        sport: str,
        match_links: List[str],
        markets: Optional[List[str]] = None,
        scrape_odds_history: bool = False,
        target_bookmaker: str | None = None,
        concurrent_scraping_task: int = SCRAPE_CONCURRENCY_TASKS
    ) -> List[Dict[str, Any]]:
        """
        Extract odds for a list of match links concurrently.

        Args:
            sport (str): The sport to scrape odds for.
            match_links (List[str]): A list of match links to scrape odds for.
            markets (Optional[List[str]]: The list of markets to scrape.
            scrape_odds_history (bool): Whether to scrape and attach odds history.
            target_bookmaker (str): If set, only scrape odds for this bookmaker.
            concurrent_scraping_task (int): Controls how many pages are processed simultaneously.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing scraped odds data.
        """
        self.logger.info(f"Starting to scrape odds for {len(match_links)} match links...")
        semaphore = asyncio.Semaphore(concurrent_scraping_task)
        failed_links = []

        async def scrape_with_semaphore(link):
            async with semaphore:
                tab = None
                
                try:
                    tab = await self.playwright_manager.context.new_page()
                    # Ensure the odds format is set for the new page
                    await self.set_odds_format(tab, odds_format=ODDS_FORMAT)
                    
                    data = await self._scrape_match_data(
                        page=tab, 
                        sport=sport, 
                        match_link=link, 
                        markets=markets,
                        scrape_odds_history=scrape_odds_history,
                        target_bookmaker=target_bookmaker
                    )
                    self.logger.info(f"Successfully scraped match link: {link}")
                    return data
                
                except Exception as e:
                    self.logger.error(f"Error scraping link {link}: {e}")
                    failed_links.append(link)
                    return None
                
                finally:
                    if tab:
                        await tab.close()

        tasks = [scrape_with_semaphore(link) for link in match_links]
        results = await asyncio.gather(*tasks)
        odds_data = [result for result in results if result is not None]
        self.logger.info(f"Successfully scraped odds data for {len(odds_data)} matches.")

        if failed_links:
            self.logger.warning(f"Failed to scrape data for {len(failed_links)} links: {failed_links}")

        return odds_data

    async def _scrape_match_data(
        self, 
        page: Page,
        sport: str,
        match_link: str, 
        markets: Optional[List[str]] = None,
        scrape_odds_history: bool = False,
        target_bookmaker: str | None = None
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape data for a specific match based on the desired markets.

        Args:
            page (Page): A Playwright Page instance for this task.
            sport (str): The sport to scrape odds for.
            match_link (str): The link to the match page.
            markets (Optional[List[str]]): A list of markets to scrape (e.g., ['1x2', 'over_under_2_5']).
            scrape_odds_history (bool): Whether to scrape and attach odds history.
            target_bookmaker (str): If set, only scrape odds for this bookmaker.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing scraped data, or None if scraping fails.
        """
        self.logger.info(f"Scraping match: {match_link}")

        try:
            await page.goto(match_link, timeout=5000, wait_until="domcontentloaded")
            match_details = await self._extract_match_details_event_header(page)

            if not match_details:
                self.logger.warning(f"No match details found for {match_link}")
                return None

            if markets:
                self.logger.info(f"Scraping markets: {markets} for sport: {sport}")
                market_data_from_extractor = await self.market_extractor.scrape_markets(
                    page=page, 
                    sport=sport, 
                    markets=markets,
                    period="FullTime",
                    scrape_odds_history=scrape_odds_history,
                    target_bookmaker=target_bookmaker
                )
                
                for market_key, odds_list in market_data_from_extractor.items():
                    # market_key is like "moneyline_market"
                    # odds_list is a list of dicts, e.g., [{"1": "1.90", "2": "1.95", "bookmaker_name": "Pinnacle", ...}]
                    
                    if sport.lower() == "baseball" and \
                       market_key == f"{BaseballMarket.MONEYLINE.value}_market" and \
                       isinstance(odds_list, list) and odds_list:
                        
                        self.logger.info(f"Processing baseball moneyline for individual bookmaker columns for {match_link}")
                        # Assuming moneyline uses "1" for home and "2" for away as per previous logic/constants
                        # These labels might need to be dynamically fetched or passed if they can vary
                        home_odds_label = "1" 
                        away_odds_label = "2"

                        for bookmaker_odds_data in odds_list:
                            if isinstance(bookmaker_odds_data, dict):
                                bookmaker_name = bookmaker_odds_data.get("bookmaker_name")
                                home_odds_value = bookmaker_odds_data.get(home_odds_label)
                                away_odds_value = bookmaker_odds_data.get(away_odds_label)

                                if bookmaker_name and home_odds_value is not None and away_odds_value is not None:
                                    sanitized_name = self._sanitize_bookmaker_name(bookmaker_name)
                                    match_details[f"home_odds_{sanitized_name}"] = home_odds_value
                                    match_details[f"away_odds_{sanitized_name}"] = away_odds_value
                                    # Optionally, store other info like period per bookmaker if needed
                                    # match_details[f"period_{sanitized_name}"] = bookmaker_odds_data.get("period")
                                else:
                                    self.logger.warning(f"Skipping bookmaker due to missing name or odds in baseball moneyline: {bookmaker_odds_data}")
                        # After processing, we might not want to add the original market_key to match_details
                        # if it contains redundant or differently structured data.
                        # For now, this means baseball moneyline_market will not be added if processed this way.
                    else:
                        # For other markets, or if baseball moneyline wasn't processed above, keep them nested
                        match_details[market_key] = odds_list
            
            return match_details

        except Error as e:
            self.logger.error(f"Error scraping match data from {match_link}: {e}")
            return None

    async def _extract_match_details_event_header(    
        self, 
        page: Page
    ) -> Optional[Dict[str, Any]]:
        """
        Extract match details such as date, teams, and scores from the react event header.

        Args:
            page (Page): A Playwright Page instance for this task.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing match details, or None if header is is not found.
        """
        try:
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            script_tag = soup.find('div', id='react-event-header')

            if not script_tag:
                self.logger.error("Error: Couldn't find the JSON-LD script tag.")
                return None
        
            try:
                json_data = json.loads(script_tag.get('data'))

            except (TypeError, json.JSONDecodeError):
                self.logger.error("Error: Failed to parse JSON data.")
                return None

            event_body = json_data.get("eventBody", {})
            event_data = json_data.get("eventData", {})
            unix_timestamp = event_body.get("startDate")

            match_date = (
                datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
                if unix_timestamp
                else None
            )

            return {
                "scraped_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z"),
                "match_date": match_date,
                "home_team": event_data.get("home"),
                "away_team": event_data.get("away"),
                "league_name": event_data.get("tournamentName"),
                "home_score": event_body.get("homeResult"),
                "away_score": event_body.get("awayResult"),
                "partial_results": event_body.get("partialresult"),
                "venue": event_body.get("venue"),
                "venue_town": event_body.get("venueTown"),
                "venue_country": event_body.get("venueCountry"),
            }
        
        except Exception as e:
            self.logger.error(f"Error extracting match details while parsing React event Header: {e}")
            return None