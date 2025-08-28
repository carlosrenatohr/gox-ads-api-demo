from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from pathlib import Path

load_dotenv()

app = FastAPI(
    title="Google Ads API - FastAPI",
    description="API simple para obtener datos de Google Ads",
    version="1.0.0"
)

# CUSTOMER_ID = '7228068139'  # GO test account 1
CUSTOMER_ID = os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID')
CONFIG_REL_PATH = os.getenv('GOOGLE_ADS_CONFIG_FILE_PATH')

if not CUSTOMER_ID or not CONFIG_REL_PATH:
    raise ValueError("There are missing environment variables: CUSTOMER_ID or CONFIG_REL_PATH")

# Build absolute path from project root
# BASE_DIR = Path(__file__).resolve().parent.parent
# CONFIG_PATH = BASE_DIR / CONFIG_REL_PATH
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / CONFIG_REL_PATH

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint - best practices
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        dict: Service status and basic information
    """
    return {
        "status": "healthy",
        "service": "Google Ads API",
        "version": "2.0.0",
        "message": "Service is running correctly"
    }

# List accessible customers for the service account
@app.get('/')
async def list_accessible_customers():
    try:
        # Load Google Ads client from google-ads.yaml
        client = GoogleAdsClient.load_from_storage(path=str(CONFIG_PATH), version='v21')
        
        # Get CustomerService
        customer_service = client.get_service('CustomerService')
        
        # Call ListAccessibleCustomers to get all accessible customer IDs
        response = customer_service.list_accessible_customers()
        
        # Define simple schema: List of customer IDs
        customers = [{"customer_id": resource_name.split('/')[-1]} for resource_name in response.resource_names]

        return {
            "status": "success",
            "customers": customers,
            "message": "Pick one of these customer IDs in CUSTOMER_ID for the /campaigns endpoint"
        }
    
    except GoogleAdsException as ex:
        # Handle Google Ads API errors
        errors = [{"message": error.message} for error in ex.failure.errors]
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "details": errors
        })
    
    except Exception as e:
        # Handle general errors
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "details": str(e)
        })

# List campaigns for a given customer ID
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
@app.get('/campaigns/')
@app.get('/campaigns/{customer_id}')
async def get_campaigns(customer_id: str = CUSTOMER_ID):
    try:
        # Load Google Ads client from google-ads.yaml
        client = GoogleAdsClient.load_from_storage(path=str(CONFIG_PATH), version='v21')
        
        # Get Google Ads service
        ga_service = client.get_service('GoogleAdsService')
        
        # Simple query: Fetch campaign ID and name
        query = """
            SELECT campaign.id, campaign.name
            FROM campaign
            ORDER BY campaign.id
        """
        
        # Execute query in streaming mode
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        # Define simple schema: List of dicts with id and name
        campaigns = []
        for batch in stream:
            for row in batch.results:
                campaign_data = {
                    "id": row.campaign.id,
                    "name": row.campaign.name
                }
                campaigns.append(campaign_data)
        
        # Return data as JSON
        return {
            "status": "success",
            "campaigns": campaigns
        }
    
    except GoogleAdsException as ex:
        # Handle Google Ads API errors
        errors = [{"message": error.message} for error in ex.failure.errors]
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "details": errors
        })
    
    except Exception as e:
        # Handle general errors
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "details": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=4009, reload=True)