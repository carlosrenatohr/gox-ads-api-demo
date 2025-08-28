from fastapi import APIRouter, Depends, HTTPException
from google.ads.googleads.client import GoogleAdsClient
# from google.ads.googleads.errors import GoogleAdsException

from app.core.ads_client import get_google_ads_client, get_default_customer_id

router = APIRouter(prefix="", tags=["Google Ads"])

# List accessible customers
# GET /
# Returns:
# - status: success
# - customers: list of customer IDs
# - message: instructions to pick one of the customer IDs
@router.get("/")
async def list_accessible_customers(client: GoogleAdsClient = Depends(get_google_ads_client)):
    try:
        customer_service = client.get_service("CustomerService")
        response = customer_service.list_accessible_customers()
        customers = [{"customer_id": rn.split("/")[-1]} for rn in response.resource_names]
        return {
            "status": "success",
            "customers": customers,
            "message": "Pick one of these customer IDs for the /campaigns endpoint",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "details": str(e)})

# List campaigns
# GET /campaigns/
# GET /campaigns/{customer_id}
# Returns:
# - status: success
# - campaigns: list of campaigns
# - message: instructions to pick one of the campaigns
# ---
# List campaigns for the default customer ID
# GET /campaigns/
# Returns:
# - status: success
# - campaigns: list of campaigns
# - message: instructions to pick one of the campaigns
# ---
@router.get("/campaigns/")
@router.get("/campaigns/{customer_id}")
async def get_campaigns(
    customer_id: str | None = None,
    client: GoogleAdsClient = Depends(get_google_ads_client),
):
    try:
        if not customer_id:
            customer_id = get_default_customer_id()
        ga_service = client.get_service("GoogleAdsService")
        query = """
            SELECT campaign.id, campaign.name
            FROM campaign
            ORDER BY campaign.id
        """

        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        campaigns = []
        for batch in stream:
            for row in batch.results:
                campaigns.append({"id": row.campaign.id, "name": row.campaign.name})
        return {"status": "success", "campaigns": campaigns}

    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "details": str(e)})
