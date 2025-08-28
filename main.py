from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

load_dotenv()

app = FastAPI(
    title="Google Ads API - FastAPI",
    description="API simple para obtener datos de Google Ads",
    version="1.0.0"
)

CUSTOMER_ID = '7228068139'  # GO test account 1

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas

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
        "version": "1.0.0",
        "message": "Service is running correctly"
    }

@app.get('/')
async def list_accessible_customers():
    try:
        # Load Google Ads client from google-ads.yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'google-ads.yaml')
        client = GoogleAdsClient.load_from_storage(path=config_path, version='v21')
        
        # Get CustomerService
        customer_service = client.get_service('CustomerService')
        
        # Call ListAccessibleCustomers to get all accessible customer IDs
        response = customer_service.list_accessible_customers()
        
        # Define simple schema: List of customer IDs
        customers = [{"customer_id": resource_name.split('/')[-1]} for resource_name in response.resource_names]
        
        # Return data as JSON
        return {
            "status": "success",
            "customers": customers,
            "message": "Use one of these customer IDs in CUSTOMER_ID for the /campaigns endpoint"
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=4007, reload=True)