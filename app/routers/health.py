from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Google Ads API",
        "version": "2.0.0",
        "message": "Service is running correctly",
    }
