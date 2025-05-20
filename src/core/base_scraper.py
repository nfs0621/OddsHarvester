import logging, re, json, asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo  # Added import for timezone conversion
from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError, Error
from .playwright_manager import PlaywrightManager
from .browser_helper import BrowserHelper
from .odds_portal_market_extractor import OddsPortalMarketExtractor
from ..utils.constants import ODDSPORTAL_BASE_URL, ODDS_FORMAT, SCRAPE_CONCURRENCY_TASKS # Changed to relative
from ..utils.sport_market_constants import BaseballMarket # Changed to relative

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

    def _determine_game_type(self, match_link: str, tournament_name: str, season_type: str = None, tournament_stage: str = None) -> str:
        """
        Determine the type of game (regular season, playoffs, preseason, etc.) 
        based on the match URL, tournament name, season type, and tournament stage.
        
        Args:
            match_link (str): The URL of the match page
            tournament_name (str): The name of the tournament/league
            season_type (str, optional): The season type if available from the JSON data
            tournament_stage (str, optional): The tournament stage if available from the JSON data
            
        Returns:
            str: The determined game type
        """
        # Add debug logging to track classification decisions
        self.logger.debug(f"Determining game type for match: {match_link}")
        self.logger.debug(f"Input data: season_type={season_type}, tournament_name={tournament_name}, tournament_stage={tournament_stage}")
        
        # Convert inputs to lowercase for easier matching
        link_lower = match_link.lower() if match_link else ""
        tournament_lower = tournament_name.lower() if tournament_name else ""
        season_type_lower = season_type.lower() if season_type else ""
        tournament_stage_lower = tournament_stage.lower() if tournament_stage else ""
        
        # Check for MLB-specific identifiers
        if "baseball/usa/mlb" in link_lower:
            # 1. Check tournament stage first (most specific)
            if tournament_stage_lower:
                self.logger.debug(f"Checking tournament stage: {tournament_stage_lower}")
                if any(term in tournament_stage_lower for term in ["playoff", "post", "world series", "wild card", "championship series", "division series"]):
                    self.logger.debug("Classified as playoffs based on tournament stage")
                    return "playoffs"
                elif any(term in tournament_stage_lower for term in ["spring training", "pre", "exhibition"]):
                    self.logger.debug("Classified as preseason based on tournament stage")
                    return "preseason"
                elif "all-star" in tournament_stage_lower or "all star" in tournament_stage_lower:
                    self.logger.debug("Classified as exhibition based on tournament stage (All-Star)")
                    return "exhibition"
            
            # 2. Then check season type
            if season_type_lower:
                self.logger.debug(f"Checking season type: {season_type_lower}")
                if any(term in season_type_lower for term in ["playoff", "post"]):
                    self.logger.debug("Classified as playoffs based on season type")
                    return "playoffs"
                elif any(term in season_type_lower for term in ["pre", "spring"]):
                    self.logger.debug("Classified as preseason based on season type")
                    return "preseason"
            
            # 3. Then check tournament name
            self.logger.debug(f"Checking tournament name: {tournament_lower}")
            if tournament_lower:
                if "spring training" in tournament_lower:
                    self.logger.debug("Classified as preseason based on tournament name (Spring Training)")
                    return "preseason"
                elif "all-star" in tournament_lower or "all star" in tournament_lower:
                    self.logger.debug("Classified as exhibition based on tournament name (All-Star)")
                    return "exhibition"
                elif any(term in tournament_lower for term in ["world series", "playoff", "postseason", "wild card", "division series", "championship series"]):
                    self.logger.debug("Classified as playoffs based on tournament name")
                    return "playoffs"
            
            # 4. Then check URL for specific patterns
            self.logger.debug(f"Checking URL: {link_lower}")
            # Extract the specific part of the URL after mlb-year/
            mlb_part_match = re.search(r'mlb-[0-9]{4}/([^/]+)', link_lower)
            if mlb_part_match:
                mlb_specific_part = mlb_part_match.group(1)
                self.logger.debug(f"Extracted MLB-specific URL part: {mlb_specific_part}")
                
                if any(term in mlb_specific_part for term in ["playoff", "post-season", "world-series", "wild-card", "division-series", "championship-series"]):
                    self.logger.debug("Classified as playoffs based on URL specific part")
                    return "playoffs"
                elif "spring-training" in mlb_specific_part:
                    self.logger.debug("Classified as preseason based on URL specific part (Spring Training)")
                    return "preseason"
                elif "all-star" in mlb_specific_part:
                    self.logger.debug("Classified as exhibition based on URL specific part (All-Star)")
                    return "exhibition"
        
        # General pattern matching (for all sports)
        # Game type patterns to check
        game_type_patterns = {
            "playoffs": [
                "playoff", "post-season", "postseason", "world series", "wild card", "wildcard",
                "division series", "championship series", "final", "finals", "semifinal"
            ],
            "preseason": [
                "pre-season", "preseason", "spring training", "exhibition game", "warm-up",
                "preparatory", "friendly match"
            ],
            "exhibition": [
                "exhibition", "all-star", "all star", "all-stars", "friendly", "charity",
                "showcase", "celebrity", "demo", "demonstration"
            ],
            "qualification": [
                "qualification", "qualifier", "qualifying", "prelim", "preliminary",
                "play-in", "play in", "knockout stage", "group stage"
            ]
        }
        
        # Check URL and tournament name for patterns
        for game_type, patterns in game_type_patterns.items():
            for pattern in patterns:
                if (pattern in link_lower) or (tournament_lower and pattern in tournament_lower):
                    self.logger.debug(f"Classified as {game_type} based on pattern '{pattern}' found in URL or tournament name")
                    return game_type
        
        # Default to regular season if no pattern matched
        self.logger.debug("No specific game type patterns found, defaulting to regular_season")
        return "regular_season"

    def _is_non_regular_season_game(self, match_link: str, tournament_name: str) -> bool:
        """
        Determine if a game is a non-regular season game (playoffs, preseason, etc.)
        by examining the match URL and tournament name.
        
        Args:
            match_link (str): The URL of the match page
            tournament_name (str): The name of the tournament/league
            
        Returns:
            bool: True if the game is a non-regular season game, False otherwise
        """
        # This method is kept for backward compatibility but its implementation is changed
        # to use _determine_game_type
        game_type = self._determine_game_type(match_link, tournament_name)
        return game_type != "regular_season"

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

            # Filter out non-regular season games if we have tournament info
            tournament_name = match_details.get("league_name")
            is_regular_season = match_details.get("is_regular_season", True)
            game_type = match_details.get("game_type", "regular_season")
            
            # No longer filtering games by type, keeping all games
            # Instead, the game_type field can be used for filtering later if needed
            
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
                
                # Log the full JSON structure for games to analyze type indicators
                # This helps debug game type classification issues
                self.logger.debug(f"Event header JSON for game type analysis: {json.dumps(json_data, indent=2)}")

            except (TypeError, json.JSONDecodeError):
                self.logger.error("Error: Failed to parse JSON data.")
                return None

            event_body = json_data.get("eventBody", {})
            event_data = json_data.get("eventData", {})
            
            # Extract all potentially useful game type indicators
            season_type = event_data.get("seasonType")
            tournament_name = event_data.get("tournamentName")
            tournament_stage = event_data.get("tournamentStage")
            
            # Use the current URL to get match_link
            match_link = page.url
            
            # Log more details to help debug game type classification
            self.logger.debug(f"Game type indicators: URL={match_link}, tournament={tournament_name}, " +
                             f"seasonType={season_type}, tournamentStage={tournament_stage}")
            
            game_type = self._determine_game_type(match_link, tournament_name, season_type, tournament_stage)
            
            # For backward compatibility, keep is_regular_season as well
            is_regular_season = (game_type == "regular_season")
            
            unix_timestamp = event_body.get("startDate")

            # Process timestamps with graceful fallback for missing tzdata
            match_date = None
            if unix_timestamp:
                # Create UTC datetime object from timestamp
                dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
                
                # Try to convert to America/Edmonton timezone with fallback for missing tzdata
                try:
                    # Attempt to use ZoneInfo for America/Edmonton
                    dt_edmonton = dt_utc.astimezone(ZoneInfo("America/Edmonton"))
                    match_date = dt_edmonton.strftime("%Y-%m-%d %H:%M:%S %Z")
                except Exception as e:
                    self.logger.warning(f"ZoneInfo error: {e}. Falling back to UTC-7 offset for Edmonton time.")
                    # Fallback to a fixed offset approximation for Edmonton (UTC-7, or UTC-6 during DST)
                    # This is an approximation - for production use, determine correct DST dates
                    # For simplicity, we'll use UTC-7 (Mountain Standard Time) year-round here
                    mtn_offset = timedelta(hours=-7)
                    dt_edmonton_approx = dt_utc.astimezone(timezone(mtn_offset))
                    match_date = dt_edmonton_approx.strftime("%Y-%m-%d %H:%M:%S GMT-0700")
                    self.logger.info("Install 'tzdata' package to fix timezone issues: 'pip install tzdata'")

            # Also convert current time for scraped_date to Edmonton timezone with fallback
            try:
                now_utc = datetime.now(timezone.utc)
                now_edmonton = now_utc.astimezone(ZoneInfo("America/Edmonton"))
                scraped_date = now_edmonton.strftime("%Y-%m-%d %H:%M:%S %Z")
            except Exception as e:
                self.logger.warning(f"ZoneInfo error for scraped_date: {e}. Falling back to UTC-7 offset.")
                # Fallback to a fixed offset approximation
                mtn_offset = timedelta(hours=-7)
                now_edmonton_approx = now_utc.astimezone(timezone(mtn_offset))
                scraped_date = now_edmonton_approx.strftime("%Y-%m-%d %H:%M:%S GMT-0700")

            return {
                "scraped_date": scraped_date,
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
                "game_type": game_type,  # Add game_type to the returned data
                "season_type": season_type,  # Add season_type to the returned data
                "is_regular_season": is_regular_season  # Keep for backward compatibility
            }
        
        except Exception as e:
            self.logger.error(f"Error extracting match details while parsing React event Header: {e}")
            return None