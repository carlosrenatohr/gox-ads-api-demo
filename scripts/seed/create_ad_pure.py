# DEPRECATED: use create_adgroup.py instead
# python -m scripts.seed.create_ad_pure
from app.core.ads_client import get_google_ads_client, get_default_customer_id 

from dotenv import load_dotenv

load_dotenv()

client = get_google_ads_client()
customer_id = get_default_customer_id()
print(f"Customer ID: {customer_id}")

def create_ad_pure(ad_group_response: AdGroup = None):
    ad_group_ad_service = client.get_service("AdGroupAdService")

    ad_group_ad_operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = ad_group_ad_operation.create
    ad_group_ad.ad_group = ad_group_response.results[0].resource_name
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

    ad = ad_group_ad.ad
    ad.final_urls.append("https://www.example.com") # TODO: add url from env
    ad.expanded_text_ad.headline_part1 = "API Test Headline"
    ad.expanded_text_ad.headline_part2 = "Buy Now!"
    ad.expanded_text_ad.description = "This is a test ad created via API."

    ad_group_ad_response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id, operations=[ad_group_ad_operation]
    )

    print("Created ad:", ad_group_ad_response.results[0].resource_name)

if __name__ == "__main__":
    create_ad_pure()
