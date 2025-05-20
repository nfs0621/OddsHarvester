# Plan: Baseball Moneyline & All Over/Under Lines Scraping

This document outlines the plan to enhance the OddsHarvester scraper to:
1.  Ensure Baseball Moneyline odds are correctly scraped.
2.  Scrape all available Over/Under lines for Baseball matches.

## 1. Baseball Moneyline Odds

*   **Current Status:**
    *   **Constants:** The constant [`BaseballMarket.MONEYLINE`](src/utils/sport_market_constants.py:238) (`"moneyline"`) is defined in [`src/utils/sport_market_constants.py`](src/utils/sport_market_constants.py).
    *   **Registry:** In [`src/core/sport_market_registry.py`](src/core/sport_market_registry.py:220-222), `BaseballMarket.MONEYLINE.value` is registered with `main_market="Home/Away"` and `odds_labels=["1", "2"]`.
*   **Assessment:** The existing setup appears correct for scraping the main moneyline odds for Baseball.
*   **Action Required:** None for the Moneyline scraping mechanism itself. Ensure the CLI or calling code uses the `"moneyline"` market key when requesting these odds for Baseball.

## 2. Baseball Over/Under Odds (All Available Lines)

The goal is to scrape all Over/Under lines presented on the OddsPortal page for a Baseball match (e.g., O/U +3.5, O/U +4.5, etc.), as shown in the provided screenshot.

*   **Current Status:**
    *   **Constants:** The constant [`BaseballMarket.OVER_UNDER`](src/utils/sport_market_constants.py:239) (`"over_under"`) is defined.
    *   **Registry:** In [`src/core/sport_market_registry.py`](src/core/sport_market_registry.py:224-226), `BaseballMarket.OVER_UNDER.value` is registered with `main_market="Over/Under"` and `odds_labels=["odds_over", "odds_under"]`. The `specific_market` parameter is correctly omitted for this registration, which is suitable for our goal as the main "Over/Under" tab is clicked, and all lines are displayed directly.

*   **Core Change Required: Modify `_parse_market_odds()` in [`OddsPortalMarketExtractor.py`](src/core/odds_portal_market_extractor.py:157)**

    The primary modification will be within the `_parse_market_odds()` method.

    *   **A. Detection Logic:**
        *   Introduce a condition at the beginning of `_parse_market_odds()` to check if the current context is for Baseball and the "Over/Under" market.
        *   This might involve passing `sport` (e.g., `Sport.BASEBALL.value`) and `main_market_key` (e.g., `BaseballMarket.OVER_UNDER.value`) from `extract_market_odds()` down to `_parse_market_odds()`.

    *   **B. Multi-Line Parsing Logic (if Baseball Over/Under):**
        *   If the condition in (A) is true, the method will switch to a new parsing strategy:
            1.  **Identify Line Grouping Elements:** Instead of immediately looking for bookmaker rows (`div` with class `border-black-borders flex h-9`), the parser will first identify the distinct HTML elements/sections on the page that each represent a single Over/Under line (e.g., the container for "Over/Under +3.5", then the container for "Over/Under +4.5", etc.). A new CSS selector will be needed for these parent elements.
            2.  **Iterate Through Line Groups:** Loop through each identified line-grouping element.
            3.  **Extract Line Value:** From each line-grouping element, extract the actual line value (e.g., "3.5", "4.5"). This text is typically part of a header or title within the group.
            4.  **Parse Bookmakers Within Line Group:** *Within the current line-grouping element*, find all the bookmaker rows (using the existing selector for bookmaker blocks).
            5.  **Extract Odds for Each Bookmaker:** For each bookmaker row found:
                *   Extract the bookmaker name (as currently done).
                *   Extract the "Over" odds and "Under" odds using the `odds_labels` (`["odds_over", "odds_under"]`) provided from the registry.
                *   Construct a dictionary containing:
                    *   `"line"`: The extracted line value (from step 3).
                    *   `"bookmaker_name"`: The bookmaker's name.
                    *   `"odds_over"`: The over odds value.
                    *   `"odds_under"`: The under odds value.
                    *   `"period"`: The current period (passed into the function).
                *   Add this dictionary to the `odds_data` list (the list returned by `_parse_market_odds`).
        *   The method will continue to return `list[dict]`. For Baseball Over/Under, this list will now contain multiple entries if a bookmaker offers odds on multiple lines, or generally, one entry per bookmaker per line.

    *   **C. Preserve Existing Logic:**
        *   If the condition in (A) is false (i.e., not Baseball Over/Under), the method will execute its current parsing logic, which assumes a single set of odds per bookmaker based on the `odds_labels`.

*   **Data Structure Impact:**
    *   The data returned by `extract_market_odds()` for Baseball's "over_under" market will be a list of dictionaries, where each dictionary represents one specific line from one bookmaker. This is consistent with the method's return type annotation (`list[dict]`).
    *   Downstream processing and data storage will need to be aware that for this specific market, the list can contain multiple entries that are all part of the "Over/Under" result for the match, differentiated by the "line" value.

**Diagram of Proposed Change in `_parse_market_odds` for Baseball O/U:**

```mermaid
graph TD
    A[Start _parse_market_odds(html, period, odds_labels, sport, main_market_key)] --> B{Is sport == 'baseball' AND main_market_key == 'over_under'?};
    B -- Yes --> C[Find all O/U Line Grouping Elements (e.g., for O/U +3.5, O/U +4.5)];
    C --> D[For each Line Grouping Element];
    D --> E[Extract Line Value (e.g., "3.5") from Line Group Header];
    D --> F[Find Bookmaker Rows within this Line Group];
    F --> G[For each Bookmaker Row];
    G --> H[Extract Bookmaker Name];
    G --> I[Extract Over/Under Odds using odds_labels];
    G --> J[Create Dict: {line: E, bookmaker_name: H, odds_over: I.over, odds_under: I.under, period: period}];
    J --> K[Add Dict to overall_results_list];
    K --> G; % Loop back to next bookmaker
    G -- No more bookmakers in line group --> D; % Loop back to next line group
    D -- No more line groups --> L[Return overall_results_list];
    B -- No --> M[Execute Existing Parsing Logic (single set of odds per bookmaker based on odds_labels)];
    M --> L;
```

**No changes are anticipated for:**
*   The method signatures of `extract_market_odds` or `_parse_market_odds` in terms of required parameters (though optional parameters like `sport` and `main_market_key` might be added to `_parse_market_odds` to facilitate the conditional logic if not already implicitly available).
*   The `SportMarketRegistry` setup for Baseball Moneyline or the general Baseball Over/Under registration, as they correctly point to the "Over/Under" main tab without a `specific_market`.

This plan focuses the changes on the HTML parsing logic within `_parse_market_odds` specifically for the Baseball Over/Under scenario.