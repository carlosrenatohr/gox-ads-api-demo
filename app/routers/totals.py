from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional, List, Any
from app.helpers.conversions import normalize_fields, pick_fields, run_gaql_stream
from app.core.ads_client import get_google_ads_client, get_default_customer_id
from google.ads.googleads.errors import GoogleAdsException

router = APIRouter(prefix="", tags=["Google Ads"])

# Customers totals
# GET /totals/customers
# GET /totals/customers/{customer_id}
# Returns:
# - status: success
# - rows: list of customers
# - selected_fields: list of selected fields
# - scope: customer
# ---
# Customers totals for the default customer ID
# GET /totals/customers
# Returns:
# - status: success
# - rows: list of customers
# - selected_fields: list of selected fields
# - scope: customer
# ---
@router.get("/totals/customers")
async def totals_customers(
    customer_id: Optional[str] = None,
    period: Optional[str] = Query(None, description="LAST_30_DAYS, LAST_7_DAYS, THIS_MONTH, LAST_MONTH, ALL_TIME"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = Query(
        None,
        description="List of GAQL fields separated by comma. Example: metrics.clicks,metrics.conversions,metrics.cost_micros,metrics.conversions_value"
    ),
):
    """
    Data RAW of aggregated metrics at customer level.
    Default: clicks, impressions, conversions, conversions_value, cost_micros.
    """
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()

    sel = normalize_fields(
        fields,
        [
            "metrics.clicks",
            "metrics.impressions",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
        ],
    )
    # date_clause = build_date_where(period, start_date, end_date)

    query = f"SELECT {', '.join(sel)} FROM customer"

    try:
        items: List[Dict[str, Any]] = []
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                items.append(pick_fields(row, sel))
        # customer-level usuall y returns 1 row (aggregated); we return list for consistency
        return {"status": "success", "rows": items, "selected_fields": sel, "scope": "customer"}
    except GoogleAdsException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})


# Campaigns totals
# GET /totals/campaigns
# GET /totals/campaigns/{customer_id}
# Returns:
# - status: success
# - rows: list of campaigns
# - selected_fields: list of selected fields
# - scope: campaign
# ---
# Campaigns totals for the default customer ID
# GET /totals/campaigns
# Returns:
# - status: success
# - rows: list of campaigns
# - selected_fields: list of selected fields
# - scope: campaign
# ---
@router.get("/totals/campaigns")
async def totals_campaigns(
    customer_id: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = Query(
        None,
        description="Example: campaign.id,campaign.name,metrics.clicks,metrics.impressions,metrics.conversions,metrics.cost_micros,metrics.conversions_value"
    ),
    where: Optional[str] = Query(None, description="Fragment WHERE additional. Example: campaign.status = 'ENABLED'"),
    order_by: Optional[str] = Query(None, description="Example: metrics.clicks DESC"),
    limit: int = 250
):
    """
    Filas RAW por campaña. Puedes pasar WHERE/ORDER/LIMIT.
    """
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()

    sel = normalize_fields(
        fields,
        [
            "campaign.id",
            "campaign.name",
            "metrics.clicks",
            "metrics.impressions",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
        ],
    )

    # For BETWEEN we need WHERE; if you use DURING no need WHERE
    # base_date = build_date_where(period, start_date, end_date, with_where=False)
    where_clause = ""
    if start_date and end_date:
        where_clause = f" WHERE segments.date BETWEEN '{start_date}' AND '{end_date}' "
    if where:
        where_clause += (" AND " if where_clause else " WHERE ") + where

    order_clause = f" ORDER BY {order_by} " if order_by else ""
    limit_clause = f" LIMIT {int(limit)} "

    query = f"""
      SELECT {', '.join(sel)}
      FROM campaign
      {where_clause}
      {order_clause}
      {limit_clause}
    """

    try:
        rows: List[Dict[str, Any]] = []
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                rows.append(pick_fields(row, sel))
        return {"status": "success", "rows": rows, "selected_fields": sel, "scope": "campaign"}
    except GoogleAdsException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})