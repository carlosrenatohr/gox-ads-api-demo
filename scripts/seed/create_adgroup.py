# python -m scripts.seed.create_adgroup
from app.core.ads_client import get_google_ads_client, get_default_customer_id 
from dotenv import load_dotenv

load_dotenv()

# ID: 22934523255, Name: GO Test Campaign, Status: ENABLED
def create_ad_group_for_campaign_id(campaign_id: str = "22934523255", ad_group_name: str = "Test Ad Group API"):
    client = get_google_ads_client()
    customer_id = get_default_customer_id()

    campaign_rn = client.get_service("CampaignService").campaign_path(customer_id, campaign_id)

    ad_group_service = client.get_service("AdGroupService")
    enums = client.enums

    op = client.get_type("AdGroupOperation")
    ad_group = op.create
    ad_group.name = ad_group_name
    ad_group.campaign = campaign_rn
    ad_group.status = enums.AdGroupStatusEnum.ENABLED
    ad_group.type_ = enums.AdGroupTypeEnum.SEARCH_STANDARD
    ad_group.cpc_bid_micros = 1_000_000

    resp = ad_group_service.mutate_ad_groups(customer_id=customer_id, operations=[op])
    print("Created ad group:", resp.results[0].resource_name)

if __name__ == "__main__":
    create_ad_group_for_campaign_id()