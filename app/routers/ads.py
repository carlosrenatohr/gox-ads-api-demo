from fastapi import APIRouter, Depends, HTTPException, Query
from google.ads.googleads.client import GoogleAdsClient
from app.helpers.conversions import run_gaql_stream
from typing import Optional

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

# List traffic sources
# GET /traffic-sources
# GET /traffic-sources/{customer_id}
# Returns:
# - status: success
# - rows: list of traffic sources
# - scope: traffic_source
@router.get("/traffic-sources")
async def traffic_sources(
    customer_id: Optional[str] = None,
    period: Optional[str] = Query(None, description="LAST_30_DAYS, LAST_7_DAYS, THIS_MONTH, LAST_MONTH, ALL_TIME"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    List of distinct traffic sources (ad_network_type) with clicks.
    """
    try:
        client: GoogleAdsClient = get_google_ads_client()
        customer_id = customer_id or get_default_customer_id()
        # date_clause = _date_clause(period, start_date, end_date)

        query = f"""
          SELECT
            segments.ad_network_type,
            metrics.clicks
          FROM customer
        """

        seen = set()
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                if (row.metrics.clicks or 0) > 0 or (row.segments.ad_network_type is not None):
                    seen.add(row.segments.ad_network_type.name)

        return {"status": "success", "rows": sorted(seen), "scope": "traffic_sources"}
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})

# List conversion actions
# GET /conversion-actions
# Returns:
# - status: success
# - rows: list of conversion actions
# - scope: conversion_action
@router.get("/conversion-actions")
async def list_conversion_actions(
    customer_id: Optional[str] = None,
):
    client = get_google_ads_client()
    customer_id = customer_id or get_default_customer_id()

    query = """
      SELECT
        conversion_action.id,
        conversion_action.name,
        conversion_action.category,
        conversion_action.status,
        conversion_action.type,
        conversion_action.primary_for_goal
      FROM conversion_action
      ORDER BY conversion_action.name
    """

    rows = []
    try:
        for batch in run_gaql_stream(client, customer_id, query):
            for row in batch.results:
                rows.append({
                    "id": row.conversion_action.id,
                    "name": row.conversion_action.name,
                    "category": row.conversion_action.category.name,
                    "status": row.conversion_action.status.name,
                    "type": row.conversion_action.type.name,
                    "primary_for_goal": row.conversion_action.primary_for_goal,
            })
        return {"status": "success", "rows": rows, "scope": "conversion_action"}
    except Exception as e:
        raise HTTPException(500, detail={"status": "error", "details": str(e)})