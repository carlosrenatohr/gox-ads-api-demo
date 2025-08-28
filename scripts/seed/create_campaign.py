# python -m scripts.seed.create_campaign
from google.ads.googleads.client import GoogleAdsClient
from dotenv import load_dotenv
from app.core.ads_client import get_google_ads_client, get_default_customer_id 

load_dotenv()

client = get_google_ads_client()
customer_id = get_default_customer_id()
print(f"Customer ID: {customer_id}")

campaign_service = client.get_service("CampaignService")

campaign_operation = client.get_type("CampaignOperation")
campaign = campaign_operation.create
campaign.name = "Test Campaign sandbox API"
campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
campaign.status = client.enums.CampaignStatusEnum.PAUSED
# campaign.manual_cpc.CopyFrom(client.get_type("ManualCpc"))
campaign.network_settings.target_google_search = True
campaign.network_settings.target_search_network = True
campaign.network_settings.target_content_network = False
campaign.network_settings.target_partner_search_network = False
campaign.start_date = "2025-09-01"
campaign.end_date = "2025-12-31"

response = campaign_service.mutate_campaigns(customer_id=customer_id, operations=[campaign_operation])

print("Created campaign:", response.results[0].resource_name)


if __name__ == "__main__":
    pass