from fastapi import FastAPI

app = FastAPI(
    title="OddsHarvester API",
    description="API for triggering OddsHarvester scraping tasks.",
    version="0.1.0",
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to OddsHarvester API"}

# Placeholder for scrape_upcoming endpoint
@app.post("/api/scrape_upcoming")
async def scrape_upcoming_endpoint(payload: dict):
    # TODO: Implement logic to call the refactored scrape_upcoming function
    # from the core OddsHarvester application.
    # This will involve parsing the payload, validating arguments,
    # and then invoking the scraping logic.
    print(f"Received upcoming payload: {payload}")
    return {"status": "received", "command": "scrape_upcoming", "payload": payload}

# Placeholder for scrape_historic endpoint
@app.post("/api/scrape_historic")
async def scrape_historic_endpoint(payload: dict):
    # TODO: Implement logic to call the refactored scrape_historic function
    # from the core OddsHarvester application.
    # This will involve parsing the payload, validating arguments,
    # and then invoking the scraping logic.
    print(f"Received historic payload: {payload}")
    return {"status": "received", "command": "scrape_historic", "payload": payload}

if __name__ == "__main__":
    import uvicorn
    # This is for local development.
    # For production, you'd typically use a command like:
    # uvicorn odds_harvester_gui.backend.main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)