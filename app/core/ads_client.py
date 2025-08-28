from google.ads.googleads.client import GoogleAdsClient
from .config import get_env, resolve_from_root

def get_google_ads_client() -> GoogleAdsClient:
    config_rel = get_env("GOOGLE_ADS_CONFIG_FILE_PATH")
    config_path = resolve_from_root(config_rel)
    client = GoogleAdsClient.load_from_storage(path=str(config_path), version="v21")
    return client

def get_default_customer_id() -> str:
    return get_env("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
