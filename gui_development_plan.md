# OddsHarvester GUI Development Plan

This document outlines the plan for developing a Graphical User Interface (GUI) for the OddsHarvester application.

## Proposed Technology Stack

1.  **Backend:** Python with **Flask** or **FastAPI**.
    *   *Reasoning:* This allows us to easily call the existing Python logic from `OddsHarvester`. FastAPI is modern and performant for API development, while Flask is lightweight and well-established.
2.  **Frontend:** **Next.js** (a React framework).
    *   *Reasoning:* Next.js provides a robust framework for building React applications, including server-side rendering and static site generation capabilities if needed in the future. It has excellent community support and integrates well with TypeScript (recommended for larger projects).
3.  **UI Components:** **ShadCN/UI**.
    *   *Reasoning:* As per user instructions, we'll use ShadCN/UI. These are beautifully designed, accessible components that can be copied and pasted into the project, giving full control over the code.
4.  **Communication:** **REST API**.
    *   *Reasoning:* The Next.js frontend will communicate with the Python backend via REST API endpoints.

## High-Level Plan

**Phase 1: Backend API Development (Python)**

1.  **Setup:** Create a new directory for the GUI (e.g., `odds_harvester_gui`) with subdirectories for `backend` and `frontend`.
2.  **API Endpoints:**
    *   Define API endpoints in the Python backend (Flask/FastAPI) that correspond to the CLI commands:
        *   `/api/scrape_upcoming` (POST)
        *   `/api/scrape_historic` (POST)
    *   These endpoints will accept JSON payloads containing the parameters currently passed as CLI flags.
3.  **Integrate Core Logic:**
    *   Refactor the existing CLI argument handling and main scraping logic in `src/main.py` and `src/cli/cli_argument_handler.py` so that it can be imported and called as functions by the API endpoints.
    *   The API will parse the incoming JSON, validate parameters, and then call these refactored functions.
4.  **Response Handling:** The API will return JSON responses indicating success, failure, or progress updates.

**Phase 2: Frontend UI Development (Next.js + ShadCN/UI)**

1.  **Project Setup:**
    *   Initialize a new Next.js project in the `odds_harvester_gui/frontend` directory.
    *   Install and configure ShadCN/UI.
2.  **Component Design & Implementation:**
    *   **Main Layout:** Create a main application layout, possibly with tabs or distinct sections for "Scrape Upcoming" and "Scrape Historic".
    *   **Input Forms:** For each command (`scrape_upcoming`, `scrape_historic`), build a form using ShadCN/UI components to capture all the necessary arguments identified in `src/cli/cli_argument_parser.py`.
        *   **Common Arguments Section (for both forms):**
            *   `match_links`: Textarea or a dynamic list input.
            *   `sport`: Select/Dropdown (from `src/cli/cli_argument_parser.py`).
            *   `league`: Text input.
            *   `markets`: Text input (e.g., for comma-separated values).
            *   `storage`: Select/Dropdown (from `src/cli/cli_argument_parser.py`).
            *   `file_path`: Text input (potentially a file picker if feasible, though direct path input is simpler).
            *   `format`: Select/Dropdown (from `src/cli/cli_argument_parser.py`).
            *   `proxies`: Textarea for list input.
            *   `browser_user_agent`: Text input.
            *   `browser_locale_timezone`: Text input.
            *   `browser_timezone_id`: Text input.
            *   `headless`: Checkbox.
            *   `save_logs`: Checkbox.
            *   `target_bookmaker`: Text input.
            *   `scrape_odds_history`: Checkbox.
        *   **"Scrape Upcoming" Specific:**
            *   `date`: Date picker component.
        *   **"Scrape Historic" Specific:**
            *   `season`: Text input (with format hint YYYY-YYYY).
            *   `max_pages`: Number input.
    *   **Action Button:** A "Start Scraping" button for each form.
    *   **Output/Status Display:** An area to display messages from the backend (e.g., "Scraping started...", "Data saved to X", error messages).
3.  **API Integration:**
    *   Implement functions to collect data from the forms.
    *   Make API calls to the Python backend when the "Start Scraping" button is clicked.
    *   Handle API responses and update the UI accordingly.
4.  **ShadCN/UI Context:**
    *   Create or update a `ShadCN-context.md` file in the root of the `OddsHarvester` project to list all ShadCN components used.

**Phase 3: Testing and Refinement**

1.  Thoroughly test the end-to-end flow: GUI input -> Backend processing -> Scraping -> Output display.
2.  Refine UI/UX based on testing.

## Workflow Diagram

```mermaid
graph TD
    A[User Enters Parameters in GUI] --> B{Selects Command Type};
    B -- Scrape Upcoming --> C[GUI: Upcoming Form];
    B -- Scrape Historic --> D[GUI: Historic Form];
    C --> E[User Clicks "Start Scraping"];
    D --> E;
    E --> F[Frontend (Next.js) sends API Request (JSON) to Backend];
    F --> G[Backend (Python API) Receives Request];
    G --> H[Backend Validates Parameters & Calls Core Scraper Logic];
    H --> I[OddsHarvester Core Scraping Functions Execute];
    I --> J[Scraping Results/Status];
    J --> K[Backend Sends API Response (JSON) to Frontend];
    K --> L[Frontend (Next.js) Displays Results/Status to User];