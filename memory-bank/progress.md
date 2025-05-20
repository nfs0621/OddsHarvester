# Progress Log

(Track key tasks, milestones, and their status. This helps in understanding the project's evolution and current state of work.)

- **[2025-05-16 20:00:00] - Task Started:** Enhance OddsHarvester scraper for Baseball Over/Under odds.
- **[2025-05-16 20:15:00] - Milestone:** Initial modifications to `odds_portal_market_extractor.py` and `sport_market_registry.py` for O/U parameter handling.
- **[2025-05-16 20:45:00] - Issue:** Scraper failing to find MLB match links.
- **[2025-05-16 21:00:00] - Milestone:** Resolved MLB match link issue by updating selectors and adding waits in `odds_portal_scraper.py`.
- **[2025-05-16 21:15:00] - Issue:** Difficulty parsing dynamic O/U tab content on individual match pages.
- **[2025-05-16 21:30:00] - Task Started:** Create `puppeteer-mcp-server` for dynamic content fetching.
- **[2025-05-16 22:00:00] - Milestone:** `puppeteer-mcp-server` created, built, and configured.
- **[2025-05-16 22:20:00] - Milestone:** Successfully used `puppeteer-mcp-server` to click O/U tab and first collapsed row, obtaining HTML for parsing.
- **[2025-05-16 22:30:00] - Milestone:** Developed new parsing logic for Baseball O/U in `_parse_market_odds`.
- **[2025-05-16 22:45:00] - Milestone:** Refactored `OddsPortalMarketExtractor` to use `page.evaluate()` with JavaScript for expanding all O/U lines directly within Playwright. Code updated in `odds_portal_market_extractor.py`.
- **[2025-05-16 22:26:00] - Milestone:** Corrected all relative import errors across `src/main.py`, `src/core/odds_portal_market_extractor.py`, `src/core/playwright_manager.py`, `src/core/sport_market_registry.py`, `src/core/base_scraper.py`, and `src/core/scraper_app.py`.
- **[2025-05-16 22:26:00] - Milestone:** Corrected CSS selector syntax error (`p.max-sm\\:!hidden` to `p.max-sm\\:\\!hidden`) in `src/core/odds_portal_market_extractor.py`.
- **[2025-05-16 22:26:00] - Task Completed:** Successfully tested Baseball Over/Under scraping. Scraper ran without errors and logs indicate data was extracted and saved for 30 matches.

---
*Footnotes: Initial file creation.*