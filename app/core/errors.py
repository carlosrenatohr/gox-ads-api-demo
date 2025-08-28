from fastapi import Request
from fastapi.responses import JSONResponse
from google.ads.googleads.errors import GoogleAdsException

async def google_ads_exception_handler(request: Request, exc: GoogleAdsException):
    errors = [{"message": e.message} for e in exc.failure.errors]
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "details": errors,
        },
    )
