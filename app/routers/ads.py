from fastapi import APIRouter, Depends, HTTPException, Query
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from app.helpers.conversions import micros_to_amount, safe_div, run_gaql_stream, normalize_fields, pick_fields
from typing import Dict, Optional, List, Any

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


# Traffic sources
# GET /traffic-sources
# GET /traffic-sources/{customer_id}
# Returns:
# - status: success
# - items: list of traffic sources
# - message: instructions to pick one of the traffic sources
# ---
# Traffic sources for the default customer ID
# GET /traffic-sources
# Returns:
# - status: success
# - items: list of traffic sources
# - message: instructions to pick one of the traffic sources
@router.get("/traffic-sources")
async def traffic_sources(
    customer_id: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Data RAW of aggregated metrics at traffic source level.
    Default: clicks, impressions, conversions, conversions_value, cost_micros.
    """
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()
    # date_clause = build_date_where(period, start_date, end_date)

    # TODO: add date clause
    # where_clause = ""
    # if start_date and end_date:
    #     where_clause = f" WHERE segments.date BETWEEN '{start_date}' AND '{end_date}' "
    
    query = f"""
      SELECT
        segments.ad_network_type,
        metrics.clicks,
        metrics.conversions,
        metrics.conversions_value,
        metrics.cost_micros
      FROM customer
    """

    # Sum by ad_network_type
    agg: Dict[str, Dict[str, float]] = {}
    try:
        for batch in run_gaql_stream(client, customer_id, query):
            for r in batch.results:
                k = r.segments.ad_network_type.name  # enum -> string
                if k not in agg:
                    agg[k] = {"clicks": 0, "conversions": 0.0, "value": 0.0, "cost_micros": 0}
                agg[k]["clicks"] += r.metrics.clicks or 0
                agg[k]["conversions"] += r.metrics.conversions or 0.0
                agg[k]["value"] += r.metrics.conversions_value or 0.0
                agg[k]["cost_micros"] += r.metrics.cost_micros or 0

        items = []
        for k, v in agg.items():
            cost = micros_to_amount(v["cost_micros"])
            conv_rate = safe_div(v["conversions"], v["clicks"]) * 100
            cac = safe_div(cost, v["conversions"]) if v["conversions"] else 0.0
            roas = safe_div(v["value"], cost)
            items.append({
                "source": k,  # Google Search, Search Partners, Display, YouTube, etc.
                "clicks": int(v["clicks"]),
                "leads": v["conversions"],
                "sales": None,
                "conv_rate_pct": round(conv_rate, 2),
                "cac": round(cac, 2),
                "spend": cost,
                "revenue": v["value"],
                "roas": roas
            })
        # Sort by clicks descending
        items.sort(key=lambda x: x["clicks"], reverse=True)
        return {"status": "success", "items": items}
    except GoogleAdsException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})
