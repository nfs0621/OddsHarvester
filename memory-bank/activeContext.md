# Active Context

## Current Focus

- Finalize and test modifications to the scraper for extracting Baseball "Over/Under" odds from OddsPortal, ensuring all line items are expanded and parsed.
- Specifically, verify the JavaScript injection in `OddsPortalMarketExtractor` correctly expands all O/U lines.

## Recent Changes

- [`2025-05-16 22:45:00`](memory-bank/activeContext.md:1) - Updated `OddsPortalMarketExtractor` to use `page.evaluate()` with JavaScript to click and expand all `div[data-testid="over-under-collapsed-row"]` elements for Baseball O/U markets. This replaced the multi-step Puppeteer MCP approach for this specific interaction.
- Implemented new parsing logic in `_parse_market_odds` within `OddsPortalMarketExtractor` to handle the structure of expanded Baseball O/U lines.
- Updated `extract_market_odds` in `OddsPortalMarketExtractor` to pass `sport` and `market_key` to `_parse_market_odds`.
- Updated `SportMarketRegistry` to correctly pass `sport` and `market_key` via lambda to `extract_market_odds`.
- Created and configured `puppeteer-mcp-server` for dynamic page interaction (though the direct JS injection approach is now favored for O/U expansion).
- Previous task: Codebase review completed and saved to `codebase_review.md`.
- Initial Memory Bank setup.


## Open Questions/Issues

- Testing of the full Baseball Over/Under scraping process is pending.

---
*Footnotes: Initial file creation.*
*[`2025-05-16 20:07:29`](memory-bank/activeContext.md:16) - Set current focus to include Over/Under and Moneyline odds scraping.*
*[`2025-05-16 22:45:00`](memory-bank/activeContext.md:16) - Updated current focus and recent changes to reflect new JS-based expansion strategy for Baseball O/U.*