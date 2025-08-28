# python -m scripts.seed.get_campaigns
from dotenv import load_dotenv
from app.core.ads_client import get_google_ads_client, get_default_customer_id 

load_dotenv()

def get_campaigns():
    client = get_google_ads_client()
    customer_id = get_default_customer_id()
    print(f"Customer ID: {customer_id}")

    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status
        FROM campaign
        ORDER BY campaign.id
    """
    results = ga_service.search(customer_id=customer_id, query=query)

    print("\n=== Campaigns ===")
    for row in results:
        print(f"ID: {row.campaign.id}, Name: {row.campaign.name}, Status: {row.campaign.status.name}")

if __name__ == "__main__":
    get_campaigns()