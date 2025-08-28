from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional, List, Any
from app.helpers.conversions import normalize_fields, pick_fields, run_gaql_stream, micros_to_amount, safe_div
from app.core.ads_client import get_google_ads_client, get_default_customer_id
from google.ads.googleads.errors import GoogleAdsException

router = APIRouter(prefix="", tags=["Google Ads Totals"])

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
        # customer-level usually returns 1 row (aggregated); we return list for consistency
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
    Data RAW of aggregated metrics at campaign level.
    Default: clicks, impressions, conversions, conversions_value, cost_micros.
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

# Keywords totals
# GET /totals/keywords
# GET /totals/keywords/{customer_id}
# Returns:
# - status: success
# - rows: list of keywords
# - selected_fields: list of selected fields
# - scope: keyword_view
# ---
# Keywords totals for the default customer ID
# GET /totals/keywords
# Returns:
# - status: success
# - rows: list of keywords
# - selected_fields: list of selected fields
# - scope: keyword_view
@router.get("/totals/keywords")
async def totals_keywords(
    customer_id: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = Query(
        None,
        description="Example: ad_group.id,ad_group.name,ad_group_criterion.keyword.text,metrics.clicks,metrics.conversions,metrics.cost_micros"
    ),
    where: Optional[str] = Query(None, description="Example: ad_group_criterion.status = 'ENABLED'"),
    order_by: Optional[str] = Query(None, description="Example: metrics.clicks DESC"),
    limit: int = 500
):
    """
    Data RAW of aggregated metrics at keyword level.
    Default: clicks, impressions, conversions, conversions_value, cost_micros.
    """
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()

    sel = normalize_fields(
        fields,
        [
            "ad_group.id",
            "ad_group.name",
            "ad_group_criterion.keyword.text",
            "metrics.clicks",
            "metrics.impressions",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
        ],
    )

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
      FROM keyword_view
      {where_clause}
      {order_clause}
      {limit_clause}
    """

    try:
        rows: List[Dict[str, Any]] = []
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                rows.append(pick_fields(row, sel))
        return {"status": "success", "rows": rows, "selected_fields": sel, "scope": "keyword_view"}
    except GoogleAdsException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})

# Search terms totals
# GET /totals/search-terms
# GET /totals/search-terms/{customer_id}
# Returns:
# - status: success
# - rows: list of search terms
# - selected_fields: list of selected fields
# - scope: search_term_view
# ---
# Search terms totals for the default customer ID
# GET /totals/search-terms
# Returns:
# - status: success
# - rows: list of search terms
# - selected_fields: list of selected fields
# - scope: search_term_view
@router.get("/totals/search-terms")
async def totals_search_terms(
    customer_id: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = Query(
        None,
        description="Example: segments.search_term,metrics.clicks,metrics.conversions,metrics.cost_micros"
    ),
    where: Optional[str] = None,
    order_by: Optional[str] = "metrics.clicks DESC",
    limit: int = 500
):
    """
    Data RAW of aggregated metrics at search term level.
    Default: clicks, impressions, conversions, conversions_value, cost_micros.
    """
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()

    sel = normalize_fields(
        fields,
        [
            "search_term_view.search_term",
            # "segments.date",
            "metrics.clicks",
            "metrics.impressions",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
        ],
    )

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
      FROM search_term_view
      {order_clause}
      {limit_clause}
    """

    try:
        rows: List[Dict[str, Any]] = []
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                rows.append(pick_fields(row, sel))
        return {"status": "success", "rows": rows, "selected_fields": sel, "scope": "search_term_view"}
    except GoogleAdsException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})

# Traffic sources totals
# GET /totals/traffic-sources
# GET /totals/traffic-sources/{customer_id}
# Returns:
# - status: success
# - items: list of traffic sources
# - message: instructions to pick one of the traffic sources
# ---
# Traffic sources totals for the default customer ID
# GET /totals/traffic-sources
# Returns:
# - status: success
# - items: list of traffic sources
# - message: instructions to pick one of the traffic sources
@router.get("/totals/traffic-sources")
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
        metrics.impressions,
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
        return {"status": "success", "rows": items, "scope": "traffic_source", "selected_fields": ["segments.ad_network_type", "metrics.clicks", "metrics.conversions", "metrics.conversions_value", "metrics.cost_micros"]}
    except GoogleAdsException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})