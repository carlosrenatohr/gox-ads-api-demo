from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import health, ads, totals
from app.core.errors import google_ads_exception_handler
from google.ads.googleads.errors import GoogleAdsException

load_dotenv()

# App config
app = FastAPI(
    title="GrowthOptix - Google Ads API",
    description="Sample API to get data from Google Ads",
    version="1.0.0",
)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(ads.router)
app.include_router(totals.router)

# Error handling
# app.add_exception_handler(GoogleAdsException, google_ads_exception_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=4009, reload=True)