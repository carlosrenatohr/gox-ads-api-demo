from fastapi import APIRouter, HTTPException    
from typing import Optional
from app.core.ads_client import get_google_ads_client, get_default_customer_id
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from app.helpers.conversions import run_gaql_stream, micros_to_amount, safe_div

router = APIRouter(prefix="", tags=["Google Ads Sales"])

@router.get("/sales/campaigns")
async def sales_per_campaign(
    customer_id: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 250,
):
    """
    Sales by campaign.
    """
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()

    # if period:
    #     date_clause = f" DURING {period} "
    # elif start_date and end_date:
    #     date_clause = f" WHERE segments.date BETWEEN '{start_date}' AND '{end_date}' "
    # else:
    #     date_clause = " DURING LAST_30_DAYS "

    query = f"""
      SELECT
        campaign.id,
        campaign.name,
        metrics.conversions,
        metrics.conversions_value,
        metrics.cost_micros
      FROM campaign
      WHERE campaign.status = 'ENABLED'
      ORDER BY metrics.conversions_value DESC
      LIMIT {limit}
    """

    try:
        rows = []
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                cost = micros_to_amount(row.metrics.cost_micros)
                roas = safe_div(row.metrics.conversions_value, cost) if cost > 0 else None
                rows.append({
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value,
                    "cost_micros": row.metrics.cost_micros,
                    "cost": cost,
                    "roas": roas,
                })
        return {"status": "success", "rows": rows, "scope": "sales_per_campaign"}
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})