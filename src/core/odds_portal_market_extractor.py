import re, logging
from typing import Dict, Any, List
from playwright.async_api import Page
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from ..utils.sport_market_constants import Sport, BaseballMarket # Added import
from zoneinfo import ZoneInfo # Added import
from .browser_helper import BrowserHelper
from .sport_market_registry import SportMarketRegistry

class OddsPortalMarketExtractor:
    """
    Extracts betting odds data from OddsPortal using Playwright.

    This class provides methods to scrape various betting markets (e.g., 1X2, Over/Under, BTTS, ..)
    for specific match periods and bookmaker odds.
    """
    DEFAULT_TIMEOUT = 5000
    SCROLL_PAUSE_TIME = 2000 # Standard pause
    EXPANSION_PAUSE_TIME = 3000 # Longer pause after JS expansions

    def __init__(self, browser_helper: BrowserHelper):
        """
        Initialize OddsPortalMarketExtractor.

        Args:
            browser_helper (BrowserHelper): Helper class for browser interactions.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.browser_helper = browser_helper
    
    async def scrape_markets(
        self, 
        page: Page, 
        sport: str,
        markets: List[str],
        period: str = "FullTime",
        scrape_odds_history: bool = False,
        target_bookmaker: str | None = None
    ) -> Dict[str, Any]:
        """
        Extract market data for a given match.

        Args:
            page (Page): A Playwright Page instance for this task.
            sport (str): The sport to scrape odds for.
            markets (List[str]): A list of markets to scrape (e.g., ['1x2', 'over_under_2_5']).
            period (str): The match period (e.g., "FullTime").
            scrape_odds_history (bool): Whether to extract historic odds evolution.
            target_bookmaker (str): If set, only scrape odds for this bookmaker.

        Returns:
            Dict[str, Any]: A dictionary containing market data.
        """
        market_data = {}
        # The get_market_mapping now returns a callable that already has sport and market_key bound if needed by create_market_lambda
        market_methods = SportMarketRegistry.get_market_mapping(sport)


        for market_key_from_registry in markets: # market here is actually market_key like 'moneyline', 'over_under'
            try:
                if market_key_from_registry in market_methods:
                    self.logger.info(f"Scraping market: {market_key_from_registry} (Period: {period}) for sport {sport}")
                    # The lambda now correctly passes sport and market_key to extract_market_odds if needed
                    market_data[f"{market_key_from_registry}_market"] = await market_methods[market_key_from_registry](self, page, period, scrape_odds_history, target_bookmaker)
                else:
                    self.logger.warning(f"Market key '{market_key_from_registry}' is not supported for sport '{sport}'.")

            except Exception as e:
                self.logger.error(f"Error scraping market key '{market_key_from_registry}': {e}")
                market_data[f"{market_key_from_registry}_market"] = None
        
        return market_data

    async def extract_market_odds(
        self,
        page: Page,
        main_market: str, # e.g. "Over/Under" (tab name)
        specific_market: str = None, # e.g. "Over/Under 2.5" (sub-market text, if applicable)
        period: str = "FullTime",
        odds_labels: list = None, # For generic parsing path
        scrape_odds_history: bool = False,
        target_bookmaker: str | None = None,
        sport: str | None = None,      # Added: e.g., Sport.BASEBALL.value
        market_key: str | None = None  # Added: e.g., BaseballMarket.OVER_UNDER.value
    ) -> list:
        """
        Extracts odds for a given main market and optional specific sub-market.
        For Baseball Over/Under, it will attempt to expand all collapsed line items using JavaScript.
        """
        self.logger.info(f"Extracting odds for main_market: '{main_market}', specific_market: '{specific_market}', period: '{period}', sport: '{sport}', market_key: '{market_key}'")

        try:
            # Navigate to the main market tab
            if not await self.browser_helper.navigate_to_market_tab(page=page, market_tab_name=main_market, timeout=self.DEFAULT_TIMEOUT):
                self.logger.error(f"Failed to find or click '{main_market}' tab")
                return []

            # If a specific sub-market needs to be selected (e.g., for "Over/Under 2.5" AFTER clicking "Over/Under" tab)
            # This block is NOT for Baseball Over/Under (all lines) which gets HTML for all lines after one tab click.
            if specific_market and not (sport == Sport.BASEBALL.value and market_key == BaseballMarket.OVER_UNDER.value):
                self.logger.info(f"Attempting to select specific sub-market: '{specific_market}'")
                if not await self.browser_helper.scroll_until_visible_and_click_parent(
                    page=page,
                    selector='div.flex.w-full.items-center.justify-start.pl-3.font-bold p', # Generic selector for sub-market text
                    text=specific_market
                ):
                    self.logger.error(f"Failed to find or select specific sub-market '{specific_market}' within '{main_market}'")
                    return []
            
            # Special handling for Baseball Over/Under to expand all lines
            if sport == Sport.BASEBALL.value and market_key == BaseballMarket.OVER_UNDER.value:
                self.logger.info("Baseball Over/Under market detected. Attempting to expand all collapsed rows via JavaScript.")
                await page.wait_for_timeout(self.SCROLL_PAUSE_TIME) # Wait for initial tab content

                js_expand_all_ou_rows = """
                async () => {
                    const rows = document.querySelectorAll('div[data-testid="over-under-collapsed-row"]');
                    let clickedCount = 0;
                    if (rows.length === 0) {
                        console.warn('No "over-under-collapsed-row" elements found to click.');
                        return 0;
                    }
                    console.log(`Found ${rows.length} "over-under-collapsed-row" elements.`);
                    for (const row of rows) {
                        if (row && typeof row.click === 'function') {
                            row.click();
                            clickedCount++;
                            // Small delay to allow UI to update if necessary, though often not needed with Playwright's sync
                            // await new Promise(resolve => setTimeout(resolve, 50)); 
                        } else {
                            console.warn('Found a row, but it was null or had no click function:', row);
                        }
                    }
                    return clickedCount;
                }
                """
                try:
                    clicked_count = await page.evaluate(js_expand_all_ou_rows)
                    self.logger.info(f"JavaScript executed: Clicked {clicked_count} O/U collapsed rows.")
                    await page.wait_for_timeout(self.EXPANSION_PAUSE_TIME) # Wait for expansions to complete and content to load
                except Exception as js_ex:
                    self.logger.error(f"Error executing JavaScript to expand O/U rows: {js_ex}", exc_info=True)
            else:
                 await page.wait_for_timeout(self.SCROLL_PAUSE_TIME) # Standard wait for other markets

            html_content = await page.content()
            
            odds_data = await self._parse_market_odds(
                html_content=html_content, 
                period=period, 
                odds_labels=odds_labels, 
                target_bookmaker=target_bookmaker,
                sport=sport, 
                market_key=market_key
            )

            if scrape_odds_history:
                self.logger.info("Fetching odds history for all parsed bookmakers.")
                for odds_entry in odds_data: 
                    bookmaker_name = odds_entry.get("bookmaker_name")
                    if not bookmaker_name:
                        self.logger.warning(f"Skipping odds history for entry missing 'bookmaker_name': {odds_entry}")
                        continue

                    if target_bookmaker and bookmaker_name.lower() != target_bookmaker.lower():                    
                        continue
                    
                    modals = await self._extract_odds_history_for_bookmaker(page, bookmaker_name)
                    if modals:
                        all_histories = []
                        for modal_html in modals:
                            parsed_history = self._parse_odds_history_modal(modal_html)
                            if parsed_history:
                                all_histories.append(parsed_history)
                        odds_entry["odds_history_data"] = all_histories

            if specific_market and not (sport == Sport.BASEBALL.value and market_key == BaseballMarket.OVER_UNDER.value):
                self.logger.info(f"Closing specific sub-market: {specific_market}")
                if not await self.browser_helper.scroll_until_visible_and_click_parent(
                    page=page,
                    selector='div.flex.w-full.items-center.justify-start.pl-3.font-bold p',
                    text=specific_market
                ):
                    self.logger.warning(f"Failed to close specific sub-market '{specific_market}', might affect next scraping.")

            return odds_data

        except Exception as e:
            self.logger.error(f"Error extracting odds for main_market '{main_market}', specific_market '{specific_market}': {e}", exc_info=True)
            return []

    async def _parse_market_odds(
        self, 
        html_content: str, 
        period: str, 
        odds_labels: list, # For generic path
        target_bookmaker: str | None = None,
        sport: str | None = None,
        market_key: str | None = None
    ) -> list:
        """
        Parses odds for a given market type. Uses specific logic for Baseball Over/Under,
        and generic logic for other markets.
        """
        self.logger.info(f"Parsing odds from HTML. Sport: {sport}, Market Key: {market_key}, Period: {period}")
        soup = BeautifulSoup(html_content, "lxml")
        odds_data = [] # Initialize for both paths

        if sport == Sport.BASEBALL.value and market_key == BaseballMarket.OVER_UNDER.value:
            self.logger.info("Applying special parsing for Baseball Over/Under - All Lines.")
            # These are the clickable rows for each O/U line (e.g., "Over/Under +5", "Over/Under +5.5")
            line_header_rows = soup.select('div[data-testid="over-under-collapsed-row"]')
            
            if not line_header_rows:
                self.logger.warning('Found 0 O/U line header rows (div[data-testid="over-under-collapsed-row"]).')
                return odds_data

            self.logger.info(f"Found {len(line_header_rows)} O/U line header rows.")

            for header_row in line_header_rows:
                # Extract the line value (e.g., "5", "5.5")
                option_box = header_row.select_one('div[data-testid="over-under-collapsed-option-box"]')
                if not option_box:
                    self.logger.warning(f"Could not find option_box in header_row: {header_row.get_text(strip=True, limit=60)}")
                    continue

                line_text_full = ""
                # Try desktop version first (p.max-sm\:!hidden), then mobile/alternative (p.breadcrumbs-m\:!hidden)
                line_p_desktop = option_box.select_one('p.max-sm\\:\\!hidden') # Escaped !
                if line_p_desktop and line_p_desktop.get_text(strip=True):
                    line_text_full = line_p_desktop.get_text(strip=True)
                else:
                    line_p_mobile = option_box.select_one('p.breadcrumbs-m\\:\\!hidden') # Escaped !
                    if line_p_mobile and line_p_mobile.get_text(strip=True):
                         line_text_full = line_p_mobile.get_text(strip=True)
                    else: # Fallback to any <p> if specific ones fail
                        all_p_tags = option_box.select('p')
                        if all_p_tags:
                            line_text_full = all_p_tags[0].get_text(strip=True) # Take the first one

                if not line_text_full:
                    self.logger.warning(f"Could not extract line text from option_box in {header_row.get_text(strip=True, limit=60)}")
                    continue
                
                line_value_match = re.search(r'([+-]?\d+\.?\d*)\s*$', line_text_full)
                if not line_value_match:
                    self.logger.warning(f"Could not parse line value from '{line_text_full}' in header: {header_row.get_text(strip=True, limit=60)}")
                    continue
                line_value_str = line_value_match.group(1)
                self.logger.info(f"Processing O/U line: {line_value_str} from text '{line_text_full}'")

                # The expanded content with bookmaker rows is in the next sibling div of the header_row,
                # which has a 'flex-col' class, and within that, another div often holds the table.
                expanded_section_div = header_row.find_next_sibling('div', class_=lambda c: c and 'flex-col' in c.split())
                
                if not expanded_section_div:
                    # This line was likely not expanded by Puppeteer/JS, or structure is different
                    self.logger.info(f"No expanded_section_div (next sibling with 'flex-col') found for O/U line {line_value_str}. This might indicate the row was not expanded or is not present.")
                    continue
                
                # Bookmaker rows are div[data-testid="over-under-expanded-row"] within this expanded_section_div
                bookmaker_rows_for_this_line = expanded_section_div.select('div[data-testid="over-under-expanded-row"]')
                
                if not bookmaker_rows_for_this_line:
                    self.logger.info(f"No bookmaker rows (div[data-testid='over-under-expanded-row']) found for O/U line {line_value_str} in its expanded section.")
                    continue
                
                self.logger.info(f"Found {len(bookmaker_rows_for_this_line)} bookmaker rows for O/U line {line_value_str}.")

                for row_element in bookmaker_rows_for_this_line:
                    bookmaker_name_element = row_element.select_one('p[data-testid="outrights-expanded-bookmaker-name"]')
                    bookmaker_name = bookmaker_name_element.get_text(strip=True) if bookmaker_name_element else "Unknown"

                    if target_bookmaker and bookmaker_name.lower() != target_bookmaker.lower():
                        continue 
                    
                    odds_containers = row_element.select('div[data-testid="odd-container"]')
                    
                    if len(odds_containers) == 2:
                        over_odds_p = odds_containers[0].select_one('p')
                        under_odds_p = odds_containers[1].select_one('p')

                        over_odds_str = over_odds_p.get_text(strip=True) if over_odds_p else None
                        under_odds_str = under_odds_p.get_text(strip=True) if under_odds_p else None
                        
                        if over_odds_str and under_odds_str:
                            odds_data.append({
                                "line": line_value_str,
                                "bookmaker_name": bookmaker_name, 
                                "over_odds": over_odds_str,      
                                "under_odds": under_odds_str,    
                                "period": period
                            })
                            self.logger.debug(f"Added O/U: Line {line_value_str}, Bookie: {bookmaker_name}, Over: {over_odds_str}, Under: {under_odds_str}")
                        else:
                            self.logger.warning(f"Missing odds text for {bookmaker_name} on O/U line {line_value_str}.")
                    else:
                        self.logger.warning(f"Could not find 2 odds containers for {bookmaker_name} on O/U line {line_value_str}. Found: {len(odds_containers)}")
            
            if not odds_data:
                self.logger.warning("No market odds data was extracted for Baseball Over/Under after processing all headers.")
            return odds_data
        
        else: # Generic parsing logic
            self.logger.info("Applying generic odds parsing logic.")
            bookmaker_blocks = soup.find_all("div", class_=re.compile(r"^border-black-borders flex h-9")) 

            if not bookmaker_blocks:
                self.logger.warning("No bookmaker blocks found for generic parsing.")
                return odds_data 

            for block in bookmaker_blocks:
                try:
                    img_tag = block.find("img", class_="bookmaker-logo")
                    bookmaker_name = img_tag["title"] if img_tag and "title" in img_tag.attrs else "Unknown"
        
                    if not bookmaker_name or (target_bookmaker and bookmaker_name.lower() != target_bookmaker.lower()):
                        continue
                    
                    odds_value_blocks = block.find_all("div", class_=re.compile(r"flex-center.*flex-col.*font-bold"))

                    if not odds_labels:
                        self.logger.error("odds_labels not provided for generic parsing. Cannot proceed.")
                        continue 

                    if len(odds_value_blocks) < len(odds_labels):
                        self.logger.warning(f"Incomplete odds data for bookmaker: {bookmaker_name} (expected {len(odds_labels)} labels, got {len(odds_value_blocks)} odds blocks). Skipping...")
                        continue

                    extracted_odds_values = {label: odds_value_blocks[i].get_text(strip=True) for i, label in enumerate(odds_labels)}

                    for key, value in extracted_odds_values.items():
                        extracted_odds_values[key] = re.sub(r"(\d+\.\d+)\1", r"\1", value)
                    
                    extracted_odds_values["bookmaker_name"] = bookmaker_name 
                    extracted_odds_values["period"] = period
                    odds_data.append(extracted_odds_values)

                except Exception as e:
                    self.logger.error(f"Error parsing generic odds for a block: {e}", exc_info=True)
                    continue
            
            self.logger.info(f"Successfully parsed generic odds for {len(odds_data)} bookmakers.")
            return odds_data

    async def _extract_odds_history_for_bookmaker(
        self, 
        page: Page, 
        bookmaker_name: str
    ) -> List[str]:
        """
        Hover on odds for a specific bookmaker to trigger and capture the odds history modal.
        """
        self.logger.info(f"Extracting odds history for bookmaker: {bookmaker_name}")
        await page.wait_for_timeout(self.SCROLL_PAUSE_TIME)

        modals_data = []
        # Selector for bookmaker rows - needs to be robust for both generic and O/U expanded views
        # For generic, it's 'div.border-black-borders.flex.h-9'
        # For O/U expanded, it's 'div[data-testid="over-under-expanded-row"]'
        # We might need to try both or pass context. For now, assume generic for history.
        # If history is needed for O/U, this part might need adjustment or context.
        
        # Attempting a more generic selector that might cover both if structure is similar enough
        # or prioritize the one most likely to contain the logo and odds blocks for hovering.
        # The key is that `row.query_selector("img.bookmaker-logo")` and `row.query_selector_all("div.flex-center.flex-col.font-bold")`
        # must work within the selected `rows`.
        
        # Using the original generic selector for now, as history is usually on main market views.
        rows = await page.query_selector_all('div.border-black-borders.flex.h-9, div[data-testid="over-under-expanded-row"]')


        for row in rows:
            try:
                # Try to find bookmaker name from either common logo or specific testid
                logo_img = await row.query_selector("img.bookmaker-logo")
                title = None
                if logo_img:
                    title = await logo_img.get_attribute("title")
                else: # Fallback for O/U expanded rows if logo isn't there
                    bookmaker_name_element = await row.query_selector('p[data-testid="outrights-expanded-bookmaker-name"]')
                    if bookmaker_name_element:
                        title = await bookmaker_name_element.inner_text()


                if title and bookmaker_name.lower() in title.lower():
                    self.logger.info(f"Found matching bookmaker row for history: {title}")
                    # Odds blocks selector needs to be general enough or conditional
                    # Original: "div.flex-center.flex-col.font-bold"
                    # For O/U: 'div[data-testid="odd-container"] p' (but we need to hover the container or p)
                    
                    # Let's try to hover on the odds containers themselves if they exist, else the old way
                    odds_to_hover = []
                    ou_odds_containers = await row.query_selector_all('div[data-testid="odd-container"]')
                    if ou_odds_containers:
                        odds_to_hover.extend(ou_odds_containers)
                    else:
                        generic_odds_blocks = await row.query_selector_all("div.flex-center.flex-col.font-bold")
                        odds_to_hover.extend(generic_odds_blocks)

                    if not odds_to_hover:
                        self.logger.warning(f"No odds elements found to hover for bookmaker {title}")
                        continue

                    for odds_element in odds_to_hover:
                        try:
                            await odds_element.hover(timeout=5000) # Increased hover timeout
                            # Wait for modal to appear after hover
                            # Using a more specific selector for the modal's content
                            await page.wait_for_selector("div[id^='radix-'] h3:text('Odds movement')", timeout=5000) # Radix UI often used for modals
                            
                            # Get the modal content. The modal is usually a sibling or a specific overlay.
                            # This assumes the modal is structured with 'Odds movement' h3 and its parent is the main modal body.
                            modal_content_element = await page.query_selector("div[id^='radix-']:has(h3:text('Odds movement'))")

                            if modal_content_element:
                                html = await modal_content_element.inner_html()
                                modals_data.append(html)
                                self.logger.debug(f"Captured odds history modal HTML for {title}")
                                # It's good practice to move the mouse away to close the modal if it persists
                                # body_element = await page.query_selector('body')
                                # if body_element:
                                # await body_element.hover() # Move mouse to body to potentially close modal
                                # await page.wait_for_timeout(500) # Brief pause
                            else:
                                self.logger.warning(f"Unable to retrieve odds' evolution modal content for {title}")
                        except Exception as hover_ex:
                            self.logger.warning(f"Error hovering or waiting for modal for {title} on an odds element: {hover_ex}")
            
            except Exception as e:
                self.logger.warning(f"Failed to process a bookmaker row for history: {e}")

        return modals_data

    def _parse_odds_history_modal(self, modal_html: str) -> dict:
        """
        Parses the HTML content of an odds history modal.
        """
        self.logger.info("Parsing modal content for odds history.")
        soup = BeautifulSoup(modal_html, "lxml")

        try:
            odds_history = []
            # Updated selectors based on potential Radix UI structure, more robust
            history_entries = soup.select("div > div > div.flex.items-center.justify-between") # Common pattern for rows in Radix modals

            if not history_entries: # Fallback to old selectors if new ones don't work
                 timestamps = soup.select("div.flex.flex-col.gap-1 > div.flex.gap-3 > div.font-normal")
                 odds_values_elements = soup.select("div.flex.flex-col.gap-1 + div.flex.flex-col.gap-1 > div.font-bold") # Corrected this
            else: # Process new structure
                timestamps = [entry.select_one("div.text-xs") for entry in history_entries] # Assuming time is in a div with text-xs
                odds_values_elements = [entry.select_one("div.font-bold") for entry in history_entries] # Assuming odds value is in a div with font-bold


            year_to_use = datetime.now(timezone.utc).year

            for ts_element, odd_element in zip(timestamps, odds_values_elements):
                if not ts_element or not odd_element: continue # Skip if elements are missing

                time_text = ts_element.get_text(strip=True)
                odd_val_text = odd_element.get_text(strip=True)
                try:
                    dt_naive = datetime.strptime(time_text, "%d %b, %H:%M")
                    dt_utc_aware = dt_naive.replace(year=year_to_use, tzinfo=timezone.utc)
                    
                    try:
                        dt_edmonton = dt_utc_aware.astimezone(ZoneInfo("America/Edmonton"))
                        formatted_time = dt_edmonton.isoformat()
                    except Exception as tz_error:
                        self.logger.warning(f"ZoneInfo error: {tz_error}. Falling back to UTC-7 offset for Edmonton time.")
                        from datetime import timedelta
                        mtn_offset = timedelta(hours=-7) 
                        dt_edmonton_approx = dt_utc_aware.astimezone(timezone(mtn_offset))
                        formatted_time = dt_edmonton_approx.isoformat()
                        
                except ValueError:
                    self.logger.warning(f"Failed to parse datetime: {time_text}")
                    continue

                odds_history.append({
                    "timestamp": formatted_time,
                    "odds": float(odd_val_text)
                })

            opening_odds_data = None
            # Selector for opening odds might also change with Radix, look for "Opening odds" text
            opening_odds_header = soup.find(lambda tag: tag.name == "p" and "Opening odds" in tag.get_text())
            if opening_odds_header:
                opening_odds_block = opening_odds_header.find_next_sibling("div") # Assuming data is in next div
                if opening_odds_block:
                    opening_ts_div = opening_odds_block.select_one("div.text-xs") # Similar to history
                    opening_val_div = opening_odds_block.select_one("div.font-bold") # Similar to history

                    if opening_ts_div and opening_val_div:
                        try:
                            opening_time_text = opening_ts_div.get_text(strip=True)
                            opening_val_text = opening_val_div.get_text(strip=True)
                            dt_naive = datetime.strptime(opening_time_text, "%d %b, %H:%M")
                            dt_utc_aware = dt_naive.replace(year=year_to_use, tzinfo=timezone.utc)
                            
                            try:
                                dt_edmonton = dt_utc_aware.astimezone(ZoneInfo("America/Edmonton"))
                                opening_formatted_time = dt_edmonton.isoformat()
                            except Exception as tz_error:
                                self.logger.warning(f"ZoneInfo error for opening odds: {tz_error}. Using UTC-7 offset.")
                                from datetime import timedelta
                                mtn_offset = timedelta(hours=-7)
                                dt_edmonton_approx = dt_utc_aware.astimezone(timezone(mtn_offset))
                                opening_formatted_time = dt_edmonton_approx.isoformat()
                                
                            opening_odds_data = {
                                "timestamp": opening_formatted_time,
                                "odds": float(opening_val_text)
                            }
                        except ValueError:
                            self.logger.warning(f"Failed to parse opening odds timestamp: {opening_time_text if 'opening_time_text' in locals() else 'N/A'}")
                    else:
                        self.logger.warning("Could not find opening odds timestamp or value elements in modal (new structure).")
                else:
                    self.logger.warning("Could not find opening odds block (div after header) in modal (new structure).")
            else: # Fallback to old opening odds parsing
                old_opening_odds_block = soup.select_one("div.mt-2.gap-1") 
                if old_opening_odds_block:
                    opening_ts_div = old_opening_odds_block.select_one("div.flex.gap-1 div") 
                    opening_val_div = old_opening_odds_block.select_one("div.flex.gap-1 .font-bold")
                    if opening_ts_div and opening_val_div:
                         # ... (rest of old parsing logic for opening_odds)
                        try:
                            opening_time_text = opening_ts_div.get_text(strip=True)
                            opening_val_text = opening_val_div.get_text(strip=True)
                            dt_naive = datetime.strptime(opening_time_text, "%d %b, %H:%M")
                            # ... (rest of datetime conversion as above) ...
                            dt_utc_aware = dt_naive.replace(year=year_to_use, tzinfo=timezone.utc)
                            try:
                                dt_edmonton = dt_utc_aware.astimezone(ZoneInfo("America/Edmonton"))
                                opening_formatted_time = dt_edmonton.isoformat()
                            except Exception: # Simplified fallback
                                from datetime import timedelta
                                mtn_offset = timedelta(hours=-7)
                                dt_edmonton_approx = dt_utc_aware.astimezone(timezone(mtn_offset))
                                opening_formatted_time = dt_edmonton_approx.isoformat()

                            opening_odds_data = {
                                "timestamp": opening_formatted_time,
                                "odds": float(opening_val_text)
                            }
                        except ValueError:
                             self.logger.warning(f"Failed to parse opening odds timestamp (old structure): {opening_time_text if 'opening_time_text' in locals() else 'N/A'}")
                    else:
                        self.logger.warning("Could not find opening odds timestamp/value (old structure).")
                else:
                    self.logger.warning("Could not find any opening odds block in modal.")


            return {
                "odds_history": odds_history,
                "opening_odds": opening_odds_data
            }

        except Exception as e:
            self.logger.error(f"Failed to parse odds history modal: {e}", exc_info=True)
            return {}